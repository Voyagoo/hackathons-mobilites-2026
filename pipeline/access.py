"""Step 4: jobs reachable per commune, and how equal that access is across residents.

For each commune i, scenario and threshold T:

    jobs_reachable(i, T) = sum of jobs_j over communes j with travel_time(i, j) <= T

Equality is measured across **employed residents**: each commune counts as many times as it
has employed residents. The question is about people, not about communes.

Outputs:
    data/processed/access.parquet          one row per commune x scenario x threshold
    data/processed/access_summary.parquet  P10/median/P90, P90/P10, Gini, share below half the
                                           median, for the whole region and each department

Run: uv run python -m pipeline.access [--sample 20]
"""

import argparse

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.config import (
    ACCESS_PARQUET,
    COMMUNES_PARQUET,
    SCENARIOS,
    SUMMARY_PARQUET,
    THRESHOLDS_MIN,
    TTM_DIR,
)


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum = (np.cumsum(w) - 0.5 * w) / w.sum()  # midpoint rule, so q=0.5 is the weighted median
    return float(np.interp(q, cum, v))


def weighted_gini(values: np.ndarray, weights: np.ndarray) -> float:
    """Gini coefficient of `values` across a population where each value has weight `weights`."""
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cum_w = np.cumsum(w) / w.sum()
    cum_vw = np.cumsum(v * w) / (v * w).sum()
    # Area under the Lorenz curve with the trapezoid rule.
    lorenz_area = np.sum((cum_w - np.concatenate([[0], cum_w[:-1]])) *
                         (cum_vw + np.concatenate([[0], cum_vw[:-1]])) / 2)
    return max(0.0, float(1 - 2 * lorenz_area))  # clip float noise when all values are equal


def jobs_reachable(ttm: pd.DataFrame, communes: pd.DataFrame) -> pd.DataFrame:
    """Cumulative opportunities for every origin and threshold."""
    codes = communes["code"].to_numpy()
    index = {c: k for k, c in enumerate(codes)}
    jobs = communes["jobs"].to_numpy()

    origins = ttm["from_id"].map(index).to_numpy()
    dests = ttm["to_id"].map(index).to_numpy()
    times = ttm["travel_time"].to_numpy(dtype="float64", na_value=np.nan)

    result = {"code": codes}
    for t in THRESHOLDS_MIN:
        ok = times <= t  # NaN (unreachable) compares False
        result[f"jobs_{t}"] = np.bincount(origins[ok], weights=jobs[dests[ok]], minlength=len(codes))
    return pd.DataFrame(result)


def summarise(values: np.ndarray, weights: np.ndarray) -> dict:
    p10, p50, p90 = (weighted_quantile(values, weights, q) for q in (0.1, 0.5, 0.9))
    return {
        "p10": p10,
        "median": p50,
        "p90": p90,
        "p90_p10": p90 / p10 if p10 > 0 else np.nan,
        "gini": weighted_gini(values, weights),
        "share_below_half_median": float(weights[values < 0.5 * p50].sum() / weights.sum()),
        "residents": float(weights.sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, help="use the smoke-test matrices from step 3 --limit N")
    args = parser.parse_args()
    suffix = f"_sample{args.sample}" if args.sample else ""

    communes = gpd.read_parquet(COMMUNES_PARQUET).drop(columns="geometry")

    access_rows, summary_rows = [], []
    for s in SCENARIOS:
        path = TTM_DIR / f"{s.name}{suffix}.parquet"
        if not path.exists():
            print(f"skip {s.name}: {path.name} not found")
            continue

        ttm = pd.read_parquet(path)
        subset = communes[communes["code"].isin(ttm["from_id"])].reset_index(drop=True)
        acc = jobs_reachable(ttm, subset).merge(subset[["code", "dept", "residents"]], on="code")

        for t in THRESHOLDS_MIN:
            long = acc[["code", f"jobs_{t}"]].rename(columns={f"jobs_{t}": "jobs_reachable"})
            long = long.assign(scenario=s.name, mode=s.mode, threshold=t,
                               share_of_region_jobs=long["jobs_reachable"] / communes["jobs"].sum())
            access_rows.append(long)

            groups = [("Île-de-France", acc)] + [(f"dept {d}", g) for d, g in acc.groupby("dept")]
            for scope, g in groups:
                stats = summarise(g[f"jobs_{t}"].to_numpy(), g["residents"].to_numpy())
                summary_rows.append({"scenario": s.name, "mode": s.mode, "label": s.label,
                                     "threshold": t, "scope": scope, **stats})
        print(f"{s.name}: access computed for {len(acc):,} communes")

    if not access_rows:
        raise FileNotFoundError(f"no travel-time matrices in {TTM_DIR}: run step 3 first")

    access = pd.concat(access_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)

    # Transit-to-car ratio for the same commune and threshold (peak transit vs free-flow car).
    pivot = access.pivot_table(index=["code", "threshold"], columns="scenario", values="jobs_reachable")
    if {"transit_tue_0830", "car_tue_0830"} <= set(pivot.columns):
        ratio = (pivot["transit_tue_0830"] / pivot["car_tue_0830"]).rename("transit_car_ratio").reset_index()
        access = access.merge(ratio, on=["code", "threshold"], how="left")

    access_out = ACCESS_PARQUET.with_name(ACCESS_PARQUET.stem + suffix + ".parquet")
    summary_out = SUMMARY_PARQUET.with_name(SUMMARY_PARQUET.stem + suffix + ".parquet")
    access.to_parquet(access_out, index=False)
    summary.to_parquet(summary_out, index=False)

    region = summary[summary["scope"] == "Île-de-France"]
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 160):
        print(region[["scenario", "threshold", "p10", "median", "p90", "p90_p10", "gini",
                      "share_below_half_median"]].to_string(index=False))
    print(f"wrote {access_out.name} and {summary_out.name}")


if __name__ == "__main__":
    main()

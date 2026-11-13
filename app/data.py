"""Load the pipeline outputs once and serve small views of them to the Dash callbacks."""

import functools
import json

import geopandas as gpd
import numpy as np
import pandas as pd

from pipeline.config import (
    ACCESS_PARQUET,
    COMMUNES_PARQUET,
    SCENARIOS,
    SUMMARY_PARQUET,
    TTM_DIR,
)
from utils.loaders import PROCESSED_DIR

DEPT_NAMES = {
    "75": "Paris",
    "77": "Seine-et-Marne",
    "78": "Yvelines",
    "91": "Essonne",
    "92": "Hauts-de-Seine",
    "93": "Seine-Saint-Denis",
    "94": "Val-de-Marne",
    "95": "Val-d'Oise",
}
SCENARIO_LABELS = {s.name: s.label for s in SCENARIOS}
PEAK_TRANSIT = "transit_tue_0830"
CAR = "car_tue_0830"
# Display order: the car benchmark first, then transit through the day, then Saturday.
SCENARIO_ORDER = [CAR, "transit_tue_0500", PEAK_TRANSIT, "transit_tue_1200", "transit_tue_2230", "transit_sat_0830"]
# Short labels for the time-of-day control (transit only; free-flow car times ignore the clock).
TIME_LABELS = {
    "transit_tue_0500": "05:00 early shift",
    PEAK_TRANSIT: "08:30 peak",
    "transit_tue_1200": "12:00 midday",
    "transit_tue_2230": "22:30 late shift",
    "transit_sat_0830": "Saturday 08:30",
}


def scenario_for(mode: str, time_slot: str) -> str:
    return CAR if mode == "car" else time_slot

# Classes of "share of regional jobs reachable", shared by map 1 and the residents chart.
# Uneven widths on purpose: most of the territory sits below 5%, where small differences matter.
BAND_EDGES = [0, 0.01, 0.05, 0.20, 0.50, 1.01]
BANDS = ["under 1% of jobs", "1 to 5%", "5 to 20%", "20 to 50%", "over 50%"]


def band_of(share: pd.Series) -> pd.Series:
    return pd.cut(share, BAND_EDGES, labels=BANDS, right=False)


def missing_outputs() -> list[str]:
    """Pipeline outputs the app needs but cannot find."""
    return [p.name for p in (COMMUNES_PARQUET, ACCESS_PARQUET, SUMMARY_PARQUET) if not p.exists()]


@functools.cache
def communes() -> pd.DataFrame:
    df = gpd.read_parquet(COMMUNES_PARQUET).drop(columns="geometry")
    df["dept_name"] = df["dept"].map(DEPT_NAMES)
    return df


def default_origin() -> str:
    """Area shown in the commune explorer before any click: the one with the most jobs."""
    return communes().nlargest(1, "jobs")["code"].iloc[0]


def paris_is_split() -> bool:
    return communes()["code"].str.match(r"^751\d\d$").any()


@functools.cache
def geojson() -> dict:
    """Commune polygons, simplified (~50 m) to keep the page light. Feature id = commune code."""
    gdf = gpd.read_parquet(COMMUNES_PARQUET)[["code", "geometry"]]
    gdf["geometry"] = gdf.to_crs(2154).geometry.simplify(50).to_crs(4326)
    return json.loads(gdf.set_index("code").to_json())


@functools.cache
def dept_outlines() -> tuple[list, list]:
    """Department boundaries as one polyline (lon, lat lists separated by None), for orientation."""
    gdf = gpd.read_parquet(COMMUNES_PARQUET)[["dept", "geometry"]]
    depts = gdf.to_crs(2154).dissolve("dept").geometry.simplify(100).to_crs(4326)
    lon, lat = [], []
    for boundary in depts.boundary:
        lines = getattr(boundary, "geoms", [boundary])
        for line in lines:
            xs, ys = line.xy
            lon += [*xs, None]
            lat += [*ys, None]
    return lon, lat


@functools.cache
def access() -> pd.DataFrame:
    return pd.read_parquet(ACCESS_PARQUET)


@functools.cache
def summary() -> pd.DataFrame:
    return pd.read_parquet(SUMMARY_PARQUET)


def available_scenarios() -> list[str]:
    present = set(access()["scenario"])
    return [s.name for s in SCENARIOS if s.name in present]


def access_view(scenario: str, threshold: int) -> pd.DataFrame:
    a = access()
    view = a[(a["scenario"] == scenario) & (a["threshold"] == threshold)]
    return communes().merge(view, on="code", how="inner")


def region_stats(scenario: str, threshold: int) -> pd.Series:
    s = summary()
    row = s[(s["scenario"] == scenario) & (s["threshold"] == threshold) & (s["scope"] == "Île-de-France")]
    return row.iloc[0]


def dept_stats(scenario: str, threshold: int) -> pd.DataFrame:
    s = summary()
    rows = s[(s["scenario"] == scenario) & (s["threshold"] == threshold) & (s["scope"].str.startswith("dept"))].copy()
    rows["dept"] = rows["scope"].str.removeprefix("dept ")
    rows["dept_name"] = rows["dept"].map(DEPT_NAMES)
    return rows.sort_values("median")


def residents_by_band(threshold: int) -> pd.DataFrame:
    """% of employed residents per band of jobs reachable, for every scenario at this threshold."""
    a = access()
    a = a[a["threshold"] == threshold].merge(communes()[["code", "residents"]], on="code")
    a["band"] = band_of(a["share_of_region_jobs"])
    out = a.groupby(["scenario", "band"], observed=False)["residents"].sum().reset_index()
    out["pct_residents"] = 100 * out["residents"] / out.groupby("scenario")["residents"].transform("sum")
    return out


def income_quintiles(threshold: int, scenarios: list[str]) -> pd.DataFrame:
    """Mean jobs reachable per employed resident, by income quintile of the home commune.

    Quintiles split employed residents (not communes) into five equal groups by the
    median income of their commune. Communes without income data are left out.
    """
    com = communes().dropna(subset=["median_income"]).sort_values("median_income")
    cum = com["residents"].cumsum() / com["residents"].sum()
    com = com.assign(quintile=np.minimum((cum.to_numpy() * 5 - 1e-9).astype(int) + 1, 5))

    a = access()
    a = a[(a["threshold"] == threshold) & (a["scenario"].isin(scenarios))]
    df = a.merge(com[["code", "residents", "quintile"]], on="code")
    df["weighted"] = df["jobs_reachable"] * df["residents"]
    out = df.groupby(["scenario", "quintile"])[["weighted", "residents"]].sum()
    out["mean_jobs"] = out["weighted"] / out["residents"]
    out = out.reset_index()
    out["scenario_label"] = out["scenario"].map(SCENARIO_LABELS)
    out["quintile_label"] = out["quintile"].map(
        {1: "Q1 (poorest)", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 (richest)"}
    )
    return out


@functools.cache
def travel_times(scenario: str) -> pd.DataFrame:
    return pd.read_parquet(TTM_DIR / f"{scenario}.parquet")


def travel_times_from(scenario: str, origin: str) -> pd.DataFrame:
    ttm = travel_times(scenario)
    view = ttm[ttm["from_id"] == origin].rename(columns={"to_id": "code"})
    return communes().merge(view[["code", "travel_time"]], on="code", how="left")


# --- Phase 2: helpers for the workspace views --------------------------------

LOW_ACCESS = 0.05  # "very low access": under 5% of the region's jobs
SHORT_LABELS = {
    CAR: "Car · free-flow",
    "transit_tue_0500": "Tue 05:00",
    PEAK_TRANSIT: "Tue 08:30",
    "transit_tue_1200": "Tue 12:00",
    "transit_tue_2230": "Tue 22:30",
    "transit_sat_0830": "Sat 08:30",
}
WEEKDAY_SLOTS = ["transit_tue_0500", PEAK_TRANSIT, "transit_tue_1200", "transit_tue_2230"]
SATURDAY_SLOT = "transit_sat_0830"


@functools.cache
def total_jobs() -> float:
    return float(communes()["jobs"].sum())


@functools.cache
def _wide() -> pd.DataFrame:
    """One row per commune, one column per (scenario, threshold): share of regional jobs reachable."""
    return access().pivot_table(index="code", columns=["scenario", "threshold"], values="share_of_region_jobs")


def share(scenario: str, threshold: int) -> pd.Series:
    return _wide()[(scenario, threshold)]


@functools.cache
def low_access_shares(threshold: int) -> dict[str, float]:
    """% of employed residents living where under 5% of regional jobs are reachable, per scenario."""
    residents = communes().set_index("code")["residents"]
    out = {}
    for scenario in available_scenarios():
        s = share(scenario, threshold)
        out[scenario] = float(100 * residents[s.index[s < LOW_ACCESS]].sum() / residents[s.index].sum())
    return out


@functools.cache
def no_route_origins(scenario: str) -> frozenset:
    """Origins from which the router found no destination other than the origin itself (within 90 min).

    The matrices store "no route" and "over 90 minutes" the same way (empty), so this is the
    only case that can be told apart: nothing at all is reachable from the routing point.
    """
    ttm = travel_times(scenario)
    reached = ttm[ttm["travel_time"].notna()].groupby("from_id").size()
    return frozenset(reached.index[reached <= 1])


def weighted_percentile(scenario: str, threshold: int, code: str) -> float:
    """% of employed residents who live in a commune with lower access than this one."""
    s = share(scenario, threshold)
    residents = communes().set_index("code")["residents"].reindex(s.index)
    return float(100 * residents[s < s[code]].sum() / residents.sum())


def commune_profile(code: str, scenario: str, threshold: int) -> dict:
    """Everything the commune panel shows, for one commune and the selected scenario."""
    row = communes().set_index("code").loc[code]
    scenarios = available_scenarios()
    by_scenario = {s: float(share(s, threshold)[code]) for s in scenarios}
    transit_ref = scenario if scenario != CAR else PEAK_TRANSIT
    return {
        "code": code,
        "name": row["name"],
        "dept": row["dept"],
        "dept_name": DEPT_NAMES.get(row["dept"], row["dept"]),
        "residents": float(row["residents"]),
        "jobs_here": float(row["jobs"]),
        "median_income": row["median_income"],
        "anchor_stop": row.get("anchor_stop"),
        "share": by_scenario[scenario],
        "jobs_reachable": by_scenario[scenario] * total_jobs(),
        "transit_share": by_scenario.get(transit_ref),
        "transit_ref": transit_ref,
        "car_share": by_scenario.get(CAR),
        "by_scenario": by_scenario,
        "by_budget": {t: float(share(scenario, t)[code]) for t in sorted(access()["threshold"].unique())},
        "percentile": weighted_percentile(scenario, threshold, code),
        "region_median": float(region_stats(scenario, threshold)["median"] / total_jobs()),
        "no_route": scenario != CAR and code in no_route_origins(scenario),
    }


def region_profile(threshold: int) -> dict[str, float]:
    """Median employed resident's share of regional jobs reachable, per scenario."""
    return {s: float(region_stats(s, threshold)["median"] / total_jobs()) for s in available_scenarios()}


# Map metrics. Each has class edges, class labels and a palette name (see figures.PALETTES).
SHARE_EDGES = [0, 0.001, 0.005, 0.01, 0.03, 0.10, 0.25, 1.01]
METRICS = {
    "share": {
        "label": "Share of regional jobs reachable",
        "legend": "Share of the region's jobs reachable",
        "edges": SHARE_EDGES,
        "labels": ["under 0.1%", "0.1–0.5%", "0.5–1%", "1–3%", "3–10%", "10–25%", "25% or more"],
        "ticks": ["0.1%", "0.5%", "1%", "3%", "10%", "25%"],
        "palette": "teal",
    },
    "jobs": {
        "label": "Number of jobs reachable",
        "legend": "Jobs reachable",
        "edges": [0, 6_000, 30_000, 60_000, 180_000, 600_000, 1_500_000, 1e9],
        "labels": ["under 6,000", "6,000–30,000", "30,000–60,000", "60,000–180,000", "180,000–600,000",
                   "600,000–1.5 million", "1.5 million or more"],
        "ticks": ["6k", "30k", "60k", "180k", "600k", "1.5M"],
        "palette": "teal",
    },
    "ratio": {
        "label": "Public transport vs car (free-flow)",
        "legend": "Jobs reachable by public transport,\nas a share of jobs reachable by car",
        "edges": [0, 0.02, 0.05, 0.10, 0.25, 0.50, 0.75, 1e9],
        "labels": ["under 2% of car access", "2–5%", "5–10%", "10–25%", "25–50%", "50–75%", "75% or more"],
        "ticks": ["2%", "5%", "10%", "25%", "50%", "75%"],
        "palette": "teal",
    },
    "gain": {
        "label": "Gain from 30 to 60 minutes",
        "legend": "Extra share of regional jobs reachable\nwith 60 minutes instead of 30",
        "edges": [0, 0.005, 0.01, 0.03, 0.10, 0.25, 0.50, 1.01],
        "labels": ["under 0.5 points", "0.5–1", "1–3", "3–10", "10–25", "25–50", "50 points or more"],
        "ticks": ["0.5", "1", "3", "10", "25", "50 pts"],
        "palette": "teal",
    },
    "change": {
        "label": "Change vs weekday peak (08:30)",
        "legend": "Jobs reachable, selected scenario minus\nTue 08:30 (percentage points of regional jobs)",
        "edges": [-1.01, -0.10, -0.03, -0.01, -0.002, 0.002, 0.01, 1.01],
        "labels": ["loss over 10 points", "−10 to −3", "−3 to −1", "−1 to −0.2", "about the same",
                   "+0.2 to +1", "gain over 1 point"],
        "ticks": ["−10", "−3", "−1", "−0.2", "+0.2", "+1 pts"],
        "palette": "diverging",
    },
    "affected": {
        "label": "Residents in low-access communes",
        "legend": "Employed residents in communes\nreaching under 5% of regional jobs",
        "edges": [0, 250, 1_000, 2_500, 5_000, 10_000, 20_000, 1e9],
        "labels": ["under 250", "250–1,000", "1,000–2,500", "2,500–5,000", "5,000–10,000", "10,000–20,000",
                   "20,000 or more"],
        "ticks": ["250", "1k", "2.5k", "5k", "10k", "20k"],
        "palette": "warm",
    },
}
NO_ROUTE_LABEL = "No route found within 90 min"
NOT_LOW_LABEL = "5% of jobs or more (not counted)"


def metric_frame(metric: str, scenario: str, time_slot: str, threshold: int) -> pd.DataFrame:
    """Commune table with the metric value and its class label (`cls`), ready for the map.

    `scenario` is the selected mode/time; `time_slot` is the selected transit slot, which the
    transit-vs-car ratio uses even when the car is the selected mode.
    """
    spec = METRICS[metric]
    df = communes().copy()
    s = share(scenario, threshold).reindex(df["code"]).to_numpy()
    df["share"] = s
    df["jobs_reachable"] = s * total_jobs()

    if metric == "share":
        df["value"] = s
    elif metric == "jobs":
        df["value"] = df["jobs_reachable"]
    elif metric == "ratio":
        transit = share(time_slot, threshold).reindex(df["code"]).to_numpy()
        car = share(CAR, threshold).reindex(df["code"]).to_numpy()
        df["value"] = np.divide(transit, car, out=np.full_like(transit, np.nan), where=car > 0)
    elif metric == "gain":
        df["value"] = (share(scenario, 60) - share(scenario, 30)).reindex(df["code"]).to_numpy()
    elif metric == "change":
        df["value"] = s - share(PEAK_TRANSIT, threshold).reindex(df["code"]).to_numpy()
    elif metric == "affected":
        df["value"] = df["residents"].where(s < LOW_ACCESS)
    else:
        raise KeyError(metric)

    cls = pd.cut(df["value"], spec["edges"], labels=spec["labels"], right=False).astype(object)
    if metric == "affected":
        cls = cls.where(df["value"].notna(), NOT_LOW_LABEL)
    routed = scenario if metric != "ratio" else time_slot
    if routed != CAR and metric != "affected":
        cls = cls.where(~df["code"].isin(no_route_origins(routed)), NO_ROUTE_LABEL)
    df["cls"] = cls
    return df


def reach_curve(scenario: str, origin: str) -> pd.DataFrame:
    """Cumulative share of regional jobs reachable from `origin`, by travel time (minutes, 0 to 90)."""
    df = travel_times_from(scenario, origin).dropna(subset=["travel_time"]).sort_values("travel_time")
    by_minute = df.groupby("travel_time")["jobs"].sum().cumsum() / total_jobs()
    minutes = pd.RangeIndex(0, 91)
    return pd.DataFrame({"minutes": minutes, "share": by_minute.reindex(minutes).ffill().fillna(0).to_numpy()})


def priorities(scenario: str, threshold: int, limit: int = 60) -> pd.DataFrame:
    """Communes under 5% of regional jobs at the selected scenario, ranked by employed residents.

    A plain ranking on one stated metric, not a composite score. The other columns give context.
    """
    df = communes()[["code", "name", "dept", "residents", "median_income"]].copy()
    df["share"] = share(scenario, threshold).reindex(df["code"]).to_numpy()
    df["car_share"] = share(CAR, threshold).reindex(df["code"]).to_numpy()
    df["peak_share"] = share(PEAK_TRANSIT, threshold).reindex(df["code"]).to_numpy()
    df["early_share"] = share("transit_tue_0500", threshold).reindex(df["code"]).to_numpy()
    df["dept_name"] = df["dept"].map(DEPT_NAMES)
    df = df[df["share"] < LOW_ACCESS].sort_values("residents", ascending=False)
    df["rank"] = range(1, len(df) + 1)
    return df.head(limit)


@functools.cache
def bounds() -> tuple[float, float, float, float]:
    """Geographic extent of the region: (west, south, east, north) in degrees."""
    west, south, east, north = gpd.read_parquet(COMMUNES_PARQUET).total_bounds
    return float(west), float(south), float(east), float(north)


def dept_labels() -> pd.DataFrame:
    """One label point per department (inside its outline), for map orientation."""
    return _dept_label_points()


@functools.cache
def _dept_label_points() -> pd.DataFrame:
    gdf = gpd.read_parquet(COMMUNES_PARQUET)[["dept", "geometry"]]
    depts = gdf.to_crs(2154).dissolve("dept").geometry.representative_point().to_crs(4326)
    return pd.DataFrame({"dept": depts.index, "name": [DEPT_NAMES.get(d, d) for d in depts.index],
                         "lon": depts.x.to_numpy(), "lat": depts.y.to_numpy()})


# Towns labelled on the map for orientation: (commune name, label position relative to its dot).
TOWNS = {
    "Paris 4e": ("PARIS", "middle center"), "Versailles": (None, "middle left"), "Cergy": (None, "top center"),
    "Mantes-la-Jolie": (None, "top center"), "Rambouillet": (None, "bottom center"),
    "Étampes": (None, "bottom center"), "Évry-Courcouronnes": ("Évry", "middle right"),
    "Melun": (None, "middle right"), "Fontainebleau": (None, "bottom center"), "Provins": (None, "top center"),
    "Meaux": (None, "top center"), "Roissy-en-France": ("Roissy CDG", "top center"),
    "Nemours": (None, "bottom center"),
    "Coulommiers": (None, "middle right"),
}


@functools.cache
def town_labels() -> pd.DataFrame:
    """Curated reference towns for the regional view."""
    com = communes().set_index("name")
    rows = [{"code": com.loc[name, "code"], "name": label or name, "lon": com.loc[name, "lon"],
             "lat": com.loc[name, "lat"], "position": pos}
            for name, (label, pos) in TOWNS.items() if name in com.index]
    return pd.DataFrame(rows)


def labels_in(bounds: tuple[float, float, float, float], limit: int = 16) -> pd.DataFrame:
    """Labels for a zoomed view: the communes inside the bounds with the most jobs, without collisions.

    Communes are taken in order of jobs; one is skipped when it sits too close to a label already
    kept (closer than about 13% of the view width, or 5% of its height).
    """
    west, south, east, north = bounds
    com = communes()
    inside = com[com["lon"].between(west, east) & com["lat"].between(south, north)].sort_values("jobs", ascending=False)
    min_dx, min_dy = 0.13 * (east - west), 0.05 * (north - south)
    kept = []
    for _, row in inside.iterrows():
        if all(abs(row["lon"] - k["lon"]) > min_dx or abs(row["lat"] - k["lat"]) > min_dy for k in kept):
            kept.append({"code": row["code"], "name": row["name"], "lon": row["lon"], "lat": row["lat"],
                         "position": "middle center"})
        if len(kept) == limit:
            break
    return pd.DataFrame(kept, columns=["code", "name", "lon", "lat", "position"])


INNER_RING = ("75", "92", "93", "94")  # Paris and the petite couronne


@functools.cache
def _geometry() -> gpd.GeoDataFrame:
    return gpd.read_parquet(COMMUNES_PARQUET)[["code", "dept", "geometry"]].set_index("code")


def focus_view(focus: str, commune: str | None) -> dict:
    """Map extent and labels for a zoom preset: "region", "paris" (inner ring) or "selection"."""
    geo = _geometry()
    if focus == "paris":
        west, south, east, north = geo[geo["dept"].isin(INNER_RING)].total_bounds
    elif focus == "selection" and commune in geo.index:
        west, south, east, north = geo.loc[[commune]].total_bounds
        # Show the commune with its surroundings: at least about 20 km across.
        cx, cy = (west + east) / 2, (south + north) / 2
        half_x, half_y = max((east - west) * 1.5, 0.14), max((north - south) * 1.5, 0.09)
        west, east, south, north = cx - half_x, cx + half_x, cy - half_y, cy + half_y
    else:
        focus = "region"
        west, south, east, north = bounds()
    if focus != "region":
        # Widen the box to the shape of the map card (wider than tall, once the margins for the buttons and legend are counted), so the zoomed map fills it
        # instead of showing as a narrow strip. Longitude degrees are shorter than latitude degrees.
        height = (north - south) / np.cos(np.radians((south + north) / 2))
        extra = max(0.0, 1.75 * height - (east - west)) / 2
        west, east = west - extra, east + extra
    box = (float(west), float(south), float(east), float(north))
    labels = town_labels() if focus == "region" else labels_in(box)
    return {"focus": focus, "bounds": box, "labels": labels, "key": f"{focus}-{commune if focus == 'selection' else ''}"}


RAIL_GEOJSON = PROCESSED_DIR / "rail_lines.geojson"  # built by pipeline/extra_rail_lines.py (optional)


def has_rail() -> bool:
    return RAIL_GEOJSON.exists()


@functools.cache
def rail_lines() -> dict[str, tuple[list, list]]:
    """Rail overlay as polylines per group: "rail" (RER and Transilien) and "urban" (metro and tram).

    Each value is (lon, lat) with None between line pieces. Real geometry from the IDFM GTFS shapes.
    """
    out = {"rail": ([], []), "urban": ([], [])}
    if not has_rail():
        return out
    lines = gpd.read_file(RAIL_GEOJSON)
    for mode, geometry in zip(lines["mode"], lines.geometry, strict=True):
        lon, lat = out["rail" if mode == "rail" else "urban"]
        for piece in getattr(geometry, "geoms", [geometry]):
            xs, ys = piece.xy
            lon += [*xs, None]
            lat += [*ys, None]
    return out

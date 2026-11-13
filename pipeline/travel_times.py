"""Step 3: commune-to-commune travel-time matrices with r5py (Conveyal R5).

Origins and destinations are the commune centroids from step 1. One matrix per scenario
(see pipeline/config.py), written as long-format Parquet: from_id, to_id, travel_time (minutes).
Pairs that cannot be reached within MAX_TRAVEL_TIME have a null travel_time.

Run:
    uv run python -m pipeline.step3_travel_times --limit 20          # smoke test, 20 communes
    uv run python -m pipeline.step3_travel_times                     # all scenarios
    uv run python -m pipeline.step3_travel_times --scenarios transit_tue_0830 car_tue_0830
    uv run python -m pipeline.step3_travel_times --force             # recompute existing files

The first run builds the R5 network from the OSM extract and GTFS, which takes several minutes.
"""

import argparse
import sys
import time

import geopandas as gpd
import pandas as pd

from pipeline.config import (
    COMMUNES_PARQUET,
    DEPARTURE_WINDOW,
    GTFS_ZIP,
    JVM_MAX_MEMORY,
    MAX_TRAVEL_TIME,
    OSM_PBF,
    SCENARIOS,
    SCENARIOS_BY_NAME,
    TRANSIT_PERCENTILE,
    TTM_DIR,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenarios", nargs="+", choices=list(SCENARIOS_BY_NAME), help="default: all")
    parser.add_argument("--limit", type=int, help="only route the first N communes (smoke test)")
    parser.add_argument("--force", action="store_true", help="recompute matrices that already exist")
    # r5py reads its own options (such as --max-memory) from sys.argv, so ignore unknown ones here.
    args, _ = parser.parse_known_args()
    return args


def load_points(limit: int | None) -> gpd.GeoDataFrame:
    com = gpd.read_parquet(COMMUNES_PARQUET)
    if limit:
        # Spread the sample across the region: the largest communes by jobs.
        com = com.nlargest(limit, "jobs")
    return gpd.GeoDataFrame(
        {"id": com["code"].to_numpy()},
        geometry=gpd.points_from_xy(com["lon"], com["lat"]),
        crs=4326,
    )


def output_path(name: str, limit: int | None):
    suffix = f"_sample{limit}" if limit else ""
    return TTM_DIR / f"{name}{suffix}.parquet"


def load_network(r5py):
    """Build the R5 network from the OSM extract and GTFS, or reuse r5py's cached build.

    The raw OSM extract (340 MB) can be deleted to save disk once the network has been built:
    r5py keeps the built network in its cache folder, and this falls back to the newest one.
    The fallback uses r5py internals (1.1.x); with the inputs present, the public API is used.
    """
    if OSM_PBF.exists() and GTFS_ZIP.exists():
        return r5py.TransportNetwork(OSM_PBF, [GTFS_ZIP])

    from r5py.util import Config, GoodEnoughEquidistantCrs

    cached = sorted(Config().CACHE_DIR.glob("*.transport_network"), key=lambda p: p.stat().st_mtime)
    if not cached:
        raise FileNotFoundError(f"{OSM_PBF} is missing and r5py has no cached network: run step 2 first")

    print(f"note: {OSM_PBF.name} not found, reusing r5py's cached network {cached[-1].name[:12]}…")
    network = r5py.TransportNetwork.__new__(r5py.TransportNetwork)
    network._transport_network = network._load_pickled_transport_network(cached[-1])
    network.EQUIDISTANT_CRS = GoodEnoughEquidistantCrs(network.extent)
    return network


def main() -> None:
    args = parse_args()

    # r5py sizes the JVM when it is first imported; cap it unless the caller already did.
    if "--max-memory" not in sys.argv and "-m" not in sys.argv:
        sys.argv += ["--max-memory", JVM_MAX_MEMORY]
    import r5py  # imported here, after the sys.argv change above, on purpose

    if not COMMUNES_PARQUET.exists():
        raise FileNotFoundError(f"{COMMUNES_PARQUET} is missing: run step 1 first")

    scenarios = [SCENARIOS_BY_NAME[n] for n in args.scenarios] if args.scenarios else SCENARIOS
    todo = [s for s in scenarios if args.force or not output_path(s.name, args.limit).exists()]
    if not todo:
        print("all requested matrices already exist (use --force to recompute)")
        return

    points = load_points(args.limit)
    print(f"{len(points):,} origins x {len(points):,} destinations")

    started = time.perf_counter()
    network = load_network(r5py)
    print(f"network ready in {time.perf_counter() - started:,.0f} s")

    TTM_DIR.mkdir(parents=True, exist_ok=True)
    for s in todo:
        started = time.perf_counter()
        if s.mode == "transit":
            # Window centred on the scenario time; see DEPARTURE_WINDOW in config.py.
            options = {
                "transport_modes": [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
                "departure": s.departure - DEPARTURE_WINDOW / 2,
                "departure_time_window": DEPARTURE_WINDOW,
                "percentiles": [TRANSIT_PERCENTILE],
            }
        else:
            # Free-flow car times do not depend on the clock, so one departure minute is enough.
            options = {"transport_modes": [r5py.TransportMode.CAR], "departure": s.departure}

        ttm = r5py.TravelTimeMatrix(
            network,
            origins=points,
            destinations=points,
            max_time=MAX_TRAVEL_TIME,
            snap_to_network=True,
            **options,
        )
        df = pd.DataFrame(ttm)
        # r5py names the column travel_time for the median and travel_time_pNN otherwise.
        df = df.rename(columns={f"travel_time_p{TRANSIT_PERCENTILE}": "travel_time"})
        df = df[["from_id", "to_id", "travel_time"]]
        df["travel_time"] = df["travel_time"].astype("Int16")

        out = output_path(s.name, args.limit)
        df.to_parquet(out, index=False)
        reached = df["travel_time"].notna().mean()
        print(f"{s.name}: {len(df):,} pairs, {reached:.1%} reachable within "
              f"{MAX_TRAVEL_TIME.seconds // 60} min, {time.perf_counter() - started:,.0f} s -> {out.name}")


if __name__ == "__main__":
    main()

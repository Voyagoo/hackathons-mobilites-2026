"""Move routing points that the router cannot use.

Step 1 routes each area from its busiest station. For a few areas that station is not connected
to the walking network in OpenStreetMap (for example the new Neuilly - Porte Maillot station for
Paris 17e), so public transport reaches nothing from it, and nobody can reach its jobs either.

This script finds the areas that reach nothing but themselves at the weekday peak, tests the
other stations of the area with the router, and moves the routing point to the usable station
closest to the original one (so the intended hub is kept, a short walk away).
It edits data/processed/communes.parquet in place (columns lon, lat, anchor_stop, anchor).

Run it after step 3, then recompute the transit matrices and step 4:

    uv run python -m pipeline.fix_unroutable_anchors
    uv run python -m pipeline.travel_times --force --scenarios transit_tue_0830 ...
    uv run python -m pipeline.access

The car matrix is not recomputed: the point moves by a few hundred metres inside the same area.
"""

import sys

import geopandas as gpd
import pandas as pd

from pipeline import communes, travel_times
from pipeline.config import (
    COMMUNES_PARQUET,
    DEPARTURE_WINDOW,
    JVM_MAX_MEMORY,
    MAX_TRAVEL_TIME,
    SCENARIOS_BY_NAME,
    TRANSIT_PERCENTILE,
    TTM_DIR,
)

PEAK = "transit_tue_0830"
CANDIDATES_PER_AREA = 60
MIN_REACHED = 5  # a usable point reaches at least this many other areas within 90 minutes


def unroutable_areas() -> list[str]:
    ttm = pd.read_parquet(TTM_DIR / f"{PEAK}.parquet")
    reached = ttm[ttm["travel_time"].notna()].groupby("from_id").size()
    return sorted(reached.index[reached <= 1])


def candidate_stations(com: gpd.GeoDataFrame, areas: list[str]) -> gpd.GeoDataFrame:
    stations = communes.station_departures()
    stations = gpd.GeoDataFrame(stations, geometry=gpd.points_from_xy(stations["lon"], stations["lat"]), crs=4326)
    joined = gpd.sjoin(stations, com.loc[com["code"].isin(areas), ["code", "geometry"]], predicate="within")
    joined = joined.sort_values(["code", "departures"], ascending=[True, False])
    joined = joined.groupby("code").head(CANDIDATES_PER_AREA).reset_index(drop=True)
    joined["id"] = joined["code"] + "#" + joined.groupby("code").cumcount().astype(str)
    return joined


def main() -> None:
    if "--max-memory" not in sys.argv:
        sys.argv += ["--max-memory", JVM_MAX_MEMORY]
    import r5py  # after the sys.argv change, on purpose (see step 3)

    com = gpd.read_parquet(COMMUNES_PARQUET)
    areas = unroutable_areas()
    print(f"{len(areas)} areas reach nothing by public transport at the peak: "
          f"{com.loc[com['code'].isin(areas), 'name'].tolist()}")
    if not areas:
        return

    candidates = candidate_stations(com, areas)
    destinations = gpd.GeoDataFrame({"id": com["code"].to_numpy()},
                                    geometry=gpd.points_from_xy(com["lon"], com["lat"]), crs=4326)
    scenario = SCENARIOS_BY_NAME[PEAK]
    network = travel_times.load_network(r5py)
    ttm = pd.DataFrame(r5py.TravelTimeMatrix(
        network, origins=candidates[["id", "geometry"]], destinations=destinations,
        transport_modes=[r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
        departure=scenario.departure - DEPARTURE_WINDOW / 2, departure_time_window=DEPARTURE_WINDOW,
        percentiles=[TRANSIT_PERCENTILE], max_time=MAX_TRAVEL_TIME, snap_to_network=True,
    ))
    time_column = next(c for c in ttm.columns if c.startswith("travel_time"))
    reached = ttm[ttm[time_column].notna()].groupby("from_id").size()
    candidates["reached"] = candidates["id"].map(reached).fillna(0).astype(int)

    for code in areas:
        usable = candidates[(candidates["code"] == code) & (candidates["reached"] >= MIN_REACHED)]
        name = com.loc[com["code"] == code, "name"].iloc[0]
        if usable.empty:
            print(f"  {name}: no usable station among the candidates, left unchanged")
            continue
        # Stay as close as possible to the intended hub: the usable station nearest to the original one.
        row = com["code"] == code
        old_lon, old_lat = com.loc[row, "lon"].iloc[0], com.loc[row, "lat"].iloc[0]
        distance = ((usable["lon"] - old_lon) * 73) ** 2 + ((usable["lat"] - old_lat) * 111) ** 2  # km², approx.
        best = usable.loc[distance.idxmin()]
        com.loc[row, ["lon", "lat"]] = [best["lon"], best["lat"]]
        com.loc[row, "anchor_stop"] = best["stop_name"]
        com.loc[row, "anchor"] = "busiest_routable_station"
        print(f"  {name}: moved to {best['stop_name']} (reaches {best['reached']} areas within 90 min)")

    com.to_parquet(COMMUNES_PARQUET)
    print(f"updated {COMMUNES_PARQUET.name}; now recompute the transit matrices and step 4")


if __name__ == "__main__":
    main()

"""Step 1: build the commune base table for Île-de-France.

One row per commune, with jobs (EMP1), employed residents by transport mode (NAV),
population, employment zone, median income, and the routing point (`lon`, `lat`).

Routing point: geometric centroids land in parks, forests or airports for large communes
(Versailles, Roissy), and the "centre of the stops" falls between districts of polycentric towns
(Cergy). Both add long walks that no resident makes. Instead, each commune is routed from its
**busiest station**: platforms are grouped by GTFS `parent_station`, and the station with the most
scheduled departures (stop_times.txt) in the commune is the anchor. Communes without any stop
use a point inside the polygon.

Consequences, stated on the app's method panel: transit times start at the commune's main
hub, which favours transit for residents who live far from it. The car benchmark uses the
same point, so the comparison between modes stays fair.

Paris: when data/paris_arrondissements/arrondissements.geojson is present, Paris (75056) is
replaced by its 20 arrondissements (75101-75120). A single point for Paris adds a cross-Paris
trip to every journey towards the east and south. The census, population and Filosofi files
all have arrondissement rows, so only the shapes come from the extra file.

Output: data/processed/communes.parquet (GeoParquet, EPSG:4326)
Run:    uv run python -m pipeline.communes
"""

import duckdb
import geopandas as gpd
import pandas as pd

from pipeline.config import (
    COMMUNES_GEOJSON,
    COMMUNES_PARQUET,
    EMP1_CSV,
    GTFS_DIR,
    IDF_REGION,
    INCOME_GLOB,
    NAV_CSV,
    PARIS_ARR_GEOJSON,
    PARIS_CODE,
    POPULATION_CSV,
    ZONES_CSV,
)

N_COMMUNES = 1266  # Île-de-France communes, Paris counted once
PARIS_ARR_PATTERN = r"^751\d\d$"
from utils.loaders import DATA_DIR

# NAV transport mode codes -> column names (see docs/data_dictionary/nav2-commuting-flows.md)
MODE_COLUMNS = {
    "_T": "residents",
    "1": "res_no_transport",
    "2": "res_walk",
    "3": "res_bike",
    "4": "res_two_wheeler",
    "5": "res_car",
    "6": "res_transit",
}


def load_communes() -> gpd.GeoDataFrame:
    com = gpd.read_file(COMMUNES_GEOJSON)
    com = com[com["reg"] == IDF_REGION].copy()
    com = com.rename(columns={"codgeo": "code", "libgeo": "name"})
    com["code"] = com["code"].astype(str)
    com["dept"] = com["dept"].astype(str)

    arrondissements = load_paris_arrondissements()
    if arrondissements is not None:
        com = pd.concat([com[com["code"] != PARIS_CODE], arrondissements.to_crs(com.crs)], ignore_index=True)
        com = gpd.GeoDataFrame(com, geometry="geometry", crs=arrondissements.to_crs(com.crs).crs)

    # Geometric centroid in Lambert-93 (metres), then back to lon/lat. Kept for reference only.
    centroids = com.to_crs(2154).geometry.centroid.to_crs(4326)
    com["centroid_lon"] = centroids.x
    com["centroid_lat"] = centroids.y
    com = com[["code", "name", "dept", "centroid_lon", "centroid_lat", "geometry"]].reset_index(drop=True)
    return com.merge(activity_anchors(com), on="code", how="left")


def load_paris_arrondissements() -> gpd.GeoDataFrame | None:
    """The 20 Paris arrondissements (codes 75101-75120), or None when the optional file is absent."""
    if not PARIS_ARR_GEOJSON.exists():
        print(f"note: {PARIS_ARR_GEOJSON.name} not found, Paris is routed as a single point")
        return None

    arr = gpd.read_file(PARIS_ARR_GEOJSON)
    if "c_arinsee" not in arr.columns:
        raise KeyError(f"expected a 'c_arinsee' column (INSEE code) in {PARIS_ARR_GEOJSON}, got {list(arr.columns)}")
    codes = arr["c_arinsee"].astype(float).astype(int).astype(str)
    numbers = codes.str[-2:].astype(int)  # 75110 -> 10

    arr = gpd.GeoDataFrame({
        "code": codes,
        "name": "Paris " + numbers.map(lambda n: "1er" if n == 1 else f"{n}e"),
        "dept": "75",
        "geometry": arr.geometry,
    }, crs=arr.crs)
    assert len(arr) == 20 and arr["code"].str.match(PARIS_ARR_PATTERN).all(), "unexpected arrondissement codes"
    return arr


def station_departures() -> pd.DataFrame:
    """Scheduled departures per station (platforms grouped by parent_station), with its position."""
    departures = duckdb.sql(f"""
        SELECT stop_id, count(*) AS departures
        FROM read_csv('{GTFS_DIR / "stop_times.txt"}', header=true, all_varchar=true)
        GROUP BY stop_id
    """).df()

    stops = pd.read_csv(
        GTFS_DIR / "stops.txt",
        usecols=["stop_id", "stop_name", "stop_lon", "stop_lat", "location_type", "parent_station"],
        dtype={"stop_id": str, "parent_station": str},
    )
    platforms = stops[stops["location_type"].fillna(0) == 0].merge(departures, on="stop_id", how="inner")
    platforms["station_id"] = platforms["parent_station"].fillna(platforms["stop_id"])

    per_station = platforms.groupby("station_id").agg(
        departures=("departures", "sum"),
        platform_lon=("stop_lon", "mean"),
        platform_lat=("stop_lat", "mean"),
        stop_name=("stop_name", "first"),
    )
    # Use the parent station's own position when it exists, else the mean of its platforms.
    parents = stops.set_index("stop_id")[["stop_lon", "stop_lat"]]
    per_station = per_station.join(parents, how="left")
    per_station["lon"] = per_station["stop_lon"].fillna(per_station["platform_lon"])
    per_station["lat"] = per_station["stop_lat"].fillna(per_station["platform_lat"])
    return per_station[["stop_name", "departures", "lon", "lat"]].reset_index()


def activity_anchors(com: gpd.GeoDataFrame) -> pd.DataFrame:
    """Routing point per commune: its busiest station (most scheduled departures)."""
    stations = station_departures()
    stations = gpd.GeoDataFrame(
        stations, geometry=gpd.points_from_xy(stations["lon"], stations["lat"]), crs=4326
    ).to_crs(2154)

    polygons = com[["code", "geometry"]].to_crs(2154)
    joined = gpd.sjoin(stations, polygons, how="inner", predicate="within")

    anchors = joined.loc[joined.groupby("code")["departures"].idxmax(), ["code", "stop_name", "geometry"]]
    anchors = gpd.GeoDataFrame(anchors, geometry="geometry", crs=2154)
    anchors["n_stops"] = anchors["code"].map(joined["code"].value_counts())
    anchors["anchor"] = "busiest_station"

    # Communes without a stop: a point guaranteed to lie inside the polygon.
    no_stop = polygons[~polygons["code"].isin(anchors["code"])].copy()
    no_stop["geometry"] = no_stop.geometry.representative_point()
    no_stop["n_stops"] = 0
    no_stop["stop_name"] = None
    no_stop["anchor"] = "inside_point"

    points = pd.concat([anchors, no_stop], ignore_index=True).set_crs(2154, allow_override=True).to_crs(4326)
    return pd.DataFrame({
        "code": points["code"],
        "lon": points.geometry.x,
        "lat": points.geometry.y,
        "anchor_stop": points["stop_name"],
        "n_stops": points["n_stops"].astype(int),
        "anchor": points["anchor"],
    })


def load_jobs(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.sql(f"""
        SELECT GEO AS code, TRY_CAST(OBS_VALUE AS DOUBLE) AS jobs
        FROM read_csv('{EMP1_CSV}', delim=';', header=true, all_varchar=true)
        WHERE GEO_OBJECT IN ('COM', 'ARM') AND SEX = '_T' AND EMPFORM = '_T'
          AND WKTIME = '_T' AND AGE = '_T'
    """).df()  # ARM = Paris/Lyon/Marseille arrondissements; only those in the geometry table are kept


def load_residents(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Employed residents (15+) by commune of residence: by mode, and working in their own commune."""
    nav = f"read_csv('{NAV_CSV}', delim=';', header=true, all_varchar=true)"
    base_filter = ("GEO_OBJECT IN ('COM', 'ARM') AND AGE = 'Y_GE15' AND EMPSTA_ENQ = '1' AND SEX = '_T' "
                   "AND WORK_URBAN_AREA = '_T'")

    by_mode = con.sql(f"""
        SELECT GEO AS code, TRANS AS trans, TRY_CAST(OBS_VALUE AS DOUBLE) AS value
        FROM {nav}
        WHERE {base_filter} AND WORK_AREA = '_T'
    """).df()
    wide = by_mode.pivot_table(index="code", columns="trans", values="value", aggfunc="sum")
    wide = wide.rename(columns=MODE_COLUMNS)[list(MODE_COLUMNS.values())]

    own_commune = con.sql(f"""
        SELECT GEO AS code, TRY_CAST(OBS_VALUE AS DOUBLE) AS res_work_in_commune
        FROM {nav}
        WHERE {base_filter} AND TRANS = '_T' AND WORK_AREA = '10'
    """).df().set_index("code")

    return wide.join(own_commune).reset_index()


def load_population() -> pd.DataFrame:
    pop = pd.read_csv(POPULATION_CSV, sep=";", dtype=str)
    pop = pop[pop["REG"] == IDF_REGION]
    pop = pd.DataFrame({"code": pop["COM"], "population": pd.to_numeric(pop["PMUN"])})

    # This file lists Paris only by arrondissement; add the city total under 75056 too,
    # so both the single-point and the arrondissement versions of Paris find a population.
    is_paris_arr = pop["code"].str.match(PARIS_ARR_PATTERN)
    paris = pd.DataFrame({"code": [PARIS_CODE], "population": [pop.loc[is_paris_arr, "population"].sum()]})
    return pd.concat([pop, paris], ignore_index=True)


def load_zones() -> pd.DataFrame:
    zones = pd.read_csv(ZONES_CSV, sep=";", dtype=str, encoding="utf-8-sig")
    zones = zones.rename(columns={
        "Code géo": "code",
        "Code zone d'emploi": "ze_code",
        "Zone d'emploi": "ze_name",
    })[["code", "ze_code", "ze_name"]]

    # Arrondissements belong to the same employment zone as Paris.
    paris = zones[zones["code"] == PARIS_CODE].iloc[0]
    arrondissements = pd.DataFrame({"code": [f"751{i:02d}" for i in range(1, 21)],
                                    "ze_code": paris["ze_code"], "ze_name": paris["ze_name"]})
    return pd.concat([zones, arrondissements], ignore_index=True)


def load_income() -> pd.DataFrame:
    matches = sorted(DATA_DIR.glob(INCOME_GLOB))
    if len(matches) != 1:
        raise FileNotFoundError(f"Expected one Filosofi income file for {INCOME_GLOB!r}, found {matches}")

    raw = pd.read_csv(matches[0], sep=";", dtype=str)
    income = pd.DataFrame({
        "code": raw["Code géographique"],
        # Median disposable income per consumption unit; blank when hidden by statistical secrecy.
        "median_income": pd.to_numeric(raw["[DISP] Médiane (€)"], errors="coerce"),
        "households": pd.to_numeric(raw["[DISP] Nbre de ménages fiscaux"], errors="coerce"),
    })

    # Filosofi has no row for Paris as a whole, only arrondissements (75101-75120), which are kept.
    # For single-point Paris: household-weighted mean of the arrondissement medians (not a true median).
    arr = income[income["code"].str.match(PARIS_ARR_PATTERN)].dropna()
    paris_median = (arr["median_income"] * arr["households"]).sum() / arr["households"].sum()
    income = income[income["code"] != PARIS_CODE]
    income = pd.concat([income, pd.DataFrame({"code": [PARIS_CODE], "median_income": [paris_median]})])
    return income[["code", "median_income"]]


def build() -> gpd.GeoDataFrame:
    con = duckdb.connect()
    com = load_communes()

    df = (
        com.merge(load_jobs(con), on="code", how="left")
        .merge(load_residents(con), on="code", how="left")
        .merge(load_population(), on="code", how="left")
        .merge(load_zones(), on="code", how="left")
        .merge(load_income(), on="code", how="left")
    )
    return gpd.GeoDataFrame(df, geometry="geometry", crs=com.crs)


def check(df: gpd.GeoDataFrame) -> None:
    split_paris = df["code"].str.match(PARIS_ARR_PATTERN).any()
    expected = N_COMMUNES - 1 + 20 if split_paris else N_COMMUNES
    assert len(df) == expected, f"expected {expected:,} areas, got {len(df):,}"
    assert df["code"].is_unique

    required = ["jobs", "residents", "population", "ze_code", "lon", "lat"]
    missing = df[required].isna().sum()
    assert missing.sum() == 0, f"missing values in required columns:\n{missing}"

    print(f"{len(df):,} communes | {df['jobs'].sum():,.0f} jobs | "
          f"{df['residents'].sum():,.0f} employed residents | {df['population'].sum():,.0f} inhabitants")
    print(f"median income missing for {df['median_income'].isna().sum()} communes (statistical secrecy)")
    print(f"routing points: {df['anchor'].value_counts().to_dict()}")


def main() -> None:
    df = build()
    check(df)
    COMMUNES_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(COMMUNES_PARQUET)
    print(f"wrote {COMMUNES_PARQUET}")


if __name__ == "__main__":
    main()

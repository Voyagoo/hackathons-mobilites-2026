"""Optional: build the rail / metro / tram overlay for the app's maps from the GTFS shapes.

For each rail, metro and tram route (GTFS route_type 2, 1, 0) the longest shape is kept, simplified
to about 40 m and written to data/processed/rail_lines.geojson. It is a visual overlay for
orientation only; nothing in the analysis depends on it. The geometry is the operators' own
(IDFM GTFS shapes.txt), not drawn by hand.

Run: uv run python -m pipeline.extra_rail_lines
"""

import duckdb
import geopandas as gpd
from shapely.geometry import LineString

from pipeline.config import COMMUNES_PARQUET, GTFS_DIR
from utils.loaders import PROCESSED_DIR

RAIL_GEOJSON = PROCESSED_DIR / "rail_lines.geojson"
MODE_NAMES = {"0": "tram", "1": "metro", "2": "rail"}


def main() -> None:
    g = GTFS_DIR
    points = duckdb.sql(f"""
        WITH rail AS (
            SELECT route_id, route_short_name, route_type
            FROM read_csv('{g}/routes.txt', header=true, all_varchar=true)
            WHERE route_type IN ('0', '1', '2')
        ),
        route_shapes AS (
            SELECT DISTINCT t.route_id, t.shape_id
            FROM read_csv('{g}/trips.txt', header=true, all_varchar=true) t
            JOIN rail USING (route_id)
            WHERE t.shape_id IS NOT NULL
        ),
        shape_points AS (
            SELECT shape_id, CAST(shape_pt_lon AS DOUBLE) AS lon, CAST(shape_pt_lat AS DOUBLE) AS lat,
                   CAST(shape_pt_sequence AS INTEGER) AS seq
            FROM read_csv('{g}/shapes.txt', header=true, all_varchar=true)
            WHERE shape_id IN (SELECT shape_id FROM route_shapes)
        )
        SELECT r.route_id, r.route_short_name, r.route_type, p.shape_id, p.lon, p.lat, p.seq
        FROM route_shapes s JOIN rail r USING (route_id) JOIN shape_points p USING (shape_id)
        ORDER BY r.route_id, p.shape_id, p.seq
    """).df()

    # Every distinct shape of a route is kept, so branches (RER A, B, C, D...) are all drawn.
    rows = []
    for (route_id, name, route_type, _shape), part in points.groupby(
        ["route_id", "route_short_name", "route_type", "shape_id"]
    ):
        if len(part) >= 2:
            rows.append({"route_id": route_id, "name": name, "mode": MODE_NAMES[route_type],
                         "geometry": LineString(zip(part["lon"], part["lat"], strict=True))})
    lines = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326).to_crs(2154)
    # Merge each route's shapes into one geometry (overlapping trunks collapse), then simplify.
    merged = lines.dissolve(by=["route_id", "name", "mode"]).reset_index()
    merged["geometry"] = merged.geometry.line_merge().simplify(40)
    # Keep only the part inside Île-de-France: some lines continue far outside the region.
    region = gpd.read_parquet(COMMUNES_PARQUET).to_crs(2154).geometry.union_all()
    merged["geometry"] = merged.geometry.intersection(region)
    merged = merged[~merged.geometry.is_empty].to_crs(4326)

    RAIL_GEOJSON.parent.mkdir(parents=True, exist_ok=True)
    merged.to_file(RAIL_GEOJSON, driver="GeoJSON")
    print(f"wrote {RAIL_GEOJSON.name}: {len(merged)} routes {merged['mode'].value_counts().to_dict()}, "
          f"{RAIL_GEOJSON.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()

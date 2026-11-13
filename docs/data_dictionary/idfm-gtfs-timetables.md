# IDFM GTFS: Planned public transport timetables (`IDFM-gtfs/`)

**Folder:** `data/IDFM-gtfs/` (unzipped from the IDFM catalogue file `IDFM-gtfs.zip`)
**Source:** Île-de-France Mobilités, "Horaires prévus sur les lignes de transport en commun d'Ile-de-France (GTFS Datahub)", dataset `offre-horaires-tc-gtfs-idfm`. Licence ODbL.
**Format:** GTFS (General Transit Feed Specification). Plain-text files, comma-separated, UTF-8. Relationships are by ID columns. The standard spec is at gtfs.org; IDFM adds extension files and some custom IDs (`IDFM:...`).
**Time window:** the sample `calendar.txt` runs from `20261110` to `20261209`. That is the rolling window at download time, so the timetable changes when the feed is refreshed.

## Files and row counts

Row counts are data lines, excluding the header.

| File | Rows | Purpose |
| --- | --- | --- |
| `agency.txt` | 64 | Transport operators (for example, Paris Saclay) |
| `routes.txt` | 2,028 | Lines (one row per line) |
| `trips.txt` | 407,413 | One row per vehicle run on a route |
| `stop_times.txt` | 8,771,810 | Times at each stop of each trip. The largest file (about 710 MB). |
| `stops.txt` | 53,445 | Stops, stop areas and stations |
| `shapes.txt` | 3,471,672 | Geographic path of each route, as ordered points |
| `calendar.txt` | 734 | Service patterns: which weekdays, between which dates |
| `calendar_dates.txt` | 1,349 | Exceptions to `calendar.txt` (added or removed days) |
| `transfers.txt` | 191,965 | Minimum transfer times between stops |
| `pathways.txt` | 5,041 | Walking links inside stations (entrances, corridors, stairs) |
| `attributions.txt` | 2,028 | Operator attribution per route |
| `booking_rules.txt` | 22 | Booking rules for on-demand services |
| `object_codes_extension.txt` | 1,036,867 | IDFM extension: external codes for objects (IDs in other systems) |
| `ticketing_deep_links.txt` | 1 | Links to ticketing apps |

## Key columns

| File | Column | Meaning |
| --- | --- | --- |
| `stops.txt` | `stop_id`, `stop_name` | Stop identifier and name |
| `stops.txt` | `stop_lat`, `stop_lon` | WGS 84 coordinates |
| `stops.txt` | `location_type` | `0` stop or platform, `1` station, `2` entrance, `3` generic node, `4` boarding area |
| `stops.txt` | `parent_station` | Stop-level `stop_id` pointing to its station |
| `stops.txt` | `wheelchair_boarding` | Accessibility: `0` unknown, `1` accessible, `2` not accessible |
| `routes.txt` | `route_type` | Mode, GTFS standard. `3` bus in this file. Other values include `0` tram, `1` metro, `2` rail, `7` funicular |
| `routes.txt` | `route_short_name`, `route_long_name` | Line label and name |
| `routes.txt` | `route_color`, `route_text_color` | Hex colours, without `#` |
| `trips.txt` | `trip_id`, `route_id`, `service_id` | Links a run to its line and calendar |
| `trips.txt` | `direction_id` | `0` or `1` (one direction of the line) |
| `trips.txt` | `shape_id` | Links to the path in `shapes.txt` |
| `trips.txt` | `wheelchair_accessible`, `bikes_allowed` | `0` unknown, `1` yes, `2` no |
| `stop_times.txt` | `arrival_time`, `departure_time` | `HH:MM:SS`. Can exceed 24:00:00 for runs after midnight. |
| `stop_times.txt` | `stop_sequence` | Order of the stop within the trip. Sort by this, not by time. |
| `stop_times.txt` | `pickup_type`, `drop_off_type` | `0` regular, `1` none, `2` phone, `3` driver |
| `calendar.txt` | `monday` … `sunday` | `1` runs that day, `0` does not |
| `calendar.txt` | `start_date`, `end_date` | `YYYYMMDD`, inclusive |
| `calendar_dates.txt` | `exception_type` | `1` added, `2` removed |
| `transfers.txt` | `transfer_type` | `0` recommended, `1` timed, `2` minimum time required, `3` not possible |
| `transfers.txt` | `min_transfer_time` | Seconds |
| `shapes.txt` | `shape_pt_sequence` | Order of the points in the path |

## Relationships

`stops` ← `stop_times` → `trips` → `routes` → `agency`. `trips` → `calendar` (or `calendar_dates`) for when a run operates. `trips` → `shapes` for the path.

## Pointer files, not data

The folder `data/Scheduled_schedules_on_public_transport/` does not contain timetable data. It holds three files that only point to the zip:

- `offre-horaires-tc-gtfs-idfm.csv`: one row, `filename;url`
- `offre-horaires-tc-gtfs-idfm.geojson`: a feature with no geometry, holding the same URL
- `offre-horaires-tc-gtfs-idfm.parquet`: one row with the same link in a struct column

Use `IDFM-gtfs/` for the data.

## Pitfalls

- **`stop_times.txt` is very large.** Load it with only the columns you need, or use DuckDB or Polars instead of loading it all into pandas.
- **Times are not dates.** `HH:MM:SS` can be above 24:00:00. Parse it as an offset from midnight of the service day.
- **Stops are hierarchical.** `location_type` and `parent_station` decide whether a row is a platform, a station or an entrance. Counting rows in `stops.txt` counts all of them, not stations.
- **Calendar mismatch.** A trip only runs on days its `service_id` allows in `calendar.txt`, minus `calendar_dates.txt` removals, plus additions.
- **Planned, not real.** These are scheduled timetables. Works, disruptions and replacement buses are not always reflected, as IDFM notes on its portal.

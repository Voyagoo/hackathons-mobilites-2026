# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Python 3.12, managed with `uv` (`.venv/` is in the repo folder and git-ignored). r5py also needs a Java JDK 21+.

```bash
uv sync                                               # install dependencies (incl. dev group: jupyterlab, ruff)
uv run python -m pipeline.step1_communes              # pipeline steps 1-4, in order (see pipeline/__init__.py)
uv run python -m pipeline.step3_travel_times --limit 20   # r5py smoke test on 20 communes (+ step4_access --sample 20)
uv run uvicorn app.main:server --reload               # Dash app (FastAPI backend) at http://127.0.0.1:8000
uv run jupyter lab                                    # exploratory notebooks in notebooks/
uv run ruff check .                                   # lint
```

There is no test suite yet. The `data/` folder is git-ignored and must be filled locally from the sources in `docs/data_sources.md`; the column codes of each raw file are documented in `docs/data_dictionary/`.

## Architecture

Hackaviz 2026 entry, Challenge 2. Track: do all Île-de-France residents reach the same number of jobs within 30/45/60 minutes, by public transport (with a free-flow car benchmark)?

- **Pipeline (`pipeline/`)**: four scripts, each writing to `data/processed/` (`PROCESSED_DIR` in `utils/loaders.py`). All paths, thresholds and departure scenarios live in `pipeline/config.py`. Step 1 builds `communes.parquet` (one row per commune: jobs from EMP1, employed residents from NAV, population, employment zone, income). Step 3 routes station to station with r5py on the IDFM GTFS + OSM and writes one long-format matrix per scenario to `data/processed/ttm/`. Step 4 turns matrices into jobs reachable per commune and residents-weighted equality indicators. `fix_unroutable_anchors.py` runs after step 3 and moves routing points the router cannot reach on foot.
- **Dash app (`app/`)**: "Access to Work | Île-de-France", a viewport-sized workspace (`Dash(backend="fastapi")`; `app.main:server` is the FastAPI instance). Six views in one page (Explore, Compare, Equity, Commune, Priorities, Method), shown or hidden by the `route` callback; each view has one callback that returns `no_update` unless its view is active. State is the controls themselves: `view`, `mode`, `time`, `budget`, `metric`, `commune` (set by the search box, map clicks and ranking rows through `select_commune`). `app/data.py` loads the processed Parquet files once (cached) and derives every displayed number; `app/figures.py` builds the Plotly figures; map legends and scenario bars are HTML built in `app/main.py`. The app never runs r5py. `app/static/style.css` holds the design tokens from `Mobility_Atlas_Figma_Handoff/design_tokens.json`. `ATW_VIEW`, `ATW_COMMUNE`, `ATW_FOCUS`, `ATW_MAPMODE` env vars set the start view, commune, zoom preset and map mode (for screenshots). Maps use Plotly's SVG geo engine; `ATW_MAP=maplibre` is an opt-in WebGL engine that rendered only one tile in the user's browser. Headless Chrome screenshots resize the viewport at capture time, so compare layouts at the window size you launched with, and never run two screenshot runs in one shell command (the second hangs). `phase_2.md` is the redesign brief and `phase_2_progress.md` its checklist. `app/templates/` is unused.
- **Notebooks (`notebooks/`)**: exploration; import helpers with `from utils.loaders import ...`. `utils` is installed as an editable package through `pyproject.toml`.

Paths are anchored to the repo root via the constants in `utils/loaders.py` and `pipeline/config.py`; use them rather than relative paths.

Data gotchas the code relies on:
- The census CSVs (EMP1, NAV) mix geographic levels and include `_T` totals: always filter `GEO_OBJECT = 'COM'` and fix the unused dimensions to `_T`. Query them with DuckDB; they are 0.7 to 0.9 GB.
- Commune codes are text (leading zeros). When `data/paris_arrondissements/arrondissements.geojson` exists, step 1 replaces Paris (`75056`) with its 20 arrondissements (`75101`–`75120`, census `GEO_OBJECT = 'ARM'`), giving 1,285 areas; without it Paris is one point and there are 1,266. A single Paris point adds a cross-Paris trip to every journey east or south, so keep the file.
- r5py reads `--max-memory` from `sys.argv` when first imported, which is why step 3 imports it inside `main()`.
- Routing points (`lon`, `lat` in `communes.parquet`) are each commune's busiest GTFS station, not its centroid: centroids land in parks/airports (Versailles, Roissy) and stop-centre points miss polycentric towns (Cergy). `centroid_lon/lat` are kept for reference. Changing the anchor means re-running step 3 with `--force`.
- The raw census CSVs and the OSM extract were deleted from `data/` to save disk. Step 1 cannot be re-run without re-downloading them; step 3 falls back to r5py's cached network (`~/.cache/r5py`). Do not overwrite `communes.parquet` unless the raw files are back.
- Transit times are the 25th percentile over a one-hour window centred on the scenario time (`DEPARTURE_WINDOW`, `TRANSIT_PERCENTILE`); the median over 30 minutes made hourly-train communes miss their train. Car times are free-flow and clock-independent, so re-running transit never requires re-running the 30-minute car matrix.
- Empty travel times mean "over 90 minutes or no route"; only origins that reach nothing are labelled "no route found" (`data.no_route_origins`).
- `data/IDFM-gtfs/` now holds a newer GTFS feed than the one the travel-time matrices were computed from (the user re-downloaded it for the rail overlay). `pipeline/extra_rail_lines.py` builds `data/processed/rail_lines.geojson` from it; the app shows the overlay only when that file exists. Do not mix this feed with the cached r5py network when reasoning about dates.
- `rasterio` is pinned below 1.5.2 in `[tool.uv]`: 1.5.2 has no macOS 14 arm64 wheel.

## Project conventions

- Team-facing docs are in French (`docs/Guide_Spécial_Dataviz.md` is the official participant guide). The README, code comments and the Dash app's text are in English (decided with the user; do not translate the app).
- The challenge requires accessible visualisations. The guide's accessibility section (colour contrast, colour-blindness) applies to every chart in this project. Colour semantics are fixed: public transport teal (`#126F73`), car orange (`#E38C58`), warning red (`#B64F4B`); sequential maps use a single-hue ramp with labelled classes.
- Never show a number that is not derived from `data/processed/`. The Figma handoff's maps and figures are layout placeholders, not data.
- `docs/tasks.md` is the team task board and `docs/ideas.md` holds the idea log. Update them when you change task status, not in code.

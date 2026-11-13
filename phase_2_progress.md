# Phase 2 progress

Checklist for `phase_2.md`, section by section. ✅ = done and checked, 🟡 = built but needs a check in a real browser, ⬜ = not done.

"Checked" means every callback was run for all scenarios and budgets, and a screenshot of the view was inspected at 1600×900 or 1440×900. My test browser cannot draw the interactive (WebGL) map, so anything that depends on it is 🟡 until it is tried in Chrome or Safari.

## §3 Page architecture
- ✅ Compact header and left navigation (Explore, Compare, Equity, Commune, Priorities, Method)
- ✅ Headline "Same region. Very different access to work." with one sentence
- ✅ Three KPIs that follow the selected scenario
- ✅ Single-screen workspace: map (about 62%) and analysis panel side by side, no page scroll on desktop

## §4 Main map
- ✅ Interactive map: scroll to zoom, drag to pan, double-click to reset, zoom buttons, hover and click, with town labels for orientation (Plotly SVG map, checked by screenshot)
- ⬜ WebGL map with a basemap (MapLibre): tried, but it drew only one block of communes in the user's browser and cannot be debugged in my test browser. Kept as an opt-in (`ATW_MAP=maplibre`), off by default.
- ✅ Larger map, department boundaries, subtle commune boundaries
- ✅ Seven colour classes with finer breaks at the low end; "no route found" has its own class
- ✅ Map metric selector (share, jobs, transit vs car, gain 30→60 min, residents in low-access communes)
- ✅ Hover tooltip content, selected-commune outline, commune search
- ✅ Rail/metro overlay with an on/off switch (see the map upgrade section)

## §5 Synchronised views
- ✅ One shared state (view, mode, departure, budget, metric, commune); every view reads it
- ✅ Clicking a commune on any map, or a ranking row, selects it everywhere and it stays selected
- ✅ Selected commune's department is highlighted in the department chart

## §6 Scenario comparison
- ✅ Bars: share of employed residents reaching under 5% of jobs, for the car and the five transit slots
- ✅ Five-band distribution kept behind "Full distribution in five bands"

## §7 Time of day
- ✅ Time-of-day profile: weekday slots joined, Saturday separate, car as reference line
- ✅ Departure buttons update the map, KPIs, bars and commune panel

## §8 Commune exploration
- ✅ Switch inside the Explore map: "Regional access" / "From a commune"
- ✅ Travel-time bands (30, 45, 60, 90 min), origin marked, "over 90 min or no route" shown separately
- ✅ Jobs within each budget, and a jobs-by-minutes curve (transit against car)

## §9 Departments
- ✅ Sorted, median as dot, worst-to-best 10% as bar, car marker, regional median line, selected department in bold

## §10 Income
- ✅ Connected dots across income fifths (selected slot, weekday peak, car), headline for lowest vs highest fifth, commune-level wording

## §11 Priorities
- ✅ Ranking of low-access communes by employed residents affected, sortable, no composite score

## §12 Guided story
- ✅ "Key findings": three steps with live numbers, each sets the view and filters; "Explore freely" returns (button logic tested through the server, not by clicking)

## §13 Visual design
- ✅ One palette (transit teal, car orange, warning red), type hierarchy, compact controls
- 🟡 Polish pass after you have looked at it in a real browser

## §14 Filters
- ✅ One toolbar: mode, departure, budget; departure disabled for the car; filters kept across views

## §15 Performance
- ✅ Only the visible view is recomputed; data loaded once and cached; simplified geometry
- 🟡 Map redraw speed when zooming (1,285 shapes; needs a check in a real browser)

## §16 Rigour
- ✅ Method view with sources, method and nine caveats; short caveats next to car and income figures
- ✅ Data fix: Paris 17e and Chessy were routed from stations the router cannot reach on foot, so they reached nothing and nobody reached their jobs. Routing points moved to the nearest usable stop (`pipeline/fix_unroutable_anchors.py`), transit matrices and access figures recomputed. Paris 17e now reaches 63% of jobs within 45 min at the peak (was 1.8%). Four small rural communes still have no usable stop and are labelled "no route found".

## §17 Responsive
- ✅ Tablet and mobile rules; checked at 500 px wide (the narrowest my test browser allows)

## §18 Validation
- ✅ All callbacks run for every scenario, budget, metric and view (1,200 combinations)
- ✅ Displayed KPIs re-checked against an independent recomputation from `access.parquet` after the data fix: 0 mismatches over 18 scenario × budget pairs
- ✅ `docs/validation.md` updated

## Map upgrade (`improve_map.md`)

Checked by screenshot at 1600×900 and 1500×987, and by running the Explore callback for every metric, zoom preset and map mode (480 combinations). Hover, scroll zoom and clicks still need a real browser.

- ✅ §2A Background: flat light warm-grey canvas; no satellite or road clutter
- ✅ §2B Boundaries: hairline commune lines (thicker when zoomed in), one dark department line (no bright white), selected commune in magenta with a white halo
- ✅ §2C Colour scale: ColorBrewer YlGnBu, 7 classes (ordered in lightness, colour-blind safe); neutral grey for "no route found", never mixed with low values
- ✅ §2D Classification: fixed thresholds kept (0.1, 0.5, 1, 3, 10, 25%) so every scenario uses the same legend; quantiles or Jenks would change meaning between scenarios
- ✅ §3 Legend: compact floating colour bar at the bottom left with the exact thresholds, plus a separate swatch for missing routing
- ⬜ §3 Interactive legend (highlight one class): not done
- ✅ §4A Tooltip: commune · department (code), jobs within reach, share, regional median, employed residents, and the mode / departure / budget
- ✅ §4B Selection: click selects everywhere, survives filter changes, and "From a commune" switches to its travel-time map
- ✅ §4C Navigation: "Zoom to" buttons in the dashboard style (Île-de-France, Paris & inner ring, Selected commune); scroll zoom, drag, double-click reset; the view is kept when only the scenario changes
- ⬜ §4C Fullscreen: not done
- ✅ §5 Paris: "Paris & inner ring" zoom preset, with thicker boundaries and local labels (Option B + C)
- ✅ §6 Context: reference towns on the regional view (white text on dark fills), decluttered local labels when zoomed
- ✅ §6 Rail overlay: RER and Transilien (thick) and metro and tram (thin) from the IDFM GTFS shapes, clipped to the region, with a "Rail network" on/off switch on the map (`pipeline/extra_rail_lines.py`)
- ✅ §7 Map modes: share or number of jobs, transit vs car, **change vs weekday peak** (new, diverging brown–teal scale centred on zero), gain from 30 to 60 min, residents in low-access communes
- ✅ §8 Travel-time mode: origin marked, bands only up to the selected budget, "over budget, up to 90 min" and "over 90 min or no route" shown separately, legend in minutes, note that times are station to station
- ✅ §9 Map as centrepiece: legend and controls float on the map instead of taking rows above and below it
- ⬜ Smooth WebGL zoom with a basemap: the MapLibre engine drew only one block of communes in the user's browser; it stays opt-in (`ATW_MAP=maplibre`)

# PROMPT — Upgrade the Île-de-France Accessibility Map to a Professional Geospatial Visualization

You are a **senior geospatial visualization engineer, cartographic designer, and interactive data visualization specialist**, experienced with Mapbox, MapLibre, deck.gl, Observable, and award-winning geographic data journalism.

I am developing an interactive mobility and employment accessibility dashboard for **Hackaviz Mobilités 2026 — Île-de-France**.

The dashboard is already functional, and I have attached a screenshot of its current implementation.

**Your task is to substantially improve the geographic map's visual design, usability, interactivity, and analytical expressiveness.**

Do not redesign the entire dashboard. Focus primarily on the map and its associated map controls, legends, tooltips, and geographic exploration.

Implement the changes directly in my existing codebase.

---

## 1. CURRENT MAP — WHAT NEEDS IMPROVEMENT

The current map already has:

- Real Île-de-France commune boundaries.
- Department boundaries.
- A choropleth showing the share of regional jobs reachable.
- Geographic place labels.
- Interactive commune selection.
- A highlighted selected commune.
- Zoom and pan functionality.
- Mode, departure-time, and travel-budget filters.
- A regional accessibility mode.
- A selected-commune travel-time mode.
- A legend with accessibility intervals.

Preserve these capabilities.

However, several problems remain.

**Problem 1 — The geographic map still looks like a conventional GIS plot.**

The map is functional but lacks the visual refinement of a modern interactive data journalism project.

**Problem 2 — The choropleth palette does not reveal variation optimally.**

Most regions use similar pale teal tones. Important differences between neighboring communes can be difficult to identify.

The palette needs a stronger perceptual progression without becoming overly saturated.

**Problem 3 — The legend is visually cluttered.**

There are many accessibility categories, and the legend takes up considerable horizontal space below the map.

It should be redesigned to communicate the color scale quickly and intuitively.

**Problem 4 — The selected commune is insufficiently emphasized.**

The orange selection outline is visible, but the selected commune could be highlighted more elegantly and meaningfully.

**Problem 5 — The map controls look generic.**

The current zoom controls resemble default mapping-library controls. They should be visually integrated into the dashboard's existing design system.

**Problem 6 — The map does not yet fully exploit spatial exploration.**

It displays geographic inequalities but could make them easier to understand through coordinated highlighting, map modes, intelligent labels, and location-aware tooltips.

---

## 2. CARTOGRAPHIC REDESIGN

Make the map look like a professionally designed geographic visualization from Financial Times Visual Journalism, Reuters Graphics, Observable, or a modern mobility intelligence platform.

### A. Map background

Use a sophisticated, restrained geographic background.

- Replace the flat-looking background with a subtle, uncluttered basemap if it improves orientation.
- Use a very light warm-gray or cool-gray geographic canvas.
- Preserve strong contrast between commune polygons and the background.
- Avoid satellite imagery.
- Avoid excessive roads, buildings, or points of interest.
- Make regional and departmental geography easily recognizable.
- Use consistent visual hierarchy among administrative boundaries.

The map should feel elegant, precise, and geographically informative.

### B. Administrative boundaries

Use three visual hierarchy levels:

**Commune boundaries**
- Thin, subtle lines.
- Avoid overpowering the choropleth.
- Increase boundary visibility when zoomed in.

**Department boundaries**
- Slightly thicker and more prominent.
- Clearly distinguish them from commune boundaries.
- Avoid overly bright white outlines.

**Selected commune**
- Strong, high-contrast outline.
- Distinct selection color that is not confused with choropleth values.
- Optional subtle halo.
- Maintain selection when the map pans, zooms, or changes scenario.

Do not alter administrative geometries.

### C. Professional choropleth color scale

The current scale includes:

- Under 0.1%.
- 0.1–0.5%.
- 0.5–1%.
- 1–3%.
- 3–10%.
- 10–25%.
- 25% or more.
- No route found within 90 minutes.

First, inspect the actual distribution of accessibility values.

Then improve the color scale.

Requirements:

1. Use a perceptually ordered sequential palette.
2. Ensure increasing accessibility is clearly associated with increasing color intensity.
3. Maintain sufficient contrast between neighboring categories.
4. Avoid having most communes look almost identical.
5. Make both low-accessibility and high-accessibility regions interpretable.
6. Test for accessibility and color-vision deficiencies.
7. Use a separate neutral color for missing or unavailable routing information.
8. Avoid treating missing travel times as zero accessibility.
9. Preserve comparability when switching between scenarios.

Consider well-established palettes such as **Viridis, Cividis, or carefully designed custom sequential color scales**.

You may also explore a refined teal-to-deep-blue palette that fits the dashboard's existing visual identity.

Do not use a rainbow color scale.

### D. Improve classification intelligently

Compare several classification strategies:

- Existing fixed intervals.
- Quantile classification.
- Natural breaks (Jenks).
- Logarithmic or power-transformed continuous scales.
- Domain-specific thresholds.

Choose the strategy that reveals useful spatial variation without distorting the interpretation.

Important:

If users compare weekday versus Saturday, the color legend must normally retain the same numerical meaning across both maps. Do not automatically recompute independent quantiles for each scenario and present the maps as directly comparable.

The legend must always expose the actual units and thresholds.

---

## 3. REDESIGN THE MAP LEGEND

The current legend occupies too much space and looks crowded.

Create a compact, polished legend integrated with the map.

Possible layout:

- Small floating legend in the bottom-left corner.
- White or translucent neutral background.
- Subtle border.
- Compact horizontal color bar.
- Clearly labeled minimum and maximum values.
- Meaningful intermediate thresholds.
- A distinct swatch for unavailable routing data.

Example:

**Regional jobs reachable**

Very low  ░▒▓██  Very high

Use actual threshold labels rather than relying solely on verbal categories.

If using discrete bins, display their exact numerical ranges.

If using a continuous scale, use an accurately labeled color ramp.

If there are many thresholds, avoid wrapping them into two rows of visually disconnected labels.

Make the legend responsive and ensure it never obscures important geographic information.

Consider an optional interactive legend that can highlight communes belonging to a selected accessibility interval.

---

## 4. MAKE THE MAP MORE INTERACTIVE

### A. Professional hover tooltip

On hovering over a commune, display a polished compact tooltip.

Include:

- Commune name.
- Department.
- Percentage of regional jobs reachable.
- Absolute number of jobs reachable.
- Number of employed residents, if available.
- Comparison with the regional median.
- Currently selected mode, departure scenario, and travel-time budget.

Example structure:

**Plaisir · Yvelines (78)**

Jobs within reach: **450,737**

Regional job accessibility: **7.4%**

Regional median: **32%**

Public transport · Tuesday 08:30 · 45 min

Use the actual data for the hovered commune and current scenario.

Avoid overly large tooltips.

Keep tooltips inside the viewport and reposition them near edges.

### B. Commune selection

Clicking a commune should:

- Highlight it on the map.
- Update the commune information panel.
- Preserve the geographic selection when filters change.
- Update related accessibility charts.
- Allow switching to the selected commune's travel-time exploration mode.

Ensure the selection color remains distinguishable from the choropleth.

### C. Map navigation

Improve pan and zoom behavior.

- Smooth zooming.
- Sensible initial bounds for Île-de-France.
- "Reset to Île-de-France" button.
- Zoom-to-selected-commune action.
- Double-click or appropriate shortcuts for zooming.
- Optional fullscreen mode.
- No disruptive map resets when switching scenarios.

Use professional, minimal map controls that match the rest of the application.

Avoid adding unnecessary controls.

---

## 5. SOLVE THE PARIS VISUALIZATION PROBLEM

Paris and the surrounding inner suburbs contain many small geographic areas.

At the scale of the entire Île-de-France region, some important spatial variations become difficult to see.

Implement a better exploration strategy.

Consider:

**Option A — Geographic inset**

A small inset map showing Paris and the inner suburbs at a larger scale.

**Option B — Zoom-to-Paris action**

A compact action that focuses on Paris and the petite couronne.

**Option C — Automatic detail enhancement**

When zoomed into dense areas, show more detailed commune boundaries and geographic labels.

Choose the solution that provides the best balance between clarity and simplicity.

Do not clutter the regional map with an unnecessarily large inset.

---

## 6. IMPROVE GEOGRAPHIC CONTEXT

The user should immediately understand where the areas are located.

Add restrained geographic reference information.

Potential features:

- Major city labels, such as Paris, Versailles, Meaux, Cergy, Évry, Melun, and other useful regional reference points.
- Department labels or a department boundary overlay.
- Optional RER and Transilien network overlay if accurate geographic data is available.
- Important transport hubs when relevant to the analysis.
- Better labels at higher zoom levels.

Use intelligent label density.

Avoid label collisions and clutter.

Labels should not overpower accessibility colors.

Do not invent station or transport-route geometries.

Any transport overlays must use real geographic data.

---

## 7. ADD MORE ANALYTICALLY USEFUL MAP MODES

The map should go beyond showing a single accessibility metric.

Introduce a compact metric selector supporting:

### Mode 1 — Regional job accessibility

Show the percentage or absolute number of regional jobs reachable within the selected travel-time budget.

Use a sequential choropleth scale.

### Mode 2 — Transit versus car gap

Show the difference between public transport and free-flow car accessibility for the same travel-time budget.

Use a clearly labeled difference metric.

Consider a diverging palette if values can be positive and negative, or a sequential palette if the metric is explicitly a nonnegative disadvantage.

### Mode 3 — Accessibility loss outside peak hours

Show how accessibility differs between the selected departure scenario and weekday morning peak.

For example:

Accessibility at Tuesday 05:00 minus accessibility at Tuesday 08:30.

Use consistent units, preferably percentage points for shares of jobs.

Use a diverging palette centered at zero when appropriate.

### Mode 4 — Additional access from longer travel times

Show the extra number or percentage points of jobs reachable when increasing the travel-time budget from 30 to 45 or 60 minutes.

### Mode 5 — Underserved employed residents

Highlight communes below a chosen accessibility threshold, with attention to the number of employed residents affected.

For absolute counts, use an appropriate visual encoding and explain that larger communes naturally tend to contain more residents.

Only implement metrics supported by existing data.

Ensure each mode has an appropriate scale and legend.

---

## 8. IMPROVE SELECTED-COMMUNE REACHABILITY MODE

My dashboard already supports switching between:

- Regional access.
- From a commune.

Make the second mode much more visually compelling.

When users select "From a commune":

1. Mark the origin commune clearly.
2. Display destination communes colored by travel time.
3. Distinguish reachable and unreachable areas.
4. Make the selected time budget visually explicit.
5. Allow switching between 30, 45, and 60 minutes.
6. Update the total number of reachable jobs.
7. Maintain a readable legend in minutes.
8. Preserve the selected origin as filters change.

Consider an **isochrone-style visualization** if the available routing data supports it.

If only commune-to-commune travel-time matrices are available, use destination-commune coloring instead of constructing inaccurate continuous isochrone polygons.

Important: Do not assume everything inside a colored commune is reachable within the same travel time. The existing calculations use representative commune locations.

Clearly communicate this approximation.

---

## 9. MAKE THE MAP THE VISUAL CENTERPIECE

Maintain the map-first layout, but improve the proportions and available space.

- Maximize geographic area without cropping important communes.
- Fit the region properly inside the map container.
- Preserve its geographic aspect ratio.
- Reduce unnecessary internal padding.
- Keep the map toolbar compact.
- Place legends and map controls unobtrusively.
- Make the geographic canvas feel larger and more immersive.
- Avoid visually heavy borders and cards.

The map must coexist with the selected-commune analysis panel.

Do not require users to scroll to compare
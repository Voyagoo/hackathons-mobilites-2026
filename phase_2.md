# PROMPT: Redesign and Improve My Île-de-France Mobility Hackathon Dashboard

You are a **senior data visualization designer, geospatial analytics engineer, UX/UI expert, and data storytelling specialist**, with experience creating award-winning interactive dashboards and public-policy visualizations.

I am participating in **Hackaviz Mobilités 2026 — Challenge 2: Mobility and Employment in Île-de-France**.

**Your task is to significantly improve the existing application, both visually and functionally, while preserving the analytical rigor, existing data, and underlying computations.**

I want a dashboard that looks like a professional interactive data journalism project or a high-quality urban mobility intelligence platform, rather than a collection of plots in a long webpage.

Do not merely suggest improvements. **Inspect my existing codebase, implement the redesign, and deliver a working application.**

---

## 1. MAIN OBJECTIVE

Transform the dashboard into a beautiful, coherent, interactive, map-centered experience that helps users understand:

1. How many jobs residents can reach from different communes in Île-de-France.
2. How accessibility differs between public transport and cars.
3. How accessibility changes throughout the day, particularly for workers with nonstandard schedules.
4. Which communes and departments are most underserved.
5. How job accessibility is associated with the income characteristics of residential communes.
6. Which areas should receive priority for further investigation or mobility interventions.

The dashboard should answer these questions visually, with minimal effort from the user.

**My primary objective is to create an outstanding hackathon submission that impresses judges through visual clarity, interactive exploration, compelling storytelling, analytical credibility, and decision-making value.**

---

## 2. CRITICAL PROBLEM WITH THE CURRENT DASHBOARD

The current application has several major UX problems:

- It requires excessive vertical scrolling to see different charts.
- Users cannot easily compare the map with the statistical plots.
- The main geographic map is relatively small despite being the most important visualization.
- There is substantial unused whitespace around the maps.
- Maps, charts, and metrics feel like separate visualizations rather than one connected analytical system.
- The color scheme does not adequately reveal differences between low-accessibility communes.
- The introduction occupies too much valuable screen space.
- Five KPI cards compete for attention.
- There are too many prominent filter controls.
- The visual hierarchy is weak.
- The most important discoveries are not immediately obvious.
- Some charts require too much interpretation.
- The dashboard primarily describes inequalities rather than helping identify planning priorities.
- The selected commune's information is not sufficiently integrated into the main dashboard.

**The most important requirement: eliminate the need to scroll between the main map and its related visualizations.**

Scrolling may still be used for methodology, detailed analysis, or guided storytelling, but the primary analytical workspace must remain within one desktop viewport.

---

## 3. REDESIGN THE PAGE ARCHITECTURE

Replace the existing long, vertically stacked dashboard with a modern analytical workspace.

Use a structure similar to:

### A. Compact header

Create a slim navigation bar containing:

- Product name: "Access to Work | Île-de-France"
- Subtitle: Hackaviz Mobilités 2026
- Navigation: Explore | Compare | Equity | Methodology
- An optional "Key findings" action

Avoid an excessively large header.

### B. Strong analytical headline

Display a concise, powerful headline such as:

**"Same region. Very different access to work."**

Follow it with one short sentence explaining the analysis.

Do not occupy half the screen with introductory paragraphs.

### C. Compact KPI section

Display a maximum of three prominent KPIs for the selected scenario.

For the existing default scenario — public transport, Saturday around 08:30, within 30 minutes — possible KPIs include:

- 3.0%: regional jobs reachable by the median employed resident.
- 58%: employed residents reaching less than 5% of regional jobs.
- 49%: regional jobs reachable by the median employed resident by car under free-flow conditions.

Use accurate labels and clearly distinguish figures belonging to different transport scenarios.

Important: do not invent data, calculate percentages incorrectly, or confuse a median accessibility percentage with a percentage of residents.

All KPI values must come from the existing dataset and update correctly when the selected scenario changes.

### D. Single-screen analytical workspace

Target a polished desktop experience at 1440 × 900 or 1600 × 900.

Suggested layout:

- Left area: approximately 60–65% of the available width, dedicated to a large interactive geographic map.
- Right area: approximately 35–40%, dedicated to the selected commune and its associated statistics.
- Bottom area: compact synchronized comparison charts, or a tabbed analytical panel.
- Filters: a single compact toolbar above the map.

The main workspace must fit inside the viewport without requiring the user to scroll to see the map and primary statistical comparisons.

Use CSS Grid or Flexbox to create a responsive layout.

Do not make every chart permanently visible. Prioritize the most important views and use tabs or expandable panels for secondary analyses.

---

## 4. MAIN MAP: MAKE IT THE CENTERPIECE

The geographic map is the most important visual element.

Significantly improve its design.

### Geographic presentation

- Make the map substantially larger.
- Eliminate excessive whitespace.
- Fit the Île-de-France geographic extent intelligently.
- Maintain the correct geographic aspect ratio.
- Use subtle commune boundaries.
- Highlight department boundaries without overwhelming the map.
- Add informative geographic labels where practical.
- Consider a subtle basemap or transport-network overlay.
- Ensure Paris and the surrounding departments are recognizable.
- Support smooth zooming and panning.
- Provide useful hover tooltips.
- Highlight selected communes consistently.

### Improve the choropleth color scale

The current map uses large regions of nearly identical dark blue, which hides variation among the worst-served communes.

Choose a more effective scale that reveals the distribution of job accessibility.

Consider a perceptually ordered sequential palette, with suitable transformations or breaks if the data is heavily skewed.

For example, evaluate intervals around:

- 0–0.5%
- 0.5–1%
- 1–3%
- 3–10%
- 10–25%
- Above 25%

These are illustrative thresholds. Inspect the actual distribution before deciding on the final scale.

The legend must be easy to understand.

Never hide meaningful zero values, missing values, or unreachable destinations by incorrectly assigning them the same color.

Use a restrained, accessible, colorblind-conscious palette.

### Add an interactive map metric selector

Allow users to switch between:

1. Percentage of regional jobs reachable.
2. Absolute number of jobs reachable.
3. Public transport versus car accessibility gap.
4. Gain in reachable jobs when increasing the travel-time budget from 30 to 45 or 60 minutes.
5. Number of employed residents in communes below a selected accessibility threshold.

Only implement metrics that can be correctly derived from the existing data.

Do not invent indicators or introduce unsupported assumptions.

### Rich commune interaction

Clicking a commune must update the entire associated analytical panel.

Display:

- Commune name.
- Department.
- Number and share of jobs reachable.
- Accessibility by public transport.
- Accessibility by car, explicitly labeled free-flow.
- Difference between modes.
- Regional accessibility ranking or percentile, if computable.
- Comparison with the regional median.
- Accessibility profile across the available departure times.
- Relevant income context, when available.

The selected commune must remain highlighted on the map.

Add a commune search box with autocomplete if practical.

---

## 5. SYNCHRONIZE ALL VISUALIZATIONS

This is one of the most important improvements.

The dashboard must behave as **one coordinated analytical system**, not as five separate plots.

All applicable visualizations should respond coherently when the user changes:

- Transport mode.
- Departure scenario.
- Travel-time budget.
- Selected commune.
- Selected department.
- Map metric.

Examples:

When the user clicks a commune:

- The map highlights that commune.
- The side panel displays its accessibility statistics.
- The time-of-day chart highlights or displays its accessibility profile.
- The department comparison shows the corresponding department.
- The equity view can show relevant income context.

When the user changes from weekday 08:30 to weekday 05:00:

- The choropleth updates.
- The KPI values update.
- The accessibility distribution updates.
- The selected commune remains selected.
- Labels and explanatory text update accordingly.

Implement a single coherent state-management architecture.

Do not reload the full webpage on every interaction.

---

## 6. REPLACE THE MAIN STACKED BAR CHART WITH A CLEARER COMPARISON

The existing dashboard includes a 100% stacked horizontal bar chart comparing public transport at several times of day and free-flow car access.

It currently uses five accessibility categories:

- Under 1% of regional jobs.
- 1–5%.
- 5–20%.
- 20–50%.
- Over 50%.

Preserve this information, but make the default presentation simpler.

### Primary comparison

Create a compact horizontal bar chart showing:

**Percentage of employed residents who can reach less than 5% of regional jobs within the selected time budget.**

Compare the available scenarios:

- Car, free-flow.
- Public transport, weekday around 05:00.
- Public transport, weekday around 08:30.
- Public transport, weekday around 12:00.
- Public transport, weekday around 22:30.
- Public transport, Saturday around 08:30.

Use the actual values from the existing dataset.

Make the current selection visually prominent.

Use clear direct labels and avoid unnecessary legends.

### Secondary comparison

Retain the original five-category accessibility distribution in an expandable detail view or alternative chart tab.

Avoid repeating the same information in multiple charts unless the different presentation clearly adds insight.

---

## 7. MAKE TIME-OF-DAY ACCESSIBILITY A SIGNATURE FEATURE

One of the strongest aspects of the project is the ability to compare transport accessibility across different departure times.

Make this visually memorable.

Create a compact time-of-day accessibility profile.

Possible presentation:

- Horizontal timeline with the available departure scenarios.
- A line chart showing how job accessibility changes.
- Interactive scenario buttons.
- A synchronized map that updates when a scenario is selected.
- Smooth but restrained transitions.

Show how access differs for workers who travel during early shifts, conventional peak hours, midday, late shifts, and weekends.

Clearly separate weekday and Saturday scenarios. Do not connect them as if they were one continuous chronological time series.

If implementing an animation, only use actual computed scenarios. Do not interpolate between times in a way that suggests unmeasured travel-time results.

A user should understand the impact of departure time within a few seconds.

---

## 8. TRANSFORM COMMUNE EXPLORATION INTO AN INTERACTIVE EXPERIENCE

The current dashboard contains a separate travel-time map for a selected commune.

Instead of placing this as another full-height section, integrate it into the main explorer.

When a commune is selected, users should be able to switch the main map between:

**Regional Accessibility Map** and **Reachability from Selected Commune**.

The second mode should display travel times from the selected commune to other communes.

Features:

- Clearly mark the origin commune.
- Display travel time using an intuitive continuous color scale.
- Show reachable areas within 30, 45, and 60 minutes.
- Distinguish missing routing results from destinations beyond the maximum time.
- Show the number of jobs reachable within each threshold.
- Add a compact accessibility-versus-travel-time curve beside the map.

If possible, allow users to adjust the travel-time budget with an interactive slider.

For example:

At 30 minutes, display reachable jobs and destinations.

At 45 minutes, update the reachable area and total.

At 60 minutes, show the additional accessibility gained.

This feature should feel like an interactive transport accessibility simulator, while remaining faithful to the precomputed data.

Do not suggest that increasing the allowed travel time is equivalent to improving the transport network.

---

## 9. IMPROVE DEPARTMENT COMPARISONS

The current chart compares accessibility across Paris and the seven surrounding departments using dots and percentile ranges.

Preserve its analytical information but improve the design.

Requirements:

- Sort departments by accessibility, or offer intuitive sorting.
- Make public transport and car values immediately distinguishable.
- Keep color semantics consistent across the whole application.
- Show the median as a clear point.
- Explain the percentile range without relying on a long caption.
- Add a regional median reference.
- Highlight the selected department.
- Support useful hover information.
- Avoid unnecessary gridlines and visual noise.

Place this chart under the "Equity" or "Territorial differences" view, rather than forcing users to scroll past a full-height panel.

---

## 10. IMPROVE INCOME AND ACCESSIBILITY ANALYSIS

The existing dashboard compares accessibility across five groups of residential communes based on their income characteristics.

This is an important finding and should be made much more visually compelling.

For the current Saturday scenario, the existing analysis reports approximately:

- 5.8% of regional jobs reachable on average for residents in the lowest income-group fifth of communes.
- 13% for residents in the highest income-group fifth.

Preserve the exact computed values.

### Suggested design

Use a concise headline comparing the two extremes, followed by a connected-dot chart or compact trend chart across all five income groups.

Allow users to distinguish:

- Public transport at the selected time.
- Public transport at weekday peak.
- Car under free-flow conditions.

Avoid grouping too many bars with similar colors.

Consider including an accessibility gap between the lowest and highest income groups.

### Critical methodological requirement

The income indicator comes from the commune of residence, not directly from each individual.

Therefore, use wording such as:

"Residents of lower-income communes have lower access to employment opportunities."

Do not claim the analysis proves individual-level income inequality or causality.

Maintain the existing resident-weighting methodology.

---

## 11. ADD AN ACTIONABLE PRIORITY VIEW

To make the application more valuable to public-policy decision-makers, add a dedicated view:

**"Where should we investigate mobility improvements first?"**

This should identify communes or territories facing significant job accessibility challenges.

Potential criteria:

- Low public transport job accessibility.
- Large numbers of affected employed residents.
- Strong disadvantage during early or late working hours.
- Large public transport versus free-flow car accessibility gaps.
- Lower residential commune income.

Create a transparent ranking or multi-criteria exploration.

For example, display:

- Top underserved communes by affected employed population.
- Most severe off-peak accessibility losses.
- Areas with large numbers of workers and low potential job accessibility.
- Commune-specific contextual explanations.

If a composite score is introduced, clearly disclose its formula, weights, and limitations. Prefer an interpretable ranking by a specific metric over an arbitrary black-box score.

**Do not claim that a particular bus route or infrastructure project is the optimal solution without analyzing the actual network intervention.**

Present these areas as candidates for further investigation.

The aim is to make the dashboard actionable without overstating what the data proves.

---

## 12. INTRODUCE A GUIDED DATA STORY

Add a short "Key findings" or "Discover the story" experience.

This should introduce the three strongest conclusions:

### Story 1 — Geography matters

Residents do not have equal access to the region's employment opportunities.

Use the regional choropleth and a concise headline.

### Story 2 — Time matters

Public transport accessibility changes considerably between weekday peak hours, early mornings, late evenings, and weekends.

Use a clear synchronized temporal comparison.

### Story 3 — Inequality matters

Accessibility gaps have territorial and socioeconomic dimensions.

Use the department and commune-income comparisons.

Each story step should highlight the relevant visualization and provide a short, precise explanation.

Avoid overwhelming users with paragraphs.

Make the story persuasive without exaggerating the findings.

Provide a way to return to unrestricted exploration.

---

## 13. USE PROFESSIONAL VISUAL DESIGN

The current dashboard needs a complete visual design upgrade.

Aim for a modern, elegant interface inspired by high-quality work from:

- Observable / Observable Plot.
- Reuters Graphics.
- Financial Times Visual & Data Journalism.
- The Pudding.
- Datawrapper.
- Mapbox interactive storytelling.
- Conveyal accessibility analysis.
- Remix transit accessibility tools.

Research relevant real-world examples online when internet access is available.

Use them as inspiration for layout, visual hierarchy, interaction, and storytelling. Do not blindly copy existing designs.

### Visual design requirements

- Restrained, cohesive color palette.
- Strong typography hierarchy.
- Professional spacing.
- Minimal card borders.
- Reduced decorative elements.
- Clean tooltips.
- Compact controls.
- Accessible contrast.
- Meaningful color encoding.
- Subtle interactions and transitions.
- Consistent chart typography.
- Consistent map and chart color semantics.
- Clear selected, hovered, and inactive states.
- Responsive behavior.

Avoid:

- Excessively large titles.
- Too many KPI cards.
- Huge empty margins.
- Large repeated legends.
- Multiple competing accent colors.
- Unnecessary shadows.
- Decorative gradients with no analytical purpose.
- Overly complex animations.
- Tiny map features.
- Dense plots with unreadable labels.
- Full-screen chart containers with relatively little information.

Use a cohesive aesthetic suited to a serious public-policy and geospatial intelligence project, not a generic SaaS admin dashboard.

---

## 14. FILTER AND INTERACTION IMPROVEMENTS

Simplify the current controls into a compact toolbar.

Suggested controls:

**Mode:** Public transport | Car (free-flow)

**Departure:** Weekday 05:00 | Weekday 08:30 | Weekday 12:00 | Weekday 22:30 | Saturday 08:30

**Travel-time budget:** 30 | 45 | 60 minutes

When car is selected, make clear that its travel times do not vary by departure time in the current model. Disable or hide the departure-time selector appropriately.

Use a time slider only if the available scenarios can be represented accurately. Otherwise, discrete scenario buttons are preferable.

Preserve the user's current filters when navigating between Explore, Compare, and Equity.

Ensure all components update consistently.

---

## 15. PERFORMANCE AND LARGE-DATA HANDLING

The application must remain responsive.

Inspect the existing data-loading architecture and improve it where needed.

Recommendations:

- Reuse existing precomputed accessibility and routing data.
- Avoid loading unnecessary raw datasets into the browser.
- Precompute summaries for each mode, time, and travel-time budget.
- Store metrics in efficient compact formats.
- Use optimized geographic geometry.
- Simplify geometry for regional views where appropriate.
- Avoid rerendering all commune polygons unnecessarily.
- Cache repeated computations.
- Use efficient lookup structures for commune selection.
- Lazy-load secondary analytical views when appropriate.
- Use vector-map rendering if beneficial.
- Avoid expensive operations during hover interactions.

Do not introduce a new backend or dependency merely for aesthetic reasons.

Inspect the existing stack first and preserve compatible technologies where possible.

---

## 16. SCIENTIFIC RIGOR AND TRANSPARENCY

The redesign must not compromise analytical correctness.

The existing methodology includes:

- INSEE 2023 employment data.
- INSEE employed-resident counts.
- INSEE Filosofi income indicators.
- Île-de-France Mobilités GTFS timetables.
- OpenStreetMap.
- Conveyal R5 / r5py travel-time calculations.
- Departure windows centered around the indicated time.
- Public transport travel times based on the 25th percentile.
- Walking and waiting times.
- Car travel times without congestion.
- Commune-level origin and destination approximations using representative stations.
- Scheduled scenarios in November 2026.

Preserve these details.

Important caveats:

1. The 25th percentile represents relatively favorable travel times and should not be mislabeled as the median.
2. The use of each commune's busiest station may overestimate transit accessibility for residents far from that station.
3. Free-flow car accessibility is optimistic relative to congested conditions.
4. Reachable jobs represent potential geographic opportunities, not guaranteed jobs or occupation-matched vacancies.
5. Commune-level income comparisons cannot establish individual-level causal relationships.
6. Missing travel-time data must not be confused with genuine inaccessibility.
7. Population-weighted statistics must remain weighted correctly.
8. Travel-time and accessibility comparisons must always use compatible scenarios.

Put the complete methodology in a clean, expandable view.

Display shorter caveats in context, particularly when showing car comparisons or income-based findings.

Do not change the analytical results merely to make the visualization more dramatic.

---

## 17. RESPONSIVE DESIGN AND ACCESSIBILITY

Prioritize the desktop presentation for hackathon evaluation, but support smaller screens.

For desktop:

- Main map and associated plots should remain visible without vertical scrolling.
- Keep controls compact.
- Avoid clipping, overflow, or overlapping components.

For tablets:

- Adjust the proportions of the map and analysis panel.
- Consider collapsible secondary charts.

For mobile:

- Use a map-first layout.
- Display commune details in a bottom sheet or collapsible panel.
- Replace large side-by-side comparisons with mobile-friendly alternatives.

Ensure keyboard accessibility, readable contrast, and sensible tooltip behavior.

Do not use color alone to communicate important differences.

---

## 18. IMPLEMENTATION REQUIREMENTS

You have access to my existing project codebase.

Work directly with it.

Follow this process:

**Step 1 — Audit**

Inspect:

- Project structure.
- Frontend framework.
- Map library.
- Charting library.
- Current data-loading process.
- Existing filters and state.
- Calculation functions.
- Performance bottlenecks.
- Styling and responsive behavior.

**Step 2 — Redesign**

Define a coherent architecture for the new interface.

Choose reusable components, for example:

- AppShell
- ScenarioToolbar
- KeyMetrics
- AccessibilityMap
- CommuneDetails
- ScenarioComparison
- AccessibilityDistribution
- TimeOfDayProfile
- DepartmentComparison
- IncomeAccessibility
- PriorityAreas
- MethodologyPanel
- StoryMode

These are illustrative component names, not mandatory files.

**Step 3 — Implement**

Modify the existing code and build the improved application.

Preserve the underlying computations unless a genuine bug is identified.

Avoid rewriting working analytical code unnecessarily.

Implement synchronized interactions and clean state handling.

**Step 4 — Validate**

Check:

- All filters.
- All existing scenarios.
- Commune selection.
- Map rendering.
- Legend correctness.
- KPI correctness.
- Chart synchronization.
- Missing data.
- Mobile layout.
- Desktop layout.
- Performance.
- Console errors.
- Accessibility.

Verify that displayed values match the original computed results.

**Step 5 — Polish**

Refine visual spacing, typography, responsive breakpoints, chart labels, interactive feedback, and information hierarchy.

Test at 1440 × 900, 1600 × 900, and at least one mobile viewport.

At desktop resolution, verify explicitly that users can see the main map and the primary comparisons simultaneously without scrolling.

---

## 19. SUCCESS CRITERIA

The final dashboard should satisfy these requirements:

- A first-time visitor understands the core message in under five seconds.
- A judge can compare two mobility scenarios in under ten seconds.
- A user can select a commune and understand its employment accessibility immediately.
- The main map and primary chart comparisons are simultaneously visible on desktop.
- The choropleth clearly reveals spatial differences.
- The income comparison communicates the socioeconomic pattern accurately.
- The dashboard tells a coherent story.
- The application can identify potentially underserved territories.
- The experience is smooth and responsive.
- The UI looks professionally designed.
- All numbers remain scientifically correct.
- Important methodological limitations remain transparent.
- The dashboard is memorable and demonstrably useful.

---

## 20. DESIGN REFERENCES

Use these references for inspiration:

- https://observablehq.com/
- https://www.datawrapper.de/
- https://www.reuters.com/graphics/
- https://www.ft.com/visual-and-data-journalism
- https://pudding.cool/
- https://docs.conveyal.com/analysis/
- https://docs.mapbox.com/mapbox-gl-js/example/mapbox-gl-compare/
- https://maplibre.org/
- https://deck.gl/

Pay particular attention to:

- Coordinated multiple views.
- Interactive geographic exploration.
- Direct comparison of scenarios.
- Small multiples.
- Map-based storytelling.
- Interactive legends.
- Brushing and linking.
- High-information-density layouts.
- Clear visual hierarchy.
- Decision-oriented analytics.

---

## 21. PRIORITIES

If implementation time is limited, prioritize in this order:

**P0 — Essential**

1. Transform the long scrolling webpage into a map-centered analytical workspace.
2. Make the map significantly larger and visually more informative.
3. Place the main comparison charts next to the map.
4. Simplify the header, KPIs, and filters.
5. Make commune selection update a synchronized detail panel.
6. Preserve all existing scientific calculations.

**P1 — High impact**

7. Add an effective scenario comparison.
8. Improve the time-of-day visualization.
9. Improve the income-accessibility comparison.
10. Add a compelling three-part data story.
11. Improve color scales and legends.

**P2 — Differentiation**

12. Add accessible-area exploration from a selected commune.
13. Add a transparent underserved-area ranking.
14. Add synchronized map comparison or swipe interaction.
15. Add subtle transitions and additional visual polish.

Implement the highest-impact features fully before adding advanced features.

---

## 22. FINAL INSTRUCTIONS

Be ambitious with the visual redesign but disciplined about the underlying data.

I do not want another generic dashboard with vertically stacked Plotly charts.

I want an integrated, beautiful, interactive **Mobility and Employment Accessibility Explorer for Île-de-France** that combines the strengths of a modern geospatial application, an analytical decision-support tool, and an interactive data-journalism story.

**Work directly on my project and make the improvements rather than merely explaining what should be done.**

Do not fabricate metrics, analyses, maps, routing results, or policy outcomes.

Do not unnecessarily discard existing functionality.

Use actual data from my project and verify each new visualization against it.

Make justified design decisions autonomously. Use the existing technology stack where reasonable, and only introduce new libraries when they provide a clear benefit.

The goal is not to display the maximum number of charts.

**The goal is to reveal the most important insights with the minimum cognitive effort while providing rich exploration for users who need it.**

Deliver a complete, polished, working implementation suitable for presenting to a hackathon jury.

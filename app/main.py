"""Dash app: "Access to Work | Île-de-France", a map-centred workspace (phase 2).

Dash runs on its FastAPI backend, so `server` is a FastAPI app:

    uv run uvicorn app.main:server --reload

The app only reads data/processed/ (see pipeline/__init__.py); it never runs the router.

State lives in the controls themselves: `view` (left navigation), `mode`, `time`, `budget`
(toolbar), `metric` (map), `commune` (search box, also set by clicking a map or a ranking row).
Every view reads those six values, and only the visible view is recomputed.
"""

import os
from pathlib import Path

import pandas as pd
from dash import Dash, Input, Output, State, ctx, dash_table, dcc, html, no_update

from app import data, figures
from pipeline.config import THRESHOLDS_MIN

APP_DIR = Path(__file__).resolve().parent
# Development aid: open the app on a given view or commune (used for screenshots), e.g.
#   ATW_VIEW=equity ATW_COMMUNE=77317 uv run uvicorn app.main:server
START_VIEW = os.environ.get("ATW_VIEW", "explore")
START_COMMUNE = os.environ.get("ATW_COMMUNE") or None
START_FOCUS = os.environ.get("ATW_FOCUS", "region")        # region | paris | selection
START_MAP_MODE = os.environ.get("ATW_MAPMODE", "region")   # region | reach
# Scroll to zoom, drag to pan, double-click to reset. The default toolbar is hidden: zoom presets
# are the "Zoom to" buttons drawn on the map in the dashboard's own style.
MAP_CONFIG = {"displaylogo": False, "scrollZoom": True, "displayModeBar": False, "doubleClick": "reset",
              "modeBarButtons": [
    ["zoomInMap", "zoomOutMap", "resetViewMap"] if figures.MAPLIBRE else ["zoomInGeo", "zoomOutGeo", "resetGeo"]
]}
CHART_CONFIG = {"displayModeBar": False}

VIEWS = {
    "explore": ("Explore", "Same region. Very different access to work.",
                "How many of the region's jobs residents can reach, by mode, time of day and travel budget."),
    "compare": ("Compare", "Compare access across scenarios",
                "Same map, same scale, two scenarios side by side."),
    "equity": ("Equity", "Who is left behind?",
               "Territorial and income differences in access to work."),
    "commune": ("Commune", "Explore a commute from any commune",
                "Where a journey can take you from one origin, and the jobs within reach."),
    "priorities": ("Priorities", "Where should we investigate first?",
                   ("Low-access communes ranked by employed residents affected. Candidates for study, "
                   "not project recommendations.")),
    "method": ("Method", "Method and limits", "Sources, routing assumptions and what the figures do not show."),
}

app = Dash(
    __name__,
    backend="fastapi",
    title="Access to Work | Île-de-France",
    assets_folder=str(APP_DIR / "static"),
    suppress_callback_exceptions=True,
)
server = app.server


# --- Small formatting and HTML helpers ----------------------------------------

def pct(fraction: float) -> str:
    """Format a 0-1 share as a percentage, with one decimal under 10%."""
    if fraction is None or pd.isna(fraction):
        return "n/a"
    value = 100 * fraction
    return f"{value:.1f}%" if value < 10 else f"{value:.0f}%"


def scenario_text(scenario: str, budget: int) -> str:
    mode = "car, free-flow" if scenario == data.CAR else f"public transport · {data.SHORT_LABELS[scenario]}"
    return f"{mode} · {budget} min"


def overline(text: str) -> html.P:
    return html.P(text, className="overline")


def legend(spec: dict) -> list:
    """Compact map legend: a segmented colour bar with the class boundaries labelled underneath.

    `spec` comes from figures.legend_spec or figures.reach_legend_spec.
    """
    n = len(spec["colors"])
    ticks = [html.Span(label, style={"left": f"{100 * (i + 1) / n:.2f}%"}) for i, label in enumerate(spec["ticks"])]
    if "ends" in spec:
        ticks = [html.Span(spec["ends"][0], style={"left": "0%"}, className="end-left"), *ticks,
                 html.Span(spec["ends"][1], style={"left": "100%"}, className="end-right")]
    extras = [html.Span([html.I(style={"background": color}), label], className="chip")
              for label, color in spec["extras"]]
    return [
        html.Span(spec["title"], className="legend-title"),
        html.Div([html.I(style={"background": c}) for c in spec["colors"]], className="legend-bar"),
        html.Div(ticks, className="legend-ticks"),
        html.Div(extras, className="legend-extras"),
    ]


def map_box(graph_id: str, legend_id: str, *overlays) -> html.Div:
    """A map with its legend (bottom left) and optional controls floating on top of it."""
    return html.Div(className="map-wrap", children=[
        graph(graph_id, MAP_CONFIG),
        html.Div(id=legend_id, className="map-legend"),
        *overlays,
    ])


def bar_row(label: str, value: float, color: str, selected: bool) -> html.Div:
    return html.Div(className="bar-row is-selected" if selected else "bar-row", children=[
        html.Span(label, className="bar-label"),
        html.Div(html.Div(style={"width": f"{min(value, 100):.1f}%", "background": color}), className="bar-track"),
        html.Span(f"{value:.1f}%" if value < 10 else f"{value:.0f}%", className="bar-value"),
    ])


def stat(label: str, value: str, note: str = "", tone: str = "") -> html.Div:
    return html.Div(className=f"stat {tone}".strip(), children=[
        html.Span(label, className="stat-label"), html.Strong(value), html.Span(note, className="stat-note"),
    ])


def card(*children, class_name: str = "", **kwargs) -> html.Section:
    return html.Section(list(children), className=f"card {class_name}".strip(), **kwargs)


def graph(graph_id: str, config: dict, class_name: str = "fill") -> dcc.Graph:
    return dcc.Graph(id=graph_id, config=config, className=class_name, responsive=True,
                     style={"height": "100%", "width": "100%"})


# --- Layout -------------------------------------------------------------------

def _toolbar(scenarios: list[str]) -> html.Div:
    slots = [s for s in data.SCENARIO_ORDER if s in scenarios and s != data.CAR]
    communes = data.communes().sort_values("name")
    return html.Div(className="toolbar", role="group", **{"aria-label": "Scenario"}, children=[
        html.Div(className="tool", children=[
            html.Span("Mode", className="tool-label"),
            dcc.RadioItems(id="mode", className="pills", inline=True, value="transit", options=[
                {"label": "Public transport", "value": "transit"},
                {"label": "Car · free-flow", "value": "car", "disabled": data.CAR not in scenarios},
            ]),
        ]),
        html.Div(className="tool", children=[
            html.Span("Depart", className="tool-label"),
            dcc.RadioItems(id="time", className="pills", inline=True,
                           value=data.PEAK_TRANSIT if data.PEAK_TRANSIT in slots else slots[0],
                           options=[{"label": data.SHORT_LABELS[s], "value": s} for s in slots]),
        ]),
        html.Div(className="tool", children=[
            html.Span("Budget", className="tool-label"),
            dcc.RadioItems(id="budget", className="pills", inline=True, value=45,
                           options=[{"label": f"{t} min", "value": t} for t in THRESHOLDS_MIN]),
        ]),
        html.Div(className="tool tool-search", children=[
            dcc.Dropdown(id="commune", placeholder="Search a commune…", clearable=True, value=START_COMMUNE,
                         options=[{"label": f"{r['name']} ({r['dept']})", "value": r["code"]}
                                  for _, r in communes.iterrows()]),
        ]),
    ])


def _explore() -> html.Div:
    return html.Div(id="view-explore", className="view view-explore", children=[
        html.Div(id="kpis", className="kpis", **{"aria-live": "polite"}),
        card(
            html.Div(className="card-head", children=[
                html.Div([overline("Regional map"), html.H2(id="map-title"), html.P(id="map-sub", className="sub")]),
                html.Div(className="map-mode", children=[
                    html.Span("Map", className="tool-label"),
                    dcc.RadioItems(id="map-mode", className="pills", inline=True, value=START_MAP_MODE, options=[
                        {"label": "Regional access", "value": "region"},
                        {"label": "From a commune", "value": "reach"},
                    ]),
                ]),
                html.Div(className="metric-select", children=[
                    html.Label("Map shows", htmlFor="metric", className="tool-label"),
                    dcc.Dropdown(id="metric", clearable=False, searchable=False, value="share",
                                 options=[{"label": spec["label"], "value": key}
                                          for key, spec in data.METRICS.items()]),
                ]),
            ]),
            map_box("explore-map", "explore-legend", html.Div(className="map-tools", children=[
                html.Span("Zoom to", className="tool-label"),
                dcc.RadioItems(id="focus", className="pills", inline=True, value=START_FOCUS, options=[
                    {"label": "Île-de-France", "value": "region"},
                    {"label": "Paris & inner ring", "value": "paris"},
                    {"label": "Selected commune", "value": "selection"},
                ]),
                dcc.Checklist(id="overlay", className="pills", inline=True,
                              value=["rail"] if data.has_rail() else [],
                              options=[{"label": "Rail network", "value": "rail", "disabled": not data.has_rail()}]),
            ])),
            html.P(id="map-note", className="caveat"),
            class_name="map-card",
        ),
        card(id="explore-panel", class_name="panel"),
    ])


def _compare(scenarios: list[str]) -> html.Div:
    ordered = [s for s in data.SCENARIO_ORDER if s in scenarios]
    default = data.SATURDAY_SLOT if data.SATURDAY_SLOT in ordered else ordered[-1]
    return html.Div(id="view-compare", className="view view-compare hidden", children=[
        card(id="cmp-head", class_name="cmp-head"),
        card(
            overline("A · follows the toolbar"), html.H2(id="cmp-title-a"),
            html.Div(graph("cmp-map-a", MAP_CONFIG), className="map-wrap"),
            class_name="map-card",
        ),
        card(
            html.Div(className="card-head", children=[
                html.Div([overline("B · choose a scenario"), html.H2(id="cmp-title-b")]),
                html.Div(className="metric-select", children=[
                    dcc.Dropdown(id="cmp-right", clearable=False, searchable=False, value=default,
                                 options=[{"label": data.SHORT_LABELS[s], "value": s} for s in ordered]),
                ]),
            ]),
            html.Div(graph("cmp-map-b", MAP_CONFIG), className="map-wrap"),
            class_name="map-card",
        ),
        card(html.Div(id="cmp-legend", className="map-legend inline"), html.P(id="cmp-finding", className="finding"),
             class_name="cmp-foot"),
    ])


def _equity() -> html.Div:
    return html.Div(id="view-equity", className="view view-equity hidden", children=[
        card(
            overline("Territorial lens"), html.H2("Explore the accessibility divide"),
            html.P(id="equity-sub", className="sub"),
            map_box("equity-map", "equity-legend"),
            class_name="map-card",
        ),
        card(
            overline("Income context"), html.H2("An unequal starting point"),
            html.Div(id="income-head", className="stat-row"),
            html.Div(graph("income-fig", CHART_CONFIG), className="chart-wrap"),
            html.P("Commune-level median income, fifths of employed residents. An association between places, "
                   "not a cause.", className="caveat"),
            class_name="chart-card",
        ),
        card(
            overline("Territorial comparison"), html.H2("Department differences"),
            html.P(id="dept-sub", className="sub"),
            html.Div(graph("dept-fig", CHART_CONFIG), className="chart-wrap"),
            class_name="chart-card",
        ),
    ])


def _commune() -> html.Div:
    return html.Div(id="view-commune", className="view view-commune hidden", children=[
        card(
            overline("Travel-time explorer"), html.H2(id="reach-title"), html.P(id="reach-sub", className="sub"),
            map_box("reach-map", "reach-legend"),
            html.P("Coloured by travel time to each commune's main station. Not every address in a coloured "
                   "commune is within that time.", className="caveat"),
            class_name="map-card",
        ),
        card(id="origin-panel", class_name="panel"),
    ])


def _priorities() -> html.Div:
    numeric = {"type": "numeric"}
    columns = [
        {"name": "#", "id": "rank", **numeric},
        {"name": "Commune", "id": "name"},
        {"name": "Department", "id": "dept_name"},
        {"name": "Employed residents", "id": "residents", **numeric,
         "format": dash_table.Format.Format(group=dash_table.Format.Group.yes, precision=0,
                                            scheme=dash_table.Format.Scheme.fixed)},
        {"name": "Jobs reachable (%)", "id": "share", **numeric},
        {"name": "By car (%)", "id": "car_share", **numeric},
        {"name": "05:00 vs 08:30 (pts)", "id": "early_gap", **numeric},
        {"name": "Median income (€)", "id": "median_income", **numeric,
         "format": dash_table.Format.Format(group=dash_table.Format.Group.yes, precision=0,
                                            scheme=dash_table.Format.Scheme.fixed)},
    ]
    return html.Div(id="view-priorities", className="view view-priorities hidden", children=[
        card(
            overline("Transparent ranking"), html.H2("Communes with very low access, by residents affected"),
            html.P(id="prio-sub", className="sub"),
            html.Div(className="table-wrap", children=dash_table.DataTable(
                id="prio-table", columns=columns, data=[], sort_action="native", page_action="none",
                cell_selectable=True,
                css=[{"selector": "th", "rule": "position: sticky; top: 0; z-index: 2;"}],
                style_cell={"fontFamily": "Inter, Arial, sans-serif", "fontSize": "12px", "padding": "6px 10px",
                            "border": "none", "borderBottom": "1px solid #E1E9E4", "textAlign": "right",
                            "color": "#172E30", "minWidth": "70px"},
                style_cell_conditional=[{"if": {"column_id": c}, "textAlign": "left"} for c in ("name", "dept_name")],
                style_header={"fontWeight": "700", "fontSize": "10px", "textTransform": "uppercase",
                              "letterSpacing": "0.06em", "color": "#687A79", "backgroundColor": "#FFFFFF",
                              "borderBottom": "1px solid #172E30", "whiteSpace": "normal", "height": "auto"},
            )),
            class_name="table-card",
        ),
        card(
            overline("How to read this"), html.H2("Candidates for investigation"),
            html.Div(id="prio-summary", className="stat-row"),
            html.Ul(className="notes", children=[
                html.Li("The list keeps communes where residents reach under 5% of the region's jobs in the "
                        "selected scenario, and ranks them by the number of employed residents living there."),
                html.Li("It is a ranking on one stated measure, not a composite score. The other columns add "
                        "context: the car benchmark, the early-shift loss and the commune's median income."),
                html.Li("Click a row to select the commune, then open Explore or Commune to see it on the map."),
                html.Li("A low figure flags a place to study. It does not show which line, frequency or "
                        "service change would help: that needs an analysis of the network itself."),
                html.Li("Access is measured from each commune's busiest station, so residents far from that "
                        "station are worse off than shown."),
            ]),
            class_name="panel",
        ),
    ])


def _method() -> html.Div:
    split = ("Paris is split into its 20 arrondissements, each routed from its own station."
             if data.paris_is_split() else "Paris is routed from a single point.")
    return html.Div(id="view-method", className="view view-method hidden", children=[
        card(
            overline("Sources"), html.H2("What the figures are built from"),
            html.Ul(className="notes", children=[
                html.Li("Jobs: INSEE census 2023, jobs by place of work (EMP1)."),
                html.Li("Employed residents aged 15 and over: INSEE census 2023 (NAV)."),
                html.Li("Income: INSEE Filosofi, median disposable income per consumption unit, by commune."),
                html.Li("Timetables: Île-de-France Mobilités GTFS, scheduled service for Tuesday 17 and "
                        "Saturday 21 November 2026."),
                html.Li("Street network: OpenStreetMap. Routing: Conveyal R5 through r5py."),
            ]),
            overline("How access is computed"), html.H2("From travel times to jobs reachable"),
            html.Ul(className="notes", children=[
                html.Li("Each commune is routed from one point, its busiest station (most scheduled "
                        "departures). " + split),
                html.Li("Public transport: one trip per departure minute in the hour around the stated time "
                        "(08:00 to 09:00 for 08:30). The 25th percentile of those trips is kept. Times include "
                        "walking, waiting and transfers."),
                html.Li("Car: free-flow travel times, without congestion. They do not vary with the time of day."),
                html.Li("Jobs reachable from a commune = all jobs located in the communes whose station is "
                        "within the travel budget, including its own."),
                html.Li("Regional figures weight each commune by its employed residents, so they describe "
                        "people, not communes."),
            ]),
            class_name="panel",
        ),
        card(
            overline("Limits"), html.H2("What to keep in mind"),
            html.Ol(className="notes", children=[
                html.Li("The 25th percentile is a favourable travel time, for a traveller who roughly times "
                        "their departure. It is not the median trip."),
                html.Li("Routing from the busiest station overstates public transport access for residents "
                        "who live far from it."),
                html.Li("Free-flow car times are optimistic compared with real, congested conditions, "
                        "especially at the morning peak."),
                html.Li("Jobs reachable are potential opportunities. They are not vacancies, and they are not "
                        "matched to a person's occupation or skills."),
                html.Li("Income is a commune-level figure. The comparison shows an association between places "
                        "and cannot establish a cause or describe individuals."),
                html.Li("An empty travel time means over 90 minutes or no route found. Only origins that reach "
                        "nothing at all are labelled 'no route found'."),
                html.Li("A commune is all-or-nothing: if its station is within the budget all its jobs count, "
                        "and none if it is one minute over."),
                html.Li("Comparisons always use the same travel budget and the same routing points for both "
                        "sides. A larger travel budget is not a network improvement."),
                html.Li("Scheduled timetables only: disruptions, works and real-time delays are not included."),
            ]),
            class_name="panel",
        ),
    ])


def _layout() -> html.Div:
    scenarios = data.available_scenarios()
    return html.Div(className="app", children=[
        html.Nav(className="sidebar", **{"aria-label": "Views"}, children=[
            html.Div(className="brand", children=[
                html.Span("Access to Work", className="brand-name"),
                html.Span("Île-de-France", className="brand-sub"),
            ]),
            dcc.RadioItems(id="view", className="nav", value=START_VIEW if START_VIEW in VIEWS else "explore",
                           options=[{"label": label, "value": key} for key, (label, _, _) in VIEWS.items()]),
            html.Div(className="side-note", children=[
                html.Span("Hackaviz Mobilités 2026", className="overline"),
                html.Strong("Mobility & employment"),
                html.Span("Challenge 2 · Île-de-France"),
            ]),
        ]),
        html.Main(className="main", children=[
            html.Header(className="topbar", children=[
                html.Div([overline("Île-de-France / Access to work"), html.H1(id="page-title"),
                          html.P(id="page-sub", className="sub")]),
                html.Button("Key findings", id="story-open", className="btn", n_clicks=0),
            ]),
            html.Div(id="story", className="story hidden", **{"aria-live": "polite"}, children=[
                html.Div(className="story-steps", children=[
                    html.Button("1 · Geography matters", id="story-1", className="btn-step", n_clicks=0),
                    html.Button("2 · Time matters", id="story-2", className="btn-step", n_clicks=0),
                    html.Button("3 · Inequality matters", id="story-3", className="btn-step", n_clicks=0),
                ]),
                html.P(id="story-text", className="story-text"),
                html.Button("Explore freely", id="story-exit", className="btn-ghost", n_clicks=0),
            ]),
            _toolbar(scenarios),
            dcc.Store(id="resize-tick"),
            _explore(), _compare(scenarios), _equity(), _commune(), _priorities(), _method(),
        ]),
    ])


def _missing_layout(missing: list[str]) -> html.Main:
    return html.Main(className="main", children=[
        html.H1("Access to Work | Île-de-France"),
        html.P("The pipeline outputs are missing: " + ", ".join(missing)),
        html.P("Run the pipeline first (see pipeline/__init__.py), then reload this page."),
    ])


missing = data.missing_outputs()
app.layout = _missing_layout(missing) if missing else _layout


# --- Navigation, toolbar and selection -----------------------------------------

@app.callback(
    *[Output(f"view-{key}", "className") for key in VIEWS],
    Output("page-title", "children"),
    Output("page-sub", "children"),
    Input("view", "value"),
)
def route(view: str):
    classes = [f"view view-{key}" + ("" if key == view else " hidden") for key in VIEWS]
    _, title, sub = VIEWS[view]
    return (*classes, title, sub)


@app.callback(Output("time", "options"), Output("time", "className"), Input("mode", "value"))
def lock_departure(mode: str):
    """Free-flow car times do not depend on the clock, so the departure buttons are disabled."""
    slots = [s for s in data.SCENARIO_ORDER if s in data.available_scenarios() and s != data.CAR]
    options = [{"label": data.SHORT_LABELS[s], "value": s, "disabled": mode == "car"} for s in slots]
    return options, "pills is-disabled" if mode == "car" else "pills"


@app.callback(
    Output("commune", "value"),
    Input("explore-map", "clickData"),
    Input("equity-map", "clickData"),
    Input("reach-map", "clickData"),
    Input("cmp-map-a", "clickData"),
    Input("cmp-map-b", "clickData"),
    Input("prio-table", "active_cell"),
    prevent_initial_call=True,
)
def select_commune(*_):
    """A click on any map, or on a ranking row, selects that commune everywhere."""
    trigger = ctx.triggered[0]["value"] if ctx.triggered else None
    if not trigger:
        return no_update
    if ctx.triggered_id == "prio-table":
        return trigger.get("row_id") or no_update
    location = trigger.get("points", [{}])[0].get("location")
    return location or no_update


# Plotly sizes a chart when it is drawn. A view that was hidden, or a card whose text changed
# height, needs a resize event afterwards so every chart fills its card.
app.clientside_callback(
    """function() {
        [60, 300, 900, 1800].forEach(function(ms) {
            setTimeout(function() {
                document.querySelectorAll('.js-plotly-plot').forEach(function(el) {
                    if (window.Plotly && el.offsetParent !== null) { window.Plotly.Plots.resize(el); }
                });
            }, ms);
        });
        return Date.now();
    }""",
    Output("resize-tick", "data"),
    Input("view", "value"),
    Input("income-head", "children"),
    Input("dept-sub", "children"),
    Input("cmp-head", "children"),
    Input("explore-legend", "children"),
    Input("reach-legend", "children"),
)


# --- Explore ---------------------------------------------------------------------

def _kpis(scenario: str, budget: int) -> list:
    total = data.total_jobs()
    stats = data.region_stats(scenario, budget)
    low = data.low_access_shares(budget)
    is_car = scenario == data.CAR
    other = data.PEAK_TRANSIT if is_car else data.CAR
    cards = [
        html.Div(className="kpi kpi-car" if is_car else "kpi", children=[
            overline("Median accessible jobs"),
            html.Div([html.Strong(pct(stats["median"] / total)),
                      html.Span(f"of regional jobs · {scenario_text(scenario, budget)}")]),
        ]),
        html.Div(className="kpi kpi-warn", children=[
            overline("Residents with very low access"),
            html.Div([html.Strong(f"{low[scenario]:.0f}%"),
                      html.Span("of employed residents reach under 5% of regional jobs")]),
        ]),
    ]
    if other in low:
        other_stats = data.region_stats(other, budget)
        label = "Median accessible jobs by public transport" if is_car else "Median accessible jobs by car"
        note = (f"at the weekday peak · {budget} min" if is_car
                else f"free-flow benchmark, no congestion · {budget} min")
        cards.append(html.Div(className="kpi" if is_car else "kpi kpi-car", children=[
            overline(label), html.Div([html.Strong(pct(other_stats["median"] / total)), html.Span(note)]),
        ]))
    return cards


def _region_panel(scenario: str, budget: int) -> list:
    low = data.low_access_shares(budget)
    transit = {s: v for s, v in low.items() if s != data.CAR}
    worst = max(transit, key=transit.get)
    best = min(transit, key=transit.get)
    insight = (f"{data.SHORT_LABELS[worst]} is the hardest public transport slot: {transit[worst]:.0f}% of "
               f"employed residents reach under 5% of jobs, against {transit[best]:.0f}% at "
               f"{data.SHORT_LABELS[best]}.")
    if data.CAR in low:
        insight += f" By car (free-flow) it is {low[data.CAR]:.0f}%."
    rows = [bar_row(data.SHORT_LABELS[s], low[s], figures.CAR if s == data.CAR else figures.TEAL, s == scenario)
            for s in data.SCENARIO_ORDER if s in low]
    return [
        overline("Regional pulse"), html.H2("Who is left with very low access?"),
        html.Div(className="big", children=[
            html.Strong(f"{low[scenario]:.0f}%"),
            html.Span(f"of employed residents can reach less than 5% of regional jobs · "
                      f"{scenario_text(scenario, budget)}"),
        ]),
        overline("Across modes and departure times"),
        html.Div(rows, className="bars"),
        html.P(insight, className="insight"),
        overline("Time-of-day profile · median resident"),
        dcc.Graph(figure=figures.time_profile(data.region_profile(budget), None, None, scenario),
                  config=CHART_CONFIG, className="mini-graph"),
        html.P("Share of regional jobs the median resident reaches. Weekday slots are joined; Saturday is a "
               "separate point. Only computed slots are shown.", className="caveat"),
        html.Details(className="detail", children=[
            html.Summary("Full distribution in five bands"),
            dcc.Graph(figure=figures.residents_bands(data.residents_by_band(budget), scenario),
                      config=CHART_CONFIG, className="mini-graph tall"),
        ]),
        html.P("Click a commune on the map, or search for one, to see its details here.", className="hint"),
    ]


def _commune_panel(code: str, scenario: str, budget: int) -> list:
    p = data.commune_profile(code, scenario, budget)
    ratio = (p["transit_share"] / p["car_share"]) if p["car_share"] else None
    vs_median = "above" if p["share"] >= p["region_median"] else "below"
    income = "not published" if p["median_income"] != p["median_income"] else f"€{p['median_income']:,.0f}"
    notes = []
    if p["no_route"]:
        notes.append(html.P("No public transport route was found from this commune's station within 90 "
                            "minutes in this scenario. Its own jobs are the only ones counted.",
                            className="caveat warn"))
    return [
        overline("Selected commune"), html.H2(p["name"]),
        html.P(f"{p['dept_name']} · routed from {p['anchor_stop'] or 'a point inside the commune'} · "
               f"{p['residents']:,.0f} employed residents", className="sub"),
        html.Div(className="big", children=[
            html.Strong(pct(p["share"])),
            html.Span(f"of regional jobs reachable ({p['jobs_reachable']:,.0f} jobs) · "
                      f"{scenario_text(scenario, budget)}"),
        ]),
        *notes,
        html.Div(className="stat-grid", children=[
            stat("Public transport", pct(p["transit_share"]), data.SHORT_LABELS[p["transit_ref"]]),
            stat("Car · free-flow", pct(p["car_share"]), "no congestion", "car"),
            stat("Transit vs car", "n/a" if ratio is None else f"{100 * ratio:.0f}%", "of car access"),
            stat("Better served than", f"{p['percentile']:.0f}%", "of employed residents"),
            stat("Regional median", pct(p["region_median"]), f"this commune is {vs_median}"),
            stat("Median income", income, "of the commune (Filosofi)"),
        ]),
        overline("By travel budget"),
        html.Div(className="bars", children=[
            bar_row(f"{t} min", 100 * v, figures.CAR if scenario == data.CAR else figures.TEAL, t == budget)
            for t, v in p["by_budget"].items()
        ]),
        overline("Across departure times"),
        dcc.Graph(figure=figures.time_profile(data.region_profile(budget), p["by_scenario"], p["name"], scenario),
                  config=CHART_CONFIG, className="mini-graph"),
        html.P("Open the Commune view to see where a trip from here can reach. Clear the search box to "
               "return to the regional summary.", className="hint"),
    ]


@app.callback(
    Output("kpis", "children"),
    Output("map-title", "children"),
    Output("map-sub", "children"),
    Output("explore-map", "figure"),
    Output("explore-legend", "children"),
    Output("explore-panel", "children"),
    Output("map-note", "children"),
    Input("view", "value"),
    Input("mode", "value"),
    Input("time", "value"),
    Input("budget", "value"),
    Input("metric", "value"),
    Input("commune", "value"),
    Input("map-mode", "value"),
    Input("focus", "value"),
    Input("overlay", "value"),
)
def update_explore(view: str, mode: str, time_slot: str, budget: int, metric: str, commune: str | None,
                   map_mode: str = "region", focus: str = "region", overlay: list | None = None):
    if view != "explore":
        return (no_update,) * 7
    scenario = data.scenario_for(mode, time_slot)
    context = scenario_text(scenario, budget)

    def map_view(code: str | None) -> dict:
        """Zoom preset, with room left for the zoom buttons (top) and, when zoomed, the legend (bottom)."""
        preset = data.focus_view(focus, code)
        return {**preset, "pad": (0.10, 0.02) if preset["focus"] == "region" else (0.12, 0.20),
                "rail": "rail" in (overlay or [])}

    if map_mode == "reach":
        # Same map card, different question: where can a trip from the selected commune go?
        origin = commune or data.default_origin()
        name = data.communes().set_index("code").loc[origin, "name"]
        note = "" if commune else " (example origin: click a commune to change it)"
        return (
            _kpis(scenario, budget),
            f"Where can a journey from {name} take you?",
            f"Travel time to every commune · {scenario_text(scenario, budget).rsplit(' · ', 1)[0]}{note}",
            figures.reach_map(data.travel_times_from(scenario, origin), origin, budget, revision="explore-reach",
                              view=map_view(origin), context=context),
            legend(figures.reach_legend_spec(budget)),
            _commune_panel(origin, scenario, budget),
            ("Coloured by travel time to each commune's main station. Not every address in a coloured commune "
            "is within that time."),
        )
    spec = data.METRICS[metric]
    df = data.metric_frame(metric, scenario, time_slot, budget)
    sub = f"{spec['label']} · {scenario_text(scenario, budget)}"
    if metric == "ratio":
        sub = f"{spec['label']} · {data.SHORT_LABELS[time_slot]} against the car · {budget} min"
    elif metric == "gain":
        sub = f"{spec['label']} · {scenario_text(scenario, budget).rsplit(' · ', 1)[0]}"
    note = "Scroll to zoom, drag to move, double-click to reset. Lines: RER and Transilien (thick), metro and tram (thin)."
    if metric == "change":
        note = ("Percentage points of regional jobs, selected scenario minus public transport at Tue 08:30. "
                "Brown: fewer jobs reachable than at the peak.")
        if scenario == data.PEAK_TRANSIT:
            note = "The weekday peak is selected, so there is no change to show. Pick another departure time."
    elif metric == "affected":
        note = "Counts of residents: larger communes naturally hold more. Only communes under 5% of jobs are coloured."
    elif metric == "ratio":
        note = "Car times are free-flow, without congestion, so the gap to the car is overstated at peak hours."
    median = data.region_stats(scenario, budget)["median"] / data.total_jobs()
    panel = _commune_panel(commune, scenario, budget) if commune else _region_panel(scenario, budget)
    return (
        _kpis(scenario, budget),
        f"How much work is within {budget} minutes?",
        sub,
        figures.metric_map(df, metric, scenario, commune, revision="explore", view=map_view(commune),
                           context=context, median=median),
        legend(figures.legend_spec(metric, scenario)),
        panel,
        note,
    )


# --- Compare ---------------------------------------------------------------------

@app.callback(
    Output("cmp-head", "children"),
    Output("cmp-title-a", "children"),
    Output("cmp-map-a", "figure"),
    Output("cmp-title-b", "children"),
    Output("cmp-map-b", "figure"),
    Output("cmp-legend", "children"),
    Output("cmp-finding", "children"),
    Input("view", "value"),
    Input("mode", "value"),
    Input("time", "value"),
    Input("budget", "value"),
    Input("cmp-right", "value"),
    Input("commune", "value"),
)
def update_compare(view: str, mode: str, time_slot: str, budget: int, right: str, commune: str | None):
    if view != "compare":
        return (no_update,) * 7
    left = data.scenario_for(mode, time_slot)
    low = data.low_access_shares(budget)
    total = data.total_jobs()
    diff = low[right] - low[left]

    def side(tag: str, scenario: str) -> html.Div:
        median = data.region_stats(scenario, budget)["median"] / total
        return html.Div(className="cmp-side", children=[
            html.Div([overline(f"{tag} · {budget} min"), html.H3(data.SCENARIO_LABELS[scenario])]),
            stat("Reach under 5% of jobs", f"{low[scenario]:.0f}%", "of employed residents",
                 "car" if scenario == data.CAR else ""),
            stat("Median resident reaches", pct(median), "of regional jobs"),
        ])

    arrow = "=" if abs(diff) < 0.5 else ("↑" if diff > 0 else "↓")
    head = [side("A", left), side("B", right),
            html.Div(f"{arrow} {abs(diff):.0f} pts", className="delta up" if diff > 0.5 else "delta")]
    if abs(diff) < 0.5:
        finding = (f"The share of residents with very low access is the same in both scenarios "
                   f"({low[left]:.0f}%) within {budget} minutes.")
    else:
        finding = (f"The share of employed residents with very low access is {abs(diff):.0f} percentage points "
                   f"{'higher' if diff > 0 else 'lower'} with {data.SHORT_LABELS[right]} ({low[right]:.0f}%) than "
                   f"with {data.SHORT_LABELS[left]} ({low[left]:.0f}%), within {budget} minutes.")
    if data.CAR in (left, right) and left != right:
        finding += " Car times are free-flow, so the car side is optimistic."

    frame_a = data.metric_frame("share", left, time_slot, budget)
    frame_b = data.metric_frame("share", right, time_slot, budget)
    return (
        head,
        data.SCENARIO_LABELS[left],
        figures.metric_map(frame_a, "share", left, commune, revision="cmp", context=scenario_text(left, budget),
                           median=data.region_stats(left, budget)["median"] / total),
        data.SCENARIO_LABELS[right],
        figures.metric_map(frame_b, "share", right, commune, revision="cmp", context=scenario_text(right, budget),
                           median=data.region_stats(right, budget)["median"] / total),
        legend(figures.legend_spec("share", data.PEAK_TRANSIT)),
        finding,
    )


# --- Equity ----------------------------------------------------------------------

@app.callback(
    Output("equity-sub", "children"),
    Output("equity-map", "figure"),
    Output("equity-legend", "children"),
    Output("income-head", "children"),
    Output("income-fig", "figure"),
    Output("dept-sub", "children"),
    Output("dept-fig", "figure"),
    Input("view", "value"),
    Input("mode", "value"),
    Input("time", "value"),
    Input("budget", "value"),
    Input("commune", "value"),
)
def update_equity(view: str, mode: str, time_slot: str, budget: int, commune: str | None):
    if view != "equity":
        return (no_update,) * 7
    scenario = data.scenario_for(mode, time_slot)
    scenarios = data.available_scenarios()
    total = data.total_jobs()

    shown = list(dict.fromkeys(s for s in (scenario, data.PEAK_TRANSIT, data.CAR) if s in scenarios))
    income = data.income_quintiles(budget, shown)
    sel = income[income["scenario"] == scenario].set_index("quintile")["mean_jobs"] / total
    tone = "car" if scenario == data.CAR else ""
    income_head = [
        stat("Lowest-income fifth of communes", pct(sel.get(1)), "of regional jobs, on average", tone or "warn"),
        stat("Highest-income fifth of communes", pct(sel.get(5)), "of regional jobs, on average", tone),
    ]

    dept = data.communes().set_index("code")["dept"].get(commune) if commune else None
    car_dept = data.dept_stats(data.CAR, budget) if data.CAR in scenarios else None
    region_median = data.region_stats(scenario, budget)["median"] / total
    dept_sub = "Dot: median resident · bar: worst-served 10% to best-served 10% of residents"
    df = data.metric_frame("share", scenario, time_slot, budget)
    return (
        (f"Share of regional jobs reachable · {scenario_text(scenario, budget)}. Click a commune to highlight "
        "its department."),
        figures.metric_map(df, "share", scenario, commune, revision="equity",
                           context=scenario_text(scenario, budget), median=region_median),
        legend(figures.legend_spec("share", scenario)),
        income_head,
        figures.income_dots(income, scenario),
        dept_sub,
        figures.dept_ranges(data.dept_stats(scenario, budget), car_dept, scenario, region_median, dept),
    )


# --- Commune ---------------------------------------------------------------------

@app.callback(
    Output("reach-title", "children"),
    Output("reach-sub", "children"),
    Output("reach-map", "figure"),
    Output("reach-legend", "children"),
    Output("origin-panel", "children"),
    Input("view", "value"),
    Input("mode", "value"),
    Input("time", "value"),
    Input("budget", "value"),
    Input("commune", "value"),
)
def update_commune(view: str, mode: str, time_slot: str, budget: int, commune: str | None):
    if view != "commune":
        return (no_update,) * 5
    scenario = data.scenario_for(mode, time_slot)
    origin = commune or data.default_origin()
    p = data.commune_profile(origin, scenario, budget)
    df = data.travel_times_from(scenario, origin)
    within = df[df["travel_time"] <= budget]

    transit_slot = time_slot
    curve_transit = data.reach_curve(transit_slot, origin)
    curve_car = data.reach_curve(data.CAR, origin) if data.CAR in data.available_scenarios() else None

    example = "" if commune else " (example: the commune with the most jobs; pick any commune)"
    panel = [
        overline("Origin profile"), html.H2(p["name"]),
        html.P(f"{p['dept_name']} · routed from {p['anchor_stop'] or 'a point inside the commune'}{example}",
               className="sub"),
        html.Div(className="big", children=[
            html.Strong(pct(p["share"])),
            html.Span(f"of regional jobs within {budget} min ({p['jobs_reachable']:,.0f} jobs in "
                      f"{len(within):,} communes) · {scenario_text(scenario, budget).rsplit(' · ', 1)[0]}"),
        ]),
        overline("Jobs within each travel budget"),
        html.Div(className="bars", children=[
            bar_row(f"{t} min", 100 * v, figures.CAR if scenario == data.CAR else figures.TEAL, t == budget)
            for t, v in p["by_budget"].items()
        ]),
        overline("Jobs reachable by minutes of travel"),
        dcc.Graph(figure=figures.reach_curve(curve_transit, curve_car, budget, data.SHORT_LABELS[transit_slot]),
                  config=CHART_CONFIG, className="mini-graph tall"),
        html.P("The curve adds up the jobs of every commune whose station is within the given time. A longer "
               "travel budget means a longer commute; it is not an improvement of the network.",
               className="caveat"),
    ]
    if p["no_route"]:
        panel.insert(4, html.P("No public transport route was found from this station within 90 minutes in "
                               "this scenario.", className="caveat warn"))
    return (
        f"Where can a journey from {p['name']} take you?",
        (f"Travel time to every commune · {scenario_text(scenario, budget).rsplit(' · ', 1)[0]}. "
        "Click another commune to move the origin."),
        figures.reach_map(df, origin, budget, context=scenario_text(scenario, budget)),
        legend(figures.reach_legend_spec(budget)),
        panel,
    )


# --- Priorities --------------------------------------------------------------------

@app.callback(
    Output("prio-sub", "children"),
    Output("prio-table", "data"),
    Output("prio-summary", "children"),
    Input("view", "value"),
    Input("mode", "value"),
    Input("time", "value"),
    Input("budget", "value"),
)
def update_priorities(view: str, mode: str, time_slot: str, budget: int):
    if view != "priorities":
        return (no_update,) * 3
    scenario = data.scenario_for(mode, time_slot)
    full = data.priorities(scenario, budget, limit=10_000)
    top = full.head(60)
    rows = [{
        "id": r["code"], "rank": int(r["rank"]), "name": r["name"], "dept_name": r["dept_name"],
        "residents": round(r["residents"]),
        "share": round(100 * r["share"], 2), "car_share": round(100 * r["car_share"], 1),
        "early_gap": round(100 * (r["early_share"] - r["peak_share"]), 2),
        "median_income": None if r["median_income"] != r["median_income"] else round(r["median_income"]),
    } for _, r in top.iterrows()]
    residents = data.communes()["residents"].sum()
    summary = [
        stat("Communes under 5% of jobs", f"{len(full):,}", f"of {len(data.communes()):,} areas", "warn"),
        stat("Employed residents living there", f"{full['residents'].sum():,.0f}",
             f"{100 * full['residents'].sum() / residents:.0f}% of the region's employed residents"),
    ]
    sub = (f"{scenario_text(scenario, budget)} · the {len(top)} largest by employed residents. "
           "Click a column header to sort.")
    return sub, rows, summary


# --- Key findings story --------------------------------------------------------------

def _story_text(step: int, budget: int) -> str:
    total = data.total_jobs()
    low = data.low_access_shares(budget)
    if step == 1:
        s = data.region_stats(data.PEAK_TRANSIT, budget)
        return (f"Geography matters. At the weekday peak, half of employed residents reach at least "
                f"{pct(s['median'] / total)} of the region's jobs within {budget} minutes by public transport. "
                f"The worst-served 10% reach under {pct(s['p10'] / total)}, and {low[data.PEAK_TRANSIT]:.0f}% of "
                "residents reach under 5%. The map shows where.")
    if step == 2:
        late, peak = "transit_tue_2230", data.PEAK_TRANSIT
        return (f"Time matters. Around 22:30, {low[late]:.0f}% of employed residents reach under 5% of the "
                f"region's jobs within {budget} minutes, against {low[peak]:.0f}% at the 08:30 peak. Use the "
                "departure buttons to see the map change.")
    income = data.income_quintiles(budget, [data.PEAK_TRANSIT])
    q = income.set_index("quintile")["mean_jobs"] / total
    return (f"Inequality matters. At the weekday peak, residents of the lowest-income fifth of communes reach "
            f"{pct(q.get(1))} of the region's jobs on average within {budget} minutes, against {pct(q.get(5))} in "
            "the highest-income fifth. Income is measured for the commune, not the person.")


@app.callback(
    Output("story", "className"),
    Output("story-text", "children"),
    Output("view", "value"),
    Output("mode", "value"),
    Output("time", "value"),
    Input("story-open", "n_clicks"),
    Input("story-1", "n_clicks"),
    Input("story-2", "n_clicks"),
    Input("story-3", "n_clicks"),
    Input("story-exit", "n_clicks"),
    State("budget", "value"),
    prevent_initial_call=True,
)
def story(_open, _one, _two, _three, _exit, budget: int):
    trigger = ctx.triggered_id
    if trigger == "story-exit":
        return "story hidden", no_update, "explore", no_update, no_update
    step = {"story-open": 1, "story-1": 1, "story-2": 2, "story-3": 3}[trigger]
    view = "equity" if step == 3 else "explore"
    time_slot = "transit_tue_2230" if step == 2 else data.PEAK_TRANSIT
    return f"story step-{step}", _story_text(step, budget), view, "transit", time_slot

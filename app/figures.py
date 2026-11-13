"""Plotly figures for the Dash app (phase 2 workspace).

Design choices:
- Colours come from Mobility_Atlas_Figma_Handoff/design_tokens.json. Public transport is always
  teal and the car always orange, on every chart. Sequential data uses a single-hue ramp
  (light = low, dark = high), which stays ordered for colour-blind readers; class legends are
  drawn in HTML next to the map, with text labels, so colour is never the only cue.
- Maps are drawn on the real commune polygons with Plotly's SVG map (scroll zoom, pan, hover,
  click; offline, no WebGL). ATW_MAP=maplibre opts into a WebGL map with a basemap.
- Figures have no titles: titles are HTML headings in the page, so they never get clipped.
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from app import data

INK = "#172E30"
MUTED = "#687A79"
LINE = "#E1E9E4"
TEAL = "#126F73"
TEAL_LIGHT = "#8CC0B8"
CAR = "#E38C58"
WARN = "#B64F4B"
FONT = {"family": "Inter, Arial, sans-serif", "size": 12, "color": INK}

# Map engine. The default is Plotly's SVG map: it works offline and without WebGL, and supports
# scroll zoom, drag to pan, hover and click. ATW_MAP=maplibre switches to a WebGL vector map with a
# basemap; on the development machine it drew only one tile of communes, so it is opt-in.
MAPLIBRE = os.environ.get("ATW_MAP", "svg") == "maplibre"
FILL_OPACITY = 0.78 if MAPLIBRE else 1.0

# Sequential maps: ColorBrewer YlGnBu, 7 classes. Lightness falls steadily from pale yellow to
# deep blue, so order survives greyscale printing and the common colour-vision deficiencies, and
# neighbouring classes differ in both hue and lightness (the earlier single-hue teal ramp did not).
# Diverging map (change vs peak): ColorBrewer BrBG, brown = loss, neutral = no change, teal = gain.
PALETTES = {
    "teal": ["#FFFFCC", "#C7E9B4", "#7FCDBB", "#41B6C4", "#1D91C0", "#225EA8", "#0C2C84"],
    "warm": ["#FEE8D6", "#FDD0A2", "#FDAE6B", "#F4873D", "#DE5E1B", "#B33E0A", "#7F2704"],
    "diverging": ["#8C510A", "#BF812D", "#DFC27D", "#F6E8C3", "#EEF0EC", "#80CDC1", "#01665E"],
}
DARK_FROM = {"teal": 4, "warm": 4}  # class index from which labels on top must be white
NO_ROUTE_COLOR = "#A9AEAB"   # neutral grey: "no data", never read as a low value
NOT_LOW_COLOR = "#F3F4F0"
SELECT_COLOR = "#D81B60"     # magenta: not used by any palette, the car or the transit colour
BOUNDARY_DEPT = "#3B4B4D"
# Reach map: destinations within the selected budget, in travel-time bands (close = dark).
REACH_BANDS = [("up to 30 min", 30, "#0C2C84"), ("30–45 min", 45, "#1D91C0"), ("45–60 min", 60, "#7FCDBB")]
REACH_BEYOND_BUDGET = "#C5CEC8"   # reachable within 90 min, but over the selected budget
REACH_NONE = "#F8F8F5"            # over 90 min, or no route found
BAND_COLORS = ["#D9E7E2", "#AED3CA", "#6FB0AA", "#2A7F82", "#0D5357"]  # five-band detail chart


def _base(fig: go.Figure, **margin) -> go.Figure:
    m = {"l": 8, "r": 8, "t": 8, "b": 8} | margin
    fig.update_layout(font=FONT, margin=m, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      hoverlabel={"font_size": 12, "bgcolor": "white", "bordercolor": LINE}, autosize=True)
    return fig


# --- Maps --------------------------------------------------------------------

def legend_spec(metric: str, scenario: str) -> dict:
    """Legend content for a metric map: ordered class colours, boundary labels, and extra swatches."""
    spec = data.METRICS[metric]
    extras = []
    if metric == "affected":
        extras.append((data.NOT_LOW_LABEL, NOT_LOW_COLOR))
    elif scenario != data.CAR or metric == "ratio":
        extras.append((data.NO_ROUTE_LABEL, NO_ROUTE_COLOR))
    return {"title": spec["legend"].replace("\n", " "), "colors": PALETTES[spec["palette"]],
            "ticks": spec["ticks"], "extras": extras}


def reach_legend_spec(budget: int) -> dict:
    bands = [b for b in REACH_BANDS if b[1] <= budget]
    return {"title": f"Travel time from the origin (budget: {budget} min)",
            "colors": [b[2] for b in bands], "ticks": [f"{b[1]}" for b in bands[:-1]],
            "ends": ("0", f"{budget} min"),
            "extras": [(f"over {budget} min, up to 90", REACH_BEYOND_BUDGET), ("over 90 min or no route", REACH_NONE)]}


def _stepped(colors: list[str]) -> list:
    n = len(colors)
    return [[k / n, c] for i, c in enumerate(colors) for k in (i, i + 1)]


def _choropleth(**kwargs):
    """A filled-polygon trace for the active map engine."""
    return go.Choroplethmap(**kwargs) if MAPLIBRE else go.Choropleth(**kwargs)


def _scatter(**kwargs):
    return go.Scattermap(**kwargs) if MAPLIBRE else go.Scattergeo(**kwargs)


def _map_layout(fig: go.Figure, revision: str, view: dict | None = None, dark: set | None = None) -> go.Figure:
    """Shared map styling: department boundaries, place labels, extent.

    `view` comes from data.focus_view (extent and labels of a zoom preset). `dark` is the set of
    commune codes with a dark fill, where labels are drawn in white. `revision` plus the view key
    keeps the user's own zoom and position when only the data changes.
    """
    view = view or data.focus_view("region", None)
    dark = dark or set()
    lon, lat = data.dept_outlines()
    fig.add_trace(_scatter(lon=lon, lat=lat, mode="lines", hoverinfo="skip", showlegend=False,
                           line={"color": BOUNDARY_DEPT, "width": 1.3}))
    west, south, east, north = view["bounds"]
    if MAPLIBRE:
        fig.update_layout(map={"style": "carto-positron", "bounds": {"west": west, "south": south,
                                                                    "east": east, "north": north}})
    else:
        labels = view["labels"]
        if len(labels):
            colors = ["#FFFFFF" if code in dark else INK for code in labels["code"]]
            zoomed = view["focus"] != "region"
            fig.add_trace(go.Scattergeo(
                lon=labels["lon"], lat=labels["lat"], text=labels["name"],
                mode="text" if zoomed else "markers+text", textposition=labels["position"],
                hoverinfo="skip", showlegend=False,
                marker={"size": 4, "color": colors, "line": {"color": "rgba(255,255,255,0.8)", "width": 0.8}},
                textfont={"size": 11 if zoomed else 10, "color": colors, "family": FONT["family"]},
            ))
        # Margins as shares of the extent. Extra room at the top keeps the region clear of the zoom
        # buttons; zoomed views also leave room at the bottom for the floating legend.
        pad_top, pad_bottom = view.get("pad", (0.02, 0.02))
        pad_x = 0.02 * (east - west)
        fig.update_geos(visible=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)",
                        lonaxis_range=[west - pad_x, east + pad_x],
                        lataxis_range=[south - pad_bottom * (north - south), north + pad_top * (north - south)])
    fig.update_layout(dragmode="pan", uirevision=f"{revision}-{view['key']}", showlegend=False,
                      hoverlabel={"align": "left", "font_size": 12, "bgcolor": "white", "bordercolor": "#C9D3CE",
                                  "font_color": INK})
    return _base(fig, l=0, r=0, t=0, b=0)


def _selection(code: str | None) -> list:
    """Selected commune: a white halo under a magenta outline, drawn above the fill."""
    if not code:
        return []
    clear = [[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]]
    return [
        _choropleth(geojson=data.geojson(), locations=[code], z=[0], showscale=False, hoverinfo="skip",
                    colorscale=clear, marker_line_color=color, marker_line_width=width)
        for color, width in (("#FFFFFF", 5.5), (SELECT_COLOR, 2.6))
    ]


def _boundary_width(view: dict | None) -> float:
    """Commune boundaries: hairlines for the whole region, clearer when zoomed in."""
    return 0.7 if view and view["focus"] != "region" else 0.2


def metric_map(df: pd.DataFrame, metric: str, scenario: str, selected: str | None = None,
               revision: str = "map", view: dict | None = None, context: str = "",
               median: float | None = None, **_ignored) -> go.Figure:
    """Choropleth of a metric frame from data.metric_frame, one colour per class.

    `context` (mode, departure, budget) and `median` (regional median share) are shown in the tooltip.
    """
    spec = data.METRICS[metric]
    legend = legend_spec(metric, scenario)
    labels = [*spec["labels"], *[label for label, _ in legend["extras"]]]
    colors = [*legend["colors"], *[color for _, color in legend["extras"]]]
    index = df["cls"].map({label: i for i, label in enumerate(labels)})

    extra = None
    if metric == "ratio":
        extra = df["value"].map(lambda v: "n/a" if pd.isna(v) else f"{100 * v:.0f}% of car access (free-flow)")
    elif metric == "gain":
        extra = df["value"].map(lambda v: f"+{100 * v:.1f} points from 30 to 60 min")
    elif metric == "change":
        extra = df["value"].map(lambda v: f"{100 * v:+.1f} points vs Tue 08:30")
    elif metric == "affected":
        extra = df["value"].map(lambda v: "5% of jobs or more: not counted" if pd.isna(v)
                                else "under 5% of jobs: counted as low access")
    no_route = df["cls"] == data.NO_ROUTE_LABEL
    custom = np.column_stack([
        df["name"], df["dept_name"], df["dept"],
        df["jobs_reachable"].map(lambda v: f"{v:,.0f}"),
        df["share"].map(lambda v: f"{100 * v:.1f}%" if v < 0.1 else f"{100 * v:.0f}%"),
        df["residents"].map(lambda v: f"{v:,.0f}"),
        extra if extra is not None else [""] * len(df),
        np.where(no_route, "<br><i>No public transport route found within 90 min</i>", ""),
    ])
    template = ("<b>%{customdata[0]}</b> · %{customdata[1]} (%{customdata[2]})<br>"
                "Jobs within reach: <b>%{customdata[3]}</b><br>"
                "Regional job accessibility: <b>%{customdata[4]}</b><br>")
    if median is not None:
        template += f"Regional median: {100 * median:.0f}%<br>"
    if extra is not None:
        template += "%{customdata[6]}<br>"
    template += "Employed residents: %{customdata[5]}%{customdata[7]}"
    if context:
        template += f"<br><span style='color:{MUTED}'>{context}</span>"

    fig = go.Figure(_choropleth(
        geojson=data.geojson(), locations=df["code"], z=index + 0.5, zmin=0, zmax=len(labels),
        colorscale=_stepped(colors), showscale=False, marker_opacity=FILL_OPACITY,
        marker_line_width=_boundary_width(view), marker_line_color="rgba(255,255,255,0.75)",
        customdata=custom, hovertemplate=template + "<extra></extra>",
    ))
    fig.add_traces(_selection(selected))
    dark_from = DARK_FROM.get(spec["palette"])
    if spec["palette"] == "diverging":
        dark = set(df.loc[index.isin([0, 1, 6]), "code"])
    else:
        dark = set(df.loc[(index >= dark_from) & (index < len(spec["labels"])), "code"])
    return _map_layout(fig, revision, view, dark)


def reach_map(df: pd.DataFrame, origin: str, budget: int = 45, revision: str = "reach",
              view: dict | None = None, context: str = "") -> go.Figure:
    """Travel time from one origin to every commune.

    Communes within the selected budget are coloured by travel-time band; those reachable only with
    more time (up to 90 min) are pale; the rest are left neutral. Times are station to station, so a
    coloured commune is not reachable in that time from every address.
    """
    df = df.assign(travel_time=df["travel_time"].astype("float64"))  # nullable ints -> NaN for "no time"
    bands = [b for b in REACH_BANDS if b[1] <= budget]
    labels = [b[0] for b in bands]
    band = pd.cut(df["travel_time"], [-1] + [b[1] for b in bands], labels=labels).astype(object)
    band = band.where(band.notna(), np.where(df["travel_time"].notna(), "beyond", "none"))
    order = [*labels, "beyond", "none"]
    colors = [b[2] for b in bands] + [REACH_BEYOND_BUDGET, REACH_NONE]
    index = band.map({label: i for i, label in enumerate(order)})
    minutes = df["travel_time"].map(lambda v: "over 90 min, or no route found" if pd.isna(v) else f"{v:.0f} min")
    status = np.where(df["travel_time"] <= budget, f"within the {budget}-min budget",
                      np.where(df["travel_time"].notna(), f"over the {budget}-min budget", "not counted"))
    template = ("<b>%{customdata[0]}</b> · %{customdata[1]} (%{customdata[2]})<br>"
                "Travel time from the origin: <b>%{customdata[3]}</b><br>%{customdata[5]}<br>"
                "Jobs located here: %{customdata[4]}")
    if context:
        template += f"<br><span style='color:{MUTED}'>{context}</span>"

    fig = go.Figure(_choropleth(
        geojson=data.geojson(), locations=df["code"], z=index + 0.5, zmin=0, zmax=len(order),
        colorscale=_stepped(colors), showscale=False, marker_opacity=FILL_OPACITY,
        marker_line_width=_boundary_width(view), marker_line_color="rgba(255,255,255,0.8)",
        customdata=np.column_stack([df["name"], df["dept_name"], df["dept"], minutes,
                                    df["jobs"].map(lambda v: f"{v:,.0f}"), status]),
        hovertemplate=template + "<extra></extra>",
    ))
    fig.add_traces(_selection(origin))
    row = df[df["code"] == origin]
    # Origin marker: a white disc under a magenta one (map engines differ on symbols and outlines).
    for size, color in ((16, "#FFFFFF"), (10, SELECT_COLOR)):
        fig.add_trace(_scatter(lon=row["lon"], lat=row["lat"], mode="markers", hoverinfo="skip",
                               showlegend=False, marker={"size": size, "color": color}))
    dark = set(df.loc[index < min(2, len(labels)), "code"])
    return _map_layout(fig, revision, view, dark)


# --- Charts ------------------------------------------------------------------

def time_profile(region: dict, commune: dict | None, commune_name: str | None, selected: str) -> go.Figure:
    """Share of jobs reachable at each computed departure slot.

    Weekday slots are joined by a line; Saturday is a separate point (it is not the next point in
    time). The car is a dashed reference line, because free-flow times do not vary by departure.
    """
    weekday = [s for s in data.WEEKDAY_SLOTS if s in region]
    x_week = [data.SHORT_LABELS[s] for s in weekday]
    sat = data.SATURDAY_SLOT if data.SATURDAY_SLOT in region else None
    x_all = x_week + ([data.SHORT_LABELS[sat]] if sat else [])

    fig = go.Figure()

    def series(values: dict, name: str, color: str, width: float) -> None:
        y_week = [100 * values[s] for s in weekday]
        fig.add_trace(go.Scatter(
            x=x_week, y=y_week, mode="lines+markers", name=name, line={"color": color, "width": width},
            marker={"size": [11 if s == selected else 7 for s in weekday], "color": color,
                    "line": {"color": "white", "width": 1.5}},
            hovertemplate="%{x}: %{y:.1f}% of jobs<extra>" + name + "</extra>",
        ))
        if sat:
            fig.add_trace(go.Scatter(
                x=[data.SHORT_LABELS[sat]], y=[100 * values[sat]], mode="markers", name=name, showlegend=False,
                marker={"size": 11 if sat == selected else 8, "color": color, "symbol": "diamond",
                        "line": {"color": "white", "width": 1.5}},
                hovertemplate="%{x}: %{y:.1f}% of jobs<extra>" + name + "</extra>",
            ))

    series(region, "Median resident (region)", TEAL, 2.5)
    if commune is not None:
        series(commune, commune_name or "Selected commune", INK, 2)

    reference = (commune or region).get(data.CAR)
    if reference is not None:
        who = commune_name if commune is not None else "median resident"
        fig.add_trace(go.Scatter(
            x=x_all, y=[100 * reference] * len(x_all), mode="lines", name=f"Car, free-flow ({who})",
            line={"color": CAR, "width": 1.6, "dash": "dash"},
            hovertemplate="Car, free-flow: %{y:.0f}% of jobs<extra></extra>",
        ))
    if sat:
        fig.add_vline(x=len(x_week) - 0.5, line={"color": LINE, "width": 1})
    fig.update_xaxes(showgrid=False, tickfont={"size": 10, "color": MUTED}, fixedrange=True)
    fig.update_yaxes(ticksuffix="%", rangemode="tozero", gridcolor=LINE, zeroline=False, fixedrange=True,
                     tickfont={"size": 10, "color": MUTED})
    fig.update_layout(legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "font": {"size": 10}},
                      hovermode="x")
    return _base(fig, l=36, t=4, b=24)


def residents_bands(df: pd.DataFrame, selected: str) -> go.Figure:
    """Stacked bars: % of employed residents in each band of jobs reachable, one bar per scenario."""
    order = [s for s in data.SCENARIO_ORDER if s in set(df["scenario"])][::-1]
    names = [data.SHORT_LABELS[s] for s in order]
    fig = go.Figure()
    for i, (band, color) in enumerate(zip(data.BANDS, BAND_COLORS, strict=True)):
        part = df[df["band"] == band].set_index("scenario").reindex(order)
        fig.add_trace(go.Bar(
            y=names, x=part["pct_residents"], name=band, orientation="h", marker_color=color,
            text=[f"{v:.0f}%" if v >= 8 else "" for v in part["pct_residents"]],
            textposition="inside", insidetextanchor="middle",
            textfont={"color": "white" if i >= 3 else INK, "size": 10},
            hovertemplate="%{y}: %{x:.0f}% of residents reach " + band + "<extra></extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.28,
                      legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "font": {"size": 10},
                              "traceorder": "normal"})
    fig.update_xaxes(range=[0, 100], ticksuffix="%", showgrid=False, tickfont={"size": 10, "color": MUTED},
                     fixedrange=True)
    fig.update_yaxes(
        tickvals=names, fixedrange=True, tickfont={"size": 11},
        ticktext=[f"<b>{n}</b>" if s == selected else n for s, n in zip(order, names, strict=True)],
    )
    return _base(fig, l=4, t=4, b=20)


def income_dots(df: pd.DataFrame, selected: str) -> go.Figure:
    """Connected dots: mean share of jobs reachable per income fifth of the home commune."""
    labels = {1: "Q1 lowest", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 highest"}
    fig = go.Figure()
    for scenario in [s for s in data.SCENARIO_ORDER if s in set(df["scenario"])]:
        part = df[df["scenario"] == scenario].sort_values("quintile")
        y = 100 * part["mean_jobs"] / data.total_jobs()
        is_car, is_sel = scenario == data.CAR, scenario == selected
        color = CAR if is_car else (TEAL if is_sel else TEAL_LIGHT)
        fig.add_trace(go.Scatter(
            x=part["quintile"].map(labels), y=y, mode="lines+markers+text", name=data.SHORT_LABELS[scenario],
            line={"color": color, "width": 3 if is_sel else 2, "dash": "solid" if (is_sel or is_car) else "dot"},
            marker={"size": 9, "color": "white", "line": {"color": color, "width": 2.5}},
            text=[f"{v:.0f}%" if i in (0, len(y) - 1) else "" for i, v in enumerate(y)],
            textposition="top center", textfont={"size": 10, "color": color},
            hovertemplate="%{x}: %{y:.1f}% of jobs<extra>" + data.SHORT_LABELS[scenario] + "</extra>",
        ))
    fig.update_xaxes(showgrid=False, tickfont={"size": 10, "color": MUTED}, fixedrange=True)
    fig.update_yaxes(ticksuffix="%", rangemode="tozero", gridcolor=LINE, zeroline=False, fixedrange=True,
                     tickfont={"size": 10, "color": MUTED})
    fig.update_layout(legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "font": {"size": 10}})
    return _base(fig, l=36, t=4, b=24)


def dept_ranges(df: pd.DataFrame, car: pd.DataFrame | None, scenario: str, region_median: float,
                selected_dept: str | None) -> go.Figure:
    """Per department: median resident (dot) and P10 to P90 (bar), sorted, with the regional median."""
    total = data.total_jobs()
    df = df.sort_values("median").assign(**{c: 100 * df[c] / total for c in ("median", "p10", "p90")})
    color = CAR if scenario == data.CAR else TEAL
    names = df["dept_name"].tolist()

    fig = go.Figure()
    for _, row in df.iterrows():
        strong = row["dept"] == selected_dept
        fig.add_trace(go.Scatter(
            x=[row["p10"], row["p90"]], y=[row["dept_name"]] * 2, mode="lines", hoverinfo="skip", showlegend=False,
            line={"color": color, "width": 7 if strong else 5}, opacity=0.5 if strong else 0.25,
        ))
    fig.add_trace(go.Scatter(
        x=df["median"], y=names, mode="markers", name=f"{data.SHORT_LABELS[scenario]} · median resident",
        marker={"color": color, "size": 11, "line": {"color": "white", "width": 1.5}},
        customdata=df[["p10", "p90"]],
        hovertemplate="%{y}<br>median %{x:.1f}% of jobs<br>worst-served 10%: %{customdata[0]:.1f}% · "
                      "best-served 10%: %{customdata[1]:.1f}%<extra></extra>",
    ))
    if car is not None and scenario != data.CAR:
        car = car.set_index("dept_name").reindex(names)
        fig.add_trace(go.Scatter(
            x=100 * car["median"] / total, y=names, mode="markers", name="Car · free-flow · median resident",
            marker={"symbol": "diamond", "color": CAR, "size": 9, "line": {"color": "white", "width": 1}},
            hovertemplate="%{y}<br>car, free-flow: median %{x:.1f}% of jobs<extra></extra>",
        ))
    fig.add_vline(x=100 * region_median, line={"color": INK, "width": 1, "dash": "dot"},
                  annotation_text="regional median", annotation_position="top",
                  annotation_font={"size": 9, "color": MUTED})
    fig.update_xaxes(range=[-2, 102], ticksuffix="%", showgrid=False, tickfont={"size": 10, "color": MUTED},
                     fixedrange=True)
    fig.update_yaxes(
        showgrid=False, fixedrange=True, tickvals=names, tickfont={"size": 11},
        ticktext=[f"<b>{n}</b>" if d == selected_dept else n for d, n in zip(df["dept"], names, strict=True)],
    )
    fig.update_layout(legend={"orientation": "h", "y": 1.06, "yanchor": "bottom", "x": 0, "font": {"size": 10}})
    return _base(fig, l=4, t=4, b=20)


def reach_curve(transit: pd.DataFrame | None, car: pd.DataFrame | None, threshold: int,
                transit_label: str) -> go.Figure:
    """Cumulative share of regional jobs reachable from the origin, by minutes of travel."""
    fig = go.Figure()
    if car is not None:
        fig.add_trace(go.Scatter(x=car["minutes"], y=100 * car["share"], mode="lines", name="Car · free-flow",
                                 line={"color": CAR, "width": 2, "shape": "hv"},
                                 hovertemplate="%{x} min by car: %{y:.1f}% of jobs<extra></extra>"))
    if transit is not None:
        fig.add_trace(go.Scatter(x=transit["minutes"], y=100 * transit["share"], mode="lines", name=transit_label,
                                 line={"color": TEAL, "width": 3, "shape": "hv"},
                                 hovertemplate="%{x} min: %{y:.1f}% of jobs<extra></extra>"))
    for minutes in (30, 45, 60):
        fig.add_vline(x=minutes, line={"color": INK if minutes == threshold else LINE,
                                       "width": 1.4 if minutes == threshold else 1, "dash": "dot"})
    fig.update_xaxes(range=[0, 90], tickvals=[0, 30, 45, 60, 90], ticksuffix=" min", showgrid=False,
                     tickfont={"size": 10, "color": MUTED}, fixedrange=True)
    fig.update_yaxes(ticksuffix="%", rangemode="tozero", gridcolor=LINE, zeroline=False, fixedrange=True,
                     tickfont={"size": 10, "color": MUTED})
    fig.update_layout(legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0, "font": {"size": 10}},
                      hovermode="x unified")
    return _base(fig, l=36, t=4, b=24)

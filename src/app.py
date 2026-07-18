# app.py

import logging
import os
from typing import Any

import pandas as pd
from dash import Dash, Input, NoUpdate, Output, State, dcc, html, no_update

import translations
from utils import (
    calculate_price_change,
    calculate_summary_stats,
    find_region_extremes,
    format_number,
)

logger = logging.getLogger(__name__)

TooltipChildren = list[str | html.Span]
HeaderText = list[str | html.A]
DropdownOptions = list[dcc.Dropdown.Options]


REQUIRED_DATA_COLUMNS = {"Date", "AveragePrice", "Total Volume", "type", "region"}


def load_data() -> pd.DataFrame:
    """Load and preprocess the avocado dataset. The source path defaults to
    the bundled CSV but can be overridden via AVOCADO_DATA_PATH (e.g. to
    swap in a different dataset without a code change)."""
    csv_path = os.environ.get(
        "AVOCADO_DATA_PATH",
        os.path.join(os.path.dirname(__file__), "avocado.csv"),
    )
    try:
        raw_data = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find avocado.csv at {csv_path}")
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

    missing_columns = REQUIRED_DATA_COLUMNS - set(raw_data.columns)
    if missing_columns:
        raise ValueError(
            f"CSV at {csv_path} is missing required columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    return raw_data.assign(
        Date=lambda df: pd.to_datetime(df["Date"], format="%Y-%m-%d")
    ).sort_values(by="Date")


def filter_data(
    regions: list[str], avocado_type: str, start_date: str, end_date: str
) -> pd.DataFrame:
    """Filter the module-level dataset by selected regions/type/date-range."""
    return data.query(
        "region in @regions and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"
    )


EMPTY_REGION_MESSAGE = translations.t("empty.select_region", "en")


def empty_state_figure(message: str, lang: str = "en") -> dict[str, Any]:
    """Empty Plotly figure with a centered annotation explaining why."""
    return {
        "data": [],
        "layout": {
            "title": translations.t("empty.no_data_filters", lang),
            "annotations": [
                {
                    "text": message,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0.5,
                    "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 16},
                }
            ],
        },
    }


# Load data
data = load_data()
regions = sorted(data["region"].unique())
avocado_types = sorted(data["type"].unique())

# Categorical palette for per-region chart lines (validated with the
# /dataviz skill: 8 hues, worst adjacent CVD ΔE 24.2). Colors are assigned
# per chart render, in the fixed order below, to whichever regions are
# currently selected (not pre-assigned per region across the full ~50-region
# roster) — with only 8 well-separated hues, a fixed global assignment would
# alias two arbitrary regions onto the same color as soon as they're 8 apart
# alphabetically (e.g. "Albany" and "Chicago" both selected). Since a single
# chart realistically compares a handful of regions at once, keying color to
# the current selection's order guarantees distinct colors for any 2-8
# regions shown together, at the cost of a region's color shifting if the
# selection changes — an acceptable trade-off here since the legend and
# hover tooltip always name the region directly (never color-only identity).
REGION_COLOR_PALETTE = [
    "#2a78d6",  # blue
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#008300",  # green
    "#4a3aa7",  # violet
    "#e34948",  # red
    "#e87ba4",  # magenta
    "#eb6834",  # orange
]

# Chart chrome — same design tokens as style.css, duplicated here because
# Plotly figure dicts render via JS/canvas and can't reference CSS custom
# properties.
CHART_BG = "#F6F1E4"  # --parchment
CHART_GRIDCOLOR = "#D8CBAE"  # muted parchment-adjacent tone
TYPE_COLOR_MAP = {"conventional": "#7C8F3E", "organic": "#B4432E"}  # --flesh / --bruise

# Define numeric columns for scatter plot
numeric_columns = [
    "AveragePrice",
    "Total Volume",
    "Total Bags",
    "Small Bags",
    "Large Bags",
    "XLarge Bags",
    "year",
]


def cross_section_mark() -> html.Div:
    """The Cross-Section Mark: concentric rings echoing the avocado's
    skin/flesh/pit layering — the app's signature element, replacing the
    generic 🥑 emoji as the header brand mark."""
    return html.Div(
        html.Img(
            src=(
                "data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'>"
                "<circle cx='24' cy='24' r='22' fill='%231F1710' "
                "stroke='%23EDE6D6' stroke-width='1' stroke-opacity='0.3'/>"
                "<circle cx='24' cy='24' r='16' fill='%237C8F3E'/>"
                "<circle cx='24' cy='24' r='7' fill='%238B5A2B'/>"
                "</svg>"
            ),
            width="48",
            height="48",
            alt="",
        ),
        id="header-mark",
        className="header-mark",
    )


def info_icon(tooltip_text: str) -> html.Span:
    """Small circular "i" badge that shows `tooltip_text` as a tooltip on hover."""
    return html.Span("i", className="info-icon", title=tooltip_text)


def label_with_tooltip(text: str, tooltip_text: str) -> TooltipChildren:
    """Menu-title `children` list: the label text plus its info-icon tooltip."""
    return [text, info_icon(tooltip_text)]


def build_type_options(lang: str) -> DropdownOptions:
    return [
        {"label": translations.type_label(avocado_type, lang), "value": avocado_type}
        for avocado_type in avocado_types
    ]


def build_numeric_column_options(lang: str) -> DropdownOptions:
    return [
        {
            "label": translations.column_label(col, lang),
            "value": col,
            "title": translations.column_tooltip(col, lang),
        }
        for col in numeric_columns
    ]


def build_groupby_options(lang: str) -> DropdownOptions:
    return [
        {
            "label": translations.groupby_label(value, lang),
            "value": value,
            "title": translations.groupby_tooltip(value, lang),
        }
        for value in ("type", "region", "year")
    ]


external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Fraunces:opsz,wght@9..144,400;9..144,600&"
            "family=Inter:wght@400;600;700&"
            "family=IBM+Plex+Mono:wght@400;600&"
            "display=swap"
        ),
        "rel": "stylesheet",
    },
]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Avocado Analytics"
server = app.server  # This is needed for Railway deployment

# Default language on load — the target audience is primarily Spanish-speaking.
INITIAL_LANG = "es"

LANGUAGE_TOGGLE_OPTIONS: list[dcc.RadioItems.Options] = [
    {"label": "ES", "value": "es"},
    {"label": "EN", "value": "en"},
]

REGION_FILTER_OPTIONS: DropdownOptions = [
    {"label": region, "value": region} for region in regions
]

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                dcc.RadioItems(
                    id="language-toggle",
                    options=LANGUAGE_TOGGLE_OPTIONS,
                    value=INITIAL_LANG,
                    inline=True,
                    className="language-toggle",
                ),
                cross_section_mark(),
                html.H1(children="Avocado Analytics", className="header-title"),
                html.P(
                    id="header-subtitle",
                    children=[
                        translations.t("header.subtitle_by", INITIAL_LANG),
                        html.A(
                            "@Kuautli",
                            href="https://github.com/cuauhtemocbe",
                            target="_blank",
                            className="header-link",
                        ),
                        " | ",
                        html.A(
                            translations.t("header.view_on_github", INITIAL_LANG),
                            href="https://github.com/cuauhtemocbe/AvocadoDash",
                            target="_blank",
                            className="header-link",
                        ),
                    ],
                    className="header-subtitle",
                ),
                html.P(
                    id="header-description",
                    children=translations.t("header.description", INITIAL_LANG),
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(
                            id="region-filter-label",
                            children=label_with_tooltip(
                                translations.t("filters.region.label", INITIAL_LANG),
                                translations.t("filters.region.tooltip", INITIAL_LANG),
                            ),
                            className="menu-title",
                        ),
                        dcc.Dropdown(
                            id="region-filter",
                            options=REGION_FILTER_OPTIONS,
                            value=["Albany"],
                            multi=True,
                            clearable=True,
                            searchable=True,
                            placeholder=translations.t(
                                "filters.region.placeholder", INITIAL_LANG
                            ),
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            id="type-filter-label",
                            children=label_with_tooltip(
                                translations.t("filters.type.label", INITIAL_LANG),
                                translations.t("filters.type.tooltip", INITIAL_LANG),
                            ),
                            className="menu-title",
                        ),
                        dcc.Dropdown(
                            id="type-filter",
                            options=build_type_options(INITIAL_LANG),
                            value="organic",
                            clearable=False,
                            searchable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Div(
                            id="date-range-label",
                            children=label_with_tooltip(
                                translations.t(
                                    "filters.date_range.label", INITIAL_LANG
                                ),
                                translations.t(
                                    "filters.date_range.tooltip", INITIAL_LANG
                                ),
                            ),
                            className="menu-title",
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=data["Date"].min().date(),
                            max_date_allowed=data["Date"].max().date(),
                            start_date=data["Date"].min().date(),
                            end_date=data["Date"].max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Button(
                    translations.t("download.button", INITIAL_LANG),
                    id="download-csv-button",
                    className="download-button",
                ),
                html.Span(id="download-status", className="download-status"),
                dcc.Download(id="download-dataframe-csv"),
            ],
            className="export-section",
        ),
        html.Div(
            id="summary-panel",
            className="summary-panel",
        ),
        dcc.Loading(
            id="charts-loading",
            type="circle",
            children=html.Div(
                children=[
                    html.Div(
                        children=dcc.Graph(
                            id="price-chart",
                            config={"displayModeBar": False},
                        ),
                        className="card",
                    ),
                    html.Div(
                        children=dcc.Graph(
                            id="volume-chart",
                            config={"displayModeBar": False},
                        ),
                        className="card",
                    ),
                ],
                className="wrapper",
            ),
        ),
        html.Div(
            children=[
                html.H2(
                    id="scatter-section-title",
                    children=translations.t("sections.scatter_title", INITIAL_LANG),
                    style={
                        "text-align": "center",
                        "margin": "40px 0 20px 0",
                        "color": "var(--pit)",
                        "font-family": "Fraunces, serif",
                        "font-size": "28px",
                    },
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(
                                    id="x-axis-label",
                                    children=label_with_tooltip(
                                        translations.t(
                                            "filters.x_axis.label", INITIAL_LANG
                                        ),
                                        translations.t(
                                            "filters.x_axis.tooltip", INITIAL_LANG
                                        ),
                                    ),
                                    className="menu-title",
                                ),
                                dcc.Dropdown(
                                    id="x-axis-dropdown",
                                    options=build_numeric_column_options(INITIAL_LANG),
                                    value="AveragePrice",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={"width": "45%", "display": "inline-block"},
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    id="y-axis-label",
                                    children=label_with_tooltip(
                                        translations.t(
                                            "filters.y_axis.label", INITIAL_LANG
                                        ),
                                        translations.t(
                                            "filters.y_axis.tooltip", INITIAL_LANG
                                        ),
                                    ),
                                    className="menu-title",
                                ),
                                dcc.Dropdown(
                                    id="y-axis-dropdown",
                                    options=build_numeric_column_options(INITIAL_LANG),
                                    value="Total Volume",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={
                                "width": "45%",
                                "display": "inline-block",
                                "margin-left": "10%",
                            },
                        ),
                    ],
                    style={"margin": "20px auto", "max-width": "800px"},
                ),
                dcc.Loading(
                    id="scatter-loading",
                    type="circle",
                    children=html.Div(
                        children=dcc.Graph(
                            id="scatter-chart",
                            config={"displayModeBar": True},
                        ),
                        className="card",
                        style={"margin": "20px auto", "max-width": "1000px"},
                    ),
                ),
            ]
        ),
        html.Div(
            children=[
                html.H2(
                    id="box-plot-section-title",
                    children=translations.t("sections.box_plot_title", INITIAL_LANG),
                    style={
                        "text-align": "center",
                        "margin": "40px 0 20px 0",
                        "color": "var(--pit)",
                        "font-family": "Fraunces, serif",
                        "font-size": "28px",
                    },
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(
                                    id="box-plot-column-label",
                                    children=label_with_tooltip(
                                        translations.t(
                                            "filters.box_plot_column.label",
                                            INITIAL_LANG,
                                        ),
                                        translations.t(
                                            "filters.box_plot_column.tooltip",
                                            INITIAL_LANG,
                                        ),
                                    ),
                                    className="menu-title",
                                ),
                                dcc.Dropdown(
                                    id="box-plot-column",
                                    options=build_numeric_column_options(INITIAL_LANG),
                                    value="AveragePrice",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={"width": "45%", "display": "inline-block"},
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    id="box-plot-groupby-label",
                                    children=label_with_tooltip(
                                        translations.t(
                                            "filters.box_plot_groupby.label",
                                            INITIAL_LANG,
                                        ),
                                        translations.t(
                                            "filters.box_plot_groupby.tooltip",
                                            INITIAL_LANG,
                                        ),
                                    ),
                                    className="menu-title",
                                ),
                                dcc.Dropdown(
                                    id="box-plot-groupby",
                                    options=build_groupby_options(INITIAL_LANG),
                                    value="type",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={
                                "width": "45%",
                                "display": "inline-block",
                                "margin-left": "10%",
                            },
                        ),
                    ],
                    style={"margin": "20px auto", "max-width": "800px"},
                ),
                dcc.Loading(
                    id="box-plot-loading",
                    type="circle",
                    children=html.Div(
                        children=dcc.Graph(
                            id="box-plot-chart",
                            config={"displayModeBar": True},
                        ),
                        className="card",
                        style={"margin": "20px auto", "max-width": "1000px"},
                    ),
                ),
            ]
        ),
        html.Div(
            children=[
                html.P(
                    id="footer-text",
                    children=[
                        translations.t("footer.created_by", INITIAL_LANG),
                        html.A(
                            "@Kuautli",
                            href="https://github.com/cuauhtemocbe",
                            target="_blank",
                            className="footer-link",
                        ),
                        " | ",
                        html.A(
                            translations.t("header.view_on_github", INITIAL_LANG),
                            href="https://github.com/cuauhtemocbe/AvocadoDash",
                            target="_blank",
                            className="footer-link",
                        ),
                    ],
                    className="footer-text",
                )
            ],
            className="footer",
        ),
    ]
)


TREND_GLYPHS = {"summary-stat-up": "▲ ", "summary-stat-down": "▼ "}


def summary_stat_card(label: str, value: str, extra_class: str = "") -> html.Div:
    """A single KPI card for the summary panel. A `summary-stat-up`/
    `summary-stat-down` extra_class also prefixes `value` with a ▲/▼ glyph,
    so trend direction is never communicated by color alone."""
    glyph = TREND_GLYPHS.get(extra_class, "")
    return html.Div(
        children=[
            html.Div(label, className="summary-stat-label"),
            html.Div(
                f"{glyph}{value}",
                className=f"summary-stat-value {extra_class}".strip(),
            ),
        ],
        className="summary-stat",
    )


def create_summary_panel(
    filtered_data: pd.DataFrame,
    regions: list[str],
    avocado_type: str,
    start_date: str,
    end_date: str,
    lang: str = "en",
) -> html.Div:
    """Build the summary panel's KPI cards for the current filter selection."""
    if filtered_data.empty:
        return html.Div(
            translations.t("empty.no_data_summary", lang),
            className="summary-empty",
        )

    stats = calculate_summary_stats(filtered_data)
    price_change = calculate_price_change(
        data, regions, avocado_type, start_date, end_date
    )
    extremes = find_region_extremes(data, avocado_type, start_date, end_date)

    cards = [
        summary_stat_card(
            translations.column_label("AveragePrice", lang),
            f"${stats['avg_price']:.2f}",
        ),
        summary_stat_card(
            translations.column_label("Total Volume", lang),
            format_number(stats["total_volume"]),
        ),
    ]

    if price_change is not None:
        sign = "+" if price_change >= 0 else ""
        trend_class = "summary-stat-up" if price_change >= 0 else "summary-stat-down"
        cards.append(
            summary_stat_card(
                translations.t("summary.price_change", lang),
                f"{sign}{price_change:.1f}%",
                trend_class,
            )
        )

    if extremes is not None:
        cards.append(
            summary_stat_card(
                translations.t("summary.best_region", lang),
                f"{extremes['best_region']} (${extremes['best_price']:.2f})",
            )
        )
        cards.append(
            summary_stat_card(
                translations.t("summary.worst_region", lang),
                f"{extremes['worst_region']} (${extremes['worst_price']:.2f})",
            )
        )

    return html.Div(cards, className="summary-stats")


def _region_traces(
    filtered_data: pd.DataFrame,
    y_column: str,
    hover_label: str,
    hover_format: str,
    lang: str = "en",
) -> list[dict[str, Any]]:
    """One line+marker trace per region present in `filtered_data`, colored
    in a fixed palette order by the current selection (see
    REGION_COLOR_PALETTE for why this isn't a fixed per-region color)."""
    traces: list[dict[str, Any]] = []
    selected_regions = sorted(filtered_data["region"].unique())
    date_label = translations.t("common.date", lang)
    for i, region in enumerate(selected_regions):
        region_data = filtered_data[filtered_data["region"] == region]
        color = REGION_COLOR_PALETTE[i % len(REGION_COLOR_PALETTE)]
        traces.append(
            {
                "x": region_data["Date"],
                "y": region_data[y_column],
                "type": "scatter",
                "mode": "lines+markers",
                "name": region,
                "hovertemplate": (
                    f"<b>%{{fullData.name}}</b><br>{date_label}: %{{x}}<br>"
                    f"{hover_label}: {hover_format}<extra></extra>"
                ),
                "line": {"width": 3, "color": color},
                "marker": {"size": 4, "color": color},
            }
        )
    return traces


def create_price_chart(filtered_data: pd.DataFrame, lang: str = "en") -> dict[str, Any]:
    """Create the price chart, one line per region in `filtered_data`."""
    price_label = translations.t("common.price", lang)
    traces = _region_traces(
        filtered_data, "AveragePrice", price_label, "$%{y:.2f}", lang
    )
    return {
        "data": traces,
        "layout": {
            "title": {
                "text": translations.t("charts.price.title", lang),
                "x": 0.05,
                "xanchor": "left",
                "font": {"size": 20},
            },
            "xaxis": {
                "fixedrange": True,
                "title": translations.t("common.date", lang),
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "yaxis": {
                "tickprefix": "$",
                "fixedrange": True,
                "title": translations.t("charts.price.yaxis", lang),
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "plot_bgcolor": CHART_BG,
            "paper_bgcolor": CHART_BG,
            "showlegend": len(traces) > 1,
            "legend": {
                "x": 1.02,
                "y": 1,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "gray",
                "borderwidth": 1,
            },
        },
    }


def create_volume_chart(
    filtered_data: pd.DataFrame, lang: str = "en"
) -> dict[str, Any]:
    """Create the volume chart, one line per region in `filtered_data`."""
    volume_label = translations.t("common.volume", lang)
    traces = _region_traces(
        filtered_data, "Total Volume", volume_label, "%{y:,.0f}", lang
    )
    return {
        "data": traces,
        "layout": {
            "title": {
                "text": translations.t("charts.volume.title", lang),
                "x": 0.05,
                "xanchor": "left",
                "font": {"size": 20},
            },
            "xaxis": {
                "fixedrange": True,
                "title": translations.t("common.date", lang),
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "yaxis": {
                "fixedrange": True,
                "title": volume_label,
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "plot_bgcolor": CHART_BG,
            "paper_bgcolor": CHART_BG,
            "showlegend": len(traces) > 1,
            "legend": {
                "x": 1.02,
                "y": 1,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "gray",
                "borderwidth": 1,
            },
        },
    }


def create_box_plot(
    filtered_data: pd.DataFrame, column: str, group_by: str, lang: str = "en"
) -> dict[str, Any]:
    """Create a box plot for the selected column grouped by the specified variable."""
    # Color mapping for different groups
    color_map = TYPE_COLOR_MAP

    traces: list[dict[str, Any]] = []

    if group_by == "type":
        # Group by avocado type
        for avocado_type in sorted(filtered_data["type"].unique()):
            type_data = filtered_data[filtered_data["type"] == avocado_type]
            traces.append(
                {
                    "y": type_data[column],
                    "type": "box",
                    "name": translations.type_label(avocado_type, lang),
                    "marker": {"color": color_map.get(avocado_type, "#17B897")},
                    "boxpoints": "outliers",
                    "jitter": 0.3,
                    "pointpos": -1.8,
                }
            )

    elif group_by == "region":
        # For regions, use a single box plot with color by type if multiple types exist
        if len(filtered_data["type"].unique()) > 1:
            for avocado_type in sorted(filtered_data["type"].unique()):
                type_data = filtered_data[filtered_data["type"] == avocado_type]
                traces.append(
                    {
                        "y": type_data[column],
                        "x": type_data["region"],
                        "type": "box",
                        "name": translations.type_label(avocado_type, lang),
                        "marker": {"color": color_map.get(avocado_type, "#17B897")},
                        "boxpoints": "outliers",
                    }
                )
        else:
            # Single type, group by region
            for region in sorted(filtered_data["region"].unique()):
                region_data = filtered_data[filtered_data["region"] == region]
                traces.append(
                    {
                        "y": region_data[column],
                        "type": "box",
                        "name": region,
                        "boxpoints": "outliers",
                        "jitter": 0.3,
                        "pointpos": -1.8,
                    }
                )

    elif group_by == "year":
        # Group by year
        for year in sorted(filtered_data["year"].unique()):
            year_data = filtered_data[filtered_data["year"] == year]
            traces.append(
                {
                    "y": year_data[column],
                    "type": "box",
                    "name": str(year),
                    "boxpoints": "outliers",
                    "jitter": 0.3,
                    "pointpos": -1.8,
                }
            )

    # Determine layout based on group_by
    if group_by == "region" and len(filtered_data["type"].unique()) > 1:
        x_title = translations.t("common.region", lang)
        show_legend = True
    else:
        x_title = translations.groupby_label(group_by, lang)
        show_legend = len(traces) > 1

    return {
        "data": traces,
        "layout": {
            "title": {
                "text": (
                    f"{translations.column_label(column, lang)} "
                    f"{translations.t('charts.box_plot.distribution_by', lang)} "
                    f"{translations.groupby_label(group_by, lang)}"
                ),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 22},
            },
            "xaxis": {
                "title": x_title,
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "yaxis": {
                "title": translations.column_label(column, lang),
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "plot_bgcolor": CHART_BG,
            "paper_bgcolor": CHART_BG,
            "showlegend": show_legend,
            "legend": {
                "x": 1.02,
                "y": 1,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "gray",
                "borderwidth": 1,
            },
        },
    }


def create_scatter_chart(
    filtered_data: pd.DataFrame, x_col: str, y_col: str, lang: str = "en"
) -> dict[str, Any]:
    """Create a scatter plot with selected columns."""
    # Create color mapping for avocado types
    color_map = TYPE_COLOR_MAP
    x_label = translations.column_label(x_col, lang)
    y_label = translations.column_label(y_col, lang)
    region_label = translations.t("common.region", lang)
    date_label = translations.t("common.date", lang)

    traces: list[dict[str, Any]] = []
    for avocado_type in filtered_data["type"].unique():
        type_data = filtered_data[filtered_data["type"] == avocado_type]
        traces.append(
            {
                "x": type_data[x_col],
                "y": type_data[y_col],
                "mode": "markers",
                "type": "scatter",
                "name": translations.type_label(avocado_type, lang),
                "marker": {
                    "size": 8,
                    "color": color_map.get(avocado_type, "#17B897"),
                    "opacity": 0.7,
                    "line": {"width": 1, "color": "white"},
                },
                "hovertemplate": (
                    f"<b>%{{fullData.name}}</b><br>"
                    f"{x_label}: %{{x}}<br>"
                    f"{y_label}: %{{y}}<br>"
                    f"{region_label}: %{{customdata[0]}}<br>"
                    f"{date_label}: %{{customdata[1]}}<extra></extra>"
                ),
                "customdata": list(
                    zip(type_data["region"], type_data["Date"].dt.strftime("%Y-%m-%d"))
                ),
            }
        )

    return {
        "data": traces,
        "layout": {
            "title": {
                "text": (
                    f"{x_label} {translations.t('charts.scatter.vs', lang)} {y_label}"
                ),
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 22},
            },
            "xaxis": {
                "title": x_label,
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "yaxis": {
                "title": y_label,
                "showgrid": True,
                "gridcolor": CHART_GRIDCOLOR,
            },
            "plot_bgcolor": CHART_BG,
            "paper_bgcolor": CHART_BG,
            "hovermode": "closest",
            "legend": {
                "x": 1.02,
                "y": 1,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "gray",
                "borderwidth": 1,
            },
        },
    }


@app.callback(
    Output("header-subtitle", "children"),
    Output("header-description", "children"),
    Output("footer-text", "children"),
    Output("scatter-section-title", "children"),
    Output("box-plot-section-title", "children"),
    Output("region-filter-label", "children"),
    Output("region-filter", "placeholder"),
    Output("type-filter-label", "children"),
    Output("type-filter", "options"),
    Output("date-range-label", "children"),
    Output("download-csv-button", "children"),
    Output("x-axis-label", "children"),
    Output("x-axis-dropdown", "options"),
    Output("y-axis-label", "children"),
    Output("y-axis-dropdown", "options"),
    Output("box-plot-column-label", "children"),
    Output("box-plot-column", "options"),
    Output("box-plot-groupby-label", "children"),
    Output("box-plot-groupby", "options"),
    Input("language-toggle", "value"),
)
def update_ui_language(
    lang: str,
) -> tuple[
    HeaderText,
    str,
    HeaderText,
    str,
    str,
    TooltipChildren,
    str,
    TooltipChildren,
    DropdownOptions,
    TooltipChildren,
    str,
    TooltipChildren,
    DropdownOptions,
    TooltipChildren,
    DropdownOptions,
    TooltipChildren,
    DropdownOptions,
    TooltipChildren,
    DropdownOptions,
]:
    """Retranslate every static, filter-independent piece of text/labels in
    the layout. Only `children`/`placeholder`/`options["label"|"title"]` are
    touched — dropdown `value`s (and thus filtering/query logic) never
    change here."""
    view_on_github = translations.t("header.view_on_github", lang)
    return (
        [
            translations.t("header.subtitle_by", lang),
            html.A(
                "@Kuautli",
                href="https://github.com/cuauhtemocbe",
                target="_blank",
                className="header-link",
            ),
            " | ",
            html.A(
                view_on_github,
                href="https://github.com/cuauhtemocbe/AvocadoDash",
                target="_blank",
                className="header-link",
            ),
        ],
        translations.t("header.description", lang),
        [
            translations.t("footer.created_by", lang),
            html.A(
                "@Kuautli",
                href="https://github.com/cuauhtemocbe",
                target="_blank",
                className="footer-link",
            ),
            " | ",
            html.A(
                view_on_github,
                href="https://github.com/cuauhtemocbe/AvocadoDash",
                target="_blank",
                className="footer-link",
            ),
        ],
        translations.t("sections.scatter_title", lang),
        translations.t("sections.box_plot_title", lang),
        label_with_tooltip(
            translations.t("filters.region.label", lang),
            translations.t("filters.region.tooltip", lang),
        ),
        translations.t("filters.region.placeholder", lang),
        label_with_tooltip(
            translations.t("filters.type.label", lang),
            translations.t("filters.type.tooltip", lang),
        ),
        build_type_options(lang),
        label_with_tooltip(
            translations.t("filters.date_range.label", lang),
            translations.t("filters.date_range.tooltip", lang),
        ),
        translations.t("download.button", lang),
        label_with_tooltip(
            translations.t("filters.x_axis.label", lang),
            translations.t("filters.x_axis.tooltip", lang),
        ),
        build_numeric_column_options(lang),
        label_with_tooltip(
            translations.t("filters.y_axis.label", lang),
            translations.t("filters.y_axis.tooltip", lang),
        ),
        build_numeric_column_options(lang),
        label_with_tooltip(
            translations.t("filters.box_plot_column.label", lang),
            translations.t("filters.box_plot_column.tooltip", lang),
        ),
        build_numeric_column_options(lang),
        label_with_tooltip(
            translations.t("filters.box_plot_groupby.label", lang),
            translations.t("filters.box_plot_groupby.tooltip", lang),
        ),
        build_groupby_options(lang),
    )


@app.callback(
    Output("summary-panel", "children"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("language-toggle", "value"),
)
def update_summary_panel(
    regions: list[str] | None,
    avocado_type: str,
    start_date: str,
    end_date: str,
    lang: str = "en",
) -> html.Div:
    """Update the summary panel based on filter selections."""
    try:
        if not regions:
            return html.Div(
                translations.t("empty.select_region", lang), className="summary-empty"
            )
        filtered_data = filter_data(regions, avocado_type, start_date, end_date)
        return create_summary_panel(
            filtered_data, regions, avocado_type, start_date, end_date, lang
        )
    except Exception as e:
        logger.error(f"Error in summary panel callback: {str(e)}", exc_info=True)
        error_prefix = translations.t("common.error_prefix", lang)
        return html.Div(f"{error_prefix}: {str(e)}", className="summary-empty")


@app.callback(
    Output("download-csv-button", "disabled"),
    Output("download-status", "children"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("language-toggle", "value"),
)
def update_download_controls(
    regions: list[str] | None,
    avocado_type: str,
    start_date: str,
    end_date: str,
    lang: str = "en",
) -> tuple[bool, str]:
    """Enable/disable the CSV download button based on filter selections."""
    try:
        if not regions:
            return True, translations.t("empty.select_region", lang)
        filtered_data = filter_data(regions, avocado_type, start_date, end_date)
        if filtered_data.empty:
            return True, translations.t("download.no_data", lang)
        return False, ""
    except Exception as e:
        logger.error(f"Error in download controls callback: {str(e)}", exc_info=True)
        error_prefix = translations.t("common.error_prefix", lang)
        return True, f"{error_prefix}: {str(e)}"


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("download-csv-button", "n_clicks"),
    State("region-filter", "value"),
    State("type-filter", "value"),
    State("date-range", "start_date"),
    State("date-range", "end_date"),
    prevent_initial_call=True,
)
def download_filtered_csv(
    n_clicks: int | None,
    regions: list[str] | None,
    avocado_type: str,
    start_date: str,
    end_date: str,
) -> dict[str, Any] | NoUpdate:
    """Export the currently filtered rows as a downloadable CSV."""
    try:
        if not regions:
            return no_update
        filtered_data = filter_data(regions, avocado_type, start_date, end_date)
        if filtered_data.empty:
            return no_update
        # dash.dcc's dynamic __all__ defeats mypy's re-export check, and
        # express.send_data_frame has no upstream annotations — both Dash-stub
        # gaps; kept as `dcc.send_data_frame` (vs. a direct import) so tests
        # can still `patch("app.dcc.send_data_frame", ...)`.
        return dcc.send_data_frame(  # type: ignore[attr-defined,no-untyped-call,no-any-return]
            filtered_data.to_csv, "avocado_filtered.csv", index=False
        )
    except Exception as e:
        logger.error(f"Error in download callback: {str(e)}", exc_info=True)
        return no_update


@app.callback(
    Output("price-chart", "figure"),
    Output("volume-chart", "figure"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("language-toggle", "value"),
)
def update_charts(
    regions: list[str] | None,
    avocado_type: str,
    start_date: str,
    end_date: str,
    lang: str = "en",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Update charts based on filter selections."""
    try:
        if not regions:
            empty_fig = empty_state_figure(
                translations.t("empty.select_region", lang), lang
            )
            return empty_fig, empty_fig

        # Filter data based on selections
        filtered_data = filter_data(regions, avocado_type, start_date, end_date)

        # Handle empty data case
        if filtered_data.empty:
            empty_fig = empty_state_figure(
                translations.t("empty.try_adjusting", lang), lang
            )
            return empty_fig, empty_fig

        return (
            create_price_chart(filtered_data, lang),
            create_volume_chart(filtered_data, lang),
        )

    except Exception as e:
        logger.error(f"Error in callback: {str(e)}", exc_info=True)
        # Return empty figures on error
        error_prefix = translations.t("common.error_prefix", lang)
        error_fig = {"data": [], "layout": {"title": f"{error_prefix}: {str(e)}"}}
        return error_fig, error_fig


@app.callback(
    Output("scatter-chart", "figure"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("x-axis-dropdown", "value"),
    Input("y-axis-dropdown", "value"),
    Input("language-toggle", "value"),
)
def update_scatter_chart(
    regions: list[str] | None,
    avocado_type: str,
    start_date: str,
    end_date: str,
    x_col: str,
    y_col: str,
    lang: str = "en",
) -> dict[str, Any]:
    """Update scatter chart based on filter selections and axis choices."""
    try:
        if not regions:
            return empty_state_figure(translations.t("empty.select_region", lang), lang)

        # Filter data based on selections
        filtered_data = filter_data(regions, avocado_type, start_date, end_date)

        # Handle empty data case
        if filtered_data.empty:
            return empty_state_figure(translations.t("empty.try_adjusting", lang), lang)

        return create_scatter_chart(filtered_data, x_col, y_col, lang)

    except Exception as e:
        logger.error(f"Error in scatter chart callback: {str(e)}", exc_info=True)
        error_prefix = translations.t("common.error_prefix", lang)
        return {"data": [], "layout": {"title": f"{error_prefix}: {str(e)}"}}


@app.callback(
    Output("box-plot-chart", "figure"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("box-plot-column", "value"),
    Input("box-plot-groupby", "value"),
    Input("language-toggle", "value"),
)
def update_box_plot(
    regions: list[str] | None,
    avocado_type: str,
    start_date: str,
    end_date: str,
    column: str,
    group_by: str,
    lang: str = "en",
) -> dict[str, Any]:
    """Update box plot based on filter selections and grouping choice."""
    try:
        # For box plots, we might want to show data across different groups
        # So we'll modify the filtering based on the group_by selection
        if group_by == "region":
            # Show data for selected type across every region, regardless of
            # the region filter (grouping by region shouldn't also pin it).
            filtered_data = data.query(
                "type == @avocado_type and Date >= @start_date and Date <= @end_date"
            )
        else:
            if not regions:
                return empty_state_figure(
                    translations.t("empty.select_region", lang), lang
                )
            if group_by == "type":
                # Show both types, but filter by regions and date
                filtered_data = data.query(
                    "region in @regions and Date >= @start_date and Date <= @end_date"
                )
            else:
                # "year", or any other grouping: full region/type/date filter
                filtered_data = filter_data(regions, avocado_type, start_date, end_date)

        # Handle empty data case
        if filtered_data.empty:
            return empty_state_figure(translations.t("empty.try_adjusting", lang), lang)

        return create_box_plot(filtered_data, column, group_by, lang)

    except Exception as e:
        logger.error(f"Error in box plot callback: {str(e)}", exc_info=True)
        error_prefix = translations.t("common.error_prefix", lang)
        return {"data": [], "layout": {"title": f"{error_prefix}: {str(e)}"}}


if __name__ == "__main__":
    # Get port from environment variable for Railway deployment
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(debug=debug, host="0.0.0.0", port=port)

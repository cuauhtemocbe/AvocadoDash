"""Scatter and box-plot callbacks through Dash's HTTP endpoints (issue #49).

Builds on the `dash_client` fixture from conftest.py (issue #42). Titles and
axis labels are derived from `translations`; trace data is compared as-is.
"""

from typing import Any
from urllib.parse import parse_qs

import pytest

from app import _chart_chrome, data
from translations import column_label, groupby_label, t

SCATTER = "scatter-chart.figure"
BOX_PLOT = "box-plot-chart.figure"
CHARTS = [SCATTER, BOX_PLOT]

ALL_REGIONS = data["region"].nunique()

NO_REGIONS: dict[str, Any] = {"region-filter.value": []}


def lang(code):
    return {"language-toggle.value": code}


def theme(name):
    return {"theme-resolved.data": name}


def trace_names(figure):
    return [trace["name"] for trace in figure["data"]]


def trace_values(figure):
    """Only the plotted numbers: names and hover text change with language."""
    return [(trace.get("x"), trace.get("y")) for trace in figure["data"]]


def scatter_title(x_col, y_col, code):
    return f"{column_label(x_col, code)} {t('charts.scatter.vs', code)} " + (
        column_label(y_col, code)
    )


def box_title(column, group_by, code):
    return (
        f"{column_label(column, code)} {t('charts.box_plot.distribution_by', code)} "
        f"{groupby_label(group_by, code)}"
    )


def test_changing_the_scatter_axes_updates_title_and_axis_titles(dash_client):
    figure = dash_client.figure(
        SCATTER,
        {"x-axis-dropdown.value": "Large Bags", "y-axis-dropdown.value": "Total Bags"},
    )

    layout = figure["layout"]
    assert layout["title"]["text"] == scatter_title("Large Bags", "Total Bags", "es")
    assert layout["xaxis"]["title"] == column_label("Large Bags", "es")
    assert layout["yaxis"]["title"] == column_label("Total Bags", "es")


def test_box_plot_by_type_shows_both_types_regardless_of_type_filter(dash_client):
    figure = dash_client.figure(
        BOX_PLOT, {"type-filter.value": "organic", "box-plot-groupby.value": "type"}
    )

    assert len(figure["data"]) == 2


def test_box_plot_by_region_ignores_the_region_filter(dash_client):
    figure = dash_client.figure(
        BOX_PLOT,
        {"region-filter.value": ["Albany"], "box-plot-groupby.value": "region"},
    )

    assert len(figure["data"]) == ALL_REGIONS
    assert "Albany" in trace_names(figure)


def test_box_plot_by_year_shows_one_box_per_year_in_range(dash_client):
    by_year = {"box-plot-groupby.value": "year"}
    full = dash_client.figure(BOX_PLOT, by_year)
    one_year = dash_client.figure(
        BOX_PLOT,
        {
            **by_year,
            "date-range.start_date": "2016-01-03",
            "date-range.end_date": "2016-12-25",
        },
    )

    assert trace_names(full) == ["2015", "2016", "2017", "2018"]
    assert trace_names(one_year) == ["2016"]


def test_with_no_region_selected_only_grouping_by_region_still_renders(dash_client):
    by_region = {**NO_REGIONS, "box-plot-groupby.value": "region"}
    scatter = dash_client.figure(SCATTER, NO_REGIONS)

    assert len(dash_client.figure(BOX_PLOT, by_region)["data"]) == ALL_REGIONS
    assert scatter["data"] == []
    assert scatter["layout"]["annotations"][0]["text"] == t("empty.select_region", "es")


@pytest.mark.parametrize("group_by", ["type", "year"])
def test_with_no_region_selected_other_groupings_show_the_empty_state(
    dash_client, group_by
):
    figure = dash_client.figure(
        BOX_PLOT, {**NO_REGIONS, "box-plot-groupby.value": group_by}
    )

    assert figure["data"] == []
    assert figure["layout"]["annotations"][0]["text"] == t("empty.select_region", "es")


def test_language_toggle_relabels_both_charts_without_touching_the_data(dash_client):
    scatter_values = {"x-axis-dropdown.value": "Large Bags"}
    box_values = {
        "box-plot-column.value": "Total Bags",
        "box-plot-groupby.value": "year",
    }
    scatter = {
        c: dash_client.figure(SCATTER, {**scatter_values, **lang(c)})
        for c in ("en", "es")
    }
    box = {
        c: dash_client.figure(BOX_PLOT, {**box_values, **lang(c)}) for c in ("en", "es")
    }

    for code in ("en", "es"):
        assert scatter[code]["layout"]["title"]["text"] == scatter_title(
            "Large Bags", "Total Volume", code
        )
        assert scatter[code]["layout"]["xaxis"]["title"] == column_label(
            "Large Bags", code
        )
        assert box[code]["layout"]["title"]["text"] == box_title(
            "Total Bags", "year", code
        )
        assert box[code]["layout"]["yaxis"]["title"] == column_label("Total Bags", code)
        assert box[code]["layout"]["xaxis"]["title"] == groupby_label("year", code)
    assert scatter["en"]["layout"]["title"] != scatter["es"]["layout"]["title"]
    assert trace_values(scatter["en"]) == trace_values(scatter["es"])
    assert trace_values(box["en"]) == trace_values(box["es"])


@pytest.mark.parametrize("output_prop", CHARTS)
def test_resolved_theme_restyles_the_chart_without_touching_the_data(
    dash_client, output_prop
):
    light = dash_client.figure(output_prop, theme("light"))
    dark = dash_client.figure(output_prop, theme("dark"))

    for figure, name in ((light, "light"), (dark, "dark")):
        chart_bg, gridcolor, text_color = _chart_chrome(name)
        layout = figure["layout"]
        assert layout["plot_bgcolor"] == layout["paper_bgcolor"] == chart_bg
        assert layout["xaxis"]["gridcolor"] == layout["yaxis"]["gridcolor"] == gridcolor
        assert layout["font"]["color"] == text_color
    assert _chart_chrome("light") != _chart_chrome("dark")
    assert trace_values(light) == trace_values(dark)


def test_axis_and_groupby_selections_round_trip_through_the_url(dash_client):
    search = "?x=Large+Bags&y=XLarge+Bags&col=Total+Bags&groupby=year"

    restored = dash_client.call("url.search", {"url.search": search})

    assert restored["x-axis-dropdown.value"] == "Large Bags"
    assert restored["y-axis-dropdown.value"] == "XLarge Bags"
    assert restored["box-plot-column.value"] == "Total Bags"
    assert restored["box-plot-groupby.value"] == "year"

    scatter = dash_client.figure(
        SCATTER,
        {
            "x-axis-dropdown.value": restored["x-axis-dropdown.value"],
            "y-axis-dropdown.value": restored["y-axis-dropdown.value"],
        },
    )
    box = dash_client.figure(
        BOX_PLOT,
        {
            "box-plot-column.value": restored["box-plot-column.value"],
            "box-plot-groupby.value": restored["box-plot-groupby.value"],
        },
    )
    assert scatter["layout"]["title"]["text"] == scatter_title(
        "Large Bags", "XLarge Bags", "es"
    )
    assert box["layout"]["title"]["text"] == box_title("Total Bags", "year", "es")

    written = dash_client.call(
        "url.search",
        {"box-plot-groupby.value": "region", "url.search": search},
        changed=["box-plot-groupby.value"],
    )
    assert parse_qs(written["url.search"].lstrip("?"))["groupby"] == ["region"]

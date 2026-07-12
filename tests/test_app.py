from unittest.mock import patch

import pytest
from dash import dcc

from app import (
    app,
    create_box_plot,
    create_price_chart,
    create_scatter_chart,
    create_summary_panel,
    create_volume_chart,
    data,
    update_box_plot,
    update_charts,
    update_scatter_chart,
)
from utils import calculate_price_change, find_region_extremes, format_number

CONTROL_LABEL_IDS = [
    "region-filter-label",
    "type-filter-label",
    "date-range-label",
    "x-axis-label",
    "y-axis-label",
    "box-plot-column-label",
    "box-plot-groupby-label",
]

METRIC_DROPDOWN_IDS = [
    "x-axis-dropdown",
    "y-axis-dropdown",
    "box-plot-column",
]


def find_component_by_id(component, component_id):
    """Recursively search a Dash component tree for a component by id."""
    if getattr(component, "id", None) == component_id:
        return component

    children = getattr(component, "children", None)
    if children is None:
        return None
    if not isinstance(children, list):
        children = [children]

    for child in children:
        if hasattr(child, "id") or hasattr(child, "children"):
            found = find_component_by_id(child, component_id)
            if found is not None:
                return found
    return None


def find_loading_ancestor(component, target_id, current_loading=None):
    """Walk the layout tree, returning the nearest dcc.Loading ancestor of
    the component with `target_id`, or None if it has no such ancestor."""
    if isinstance(component, dcc.Loading):
        current_loading = component

    if getattr(component, "id", None) == target_id:
        return current_loading

    children = getattr(component, "children", None)
    if children is None:
        return None
    if not isinstance(children, list):
        children = [children]

    for child in children:
        if hasattr(child, "id") or hasattr(child, "children"):
            found = find_loading_ancestor(child, target_id, current_loading)
            if found is not None:
                return found
    return None


def test_price_and_volume_charts_share_a_loading_indicator():
    price_loading = find_loading_ancestor(app.layout, "price-chart")
    volume_loading = find_loading_ancestor(app.layout, "volume-chart")

    assert price_loading is not None
    assert price_loading is volume_loading


def test_scatter_chart_has_its_own_loading_indicator_isolated_from_other_charts():
    scatter_loading = find_loading_ancestor(app.layout, "scatter-chart")
    price_loading = find_loading_ancestor(app.layout, "price-chart")
    box_loading = find_loading_ancestor(app.layout, "box-plot-chart")

    assert scatter_loading is not None
    assert scatter_loading is not price_loading
    assert scatter_loading is not box_loading


def test_box_plot_chart_has_its_own_loading_indicator_isolated_from_other_charts():
    box_loading = find_loading_ancestor(app.layout, "box-plot-chart")
    price_loading = find_loading_ancestor(app.layout, "price-chart")
    scatter_loading = find_loading_ancestor(app.layout, "scatter-chart")

    assert box_loading is not None
    assert box_loading is not price_loading
    assert box_loading is not scatter_loading


def test_load_data_has_expected_columns():
    assert not data.empty
    for column in ("Date", "AveragePrice", "Total Volume", "region", "type"):
        assert column in data.columns


def test_create_price_chart_returns_plotly_figure_dict():
    figure = create_price_chart(data.head(50))

    assert "data" in figure
    assert "layout" in figure
    assert isinstance(figure["data"], list)


def find_info_icon(component):
    """Recursively search a Dash component tree for the first info-icon span."""
    if getattr(component, "className", None) == "info-icon":
        return component

    children = getattr(component, "children", None)
    if children is None:
        return None
    if not isinstance(children, list):
        children = [children]

    for child in children:
        if hasattr(child, "children") or hasattr(child, "className"):
            found = find_info_icon(child)
            if found is not None:
                return found
    return None


def test_control_labels_have_tooltip_icons():
    for label_id in CONTROL_LABEL_IDS:
        label = find_component_by_id(app.layout, label_id)
        assert label is not None, f"{label_id} not found in layout"

        icon = find_info_icon(label)
        assert icon is not None, f"{label_id} has no info-icon tooltip"
        assert isinstance(icon.title, str) and icon.title.strip()


def test_metric_dropdown_options_have_tooltip_titles():
    for dropdown_id in METRIC_DROPDOWN_IDS:
        dropdown = find_component_by_id(app.layout, dropdown_id)
        assert dropdown is not None, f"{dropdown_id} not found in layout"
        for option in dropdown.options:
            assert "label" in option and "value" in option
            assert isinstance(option.get("title"), str) and option["title"].strip()


def test_box_plot_groupby_options_have_tooltip_titles():
    dropdown = find_component_by_id(app.layout, "box-plot-groupby")
    assert dropdown is not None
    for option in dropdown.options:
        assert isinstance(option.get("title"), str) and option["title"].strip()


def collect_text(component):
    """Recursively collect all string children from a Dash component tree."""
    texts = []
    children = getattr(component, "children", None)
    if isinstance(children, str):
        texts.append(children)
    elif isinstance(children, list):
        for child in children:
            if isinstance(child, str):
                texts.append(child)
            else:
                texts.extend(collect_text(child))
    elif children is not None:
        texts.extend(collect_text(children))
    return texts


def test_summary_panel_shows_avg_price_and_total_volume():
    region, avocado_type = "Albany", "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = data.query(
        "region == @region and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"
    )
    assert not filtered.empty

    panel = create_summary_panel(filtered, region, avocado_type, start_date, end_date)
    texts = collect_text(panel)

    expected_price = f"${filtered['AveragePrice'].mean():.2f}"
    expected_volume = format_number(filtered["Total Volume"].sum())
    assert any(expected_price in t for t in texts)
    assert any(expected_volume in t for t in texts)


def test_summary_panel_shows_price_change_vs_previous_period():
    region, avocado_type = "Albany", "organic"
    start_date, end_date = "2016-01-01", "2016-12-31"
    filtered = data.query(
        "region == @region and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"
    )
    assert not filtered.empty

    expected_change = calculate_price_change(
        data, region, avocado_type, start_date, end_date
    )
    assert expected_change is not None

    panel = create_summary_panel(filtered, region, avocado_type, start_date, end_date)
    texts = collect_text(panel)
    sign = "+" if expected_change >= 0 else ""
    expected_text = f"{sign}{expected_change:.1f}%"
    assert any(expected_text in t for t in texts)


def test_summary_panel_highlights_best_worst_region():
    region, avocado_type = "Albany", "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = data.query(
        "region == @region and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"
    )
    assert not filtered.empty

    extremes = find_region_extremes(data, avocado_type, start_date, end_date)
    assert extremes is not None

    panel = create_summary_panel(filtered, region, avocado_type, start_date, end_date)
    joined = " ".join(collect_text(panel))
    assert extremes["best_region"] in joined
    assert extremes["worst_region"] in joined


def test_summary_panel_handles_no_data():
    region, avocado_type = "Albany", "organic"
    # A date range entirely outside the dataset yields zero rows.
    start_date, end_date = "1999-01-01", "1999-12-31"
    filtered = data.query(
        "region == @region and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"
    )
    assert filtered.empty

    panel = create_summary_panel(filtered, region, avocado_type, start_date, end_date)
    assert panel.className == "summary-empty"
    assert "no data" in panel.children.lower()


@pytest.mark.parametrize(
    "raw_value,formatted_value",
    [
        (1_500_000, "1.5M"),
        (2_500, "2.5K"),
        (850, "850"),
    ],
)
def test_format_number_formats_for_readability(raw_value, formatted_value):
    assert format_number(raw_value) == formatted_value


def test_create_volume_chart_returns_plotly_figure_dict():
    filtered = data.query("region == 'Albany' and type == 'organic'").head(50)

    figure = create_volume_chart(filtered)

    assert "data" in figure
    assert "layout" in figure
    volume_trace = figure["data"][0]
    assert list(volume_trace["x"]) == list(filtered["Date"])
    assert list(volume_trace["y"]) == list(filtered["Total Volume"])


@pytest.mark.parametrize(
    "group_by,query,expected_group_count",
    [
        (
            "type",
            "region == 'Albany' and Date >= '2015-01-01' and Date <= '2015-12-31'",
            2,
        ),
        (
            "region",
            "type == 'organic' and Date >= '2015-01-01' and Date <= '2015-01-31'",
            54,
        ),
        ("year", "region == 'Albany' and type == 'organic'", 4),
    ],
)
def test_create_box_plot_produces_one_trace_per_group(
    group_by, query, expected_group_count
):
    filtered = data.query(query)
    assert filtered[group_by].nunique() == expected_group_count

    figure = create_box_plot(filtered, "AveragePrice", group_by)

    assert len(figure["data"]) == expected_group_count
    assert all(trace["type"] == "box" for trace in figure["data"])


def test_update_charts_returns_empty_state_for_no_matching_data():
    price_fig, volume_fig = update_charts(
        "Albany", "organic", "1999-01-01", "1999-12-31"
    )

    assert price_fig["data"] == []
    assert volume_fig["data"] == []
    assert "no data available" in price_fig["layout"]["title"].lower()
    assert "no data available" in volume_fig["layout"]["title"].lower()


def test_update_box_plot_groups_by_type_regardless_of_type_filter():
    figure = update_box_plot(
        "Albany", "organic", "2015-01-01", "2015-12-31", "AveragePrice", "type"
    )

    trace_names = {trace["name"] for trace in figure["data"]}
    assert trace_names == {"Conventional", "Organic"}


def test_update_charts_callback_handles_exception_without_crashing():
    with patch("app.create_price_chart", side_effect=RuntimeError("boom")):
        price_fig, volume_fig = update_charts(
            "Albany", "organic", "2015-01-01", "2015-12-31"
        )

    assert price_fig["data"] == []
    assert volume_fig["data"] == []
    assert "error" in price_fig["layout"]["title"].lower()
    assert "boom" in price_fig["layout"]["title"]


def test_create_box_plot_region_grouping_with_multiple_types_uses_one_trace_per_type():
    filtered = data.query("Date >= '2015-01-01' and Date <= '2015-01-31'")
    assert filtered["type"].nunique() == 2
    assert filtered["region"].nunique() > 1

    figure = create_box_plot(filtered, "AveragePrice", "region")

    assert len(figure["data"]) == 2
    assert {trace["name"] for trace in figure["data"]} == {
        "Conventional",
        "Organic",
    }
    assert figure["layout"]["xaxis"]["title"] == "Region"


def test_create_scatter_chart_returns_plotly_figure_dict():
    filtered = data.query("region == 'Albany'").head(50)

    figure = create_scatter_chart(filtered, "AveragePrice", "Total Volume")

    assert "data" in figure
    assert "layout" in figure
    trace_names = {trace["name"] for trace in figure["data"]}
    assert trace_names == {t.title() for t in filtered["type"].unique()}


def test_update_scatter_chart_returns_valid_figure_for_matching_data():
    figure = update_scatter_chart(
        "Albany",
        "organic",
        "2015-01-01",
        "2015-12-31",
        "AveragePrice",
        "Total Volume",
    )

    assert figure["data"]
    assert figure["layout"]["title"]["text"] == "Averageprice vs Total Volume"


def test_update_scatter_chart_returns_empty_state_for_no_matching_data():
    figure = update_scatter_chart(
        "Albany", "organic", "1999-01-01", "1999-12-31", "AveragePrice", "Total Volume"
    )

    assert figure["data"] == []
    assert "no data available" in figure["layout"]["title"].lower()


def test_update_scatter_chart_callback_handles_exception_without_crashing():
    with patch("app.create_scatter_chart", side_effect=RuntimeError("boom")):
        figure = update_scatter_chart(
            "Albany",
            "organic",
            "2015-01-01",
            "2015-12-31",
            "AveragePrice",
            "Total Volume",
        )

    assert figure["data"] == []
    assert "error" in figure["layout"]["title"].lower()


@pytest.mark.parametrize(
    "group_by,filter_region,filter_type",
    [
        ("region", "Boise", "organic"),
        ("year", "Albany", "organic"),
    ],
)
def test_update_box_plot_applies_query_for_each_group_by_mode(
    group_by, filter_region, filter_type
):
    figure = update_box_plot(
        filter_region,
        filter_type,
        "2015-01-01",
        "2018-12-31",
        "AveragePrice",
        group_by,
    )

    assert figure["data"]


def test_update_box_plot_returns_empty_state_for_no_matching_data():
    figure = update_box_plot(
        "Albany", "organic", "1999-01-01", "1999-12-31", "AveragePrice", "year"
    )

    assert figure["data"] == []
    assert "no data available" in figure["layout"]["title"].lower()


def test_update_box_plot_callback_handles_exception_without_crashing():
    with patch("app.create_box_plot", side_effect=RuntimeError("boom")):
        figure = update_box_plot(
            "Albany", "organic", "2015-01-01", "2015-12-31", "AveragePrice", "year"
        )

    assert figure["data"] == []
    assert "error" in figure["layout"]["title"].lower()

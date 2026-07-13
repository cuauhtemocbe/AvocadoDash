import io
import logging
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
from dash import dcc, no_update

from app import (
    EMPTY_REGION_MESSAGE,
    app,
    create_box_plot,
    create_price_chart,
    create_scatter_chart,
    create_summary_panel,
    create_volume_chart,
    data,
    download_filtered_csv,
    filter_data,
    update_box_plot,
    update_charts,
    update_download_controls,
    update_scatter_chart,
    update_summary_panel,
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


def test_region_filter_is_multi_select_with_single_region_default():
    dropdown = find_component_by_id(app.layout, "region-filter")

    assert dropdown is not None
    assert dropdown.multi is True
    assert dropdown.value == ["Albany"]


def test_filter_data_matches_today_s_single_region_query():
    regions, avocado_type = ["Albany"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"

    result = filter_data(regions, avocado_type, start_date, end_date)
    expected = data.query(
        "region == 'Albany' and type == @avocado_type"
        " and Date >= @start_date and Date <= @end_date"
    )

    assert list(result.index) == list(expected.index)


def test_filter_data_unions_multiple_regions():
    regions, avocado_type = ["Albany", "Chicago"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"

    result = filter_data(regions, avocado_type, start_date, end_date)

    assert set(result["region"].unique()) == {"Albany", "Chicago"}
    assert len(result) == sum(
        len(filter_data([region], avocado_type, start_date, end_date))
        for region in regions
    )


def test_filter_data_returns_empty_for_no_regions():
    result = filter_data([], "organic", "2015-01-01", "2015-12-31")

    assert result.empty


def test_create_price_chart_returns_plotly_figure_dict():
    figure = create_price_chart(data.head(50))

    assert "data" in figure
    assert "layout" in figure
    assert isinstance(figure["data"], list)


def test_create_price_chart_single_region_returns_one_named_trace():
    filtered = filter_data(["Albany"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered)

    assert len(figure["data"]) == 1
    assert figure["data"][0]["name"] == "Albany"
    assert list(figure["data"][0]["y"]) == list(filtered["AveragePrice"])
    assert figure["layout"]["showlegend"] is False


def test_create_price_chart_multiple_regions_returns_one_trace_per_region():
    filtered = filter_data(["Albany", "Chicago"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered)

    assert {trace["name"] for trace in figure["data"]} == {"Albany", "Chicago"}
    assert figure["layout"]["showlegend"] is True
    for trace in figure["data"]:
        region_rows = filtered[filtered["region"] == trace["name"]]
        assert list(trace["y"]) == list(region_rows["AveragePrice"])


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
    regions, avocado_type = ["Albany"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)
    assert not filtered.empty

    panel = create_summary_panel(filtered, regions, avocado_type, start_date, end_date)
    texts = collect_text(panel)

    expected_price = f"${filtered['AveragePrice'].mean():.2f}"
    expected_volume = format_number(filtered["Total Volume"].sum())
    assert any(expected_price in t for t in texts)
    assert any(expected_volume in t for t in texts)


def test_summary_panel_aggregates_avg_price_across_multiple_regions():
    regions, avocado_type = ["Albany", "Chicago"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)
    assert set(filtered["region"].unique()) == {"Albany", "Chicago"}

    panel = create_summary_panel(filtered, regions, avocado_type, start_date, end_date)
    texts = collect_text(panel)

    expected_price = f"${filtered['AveragePrice'].mean():.2f}"
    expected_volume = format_number(filtered["Total Volume"].sum())
    assert any(expected_price in t for t in texts)
    assert any(expected_volume in t for t in texts)


def test_summary_panel_shows_price_change_vs_previous_period():
    regions, avocado_type = ["Albany"], "organic"
    start_date, end_date = "2016-01-01", "2016-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)
    assert not filtered.empty

    expected_change = calculate_price_change(
        data, regions, avocado_type, start_date, end_date
    )
    assert expected_change is not None

    panel = create_summary_panel(filtered, regions, avocado_type, start_date, end_date)
    texts = collect_text(panel)
    sign = "+" if expected_change >= 0 else ""
    expected_text = f"{sign}{expected_change:.1f}%"
    assert any(expected_text in t for t in texts)


def test_summary_panel_highlights_best_worst_region():
    regions, avocado_type = ["Albany"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)
    assert not filtered.empty

    extremes = find_region_extremes(data, avocado_type, start_date, end_date)
    assert extremes is not None

    panel = create_summary_panel(filtered, regions, avocado_type, start_date, end_date)
    joined = " ".join(collect_text(panel))
    assert extremes["best_region"] in joined
    assert extremes["worst_region"] in joined


def test_summary_panel_handles_no_data():
    regions, avocado_type = ["Albany"], "organic"
    # A date range entirely outside the dataset yields zero rows.
    start_date, end_date = "1999-01-01", "1999-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)
    assert filtered.empty

    panel = create_summary_panel(filtered, regions, avocado_type, start_date, end_date)
    assert panel.className == "summary-empty"
    assert "no data" in panel.children.lower()


def test_update_summary_panel_shows_message_when_no_regions_selected():
    panel = update_summary_panel([], "organic", "2015-01-01", "2015-12-31")

    assert panel.className == "summary-empty"
    assert panel.children == EMPTY_REGION_MESSAGE


def test_update_summary_panel_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.filter_data", side_effect=RuntimeError("boom")):
            panel = update_summary_panel(
                ["Albany"], "organic", "2015-01-01", "2015-12-31"
            )

    assert panel.className == "summary-empty"
    assert "boom" in panel.children.lower()
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None


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


def test_calculate_price_change_multi_region_aggregates_combined_rows():
    regions, avocado_type = ["Albany", "Chicago"], "organic"
    start_date, end_date = "2016-01-01", "2016-12-31"

    result = calculate_price_change(data, regions, avocado_type, start_date, end_date)

    current = filter_data(regions, avocado_type, start_date, end_date)
    assert result is not None
    assert current["region"].nunique() == 2


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


def test_update_charts_shows_one_line_per_selected_region():
    price_fig, volume_fig = update_charts(
        ["Albany", "Chicago"], "organic", "2015-01-01", "2015-12-31"
    )

    assert {trace["name"] for trace in price_fig["data"]} == {"Albany", "Chicago"}
    assert {trace["name"] for trace in volume_fig["data"]} == {"Albany", "Chicago"}


def test_update_charts_single_region_behaves_like_before():
    price_fig, volume_fig = update_charts(
        ["Albany"], "organic", "2015-01-01", "2015-12-31"
    )

    assert len(price_fig["data"]) == 1
    assert len(volume_fig["data"]) == 1
    assert price_fig["data"][0]["name"] == "Albany"
    assert volume_fig["data"][0]["name"] == "Albany"


def test_update_charts_returns_empty_state_for_no_matching_data():
    price_fig, volume_fig = update_charts(
        ["Albany"], "organic", "1999-01-01", "1999-12-31"
    )

    assert price_fig["data"] == []
    assert volume_fig["data"] == []
    assert "no data available" in price_fig["layout"]["title"].lower()
    assert "no data available" in volume_fig["layout"]["title"].lower()


def test_update_charts_returns_region_specific_message_when_no_regions_selected():
    price_fig, volume_fig = update_charts([], "organic", "2015-01-01", "2015-12-31")

    assert price_fig["data"] == []
    assert volume_fig["data"] == []
    price_text = price_fig["layout"]["annotations"][0]["text"]
    volume_text = volume_fig["layout"]["annotations"][0]["text"]
    assert price_text == EMPTY_REGION_MESSAGE
    assert volume_text == EMPTY_REGION_MESSAGE


def test_update_box_plot_groups_by_type_regardless_of_type_filter():
    figure = update_box_plot(
        ["Albany"], "organic", "2015-01-01", "2015-12-31", "AveragePrice", "type"
    )

    trace_names = {trace["name"] for trace in figure["data"]}
    assert trace_names == {"Conventional", "Organic"}


def test_update_charts_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.create_price_chart", side_effect=RuntimeError("boom")):
            price_fig, volume_fig = update_charts(
                ["Albany"], "organic", "2015-01-01", "2015-12-31"
            )

    assert price_fig["data"] == []
    assert volume_fig["data"] == []
    assert "error" in price_fig["layout"]["title"].lower()
    assert "boom" in price_fig["layout"]["title"]
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None


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
        ["Albany"],
        "organic",
        "2015-01-01",
        "2015-12-31",
        "AveragePrice",
        "Total Volume",
    )

    assert figure["data"]
    assert figure["layout"]["title"]["text"] == "Averageprice vs Total Volume"


def test_update_scatter_chart_pools_data_from_multiple_regions():
    figure = update_scatter_chart(
        ["Albany", "Chicago"],
        "organic",
        "2015-01-01",
        "2015-12-31",
        "AveragePrice",
        "Total Volume",
    )
    total_points = sum(len(trace["x"]) for trace in figure["data"])

    filtered = filter_data(["Albany", "Chicago"], "organic", "2015-01-01", "2015-12-31")
    assert total_points == len(filtered)


def test_update_scatter_chart_returns_empty_state_for_no_matching_data():
    figure = update_scatter_chart(
        ["Albany"],
        "organic",
        "1999-01-01",
        "1999-12-31",
        "AveragePrice",
        "Total Volume",
    )

    assert figure["data"] == []
    assert "no data available" in figure["layout"]["title"].lower()


def test_update_scatter_chart_returns_region_specific_message_when_no_regions():
    figure = update_scatter_chart(
        [], "organic", "2015-01-01", "2015-12-31", "AveragePrice", "Total Volume"
    )

    assert figure["data"] == []
    assert figure["layout"]["annotations"][0]["text"] == EMPTY_REGION_MESSAGE


def test_update_scatter_chart_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.create_scatter_chart", side_effect=RuntimeError("boom")):
            figure = update_scatter_chart(
                ["Albany"],
                "organic",
                "2015-01-01",
                "2015-12-31",
                "AveragePrice",
                "Total Volume",
            )

    assert figure["data"] == []
    assert "error" in figure["layout"]["title"].lower()
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None


@pytest.mark.parametrize(
    "group_by,filter_regions,filter_type",
    [
        ("region", ["Boise"], "organic"),
        ("year", ["Albany"], "organic"),
    ],
)
def test_update_box_plot_applies_query_for_each_group_by_mode(
    group_by, filter_regions, filter_type
):
    figure = update_box_plot(
        filter_regions,
        filter_type,
        "2015-01-01",
        "2018-12-31",
        "AveragePrice",
        group_by,
    )

    assert figure["data"]


def test_update_box_plot_pools_data_from_multiple_regions_when_grouped_by_type():
    figure = update_box_plot(
        ["Albany", "Chicago"],
        "organic",
        "2015-01-01",
        "2015-12-31",
        "AveragePrice",
        "type",
    )

    trace_names = {trace["name"] for trace in figure["data"]}
    assert trace_names == {"Conventional", "Organic"}


def test_update_box_plot_region_grouping_ignores_empty_region_selection():
    figure = update_box_plot(
        [], "organic", "2015-01-01", "2015-01-31", "AveragePrice", "region"
    )

    assert figure["data"]


def test_update_box_plot_returns_region_specific_message_when_no_regions():
    for group_by in ("type", "year"):
        figure = update_box_plot(
            [], "organic", "2015-01-01", "2015-12-31", "AveragePrice", group_by
        )

        assert figure["data"] == []
        assert figure["layout"]["annotations"][0]["text"] == EMPTY_REGION_MESSAGE


def test_update_box_plot_returns_empty_state_for_no_matching_data():
    figure = update_box_plot(
        ["Albany"], "organic", "1999-01-01", "1999-12-31", "AveragePrice", "year"
    )

    assert figure["data"] == []
    assert "no data available" in figure["layout"]["title"].lower()


def test_update_box_plot_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.create_box_plot", side_effect=RuntimeError("boom")):
            figure = update_box_plot(
                ["Albany"],
                "organic",
                "2015-01-01",
                "2015-12-31",
                "AveragePrice",
                "year",
            )

    assert figure["data"] == []
    assert "error" in figure["layout"]["title"].lower()
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None


def test_download_button_and_dcc_download_exist_in_layout():
    button = find_component_by_id(app.layout, "download-csv-button")
    download = find_component_by_id(app.layout, "download-dataframe-csv")

    assert button is not None
    assert isinstance(download, dcc.Download)


def test_download_filtered_csv_exports_exactly_the_filtered_rows():
    regions, avocado_type = ["Albany"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)
    assert not filtered.empty

    result = download_filtered_csv(1, regions, avocado_type, start_date, end_date)

    assert result["filename"] == "avocado_filtered.csv"
    downloaded = pd.read_csv(io.StringIO(result["content"]))
    assert len(downloaded) == len(filtered)
    assert list(downloaded.columns) == list(filtered.columns)


def test_download_filtered_csv_includes_every_selected_region():
    regions = ["Albany", "Chicago"]
    result = download_filtered_csv(1, regions, "organic", "2015-01-01", "2015-12-31")

    downloaded = pd.read_csv(io.StringIO(result["content"]))
    assert set(downloaded["region"].unique()) == set(regions)


def test_download_filtered_csv_header_matches_dataset_columns():
    result = download_filtered_csv(1, ["Albany"], "organic", "2015-01-01", "2015-12-31")

    header_row = result["content"].splitlines()[0]
    assert header_row.split(",") == list(data.columns)


def test_download_filtered_csv_returns_no_update_for_no_matching_data():
    result = download_filtered_csv(1, ["Albany"], "organic", "1999-01-01", "1999-12-31")

    assert result is no_update


def test_download_filtered_csv_returns_no_update_when_no_regions_selected():
    result = download_filtered_csv(1, [], "organic", "2015-01-01", "2015-12-31")

    assert result is no_update


def test_download_filtered_csv_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.dcc.send_data_frame", side_effect=RuntimeError("boom")):
            result = download_filtered_csv(
                1, ["Albany"], "organic", "2015-01-01", "2015-12-31"
            )

    assert result is no_update
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None


def test_update_download_controls_disables_button_when_no_data():
    disabled, status = update_download_controls(
        ["Albany"], "organic", "1999-01-01", "1999-12-31"
    )

    assert disabled is True
    assert "no data" in status.lower()


def test_update_download_controls_enables_button_when_data_available():
    disabled, status = update_download_controls(
        ["Albany"], "organic", "2015-01-01", "2015-12-31"
    )

    assert disabled is False
    assert status == ""


def test_update_download_controls_disables_button_when_no_regions_selected():
    disabled, status = update_download_controls(
        [], "organic", "2015-01-01", "2015-12-31"
    )

    assert disabled is True
    assert status == EMPTY_REGION_MESSAGE


def test_update_download_controls_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.filter_data", side_effect=RuntimeError("boom")):
            disabled, status = update_download_controls(
                ["Albany"], "organic", "2015-01-01", "2015-12-31"
            )

    assert disabled is True
    assert status != ""
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None


def test_no_print_statements_remain_in_app_source():
    app_source = Path(__file__).parent.parent.joinpath("src", "app.py").read_text()

    assert "print(" not in app_source

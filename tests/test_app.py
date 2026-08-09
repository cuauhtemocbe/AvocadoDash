import io
import logging
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import sentry_sdk
from dash import dcc, no_update
from dash._callback_context import context_value
from dash._utils import AttributeDict

from app import (
    DATA_MAX_DATE,
    DATA_MIN_DATE,
    DEFAULT_URL_BOX_PLOT_COLUMN,
    DEFAULT_URL_BOX_PLOT_GROUPBY,
    DEFAULT_URL_REGIONS,
    DEFAULT_URL_TYPE,
    DEFAULT_URL_X_AXIS,
    DEFAULT_URL_Y_AXIS,
    EMPTY_REGION_MESSAGE,
    REGION_COLOR_PALETTE,
    app,
    avocado_types,
    create_box_plot,
    create_price_chart,
    create_scatter_chart,
    create_summary_panel,
    create_volume_chart,
    data,
    decode_query_to_filters,
    download_filtered_csv,
    encode_filters_to_query,
    external_stylesheets,
    filter_data,
    init_sentry,
    load_data,
    summary_stat_card,
    sync_url_and_filters,
    update_box_plot,
    update_charts,
    update_download_controls,
    update_scatter_chart,
    update_summary_panel,
    update_ui_language,
)
from translations import column_label, t
from utils import (
    calculate_price_change,
    detect_price_anomalies,
    find_region_extremes,
    format_number,
)

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


def test_load_data_uses_default_path_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("AVOCADO_DATA_PATH", raising=False)

    result = load_data()

    assert not result.empty
    assert set(result.columns) == set(data.columns)


def test_load_data_uses_env_var_path_when_set(monkeypatch, tmp_path):
    csv_path = tmp_path / "custom.csv"
    csv_path.write_text(
        "Date,AveragePrice,Total Volume,type,region\n"
        "2020-01-01,1.50,1000,organic,Testville\n"
    )
    monkeypatch.setenv("AVOCADO_DATA_PATH", str(csv_path))

    result = load_data()

    assert len(result) == 1
    assert result.iloc[0]["region"] == "Testville"


def test_load_data_raises_file_not_found_for_missing_env_path(monkeypatch):
    monkeypatch.setenv("AVOCADO_DATA_PATH", "/nonexistent/path/data.csv")

    with pytest.raises(FileNotFoundError, match="/nonexistent/path/data.csv"):
        load_data()


def test_load_data_raises_clear_error_for_missing_required_column(
    monkeypatch, tmp_path
):
    csv_path = tmp_path / "missing_region.csv"
    csv_path.write_text(
        "Date,AveragePrice,Total Volume,type\n2020-01-01,1.50,1000,organic\n"
    )
    monkeypatch.setenv("AVOCADO_DATA_PATH", str(csv_path))

    with pytest.raises(ValueError, match="region"):
        load_data()


def test_region_filter_is_multi_select_with_single_region_default():
    dropdown = find_component_by_id(app.layout, "region-filter")

    assert dropdown is not None
    assert dropdown.multi is True
    assert dropdown.value == ["Albany"]


def test_theme_store_persists_to_local_storage():
    """Issue #45: the explicit theme choice must survive a page reload."""
    store = find_component_by_id(app.layout, "theme-store")
    assert store is not None
    assert store.storage_type == "local"


def test_theme_toggle_offers_light_and_dark_with_no_initial_value():
    """The toggle starts unset (None) — its displayed value is resolved
    client-side (explicit store choice, else OS preference) rather than
    hardcoded to light or dark at layout-build time."""
    toggle = find_component_by_id(app.layout, "theme-toggle")
    assert toggle is not None
    assert {opt["value"] for opt in toggle.options} == {"light", "dark"}
    assert toggle.value is None


def test_theme_sync_clientside_callback_is_registered_both_directions():
    """theme-toggle.value and theme-store.data are each registered as
    both an Output and an Input of the same clientside callback — the
    self-referencing shape already validated for sync_url_and_filters
    (specs/shareable-url-state-plan.md), needed here because OS-preference
    detection and the data-theme DOM attribute are only reachable
    client-side. theme-resolved.data is an Output-only third leg: the
    resolved value server-side chart callbacks key off of, since
    theme-store deliberately stays empty until an explicit choice."""
    matches = [
        entry
        for entry in app.callback_map.values()
        if {inp["id"] for inp in entry["inputs"]} == {"theme-toggle", "theme-store"}
    ]
    assert len(matches) == 1
    callback = matches[0]
    output_targets = {
        (output.component_id, output.component_property)
        for output in callback["output"]
    }
    assert output_targets == {
        ("theme-toggle", "value"),
        ("theme-store", "data"),
        ("theme-resolved", "data"),
    }


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


def region_traces_only(figure):
    """A price chart's `data` can include anomaly-marker traces (issue
    #39) alongside the per-region lines — filter those out for
    assertions that are specifically about the region lines."""
    return [trace for trace in figure["data"] if trace.get("legendgroup") != "anomaly"]


def test_create_price_chart_returns_plotly_figure_dict():
    figure = create_price_chart(data.head(50))

    assert "data" in figure
    assert "layout" in figure
    assert isinstance(figure["data"], list)


def test_create_price_chart_single_region_returns_one_named_trace():
    filtered = filter_data(["Albany"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered)
    region_traces = region_traces_only(figure)

    assert len(region_traces) == 1
    assert region_traces[0]["name"] == "Albany"
    assert list(region_traces[0]["y"]) == list(filtered["AveragePrice"])


def test_create_price_chart_multiple_regions_returns_one_trace_per_region():
    filtered = filter_data(["Albany", "Chicago"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered)
    region_traces = region_traces_only(figure)

    assert {trace["name"] for trace in region_traces} == {"Albany", "Chicago"}
    assert figure["layout"]["showlegend"] is True
    for trace in region_traces:
        region_rows = filtered[filtered["region"] == trace["name"]]
        assert list(trace["y"]) == list(region_rows["AveragePrice"])


# --- Price anomaly detection (issue #39) --------------------------------


@pytest.mark.parametrize(
    "prices,expected",
    [
        # mean=1.0, std=0.1 (population). Only the 1.5 point (5 std away)
        # is beyond the 2.0 threshold.
        (
            pd.Series([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.5]),
            [False] * 9 + [True],
        ),
        # No point beyond 2 std: near-uniform noise around 1.0.
        (pd.Series([0.95, 1.0, 1.05, 0.98, 1.02, 1.0, 0.97, 1.03]), [False] * 8),
    ],
)
def test_detect_price_anomalies_flags_points_beyond_threshold(prices, expected):
    result = detect_price_anomalies(prices)
    assert list(result) == expected


def test_detect_price_anomalies_boundary_exactly_at_threshold_is_not_flagged():
    """9 copies of `a` + 1 copy of `b` always puts the odd point at
    exactly (n-1)/sqrt(n) standard deviations from the series' own
    mean, regardless of the gap between `a` and `b` (scale-invariant).
    Using that exact ratio as the threshold directly exercises the
    strict `>` (not `>=`) boundary rule."""
    prices = pd.Series([1.0] * 9 + [1.2])
    exact_ratio = (prices - prices.mean()).abs().iloc[-1] / prices.std()

    result = detect_price_anomalies(prices, std_threshold=exact_ratio)

    assert result.iloc[-1] == False  # noqa: E712 — pandas bool, not Python bool


def test_detect_price_anomalies_just_beyond_threshold_is_flagged():
    prices = pd.Series([1.0] * 9 + [1.2])
    exact_ratio = (prices - prices.mean()).abs().iloc[-1] / prices.std()

    result = detect_price_anomalies(prices, std_threshold=exact_ratio - 1e-9)

    assert result.iloc[-1] == True  # noqa: E712 — pandas bool, not Python bool


def test_detect_price_anomalies_single_point_does_not_crash():
    result = detect_price_anomalies(pd.Series([1.5]))
    assert list(result) == [False]


def test_detect_price_anomalies_flat_series_has_no_anomalies():
    """std == 0 (every value identical) must not divide by zero."""
    result = detect_price_anomalies(pd.Series([1.0, 1.0, 1.0, 1.0]))
    assert list(result) == [False] * 4


def test_create_price_chart_flags_an_anomalous_point_with_a_distinct_marker():
    filtered = filter_data(["Albany"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered)
    anomaly_traces = [
        trace for trace in figure["data"] if trace.get("legendgroup") == "anomaly"
    ]

    assert len(anomaly_traces) == 1
    assert anomaly_traces[0]["marker"]["symbol"] == "x"
    assert anomaly_traces[0]["mode"] == "markers"
    assert anomaly_traces[0]["showlegend"] is True
    assert figure["layout"]["showlegend"] is True


def test_create_price_chart_renders_without_markers_when_no_anomalies():
    # Two points can never be > 2 std from their own mean (equidistant).
    filtered = filter_data(["Albany"], "organic", "2015-01-04", "2015-01-11")

    figure = create_price_chart(filtered)
    anomaly_traces = [
        trace for trace in figure["data"] if trace.get("legendgroup") == "anomaly"
    ]

    assert anomaly_traces == []


def test_create_price_chart_multiple_regions_share_one_anomaly_legend_entry():
    filtered = filter_data(["Albany", "Chicago"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered)
    anomaly_traces = [
        trace for trace in figure["data"] if trace.get("legendgroup") == "anomaly"
    ]

    assert len(anomaly_traces) == 2
    assert [trace["showlegend"] for trace in anomaly_traces] == [True, False]


def test_create_price_chart_single_data_point_does_not_crash():
    filtered = filter_data(["Albany"], "organic", "2015-01-04", "2015-01-04")

    figure = create_price_chart(filtered)
    anomaly_traces = [
        trace for trace in figure["data"] if trace.get("legendgroup") == "anomaly"
    ]

    assert anomaly_traces == []


def test_update_charts_empty_filtered_data_skips_anomaly_logic():
    """Issue #39's empty-dataset scenario: the existing empty-state
    figure is returned and anomaly logic is never invoked (already true
    since update_charts short-circuits before calling create_price_chart
    at all — this just locks that path in for the anomaly feature)."""
    price_fig, _ = update_charts(["Albany"], "organic", "1999-01-01", "1999-12-31")

    assert price_fig["data"] == []
    assert "no data available" in price_fig["layout"]["title"].lower()


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


def test_google_fonts_link_loads_brand_fonts_and_drops_lato():
    hrefs = " ".join(sheet["href"] for sheet in external_stylesheets)
    assert "Fraunces" in hrefs
    assert "Inter" in hrefs
    assert "IBM+Plex+Mono" in hrefs
    assert "Lato" not in hrefs


def test_section_titles_use_the_display_typeface():
    for title_id in ("scatter-section-title", "box-plot-section-title"):
        title = find_component_by_id(app.layout, title_id)
        assert title is not None, f"{title_id} not found in layout"
        assert "Fraunces" in title.style["font-family"]


def test_header_contains_the_cross_section_mark():
    mark = find_component_by_id(app.layout, "header-mark")
    assert mark is not None


def test_header_no_longer_renders_the_emoji():
    assert "🥑" not in collect_text(app.layout)


def test_header_mark_image_is_hidden_from_assistive_technology():
    """Issue #44: the decorative Cross-Section Mark must not be announced
    by screen readers — empty alt text is the standard way to hide a
    purely decorative <img> from assistive technology."""
    mark = find_component_by_id(app.layout, "header-mark")
    assert mark is not None
    image = mark.children
    assert image.alt == ""


def iter_all_components(component):
    """Recursively yield every Dash component in the layout tree."""
    yield component
    children = getattr(component, "children", None)
    if children is None:
        return
    if not isinstance(children, list):
        children = [children]
    for child in children:
        if hasattr(child, "to_plotly_json"):
            yield from iter_all_components(child)


def test_no_component_overrides_natural_keyboard_tab_order():
    """Issue #44: filter controls must be reachable via keyboard in
    logical order. Dash's default DOM order already matches the visual
    order the controls are declared in; the risk is a future explicit
    tabIndex silently breaking that — so this guards against any
    component setting tabIndex at all."""
    offending = [
        component
        for component in iter_all_components(app.layout)
        if "tabIndex" in component.to_plotly_json().get("props", {})
    ]
    assert offending == []


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


def test_summary_stat_card_positive_trend_shows_up_glyph():
    card = summary_stat_card("Price change", "+3.2%", "summary-stat-up")

    value_div = card.children[1]
    assert value_div.children.startswith("▲")


def test_summary_stat_card_negative_trend_shows_down_glyph():
    card = summary_stat_card("Price change", "-1.5%", "summary-stat-down")

    value_div = card.children[1]
    assert value_div.children.startswith("▼")


def test_summary_stat_card_without_trend_class_has_no_glyph_prefix():
    card = summary_stat_card("Avg. Price", "$1.23")

    value_div = card.children[1]
    assert value_div.children == "$1.23"


def test_update_summary_panel_shows_message_when_no_regions_selected():
    panel = update_summary_panel([], "organic", "2015-01-01", "2015-12-31")

    assert panel.className == "summary-empty"
    assert panel.children == EMPTY_REGION_MESSAGE


def test_update_summary_panel_callback_handles_exception_without_crashing(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.filter_data", side_effect=RuntimeError("boom")):
            with patch("app.sentry_sdk.capture_exception") as mock_capture:
                panel = update_summary_panel(
                    ["Albany"], "organic", "2015-01-01", "2015-12-31"
                )

    assert panel.className == "summary-empty"
    assert "boom" in panel.children.lower()
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None
    mock_capture.assert_called_once()
    error_arg, kwargs = mock_capture.call_args.args[0], mock_capture.call_args.kwargs
    assert str(error_arg) == "boom"
    assert kwargs["extras"] == {
        "regions": ["Albany"],
        "type": "organic",
        "start_date": "2015-01-01",
        "end_date": "2015-12-31",
    }


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


CHART_BUILDERS_WITH_FILTERED_DATA = [
    lambda filtered: create_price_chart(filtered),
    lambda filtered: create_volume_chart(filtered),
    lambda filtered: create_box_plot(filtered, "AveragePrice", "type"),
    lambda filtered: create_scatter_chart(filtered, "AveragePrice", "Total Volume"),
]

CHART_BUILDERS_WITH_FILTERED_DATA_AND_THEME = [
    lambda filtered, theme: create_price_chart(filtered, theme=theme),
    lambda filtered, theme: create_volume_chart(filtered, theme=theme),
    lambda filtered, theme: create_box_plot(
        filtered, "AveragePrice", "type", theme=theme
    ),
    lambda filtered, theme: create_scatter_chart(
        filtered, "AveragePrice", "Total Volume", theme=theme
    ),
]


@pytest.mark.parametrize("build_chart", CHART_BUILDERS_WITH_FILTERED_DATA)
def test_chart_backgrounds_use_the_parchment_token(build_chart):
    filtered = data.query("region == 'Albany'").head(50)

    figure = build_chart(filtered)

    assert figure["layout"]["plot_bgcolor"] == "#F6F1E4"
    assert figure["layout"]["paper_bgcolor"] == "#F6F1E4"


@pytest.mark.parametrize("build_chart", CHART_BUILDERS_WITH_FILTERED_DATA_AND_THEME)
def test_chart_backgrounds_and_text_switch_to_dark_theme(build_chart):
    """Issue #45: theme="dark" re-renders chart chrome (background, grid,
    legend, and — critically — text color, or titles/axes would be
    unreadable dark-on-dark) with the dark-mode tokens, mirroring
    style.css's --parchment dark-mode value."""
    filtered = data.query("region == 'Albany'").head(50)

    figure = build_chart(filtered, "dark")

    assert figure["layout"]["plot_bgcolor"] == "#241C13"
    assert figure["layout"]["paper_bgcolor"] == "#241C13"
    assert figure["layout"]["font"]["color"] == "#EDE6D6"


@pytest.mark.parametrize("build_chart", CHART_BUILDERS_WITH_FILTERED_DATA_AND_THEME)
def test_chart_backgrounds_default_to_light_theme(build_chart):
    filtered = data.query("region == 'Albany'").head(50)

    figure = build_chart(filtered, "light")

    assert figure["layout"]["plot_bgcolor"] == "#F6F1E4"
    assert figure["layout"]["font"]["color"] == "#1F1710"


def test_create_box_plot_uses_the_new_type_color_map():
    filtered = data.query(
        "region == 'Albany' and Date >= '2015-01-01' and Date <= '2015-12-31'"
    )
    assert set(filtered["type"].unique()) == {"conventional", "organic"}

    figure = create_box_plot(filtered, "AveragePrice", "type")

    colors_by_name = {
        trace["name"]: trace["marker"]["color"] for trace in figure["data"]
    }
    assert colors_by_name["Conventional"] == "#7C8F3E"
    assert colors_by_name["Organic"] == "#B4432E"


def test_create_scatter_chart_uses_the_new_type_color_map():
    filtered = data.query(
        "region == 'Albany' and Date >= '2015-01-01' and Date <= '2015-12-31'"
    )
    assert set(filtered["type"].unique()) == {"conventional", "organic"}

    figure = create_scatter_chart(filtered, "AveragePrice", "Total Volume")

    colors_by_name = {
        trace["name"]: trace["marker"]["color"] for trace in figure["data"]
    }
    assert colors_by_name["Conventional"] == "#7C8F3E"
    assert colors_by_name["Organic"] == "#B4432E"


def test_region_line_palette_is_unchanged_by_the_chart_chrome_recolor():
    filtered = data.query(
        "region in ['Albany', 'Chicago', 'Houston'] and type == 'organic'"
    )

    figure = create_price_chart(filtered)

    trace_colors = {trace["line"]["color"] for trace in region_traces_only(figure)}
    assert trace_colors <= set(REGION_COLOR_PALETTE)


def test_region_line_palette_is_reused_unchanged_in_dark_mode():
    """Issue #51: re-validated against the dark chart surface with
    /dataviz's validate_palette.js (see the comment above
    REGION_COLOR_PALETTE) — same 8 hues clear the same CVD/contrast bar
    in both themes, so dark mode draws from the identical palette rather
    than a separate dark-specific one. This regression test is the
    trip-wire: if REGION_COLOR_PALETTE ever changes, dark-mode charts
    must keep drawing from it (not a stale copy) — otherwise this fails
    and the palette needs re-running through the validator for both
    surfaces before the change ships."""
    filtered = data.query(
        "region in ['Albany', 'Chicago', 'Houston'] and type == 'organic'"
    )

    figure = create_price_chart(filtered, theme="dark")

    trace_colors = {trace["line"]["color"] for trace in region_traces_only(figure)}
    assert trace_colors <= set(REGION_COLOR_PALETTE)


def test_type_color_map_is_reused_unchanged_in_dark_mode():
    """Issue #51: TYPE_COLOR_MAP's two hues also passed validate_palette.js
    unchanged against the dark surface (see the comment above CHART_BG)."""
    filtered = data.query(
        "region == 'Albany' and Date >= '2015-01-01' and Date <= '2015-12-31'"
    )

    figure = create_box_plot(filtered, "AveragePrice", "type", theme="dark")

    colors_by_name = {
        trace["name"]: trace["marker"]["color"] for trace in figure["data"]
    }
    assert colors_by_name["Conventional"] == "#7C8F3E"
    assert colors_by_name["Organic"] == "#B4432E"


def test_update_charts_shows_one_line_per_selected_region():
    price_fig, volume_fig = update_charts(
        ["Albany", "Chicago"], "organic", "2015-01-01", "2015-12-31"
    )

    price_region_names = {trace["name"] for trace in region_traces_only(price_fig)}
    assert price_region_names == {"Albany", "Chicago"}
    assert {trace["name"] for trace in volume_fig["data"]} == {"Albany", "Chicago"}


def test_update_charts_single_region_behaves_like_before():
    price_fig, volume_fig = update_charts(
        ["Albany"], "organic", "2015-01-01", "2015-12-31"
    )

    price_region_traces = region_traces_only(price_fig)
    assert len(price_region_traces) == 1
    assert len(volume_fig["data"]) == 1
    assert price_region_traces[0]["name"] == "Albany"
    assert volume_fig["data"][0]["name"] == "Albany"


def test_update_charts_honors_the_resolved_theme_input():
    price_fig, volume_fig = update_charts(
        ["Albany"], "organic", "2015-01-01", "2015-12-31", "en", "dark"
    )

    assert price_fig["layout"]["plot_bgcolor"] == "#241C13"
    assert volume_fig["layout"]["plot_bgcolor"] == "#241C13"


def test_update_charts_defaults_to_light_theme_when_resolved_theme_is_none():
    price_fig, volume_fig = update_charts(
        ["Albany"], "organic", "2015-01-01", "2015-12-31"
    )

    assert price_fig["layout"]["plot_bgcolor"] == "#F6F1E4"
    assert volume_fig["layout"]["plot_bgcolor"] == "#F6F1E4"


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
            with patch("app.sentry_sdk.capture_exception") as mock_capture:
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
    mock_capture.assert_called_once()
    assert mock_capture.call_args.kwargs["extras"] == {
        "regions": ["Albany"],
        "type": "organic",
        "start_date": "2015-01-01",
        "end_date": "2015-12-31",
    }


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
    assert figure["layout"]["title"]["text"] == "Average Price vs Total Volume"


def test_update_scatter_chart_honors_the_resolved_theme_input():
    figure = update_scatter_chart(
        ["Albany"],
        "organic",
        "2015-01-01",
        "2015-12-31",
        "AveragePrice",
        "Total Volume",
        "en",
        "dark",
    )

    assert figure["layout"]["plot_bgcolor"] == "#241C13"


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
            with patch("app.sentry_sdk.capture_exception") as mock_capture:
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
    mock_capture.assert_called_once()
    assert mock_capture.call_args.kwargs["extras"] == {
        "regions": ["Albany"],
        "type": "organic",
        "start_date": "2015-01-01",
        "end_date": "2015-12-31",
        "x_col": "AveragePrice",
        "y_col": "Total Volume",
    }


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


def test_update_box_plot_honors_the_resolved_theme_input():
    figure = update_box_plot(
        ["Albany"],
        "organic",
        "2015-01-01",
        "2015-12-31",
        "AveragePrice",
        "type",
        "en",
        "dark",
    )

    assert figure["layout"]["plot_bgcolor"] == "#241C13"


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
            with patch("app.sentry_sdk.capture_exception") as mock_capture:
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
    mock_capture.assert_called_once()
    assert mock_capture.call_args.kwargs["extras"] == {
        "regions": ["Albany"],
        "type": "organic",
        "start_date": "2015-01-01",
        "end_date": "2015-12-31",
        "column": "AveragePrice",
        "group_by": "year",
    }


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
            with patch("app.sentry_sdk.capture_exception") as mock_capture:
                result = download_filtered_csv(
                    1, ["Albany"], "organic", "2015-01-01", "2015-12-31"
                )

    assert result is no_update
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None
    mock_capture.assert_called_once()
    assert mock_capture.call_args.kwargs["extras"] == {
        "regions": ["Albany"],
        "type": "organic",
        "start_date": "2015-01-01",
        "end_date": "2015-12-31",
    }


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
            with patch("app.sentry_sdk.capture_exception") as mock_capture:
                disabled, status = update_download_controls(
                    ["Albany"], "organic", "2015-01-01", "2015-12-31"
                )

    assert disabled is True
    assert status != ""
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].exc_info is not None
    mock_capture.assert_called_once()
    assert mock_capture.call_args.kwargs["extras"] == {
        "regions": ["Albany"],
        "type": "organic",
        "start_date": "2015-01-01",
        "end_date": "2015-12-31",
    }


def test_price_chart_exposes_a_download_as_image_control():
    graph = find_component_by_id(app.layout, "price-chart")

    assert graph is not None
    assert graph.config["displayModeBar"] is True
    assert "toImage" not in graph.config.get("modeBarButtonsToRemove", [])


def test_volume_chart_exposes_a_download_as_image_control():
    graph = find_component_by_id(app.layout, "volume-chart")

    assert graph is not None
    assert graph.config["displayModeBar"] is True
    assert "toImage" not in graph.config.get("modeBarButtonsToRemove", [])


def test_scatter_chart_still_exposes_its_download_control():
    graph = find_component_by_id(app.layout, "scatter-chart")

    assert graph is not None
    assert graph.config["displayModeBar"] is True


def test_box_plot_chart_still_exposes_its_download_control():
    graph = find_component_by_id(app.layout, "box-plot-chart")

    assert graph is not None
    assert graph.config["displayModeBar"] is True


NON_DOWNLOAD_MODEBAR_BUTTONS = {
    "zoom2d",
    "pan2d",
    "select2d",
    "lasso2d",
    "zoomIn2d",
    "zoomOut2d",
    "autoScale2d",
    "resetScale2d",
    "hoverClosestCartesian",
    "hoverCompareCartesian",
    "toggleSpikelines",
}


@pytest.mark.parametrize(
    "chart_id",
    ["price-chart", "volume-chart", "scatter-chart", "box-plot-chart"],
)
def test_chart_modebar_shows_only_the_download_button(chart_id):
    graph = find_component_by_id(app.layout, chart_id)

    assert graph is not None
    assert graph.config["displayModeBar"] is True
    assert graph.config["displaylogo"] is False
    removed = set(graph.config.get("modeBarButtonsToRemove", []))
    assert NON_DOWNLOAD_MODEBAR_BUTTONS <= removed


def test_sentry_capture_is_a_no_op_without_a_dsn():
    sentry_sdk.init(dsn=None)

    assert sentry_sdk.capture_exception(RuntimeError("boom")) is None


def test_init_sentry_with_an_invalid_dsn_does_not_raise(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "not-a-valid-dsn")
    try:
        init_sentry()
    except Exception as e:
        pytest.fail(f"init_sentry() raised with an invalid DSN: {e}")
    finally:
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        sentry_sdk.init(dsn=None)


def test_no_print_statements_remain_in_app_source():
    app_source = Path(__file__).parent.parent.joinpath("src", "app.py").read_text()

    assert "print(" not in app_source


def test_update_ui_language_translates_static_text_to_spanish():
    (
        header_subtitle,
        header_description,
        footer_text,
        scatter_title,
        box_plot_title,
        region_label,
        region_placeholder,
        type_label_children,
        type_options,
        date_range_label,
        download_button,
        x_axis_label,
        x_axis_options,
        y_axis_label,
        y_axis_options,
        box_plot_column_label,
        box_plot_column_options,
        box_plot_groupby_label,
        box_plot_groupby_options,
    ) = update_ui_language("es")

    assert header_subtitle[0] == t("header.subtitle_by", "es")
    assert header_description == t("header.description", "es")
    assert footer_text[0] == t("footer.created_by", "es")
    assert scatter_title == t("sections.scatter_title", "es")
    assert box_plot_title == t("sections.box_plot_title", "es")
    assert region_label[0] == t("filters.region.label", "es")
    assert region_placeholder == t("filters.region.placeholder", "es")
    assert type_label_children[0] == t("filters.type.label", "es")
    assert date_range_label[0] == t("filters.date_range.label", "es")
    assert download_button == t("download.button", "es")
    assert x_axis_label[0] == t("filters.x_axis.label", "es")
    assert y_axis_label[0] == t("filters.y_axis.label", "es")
    assert box_plot_column_label[0] == t("filters.box_plot_column.label", "es")
    assert box_plot_groupby_label[0] == t("filters.box_plot_groupby.label", "es")

    assert {opt["value"] for opt in type_options} == {"conventional", "organic"}
    assert {opt["label"] for opt in type_options} == {"Convencional", "Orgánico"}
    assert {opt["value"] for opt in box_plot_groupby_options} == {
        "type",
        "region",
        "year",
    }
    assert [opt["value"] for opt in x_axis_options] == [
        opt["value"] for opt in y_axis_options
    ]
    assert [opt["value"] for opt in x_axis_options] == [
        opt["value"] for opt in box_plot_column_options
    ]


def test_update_ui_language_dropdown_values_unchanged_between_languages():
    es_result = update_ui_language("es")
    en_result = update_ui_language("en")

    es_type_options, en_type_options = es_result[8], en_result[8]
    assert [opt["value"] for opt in es_type_options] == [
        opt["value"] for opt in en_type_options
    ]

    es_numeric_options, en_numeric_options = es_result[12], en_result[12]
    assert [opt["value"] for opt in es_numeric_options] == [
        opt["value"] for opt in en_numeric_options
    ]

    es_groupby_options, en_groupby_options = es_result[18], en_result[18]
    assert [opt["value"] for opt in es_groupby_options] == [
        opt["value"] for opt in en_groupby_options
    ]


def test_create_price_chart_spanish_translates_titles_and_axis_labels():
    filtered = filter_data(["Albany"], "organic", "2015-01-01", "2015-12-31")

    figure = create_price_chart(filtered, lang="es")

    assert figure["layout"]["title"]["text"] == t("charts.price.title", "es")
    assert figure["layout"]["xaxis"]["title"] == t("common.date", "es")
    assert figure["layout"]["yaxis"]["title"] == t("charts.price.yaxis", "es")


def test_create_volume_chart_spanish_translates_titles_and_axis_labels():
    filtered = data.query("region == 'Albany' and type == 'organic'").head(50)

    figure = create_volume_chart(filtered, lang="es")

    assert figure["layout"]["title"]["text"] == t("charts.volume.title", "es")
    assert figure["layout"]["yaxis"]["title"] == t("common.volume", "es")


def test_create_scatter_chart_spanish_translates_titles_and_axis_labels():
    filtered = data.query("region == 'Albany'").head(50)

    figure = create_scatter_chart(filtered, "AveragePrice", "Total Volume", lang="es")

    x_label = column_label("AveragePrice", "es")
    y_label = column_label("Total Volume", "es")
    assert figure["layout"]["title"]["text"] == f"{x_label} vs {y_label}"
    assert figure["layout"]["xaxis"]["title"] == x_label
    assert figure["layout"]["yaxis"]["title"] == y_label


def test_create_box_plot_region_grouping_spanish_xaxis_title():
    filtered = data.query("Date >= '2015-01-01' and Date <= '2015-01-31'")
    assert filtered["type"].nunique() == 2

    figure = create_box_plot(filtered, "AveragePrice", "region", lang="es")

    assert figure["layout"]["xaxis"]["title"] == t("common.region", "es")
    assert {trace["name"] for trace in figure["data"]} == {"Convencional", "Orgánico"}


def test_create_summary_panel_spanish_translates_card_labels():
    regions, avocado_type = ["Albany"], "organic"
    start_date, end_date = "2015-01-01", "2015-12-31"
    filtered = filter_data(regions, avocado_type, start_date, end_date)

    panel = create_summary_panel(
        filtered, regions, avocado_type, start_date, end_date, lang="es"
    )
    texts = collect_text(panel)

    assert any(column_label("AveragePrice", "es") in text for text in texts)
    assert any(column_label("Total Volume", "es") in text for text in texts)


def test_update_charts_returns_spanish_empty_state_message():
    price_fig, volume_fig = update_charts(
        [], "organic", "2015-01-01", "2015-12-31", lang="es"
    )

    price_text = price_fig["layout"]["annotations"][0]["text"]
    assert price_text == t("empty.select_region", "es")


def test_update_summary_panel_callback_handles_exception_in_spanish(caplog):
    with caplog.at_level(logging.ERROR):
        with patch("app.filter_data", side_effect=RuntimeError("boom")):
            panel = update_summary_panel(
                ["Albany"], "organic", "2015-01-01", "2015-12-31", lang="es"
            )

    assert panel.children.startswith(t("common.error_prefix", "es"))
    assert "boom" in panel.children.lower()


def test_update_download_controls_spanish_no_data_message():
    disabled, status = update_download_controls(
        ["Albany"], "organic", "1999-01-01", "1999-12-31", lang="es"
    )

    assert disabled is True
    assert status == t("download.no_data", "es")


# --- Shareable URL state (V1 scope): encode_filters_to_query /
# decode_query_to_filters — see specs/shareable-url-state.md.


def test_encode_filters_to_query_single_region():
    search = encode_filters_to_query(
        ["Albany"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        "AveragePrice",
        "Total Volume",
        "AveragePrice",
        "type",
    )

    assert search == (
        "?region=Albany&type=organic&start=2015-04-01&end=2018-01-01"
        "&x=AveragePrice&y=Total+Volume&col=AveragePrice&groupby=type"
    )


def test_encode_filters_to_query_multiple_regions_comma_joined():
    search = encode_filters_to_query(
        ["Boston", "Chicago"],
        "conventional",
        "2015-04-01",
        "2016-12-31",
        "AveragePrice",
        "Total Volume",
        "AveragePrice",
        "type",
    )

    assert search.startswith("?region=Boston%2CChicago&")


def test_encode_filters_to_query_empty_regions():
    search = encode_filters_to_query(
        [],
        "organic",
        "2015-04-01",
        "2018-01-01",
        "AveragePrice",
        "Total Volume",
        "AveragePrice",
        "type",
    )

    assert search.startswith("?region=&")


def test_decode_query_to_filters_full_valid_query_restores_values():
    filters = decode_query_to_filters(
        "?region=Boston,Chicago&type=organic&start=2015-04-01&end=2016-12-31"
        "&x=Total+Bags&y=Small+Bags&col=Large+Bags&groupby=region"
    )

    assert filters == {
        "region": ["Boston", "Chicago"],
        "type": "organic",
        "start": "2015-04-01",
        "end": "2016-12-31",
        "x": "Total Bags",
        "y": "Small Bags",
        "col": "Large Bags",
        "groupby": "region",
    }


def test_decode_query_to_filters_no_query_string_uses_defaults():
    filters = decode_query_to_filters("")

    assert filters["region"] == DEFAULT_URL_REGIONS
    assert filters["type"] == DEFAULT_URL_TYPE
    assert filters["start"] == DATA_MIN_DATE.isoformat()
    assert filters["end"] == DATA_MAX_DATE.isoformat()
    assert filters["x"] == DEFAULT_URL_X_AXIS
    assert filters["y"] == DEFAULT_URL_Y_AXIS
    assert filters["col"] == DEFAULT_URL_BOX_PLOT_COLUMN
    assert filters["groupby"] == DEFAULT_URL_BOX_PLOT_GROUPBY


def test_decode_query_to_filters_none_search_uses_defaults():
    filters = decode_query_to_filters(None)

    assert filters["region"] == DEFAULT_URL_REGIONS


def test_decode_query_to_filters_partial_query_defaults_missing_fields():
    filters = decode_query_to_filters("?region=Boston")

    assert filters["region"] == ["Boston"]
    assert filters["type"] == DEFAULT_URL_TYPE
    assert filters["start"] == DATA_MIN_DATE.isoformat()
    assert filters["end"] == DATA_MAX_DATE.isoformat()


def test_decode_query_to_filters_all_invalid_regions_falls_back_to_default():
    filters = decode_query_to_filters("?region=Atlantis&type=organic")

    assert filters["region"] == DEFAULT_URL_REGIONS


def test_decode_query_to_filters_mixed_valid_and_invalid_regions_keeps_valid_only():
    filters = decode_query_to_filters("?region=Boston,Atlantis")

    assert filters["region"] == ["Boston"]


def test_decode_query_to_filters_explicit_empty_region_is_preserved():
    filters = decode_query_to_filters("?region=")

    assert filters["region"] == []


def test_decode_query_to_filters_absent_region_key_uses_default():
    filters = decode_query_to_filters("?type=organic")

    assert filters["region"] == DEFAULT_URL_REGIONS


def test_decode_query_to_filters_invalid_type_falls_back_to_default():
    filters = decode_query_to_filters("?type=avocadoish")

    assert filters["type"] == DEFAULT_URL_TYPE
    assert filters["type"] in avocado_types


def test_decode_query_to_filters_unparseable_dates_fall_back_to_defaults():
    filters = decode_query_to_filters("?start=not-a-date&end=also-not-a-date")

    assert filters["start"] == DATA_MIN_DATE.isoformat()
    assert filters["end"] == DATA_MAX_DATE.isoformat()


def test_decode_query_to_filters_out_of_range_dates_fall_back_to_defaults():
    filters = decode_query_to_filters("?start=1999-01-01&end=2999-01-01")

    assert filters["start"] == DATA_MIN_DATE.isoformat()
    assert filters["end"] == DATA_MAX_DATE.isoformat()


# --- V2 scope: scatter axis (x/y) + box-plot column/group-by (col/groupby).
# Covers issue #47's 3 Gherkin scenarios.


def test_decode_query_to_filters_partial_query_defaults_missing_v2_fields():
    filters = decode_query_to_filters("?region=Boston")

    assert filters["x"] == DEFAULT_URL_X_AXIS
    assert filters["y"] == DEFAULT_URL_Y_AXIS
    assert filters["col"] == DEFAULT_URL_BOX_PLOT_COLUMN
    assert filters["groupby"] == DEFAULT_URL_BOX_PLOT_GROUPBY


def test_decode_query_to_filters_invalid_x_axis_falls_back_to_default():
    filters = decode_query_to_filters("?x=NotARealColumn")

    assert filters["x"] == DEFAULT_URL_X_AXIS


def test_decode_query_to_filters_invalid_y_axis_falls_back_to_default():
    filters = decode_query_to_filters("?y=NotARealColumn")

    assert filters["y"] == DEFAULT_URL_Y_AXIS


def test_decode_query_to_filters_invalid_box_plot_column_falls_back_to_default():
    filters = decode_query_to_filters("?col=NotARealColumn")

    assert filters["col"] == DEFAULT_URL_BOX_PLOT_COLUMN


def test_decode_query_to_filters_invalid_groupby_falls_back_to_default():
    filters = decode_query_to_filters("?groupby=NotARealGroupBy")

    assert filters["groupby"] == DEFAULT_URL_BOX_PLOT_GROUPBY


def test_decode_query_to_filters_valid_v2_fields_are_restored():
    filters = decode_query_to_filters(
        "?x=Total+Bags&y=Small+Bags&col=Large+Bags&groupby=year"
    )

    assert filters["x"] == "Total Bags"
    assert filters["y"] == "Small Bags"
    assert filters["col"] == "Large Bags"
    assert filters["groupby"] == "year"


def test_url_state_round_trip_settles_after_one_rewrite():
    """Models the two-dispatch self-trigger the URL-sync callback produces
    on initial load: a non-canonical query string gets re-encoded once
    into canonical form, and re-encoding that canonical form again must
    be a no-op (a fixed point) — otherwise the callback would keep
    rewriting the URL instead of settling."""
    non_canonical = (
        "?type=organic&region=Boston,Chicago&end=2016-12-31&start=2015-04-01"
        "&groupby=region&col=Large+Bags&y=Small+Bags&x=Total+Bags"
    )

    decoded_once = decode_query_to_filters(non_canonical)
    canonical = encode_filters_to_query(
        decoded_once["region"],
        decoded_once["type"],
        decoded_once["start"],
        decoded_once["end"],
        decoded_once["x"],
        decoded_once["y"],
        decoded_once["col"],
        decoded_once["groupby"],
    )

    decoded_twice = decode_query_to_filters(canonical)
    re_encoded = encode_filters_to_query(
        decoded_twice["region"],
        decoded_twice["type"],
        decoded_twice["start"],
        decoded_twice["end"],
        decoded_twice["x"],
        decoded_twice["y"],
        decoded_twice["col"],
        decoded_twice["groupby"],
    )

    assert re_encoded == canonical


# --- sync_url_and_filters callback: drives the real Dash `ctx.triggered_id`
# mechanism via context_value, the same technique Dash's own test suite
# uses to unit-test callbacks without a browser. Covers issue #36's 5
# Gherkin scenarios.


def _set_triggered(prop_id: str | None) -> None:
    """Simulate Dash's callback context for a given trigger. `prop_id=None`
    models the initial page-load call, where nothing has "triggered" yet
    (ctx.triggered_id is None) — matching real Dash behavior."""
    if prop_id is None:
        context_value.set(AttributeDict(triggered_inputs=[]))
    else:
        context_value.set(
            AttributeDict(triggered_inputs=[{"prop_id": prop_id, "value": None}])
        )


DEFAULT_SYNC_ARGS = (
    "AveragePrice",  # x-axis-dropdown
    "Total Volume",  # y-axis-dropdown
    "AveragePrice",  # box-plot-column
    "type",  # box-plot-groupby
)


def test_sync_url_and_filters_region_change_updates_url():
    _set_triggered("region-filter.value")

    result = sync_url_and_filters(
        None, ["Chicago"], "organic", "2015-04-01", "2018-01-01", *DEFAULT_SYNC_ARGS
    )

    assert result[0] == (
        "?region=Chicago&type=organic&start=2015-04-01&end=2018-01-01"
        "&x=AveragePrice&y=Total+Volume&col=AveragePrice&groupby=type"
    )
    assert result[1:] == (no_update,) * 8


def test_sync_url_and_filters_url_load_restores_filters():
    _set_triggered(None)

    result = sync_url_and_filters(
        "?region=Boston,Chicago&type=organic&start=2015-04-01&end=2016-12-31",
        ["Albany"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        *DEFAULT_SYNC_ARGS,
    )

    assert result[0] is no_update
    assert result[1] == ["Boston", "Chicago"]
    assert result[2] == "organic"
    assert result[3] == "2015-04-01"
    assert result[4] == "2016-12-31"
    assert result[5] == DEFAULT_URL_X_AXIS
    assert result[6] == DEFAULT_URL_Y_AXIS
    assert result[7] == DEFAULT_URL_BOX_PLOT_COLUMN
    assert result[8] == DEFAULT_URL_BOX_PLOT_GROUPBY


def test_sync_url_and_filters_no_query_string_uses_defaults():
    _set_triggered(None)

    result = sync_url_and_filters(
        "",
        ["Chicago"],
        "conventional",
        "2015-04-01",
        "2018-01-01",
        *DEFAULT_SYNC_ARGS,
    )

    assert result[1] == DEFAULT_URL_REGIONS
    assert result[2] == DEFAULT_URL_TYPE
    assert result[3] == DATA_MIN_DATE.isoformat()
    assert result[4] == DATA_MAX_DATE.isoformat()


def test_sync_url_and_filters_invalid_region_falls_back_to_default():
    _set_triggered(None)

    result = sync_url_and_filters(
        "?region=Atlantis&type=organic",
        ["Chicago"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        *DEFAULT_SYNC_ARGS,
    )

    assert result[1] == DEFAULT_URL_REGIONS


def test_sync_url_and_filters_repeated_identical_state_is_idempotent():
    """Issue #36's loop-safety scenario: once url.search already matches
    the current filter state, re-dispatching must return no_update for
    url.search, not rewrite it — this is what prevents an update loop
    between the URL and the filters."""
    _set_triggered("region-filter.value")
    current_search = (
        "?region=Chicago&type=organic&start=2015-04-01&end=2018-01-01"
        "&x=AveragePrice&y=Total+Volume&col=AveragePrice&groupby=type"
    )

    result = sync_url_and_filters(
        current_search,
        ["Chicago"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        *DEFAULT_SYNC_ARGS,
    )

    assert result == (no_update,) * 9


def test_sync_url_and_filters_settles_after_initial_load_self_trigger():
    """Models the two-dispatch self-trigger from a non-canonical query
    string on page load (see Dry-Run Review Gate findings in
    specs/shareable-url-state.md): dispatch 1 (triggered by the URL)
    parses filters; dispatch 2 (self-triggered because those filter
    values are also this callback's own Inputs) must rebuild the exact
    same canonical URL and therefore no_update it, not loop further."""
    non_canonical = (
        "?type=organic&region=Boston,Chicago&end=2016-12-31&start=2015-04-01"
        "&x=AveragePrice&y=Total+Volume&col=AveragePrice&groupby=type"
    )

    _set_triggered(None)
    dispatch_1 = sync_url_and_filters(
        non_canonical,
        ["Albany"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        *DEFAULT_SYNC_ARGS,
    )
    assert dispatch_1[0] is no_update

    _set_triggered("region-filter.value")
    dispatch_2 = sync_url_and_filters(non_canonical, *dispatch_1[1:])
    canonical = dispatch_2[0]
    assert canonical != non_canonical  # confirms it's genuinely re-canonicalized

    _set_triggered("region-filter.value")
    dispatch_3 = sync_url_and_filters(canonical, *dispatch_1[1:])
    assert dispatch_3[0] is no_update  # settled — no further rewrite


def test_sync_url_and_filters_scatter_axis_change_updates_url():
    _set_triggered("x-axis-dropdown.value")

    result = sync_url_and_filters(
        None,
        ["Albany"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        "Total Bags",
        "Total Volume",
        "AveragePrice",
        "type",
    )

    assert "x=Total+Bags" in result[0]
    assert result[1:] == (no_update,) * 8


def test_sync_url_and_filters_box_plot_column_and_groupby_change_updates_url():
    _set_triggered("box-plot-groupby.value")

    result = sync_url_and_filters(
        None,
        ["Albany"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        "AveragePrice",
        "Total Volume",
        "Small Bags",
        "region",
    )

    assert "col=Small+Bags" in result[0]
    assert "groupby=region" in result[0]


def test_sync_url_and_filters_url_load_restores_chart_selections():
    _set_triggered(None)

    result = sync_url_and_filters(
        "?x=Large+Bags&y=XLarge+Bags&col=Total+Bags&groupby=year",
        ["Albany"],
        "organic",
        "2015-04-01",
        "2018-01-01",
        *DEFAULT_SYNC_ARGS,
    )

    assert result[5] == "Large Bags"
    assert result[6] == "XLarge Bags"
    assert result[7] == "Total Bags"
    assert result[8] == "year"

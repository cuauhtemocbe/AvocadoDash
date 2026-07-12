from app import app, create_price_chart, data

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

"""Filter-to-chart flow, driven through Dash's own HTTP endpoints (issue #42).

Unlike the unit tests, which call the callback functions directly, these go
through `/_dash-update-component`, so they also cover the wiring: Input/Output
ids, payload parsing and JSON serialization of the figures. The UI defaults to
Spanish, so assertions use trace data, component ids or `translations`.
"""

from urllib.parse import parse_qs

import pytest

from translations import t

PRICE = "price-chart.figure"
VOLUME = "volume-chart.figure"
SCATTER = "scatter-chart.figure"
BOX_PLOT = "box-plot-chart.figure"
MAIN_CHARTS = [PRICE, VOLUME, SCATTER, BOX_PLOT]

REVERSED_RANGE = {
    "date-range.start_date": "2018-03-25",
    "date-range.end_date": "2015-01-04",
}


def line_traces(figure):
    """The per-region lines (anomaly markers are `mode == "markers"`)."""
    return [trace for trace in figure["data"] if trace["mode"] == "lines+markers"]


def test_every_callback_is_wired_to_components_in_the_layout(dash_client):
    assert dash_client.dependencies
    assert not dash_client.ids_missing_from_layout()


@pytest.mark.parametrize("output_prop", MAIN_CHARTS)
def test_default_filters_produce_every_main_chart(dash_client, output_prop):
    response = dash_client.post(output_prop)

    assert response.status_code == 200
    assert dash_client.figure(output_prop)["data"]


def test_selecting_an_additional_region_adds_it_to_the_price_chart(dash_client):
    single = dash_client.figure(PRICE)
    both = dash_client.figure(PRICE, {"region-filter.value": ["Albany", "Chicago"]})

    assert [trace["name"] for trace in line_traces(single)] == ["Albany"]
    assert [trace["name"] for trace in line_traces(both)] == ["Albany", "Chicago"]


def test_narrowing_the_date_range_restricts_the_volume_chart(dash_client):
    start, end = "2016-06-05", "2016-12-25"
    full = dash_client.figure(VOLUME)
    narrowed = dash_client.figure(
        VOLUME, {"date-range.start_date": start, "date-range.end_date": end}
    )

    points = [x for trace in narrowed["data"] for x in trace["x"]]
    assert points
    # ISO timestamps: the first ten characters are the date.
    assert all(start <= x[:10] <= end for x in points)
    assert len(points) < sum(len(trace["x"]) for trace in full["data"])


def test_url_search_restores_the_filters(dash_client):
    search = "?region=Chicago,Boise&type=conventional&start=2016-01-03&end=2017-01-01"

    restored = dash_client.call("url.search", {"url.search": search})

    assert restored["region-filter.value"] == ["Chicago", "Boise"]
    assert restored["type-filter.value"] == "conventional"
    assert restored["date-range.start_date"] == "2016-01-03"
    assert restored["date-range.end_date"] == "2017-01-01"
    assert "url.search" not in restored


def test_changing_a_filter_writes_it_back_to_the_url(dash_client):
    written = dash_client.call(
        "url.search",
        {
            "region-filter.value": ["Albany", "Chicago"],
            "type-filter.value": "conventional",
            "url.search": "?region=Albany&type=organic",
        },
        changed=["type-filter.value"],
    )

    query = parse_qs(written["url.search"].lstrip("?"))
    assert query["region"] == ["Albany,Chicago"]
    assert query["type"] == ["conventional"]
    assert set(written) == {"url.search"}


@pytest.mark.parametrize("output_prop", MAIN_CHARTS)
def test_reversed_date_range_shows_the_empty_state(dash_client, output_prop):
    # Reachable through a shareable URL: start and end are only checked
    # against the data bounds, not against each other.
    response = dash_client.post(output_prop, REVERSED_RANGE)
    figure = dash_client.figure(output_prop, REVERSED_RANGE)

    assert response.status_code == 200
    assert figure["data"] == []
    assert figure["layout"]["annotations"][0]["text"] == t("empty.try_adjusting", "es")

from app import create_price_chart, data


def test_load_data_has_expected_columns():
    assert not data.empty
    for column in ("Date", "AveragePrice", "Total Volume", "region", "type"):
        assert column in data.columns


def test_create_price_chart_returns_plotly_figure_dict():
    figure = create_price_chart(data.head(50))

    assert "data" in figure
    assert "layout" in figure
    assert isinstance(figure["data"], list)

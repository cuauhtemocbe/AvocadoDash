# app.py

import os
import pandas as pd
from dash import Dash, Input, Output, dcc, html
import plotly.express as px

def load_data():
    """Load and preprocess the avocado dataset."""
    try:
        # Use relative path from the script location
        csv_path = os.path.join(os.path.dirname(__file__), "avocado.csv")
        data = (
            pd.read_csv(csv_path)
            .assign(Date=lambda df: pd.to_datetime(df["Date"], format="%Y-%m-%d"))
            .sort_values(by="Date")
        )
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find avocado.csv at {csv_path}")
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

# Load data
data = load_data()
regions = sorted(data["region"].unique())
avocado_types = sorted(data["type"].unique())

external_stylesheets = [
    {
        "href": (
            "https://fonts.googleapis.com/css2?"
            "family=Lato:wght@400;700&display=swap"
        ),
        "rel": "stylesheet",
    },
]
app = Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Avocado Analytics"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="🥑", className="header-emoji"),
                html.H1(
                    children="Avocado Analytics by Kuautli", className="header-title"
                ),
                html.P(
                    children=(
                        "Analyze the behavior of avocado prices and the number"
                        " of avocados sold in the US between 2015 and 2018"
                    ),
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Region", className="menu-title"),
                        dcc.Dropdown(
                            id="region-filter",
                            options=[
                                {"label": region, "value": region}
                                for region in regions
                            ],
                            value="Albany",
                            clearable=False,
                            searchable=True,
                            placeholder="Select a region...",
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(children="Type", className="menu-title"),
                        dcc.Dropdown(
                            id="type-filter",
                            options=[
                                {
                                    "label": avocado_type.title(),
                                    "value": avocado_type,
                                }
                                for avocado_type in avocado_types
                            ],
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
                            children="Date Range", className="menu-title"
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
    ]
)

def create_price_chart(filtered_data):
    """Create the price chart with improved styling."""
    return {
        "data": [
            {
                "x": filtered_data["Date"],
                "y": filtered_data["AveragePrice"],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Average Price",
                "hovertemplate": "Date: %{x}<br>Price: $%{y:.2f}<extra></extra>",
                "line": {"width": 3},
                "marker": {"size": 4},
            },
        ],
        "layout": {
            "title": {
                "text": "Average Price of Avocados",
                "x": 0.05,
                "xanchor": "left",
                "font": {"size": 20},
            },
            "xaxis": {
                "fixedrange": True,
                "title": "Date",
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "yaxis": {
                "tickprefix": "$", 
                "fixedrange": True,
                "title": "Price (USD)",
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "colorway": ["#17B897"],
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        },
    }

def create_volume_chart(filtered_data):
    """Create the volume chart with improved styling."""
    return {
        "data": [
            {
                "x": filtered_data["Date"],
                "y": filtered_data["Total Volume"],
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Volume Sold",
                "hovertemplate": "Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>",
                "line": {"width": 3},
                "marker": {"size": 4},
            },
        ],
        "layout": {
            "title": {
                "text": "Avocados Sold (Volume)",
                "x": 0.05,
                "xanchor": "left",
                "font": {"size": 20},
            },
            "xaxis": {
                "fixedrange": True,
                "title": "Date",
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "yaxis": {
                "fixedrange": True,
                "title": "Volume",
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "colorway": ["#E12D39"],
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
        },
    }

@app.callback(
    Output("price-chart", "figure"),
    Output("volume-chart", "figure"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
)
def update_charts(region, avocado_type, start_date, end_date):
    """Update charts based on filter selections."""
    try:
        # Filter data based on selections
        filtered_data = data.query(
            "region == @region and type == @avocado_type"
            " and Date >= @start_date and Date <= @end_date"
        )
        
        # Handle empty data case
        if filtered_data.empty:
            empty_fig = {
                "data": [],
                "layout": {
                    "title": "No data available for selected filters",
                    "annotations": [{
                        "text": "Try adjusting your filters",
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.5,
                        "y": 0.5,
                        "showarrow": False,
                        "font": {"size": 16}
                    }]
                }
            }
            return empty_fig, empty_fig
        
        return create_price_chart(filtered_data), create_volume_chart(filtered_data)
    
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        # Return empty figures on error
        error_fig = {
            "data": [],
            "layout": {"title": f"Error: {str(e)}"}
        }
        return error_fig, error_fig

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8050)
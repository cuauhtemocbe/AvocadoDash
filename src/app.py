# app.py

import os
import pandas as pd
from dash import Dash, Input, Output, dcc, html

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

# Define numeric columns for scatter plot
numeric_columns = [
    "AveragePrice", "Total Volume", 
    "Total Bags", "Small Bags", "Large Bags", "XLarge Bags", "year"
]

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
server = app.server  # This is needed for Railway deployment

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="🥑", className="header-emoji"),
                html.H1(
                    children="Avocado Analytics", className="header-title"
                ),
                html.P(
                    children=[
                        "by ",
                        html.A(
                            "@Kuautli",
                            href="https://github.com/cuauhtemocbe",
                            target="_blank",
                            className="header-link"
                        ),
                        " | ",
                        html.A(
                            "View on GitHub",
                            href="https://github.com/cuauhtemocbe/AvocadoDash",
                            target="_blank",
                            className="header-link"
                        )
                    ],
                    className="header-subtitle"
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
        html.Div(
            children=[
                html.H2(
                    children="Scatter Plot Analysis",
                    style={
                        "text-align": "center",
                        "margin": "40px 0 20px 0",
                        "color": "#079A82",
                        "font-size": "28px"
                    }
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(children="X-Axis Column", className="menu-title"),
                                dcc.Dropdown(
                                    id="x-axis-dropdown",
                                    options=[
                                        {"label": col.replace("_", " ").title(), "value": col}
                                        for col in numeric_columns
                                    ],
                                    value="AveragePrice",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={"width": "45%", "display": "inline-block"}
                        ),
                        html.Div(
                            children=[
                                html.Div(children="Y-Axis Column", className="menu-title"),
                                dcc.Dropdown(
                                    id="y-axis-dropdown",
                                    options=[
                                        {"label": col.replace("_", " ").title(), "value": col}
                                        for col in numeric_columns
                                    ],
                                    value="Total Volume",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={"width": "45%", "display": "inline-block", "margin-left": "10%"}
                        ),
                    ],
                    style={"margin": "20px auto", "max-width": "800px"}
                ),
                html.Div(
                    children=dcc.Graph(
                        id="scatter-chart",
                        config={"displayModeBar": True},
                    ),
                    className="card",
                    style={"margin": "20px auto", "max-width": "1000px"}
                ),
            ]
        ),
        html.Div(
            children=[
                html.H2(
                    children="Box Plot Analysis",
                    style={
                        "text-align": "center",
                        "margin": "40px 0 20px 0",
                        "color": "#079A82",
                        "font-size": "28px"
                    }
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(children="Column to Analyze", className="menu-title"),
                                dcc.Dropdown(
                                    id="box-plot-column",
                                    options=[
                                        {"label": col.replace("_", " ").title(), "value": col}
                                        for col in numeric_columns
                                    ],
                                    value="AveragePrice",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={"width": "45%", "display": "inline-block"}
                        ),
                        html.Div(
                            children=[
                                html.Div(children="Group By", className="menu-title"),
                                dcc.Dropdown(
                                    id="box-plot-groupby",
                                    options=[
                                        {"label": "Avocado Type", "value": "type"},
                                        {"label": "Region", "value": "region"},
                                        {"label": "Year", "value": "year"},
                                    ],
                                    value="type",
                                    clearable=False,
                                    className="dropdown",
                                ),
                            ],
                            style={"width": "45%", "display": "inline-block", "margin-left": "10%"}
                        ),
                    ],
                    style={"margin": "20px auto", "max-width": "800px"}
                ),
                html.Div(
                    children=dcc.Graph(
                        id="box-plot-chart",
                        config={"displayModeBar": True},
                    ),
                    className="card",
                    style={"margin": "20px auto", "max-width": "1000px"}
                ),
            ]
        ),
        html.Div(
            children=[
                html.P(
                    children=[
                        "Created by ",
                        html.A(
                            "@Kuautli",
                            href="https://github.com/cuauhtemocbe",
                            target="_blank",
                            className="footer-link"
                        ),
                        " | ",
                        html.A(
                            "View on GitHub",
                            href="https://github.com/cuauhtemocbe/AvocadoDash",
                            target="_blank",
                            className="footer-link"
                        )
                    ],
                    className="footer-text"
                )
            ],
            className="footer"
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

def create_box_plot(filtered_data, column, group_by):
    """Create a box plot for the selected column grouped by the specified variable."""
    # Color mapping for different groups
    color_map = {
        "conventional": "#17B897", 
        "organic": "#E12D39"
    }
    
    traces = []
    
    if group_by == "type":
        # Group by avocado type
        for avocado_type in sorted(filtered_data["type"].unique()):
            type_data = filtered_data[filtered_data["type"] == avocado_type]
            traces.append({
                "y": type_data[column],
                "type": "box",
                "name": avocado_type.title(),
                "marker": {"color": color_map.get(avocado_type, "#17B897")},
                "boxpoints": "outliers",
                "jitter": 0.3,
                "pointpos": -1.8,
            })
    
    elif group_by == "region":
        # For regions, use a single box plot with color by type if multiple types exist
        if len(filtered_data["type"].unique()) > 1:
            for avocado_type in sorted(filtered_data["type"].unique()):
                type_data = filtered_data[filtered_data["type"] == avocado_type]
                traces.append({
                    "y": type_data[column],
                    "x": type_data["region"],
                    "type": "box",
                    "name": avocado_type.title(),
                    "marker": {"color": color_map.get(avocado_type, "#17B897")},
                    "boxpoints": "outliers",
                })
        else:
            # Single type, group by region
            for region in sorted(filtered_data["region"].unique()):
                region_data = filtered_data[filtered_data["region"] == region]
                traces.append({
                    "y": region_data[column],
                    "type": "box",
                    "name": region,
                    "boxpoints": "outliers",
                    "jitter": 0.3,
                    "pointpos": -1.8,
                })
    
    elif group_by == "year":
        # Group by year
        for year in sorted(filtered_data["year"].unique()):
            year_data = filtered_data[filtered_data["year"] == year]
            traces.append({
                "y": year_data[column],
                "type": "box",
                "name": str(year),
                "boxpoints": "outliers",
                "jitter": 0.3,
                "pointpos": -1.8,
            })
    
    # Determine layout based on group_by
    if group_by == "region" and len(filtered_data["type"].unique()) > 1:
        x_title = "Region"
        show_legend = True
    else:
        x_title = group_by.replace("_", " ").title()
        show_legend = len(traces) > 1
    
    return {
        "data": traces,
        "layout": {
            "title": {
                "text": f"{column.replace('_', ' ').title()} Distribution by {group_by.replace('_', ' ').title()}",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 22},
            },
            "xaxis": {
                "title": x_title,
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "yaxis": {
                "title": column.replace("_", " ").title(),
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "showlegend": show_legend,
            "legend": {
                "x": 1.02,
                "y": 1,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "gray",
                "borderwidth": 1
            }
        },
    }

def create_scatter_chart(filtered_data, x_col, y_col):
    """Create a scatter plot with selected columns."""
    # Create color mapping for avocado types
    color_map = {"conventional": "#17B897", "organic": "#E12D39"}
    
    traces = []
    for avocado_type in filtered_data["type"].unique():
        type_data = filtered_data[filtered_data["type"] == avocado_type]
        traces.append({
            "x": type_data[x_col],
            "y": type_data[y_col],
            "mode": "markers",
            "type": "scatter",
            "name": avocado_type.title(),
            "marker": {
                "size": 8,
                "color": color_map.get(avocado_type, "#17B897"),
                "opacity": 0.7,
                "line": {"width": 1, "color": "white"}
            },
            "hovertemplate": (
                f"<b>%{{fullData.name}}</b><br>"
                f"{x_col.replace('_', ' ').title()}: %{{x}}<br>"
                f"{y_col.replace('_', ' ').title()}: %{{y}}<br>"
                f"Region: %{{customdata[0]}}<br>"
                f"Date: %{{customdata[1]}}<extra></extra>"
            ),
            "customdata": list(zip(type_data["region"], type_data["Date"].dt.strftime("%Y-%m-%d")))
        })
    
    return {
        "data": traces,
        "layout": {
            "title": {
                "text": f"{x_col.replace('_', ' ').title()} vs {y_col.replace('_', ' ').title()}",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 22},
            },
            "xaxis": {
                "title": x_col.replace("_", " ").title(),
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "yaxis": {
                "title": y_col.replace("_", " ").title(),
                "showgrid": True,
                "gridcolor": "lightgray",
            },
            "plot_bgcolor": "white",
            "paper_bgcolor": "white",
            "hovermode": "closest",
            "legend": {
                "x": 1.02,
                "y": 1,
                "bgcolor": "rgba(255,255,255,0.8)",
                "bordercolor": "gray",
                "borderwidth": 1
            }
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

@app.callback(
    Output("scatter-chart", "figure"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("x-axis-dropdown", "value"),
    Input("y-axis-dropdown", "value"),
)
def update_scatter_chart(region, avocado_type, start_date, end_date, x_col, y_col):
    """Update scatter chart based on filter selections and axis choices."""
    try:
        # Filter data based on selections
        filtered_data = data.query(
            "region == @region and type == @avocado_type"
            " and Date >= @start_date and Date <= @end_date"
        )
        
        # Handle empty data case
        if filtered_data.empty:
            return {
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
        
        return create_scatter_chart(filtered_data, x_col, y_col)
    
    except Exception as e:
        print(f"Error in scatter chart callback: {str(e)}")
        return {
            "data": [],
            "layout": {"title": f"Error: {str(e)}"}
        }

@app.callback(
    Output("box-plot-chart", "figure"),
    Input("region-filter", "value"),
    Input("type-filter", "value"),
    Input("date-range", "start_date"),
    Input("date-range", "end_date"),
    Input("box-plot-column", "value"),
    Input("box-plot-groupby", "value"),
)
def update_box_plot(region, avocado_type, start_date, end_date, column, group_by):
    """Update box plot based on filter selections and grouping choice."""
    try:
        # For box plots, we might want to show data across different groups
        # So we'll modify the filtering based on the group_by selection
        if group_by == "type":
            # Show both types, but filter by region and date
            filtered_data = data.query(
                "region == @region"
                " and Date >= @start_date and Date <= @end_date"
            )
        elif group_by == "region":
            # Show data for selected type across regions (or all types if comparing)
            filtered_data = data.query(
                "type == @avocado_type"
                " and Date >= @start_date and Date <= @end_date"
            )
        elif group_by == "year":
            # Show data for selected region and type across years
            filtered_data = data.query(
                "region == @region and type == @avocado_type"
                " and Date >= @start_date and Date <= @end_date"
            )
        else:
            # Default filtering
            filtered_data = data.query(
                "region == @region and type == @avocado_type"
                " and Date >= @start_date and Date <= @end_date"
            )
        
        # Handle empty data case
        if filtered_data.empty:
            return {
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
        
        return create_box_plot(filtered_data, column, group_by)
    
    except Exception as e:
        print(f"Error in box plot callback: {str(e)}")
        return {
            "data": [],
            "layout": {"title": f"Error: {str(e)}"}
        }

if __name__ == "__main__":
    # Get port from environment variable for Railway deployment
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host='0.0.0.0', port=port)
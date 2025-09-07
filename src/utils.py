# utils.py

import pandas as pd

def calculate_summary_stats(data):
    """Calculate summary statistics for the dataset."""
    return {
        "avg_price": data["AveragePrice"].mean(),
        "max_price": data["AveragePrice"].max(),
        "min_price": data["AveragePrice"].min(),
        "total_volume": data["Total Volume"].sum(),
        "date_range": {
            "start": data["Date"].min(),
            "end": data["Date"].max()
        }
    }

def format_number(num):
    """Format large numbers with proper suffixes."""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"

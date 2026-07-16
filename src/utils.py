# utils.py

from datetime import timedelta
from typing import Any

import pandas as pd


def calculate_summary_stats(data: pd.DataFrame) -> dict[str, Any]:
    """Calculate summary statistics for the dataset."""
    return {
        "avg_price": data["AveragePrice"].mean(),
        "max_price": data["AveragePrice"].max(),
        "min_price": data["AveragePrice"].min(),
        "total_volume": data["Total Volume"].sum(),
        "date_range": {"start": data["Date"].min(), "end": data["Date"].max()},
    }


def format_number(num: float) -> str:
    """Format large numbers with proper suffixes."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return f"{num:.0f}"


def calculate_price_change(
    data: pd.DataFrame,
    regions: list[str],
    avocado_type: str,
    start_date: str,
    end_date: str,
) -> float | None:
    """Percent change in average price vs. the immediately preceding period
    of equal length, aggregated across all `regions`. Returns None if
    either period has no data."""
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    period_length_days = (end - start).days + 1
    previous_start = start - timedelta(days=period_length_days)
    previous_end = start - timedelta(days=1)

    current = data.query(
        "region in @regions and type == @avocado_type"
        " and Date >= @start and Date <= @end"
    )
    previous = data[
        (data["region"].isin(regions))
        & (data["type"] == avocado_type)
        & (data["Date"] >= previous_start)
        & (data["Date"] <= previous_end)
    ]

    if current.empty or previous.empty:
        return None

    previous_avg = previous["AveragePrice"].mean()
    if previous_avg == 0:
        return None

    current_avg = current["AveragePrice"].mean()
    return (current_avg - previous_avg) / previous_avg * 100


def find_region_extremes(
    data: pd.DataFrame, avocado_type: str, start_date: str, end_date: str
) -> dict[str, Any] | None:
    """Find the best/worst average-price regions for a type + date filter,
    across all regions. Returns None if the filter matches no rows."""
    filtered = data.query(
        "type == @avocado_type and Date >= @start_date and Date <= @end_date"
    )
    if filtered.empty:
        return None

    region_avg = filtered.groupby("region")["AveragePrice"].mean()
    best_region = region_avg.idxmax()
    worst_region = region_avg.idxmin()
    return {
        "best_region": best_region,
        "best_price": region_avg[best_region],
        "worst_region": worst_region,
        "worst_price": region_avg[worst_region],
    }

"""FRED API utilities for fetching Treasury yield data.

This module provides functions to fetch Treasury yield data from the FRED API.
It requires a FRED API key to be set in the environment variable FRED_API_KEY.

Example:
    >>> from scripts.utils.fred_api import fetch_treasury_yields
    >>> yields = fetch_treasury_yields("2023-01-01", "2024-03-01")
"""

import os
from datetime import datetime
from typing import Optional, Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
FRED_API_KEY = os.getenv("FRED_API_KEY")
if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY environment variable not set")

FRED_BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# Treasury series with their descriptions
TREASURY_SERIES: Dict[str, str] = {
    "DGS3MO": "3-Month Treasury Bill",
    "DGS1": "1-Year Treasury Bill",
    "DGS2": "2-Year Treasury Note",
    "DGS5": "5-Year Treasury Note",
    "DGS10": "10-Year Treasury Note",
    "DGS30": "30-Year Treasury Bond",
}

# Common yield spreads to calculate
YIELD_SPREADS: List[tuple] = [
    ("DGS10", "DGS2", "10Y-2Y"),  # 10Y-2Y spread
    ("DGS10", "DGS3MO", "10Y-3M"),  # 10Y-3M spread
    ("DGS2", "DGS3MO", "2Y-3M"),  # 2Y-3M spread
]


def validate_dates(start_date: str, end_date: str) -> None:
    """Validate date formats and ranges.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Raises:
        ValueError: If dates are invalid or end_date is before start_date
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

    if end < start:
        raise ValueError("end_date must be after start_date")


def fetch_series(
    series_id: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch a single series from FRED API.

    Args:
        series_id: FRED series ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with series data

    Raises:
        requests.exceptions.RequestException: If the API request fails
    """
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }

    response = requests.get(FRED_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    # Convert to DataFrame
    df = pd.DataFrame(data["observations"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[["date", "value"]]
    df.columns = ["date", series_id]
    
    return df


def fetch_treasury_yields(
    start_date: str,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch Treasury yield data from FRED API.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format (defaults to today)

    Returns:
        DataFrame with Treasury yields indexed by date, including calculated spreads

    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the API key is not set or dates are invalid
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Validate dates
    validate_dates(start_date, end_date)

    # Fetch data for each series
    dfs = []
    for series_id in TREASURY_SERIES:
        try:
            df = fetch_series(series_id, start_date, end_date)
            dfs.append(df)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to fetch {series_id}: {e}")
            continue

    if not dfs:
        raise ValueError("No Treasury yield data could be fetched")

    # Merge all series
    result = dfs[0]
    for df in dfs[1:]:
        result = result.merge(df, on="date", how="outer")

    # Convert date to datetime and set as index
    result["date"] = pd.to_datetime(result["date"])
    result.set_index("date", inplace=True)
    result.sort_index(inplace=True)

    # Calculate yield spreads
    for long_term, short_term, spread_name in YIELD_SPREADS:
        if long_term in result.columns and short_term in result.columns:
            result[spread_name] = result[long_term] - result[short_term]

    # Validate data
    missing_pct = result.isnull().mean()
    if (missing_pct > 0.1).any():
        logger.warning("Some series have more than 10% missing data:")
        for col, pct in missing_pct[missing_pct > 0.1].items():
            logger.warning(f"  {col}: {pct:.1%} missing")

    return result


if __name__ == "__main__":
    # Example usage
    yields = fetch_treasury_yields("2023-01-01")
    print(yields.head()) 
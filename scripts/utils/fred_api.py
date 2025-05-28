"""FRED API utilities for fetching Treasury yield data.

This module provides functions to fetch Treasury yield data from the FRED API.
It requires a FRED API key to be set in the environment variable FRED_API_KEY.

Example:
    >>> from scripts.utils.fred_api import fetch_treasury_yields
    >>> yields = fetch_treasury_yields("2023-01-01", "2024-03-01")
"""

import os
from datetime import datetime
from typing import Optional

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
TREASURY_SERIES = {
    "DGS3": "3-Month Treasury Bill",
    "DGS1": "1-Year Treasury Bill",
}


def fetch_treasury_yields(
    start_date: str,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch Treasury yield data from FRED API.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format (defaults to today)

    Returns:
        DataFrame with Treasury yields indexed by date

    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the API key is not set or dates are invalid
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}")

    # Fetch data for each series
    dfs = []
    for series_id, description in TREASURY_SERIES.items():
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
        dfs.append(df)

    # Merge all series
    result = dfs[0]
    for df in dfs[1:]:
        result = result.merge(df, on="date", how="outer")

    # Convert date to datetime and set as index
    result["date"] = pd.to_datetime(result["date"])
    result.set_index("date", inplace=True)
    result.sort_index(inplace=True)

    return result


if __name__ == "__main__":
    # Example usage
    yields = fetch_treasury_yields("2023-01-01")
    print(yields.head()) 
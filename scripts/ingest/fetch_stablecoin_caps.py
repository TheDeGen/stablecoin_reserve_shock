#!/usr/bin/env python3
"""Fetch stablecoin market cap data from DefiLlama API.

This module fetches and stores stablecoin market cap data from the DefiLlama API.
It processes the aggregated data and saves it in parquet format with gzip compression.

Example:
    $ python fetch_stablecoin_caps.py --start 2023-01-01 --end 2024-03-01
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
DEFILLAMA_API_URL = "https://stablecoins.llama.fi/stablecoincharts/all"
DEFAULT_START_DATE = "2018-01-01"
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "stablecoin_caps.parq"


def parse_date(date_str: str) -> int:
    """Convert YYYY-MM-DD string to UNIX timestamp (seconds)."""
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())


def unix_to_date(ts: int) -> pd.Timestamp:
    """Convert UNIX timestamp (seconds) to pandas Timestamp."""
    return pd.to_datetime(ts, unit="s")


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
)
async def fetch_stablecoin_data(client: httpx.AsyncClient) -> dict:
    """Fetch stablecoin data from DefiLlama API with retry logic.

    Args:
        client: Async HTTP client instance
    Returns:
        Raw JSON response as dict
    Raises:
        httpx.HTTPError: If the API request fails after retries
    """
    response = await client.get(DEFILLAMA_API_URL)
    response.raise_for_status()
    return response.json()


def process_stablecoin_data(
    raw_data: list,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Process raw stablecoin data into a pandas DataFrame.

    Args:
        raw_data: Raw JSON response from API
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
    Returns:
        DataFrame with processed stablecoin data
    """
    records = []
    start_ts = parse_date(start_date) if start_date else None
    end_ts = parse_date(end_date) if end_date else None

    for entry in raw_data:
        ts = int(entry.get("date"))
        if start_ts and ts < start_ts:
            continue
        if end_ts and ts > end_ts:
            continue
            
        circulating = entry.get("totalCirculating", {}).get("peggedUSD", 0)
        circulating_usd = entry.get("totalCirculatingUSD", {}).get("peggedUSD", 0)
        
        records.append({
            "timestamp": unix_to_date(ts),
            "circulating_supply": circulating,
            "circulating_supply_usd": circulating_usd,
        })
    
    df = pd.DataFrame(records)
    if not df.empty:
        df = df.sort_values("timestamp")
    return df


async def main(
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
) -> None:
    """Main function to fetch and save stablecoin data.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient() as client:
        try:
            raw_data = await fetch_stablecoin_data(client)
            df = process_stablecoin_data(raw_data, start_date, end_date)
            df.to_parquet(
                OUTPUT_FILE,
                compression="gzip",
                index=False,
            )
            logger.info(f"Saved {len(df)} records to {OUTPUT_FILE}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch data: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch stablecoin market cap data")
    parser.add_argument(
        "--start",
        default=DEFAULT_START_DATE,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        default=DEFAULT_END_DATE,
        help="End date (YYYY-MM-DD)",
    )
    args = parser.parse_args()
    import asyncio
    asyncio.run(main(args.start, args.end)) 
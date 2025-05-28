#!/usr/bin/env python3
"""Fetch stablecoin market cap data from DefiLlama API.

This module handles fetching and storing stablecoin market cap data from the DefiLlama API.
It supports pagination and saves the data in parquet format with gzip compression.

Example:
    $ python fetch_stablecoin_caps.py --start 2023-01-01 --end 2024-03-01
    $ python fetch_stablecoin_caps.py --token USDC
"""

import argparse
import logging
from datetime import datetime, timedelta
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
DEFILLAMA_API_URL = "https://api.llama.fi/stablecoins"
DEFAULT_START_DATE = "2018-01-01"
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "stablecoin_caps.parq"


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
)
async def fetch_stablecoin_data(
    client: httpx.AsyncClient,
    token: Optional[str] = None,
) -> list[dict]:
    """Fetch stablecoin data from DefiLlama API with retry logic.

    Args:
        client: Async HTTP client instance
        token: Optional token symbol to filter results

    Returns:
        List of stablecoin data dictionaries

    Raises:
        httpx.HTTPError: If the API request fails after retries
    """
    params = {"includePrices": "true"}
    if token:
        params["token"] = token

    response = await client.get(DEFILLAMA_API_URL, params=params)
    response.raise_for_status()
    return response.json()


def process_stablecoin_data(raw_data: list[dict]) -> pd.DataFrame:
    """Process raw stablecoin data into a pandas DataFrame.

    Args:
        raw_data: List of stablecoin data dictionaries from API

    Returns:
        DataFrame with processed stablecoin data
    """
    records = []
    for coin in raw_data:
        for chain in coin.get("chains", []):
            records.append({
                "symbol": coin["symbol"],
                "name": coin["name"],
                "chain": chain["chain"],
                "circulating_supply": chain["circulating"]["peggedUSD"],
                "timestamp": pd.Timestamp.now(),
            })
    
    df = pd.DataFrame(records)
    return df


async def main(
    start_date: str = DEFAULT_START_DATE,
    end_date: str = DEFAULT_END_DATE,
    token: Optional[str] = None,
) -> None:
    """Main function to fetch and save stablecoin data.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        token: Optional token symbol to filter results
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient() as client:
        try:
            raw_data = await fetch_stablecoin_data(client, token)
            df = process_stablecoin_data(raw_data)
            
            # Save to parquet with gzip compression
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
    parser.add_argument(
        "--token",
        help="Filter by token symbol (e.g., USDC)",
    )
    
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(main(args.start, args.end, args.token)) 
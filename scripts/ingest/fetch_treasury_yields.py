#!/usr/bin/env python3
"""Fetch Treasury yield data from FRED API.

This script fetches 3-month and 1-year Treasury bill yields from the FRED API
and saves them to a parquet file.

Example:
    $ python fetch_treasury_yields.py --start 2023-01-01 --end 2024-03-01
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from scripts.utils.fred_api import fetch_treasury_yields

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_START_DATE = "2018-01-01"
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "treasury_yields.parq"


def main(start_date: str = DEFAULT_START_DATE, end_date: str = DEFAULT_END_DATE) -> None:
    """Main function to fetch and save Treasury yield data.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch data
        yields = fetch_treasury_yields(start_date, end_date)
        
        # Calculate spread
        yields["spread"] = yields["DGS3"] - yields["DGS1"]
        
        # Save to parquet with gzip compression
        yields.to_parquet(
            OUTPUT_FILE,
            compression="gzip",
        )
        logger.info(f"Saved Treasury yields to {OUTPUT_FILE}")
        
    except Exception as e:
        logger.error(f"Failed to fetch Treasury yields: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Treasury yield data")
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
    main(args.start, args.end) 
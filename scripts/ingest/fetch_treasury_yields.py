#!/usr/bin/env python3
"""Fetch Treasury yield data from FRED API.

This script fetches Treasury yields from the FRED API and saves them to a parquet file.
It includes yields for 3-month, 1-year, 2-year, 5-year, 10-year, and 30-year Treasuries,
as well as common yield spreads (10Y-2Y, 10Y-3M, 2Y-3M).

Example:
    $ python fetch_treasury_yields.py --start 2023-01-01 --end 2024-03-01
"""

import argparse
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from scripts.utils.fred_api import fetch_treasury_yields, TREASURY_SERIES, YIELD_SPREADS

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


def add_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Add metadata to the DataFrame.

    Args:
        df: DataFrame with Treasury yields

    Returns:
        DataFrame with added metadata
    """
    # Add series descriptions
    for series_id, description in TREASURY_SERIES.items():
        if series_id in df.columns:
            df[series_id].attrs["description"] = description

    # Add spread descriptions
    for long_term, short_term, spread_name in YIELD_SPREADS:
        if spread_name in df.columns:
            df[spread_name].attrs["description"] = f"{TREASURY_SERIES[long_term]} - {TREASURY_SERIES[short_term]}"

    return df


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
        
        # Add metadata
        yields = add_metadata(yields)
        
        # Save to parquet with gzip compression
        yields.to_parquet(
            OUTPUT_FILE,
            compression="gzip",
        )
        logger.info(f"Saved Treasury yields to {OUTPUT_FILE}")
        
        # Print summary statistics
        logger.info("\nSummary statistics:")
        logger.info(f"Date range: {yields.index.min()} to {yields.index.max()}")
        logger.info(f"Number of observations: {len(yields)}")
        logger.info("\nMissing data percentage:")
        missing_pct = yields.isnull().mean()
        for col, pct in missing_pct.items():
            logger.info(f"  {col}: {pct:.1%}")
        
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
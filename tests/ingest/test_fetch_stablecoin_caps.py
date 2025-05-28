"""Unit tests for fetch_stablecoin_caps.py."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pandas as pd
import pytest
from scripts.ingest.fetch_stablecoin_caps import (
    fetch_stablecoin_data,
    process_stablecoin_data,
)

# Sample API response for testing
SAMPLE_RESPONSE = [
    {
        "symbol": "USDC",
        "name": "USD Coin",
        "chains": [
            {
                "chain": "Ethereum",
                "circulating": {"peggedUSD": 1000000000},
            },
            {
                "chain": "Solana",
                "circulating": {"peggedUSD": 500000000},
            },
        ],
    },
    {
        "symbol": "USDT",
        "name": "Tether",
        "chains": [
            {
                "chain": "Ethereum",
                "circulating": {"peggedUSD": 2000000000},
            },
        ],
    },
]


@pytest.mark.asyncio
async def test_fetch_stablecoin_data():
    """Test fetching stablecoin data from API."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.json.return_value = SAMPLE_RESPONSE
    mock_client.get.return_value = mock_response

    result = await fetch_stablecoin_data(mock_client)
    assert result == SAMPLE_RESPONSE
    mock_client.get.assert_called_once()


def test_process_stablecoin_data():
    """Test processing raw stablecoin data into DataFrame."""
    df = process_stablecoin_data(SAMPLE_RESPONSE)
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3  # 2 chains for USDC + 1 for USDT
    assert list(df.columns) == [
        "symbol",
        "name",
        "chain",
        "circulating_supply",
        "timestamp",
    ]
    assert df["symbol"].nunique() == 2
    assert df["chain"].nunique() == 2


@pytest.mark.asyncio
async def test_fetch_stablecoin_data_error():
    """Test error handling in fetch_stablecoin_data."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("API Error")

    with pytest.raises(httpx.HTTPError):
        await fetch_stablecoin_data(mock_client)


@pytest.mark.asyncio
async def test_fetch_stablecoin_data_with_token():
    """Test fetching data for specific token."""
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.json.return_value = [SAMPLE_RESPONSE[0]]  # Just USDC
    mock_client.get.return_value = mock_response

    result = await fetch_stablecoin_data(mock_client, token="USDC")
    assert len(result) == 1
    assert result[0]["symbol"] == "USDC"
    mock_client.get.assert_called_once() 
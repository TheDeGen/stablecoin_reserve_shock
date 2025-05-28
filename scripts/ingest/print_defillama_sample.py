#!/usr/bin/env python3
import httpx
import asyncio
import json

API_URL = "https://stablecoins.llama.fi/stablecoincharts/all"

async def main():
    async with httpx.AsyncClient() as client:
        resp = await client.get(API_URL)
        resp.raise_for_status()
        data = resp.json()
        print(json.dumps(data[:2], indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 
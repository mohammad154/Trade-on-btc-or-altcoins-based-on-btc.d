#!/usr/bin/env python3
"""
CoinGecko Bitcoin OHLC Data Fetcher

This script fetches Open, High, Low, Close (OHLC) data for Bitcoin from CoinGecko API
and displays the last 7 data points with formatted timestamps.

Note: The 'interval' parameter (hourly/daily) is a premium feature only available
for paid/pro plan subscribers. Demo API keys use automatic granularity:
- 1-2 days: 30 minute intervals
- 3-30 days: 4 hour intervals
- 31+ days: 4 day intervals

For hourly data, you need a paid plan and use: interval=hourly parameter
"""

import requests
import sys
from datetime import datetime

# Configurable parameters
COIN_ID = "bitcoin"
VS_CURRENCY = "usd"
# Valid values: 1, 7, 14, 30, 90, 180, 365 (1 day = 30-minute intervals)
DAYS = 1
API_KEY = "CG-fyY6p9PKBQAoyR214UCs6MEe"

# API configuration
BASE_URL = "https://api.coingecko.com/api/v3"
ENDPOINT = f"/coins/{COIN_ID}/ohlc"
HEADERS = {"x-cg-demo-api-key": API_KEY}


def fetch_ohlc_data():
    """
    Fetch OHLC data from CoinGecko API.

    Returns:
        list: List of OHLC data points or None if error occurs

    Raises:
        requests.exceptions.RequestException: For network-related errors
        ValueError: For JSON parsing errors or invalid response format
    """
    params = {
        "vs_currency": VS_CURRENCY,
        "days": DAYS,
    }

    try:
        # Debug: Show the constructed API request URL
        print(
            f"API Request URL: {BASE_URL}{ENDPOINT}?vs_currency={VS_CURRENCY}&days={DAYS}")

        response = requests.get(
            f"{BASE_URL}{ENDPOINT}",
            params=params,
            headers=HEADERS,
            timeout=30
        )

        # Check HTTP status code
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Validate response format
        if not isinstance(data, list):
            raise ValueError("Invalid response format: expected list")

        if not data:
            raise ValueError("No data returned from API")

        return data

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}", file=sys.stderr)
        return None
    except ValueError as e:
        print(f"Data parsing error: {e}", file=sys.stderr)
        return None


def process_ohlc_data(data):
    """
    Process OHLC data to extract last 7 entries and format timestamps.

    Args:
        data (list): Raw OHLC data from API

    Returns:
        list: Processed data with formatted timestamps
    """
    processed_data = []

    # Get last 7 entries (or fewer if not enough data)
    last_entries = data[-7:] if len(data) >= 7 else data

    for entry in last_entries:
        if len(entry) != 5:
            print(
                f"Warning: Invalid data format in entry: {entry}", file=sys.stderr)
            continue

        timestamp_ms, open_price, high_price, low_price, close_price = entry

        # Convert milliseconds to seconds for datetime
        timestamp_seconds = timestamp_ms / 1000
        formatted_time = datetime.fromtimestamp(
            timestamp_seconds).strftime('%Y-%m-%d %H:%M:%S')

        processed_data.append({
            'timestamp': formatted_time,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price
        })

    return processed_data


def display_ohlc_data(processed_data):
    """
    Display processed OHLC data in the required format.

    Args:
        processed_data (list): Processed OHLC data
    """
    if not processed_data:
        print("No data to display", file=sys.stderr)
        return

    print(
        f"\nLast {len(processed_data)} OHLC data points for {COIN_ID.upper()} ({VS_CURRENCY.upper()}):")
    print("-" * 80)

    for entry in processed_data:
        print(f"Timestamp: {entry['timestamp']}, "
              f"Open: {entry['open']:.2f}, "
              f"High: {entry['high']:.2f}, "
              f"Low: {entry['low']:.2f}, "
              f"Close: {entry['close']:.2f}")


def main():
    """Main function to orchestrate the OHLC data fetching and processing."""
    print(
        f"Fetching OHLC data for {COIN_ID.upper()} for the last {DAYS} days...")

    # Fetch data from API
    raw_data = fetch_ohlc_data()
    if raw_data is None:
        sys.exit(1)

    # Validate we have enough data points
    if len(raw_data) < 7:
        print(f"Warning: API returned only {len(raw_data)} data points (expected at least 7)",
              file=sys.stderr)

    # Process and display data
    processed_data = process_ohlc_data(raw_data)
    display_ohlc_data(processed_data)


if __name__ == "__main__":
    main()

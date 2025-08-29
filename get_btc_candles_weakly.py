import requests
import datetime
import sys


def fetch_btc_candles():
    """Fetch 7 latest hourly BTC/USDT candles from CoinStats API"""

    # API configuration - updated to new endpoint
    api_key = "5Bpyex/DLG78WDJBudkqicJGmCP+K1DqS6J7xth5Ybg="
    base_url = "https://openapiv1.coinstats.app"
    endpoint = "/coins/charts"

    # Request parameters - updated to match API documentation
    params = {
        "coinIds": "bitcoin",  # Note: parameter name is 'coinIds' not 'coinId'
        "period": "1w",        # Valid periods: all, 24h, 1w, 1m, 3m, 6m, 1y
        # 'limit' parameter is not mentioned in the documentation for this endpoint
        # 'currency' parameter is not mentioned in the documentation for this endpoint
    }

    # Headers with API key
    headers = {
        "X-API-KEY": api_key
    }

    try:
        # Make API request
        response = requests.get(
            f"{base_url}{endpoint}", params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()

        # Debug: Print the actual response structure
        print(f"DEBUG: Response type: {type(data)}")
        if isinstance(data, list) and len(data) > 0:
            print(
                f"DEBUG: First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")
        print(f"DEBUG: Full response preview: {str(data)[:200]}...")

        # Verify response structure based on API documentation
        if not isinstance(data, list) or len(data) == 0:
            print("Error: Invalid response structure - expected list of coin data")
            sys.exit(1)

        # Extract the chart data for Bitcoin
        btc_data = None
        for coin_data in data:
            if isinstance(coin_data, dict) and coin_data.get("coinId") == "bitcoin" and "chart" in coin_data:
                btc_data = coin_data
                break

        if not btc_data:
            print("Error: Bitcoin data not found in response")
            print(
                f"Available coin data: {[coin.get('coinId') for coin in data if isinstance(coin, dict)]}")
            sys.exit(1)

        candles = btc_data["chart"]

        # Use all available candles (removed 7-candle limitation)
        if len(candles) == 0:
            print("Error: No candles found in response")
            sys.exit(1)

        # Process and print each candle
        for candle in candles:
            # Candle format: [timestamp, USD_price, BTC_price, ETH_price]
            if len(candle) >= 4:
                timestamp = datetime.datetime.fromtimestamp(
                    candle[0], datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                price = candle[1]  # USD price
                # ETH price (value represents trading volume in ETH)
                volume = candle[3]

                print(f"{timestamp} | Price: {price} | Volume: {volume}")
            else:
                print(f"Warning: Invalid candle format: {candle}")

    except requests.exceptions.RequestException as e:
        print(f"HTTP Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"JSON Parse Error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Missing expected field in response: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fetch_btc_candles()

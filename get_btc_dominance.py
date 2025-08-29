import requests
import datetime
import sys


def fetch_btc_dominance():
    """Fetch Bitcoin dominance data from CoinStats API"""

    # API configuration
    api_key = "5Bpyex/DLG78WDJBudkqicJGmCP+K1DqS6J7xth5Ybg="
    base_url = "https://openapiv1.coinstats.app"
    endpoint = "/insights/btc-dominance"

    # Request parameters
    params = {
        "type": "24h",  # Valid periods: 24h, 1w, 1m, 3m, 6m, 1y, all
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
        if not isinstance(data, dict) or "data" not in data:
            print("Error: Invalid response structure - expected dict with 'data' key")
            print(f"Actual response type: {type(data)}")
            if isinstance(data, dict):
                print(f"Available keys: {list(data.keys())}")
            sys.exit(1)

        dominance_points = data["data"]

        if not isinstance(dominance_points, list) or len(dominance_points) == 0:
            print(
                "Error: Invalid dominance data structure - expected list of timestamp/percentage pairs")
            print(f"Actual dominance data type: {type(dominance_points)}")
            sys.exit(1)

        # Process and print each dominance point
        for point in dominance_points:
            # Point format: [timestamp, percentage]
            if len(point) >= 2:
                timestamp = datetime.datetime.fromtimestamp(
                    point[0], datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                percentage = point[1]  # BTC dominance percentage

                print(f"{timestamp} | Dominance: {percentage}%")
            else:
                print(f"Warning: Invalid data point format: {point}")

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
    fetch_btc_dominance()

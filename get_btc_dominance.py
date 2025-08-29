import requests
import datetime
import sys
from collections import defaultdict


def fetch_btc_dominance_ohlc():
    """Fetch and process Bitcoin dominance data into 1-hour OHLC"""

    # API configuration (remains the same)
    api_key = "5Bpyex/DLG78WDJBudkqicJGmCP+K1DqS6J7xth5Ybg="
    base_url = "https://openapiv1.coinstats.app"
    endpoint = "/insights/btc-dominance"
    params = {"type": "24h"}
    headers = {"X-API-KEY": api_key}

    try:
        # Make API request (remains the same)
        response = requests.get(
            f"{base_url}{endpoint}", params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        dominance_points = data["data"]

        if not isinstance(dominance_points, list) or len(dominance_points) == 0:
            print("Error: No dominance data points received from the API.")
            sys.exit(1)

        # --- NEW: Group data by hour ---
        # Use a defaultdict to easily append to lists
        hourly_data = defaultdict(list)
        for timestamp, percentage in dominance_points:
            # Convert Unix timestamp to a datetime object
            dt_object = datetime.datetime.fromtimestamp(
                timestamp, datetime.UTC)
            # Create a key by truncating the datetime to the hour
            hour_key = dt_object.replace(minute=0, second=0, microsecond=0)
            # Append the percentage to the corresponding hour's list
            hourly_data[hour_key].append(percentage)

        print("--- 1-Hour OHLC Bitcoin Dominance ---")

        # --- NEW: Calculate and print OHLC for each hour ---
        # Sort keys to ensure chronological order
        for hour in sorted(hourly_data.keys()):
            percentages = hourly_data[hour]

            # Calculate OHLC from the list of percentages for the hour
            open_price = percentages[0]      # First value of the hour
            high_price = max(percentages)    # Highest value in the hour
            low_price = min(percentages)     # Lowest value in the hour
            close_price = percentages[-1]    # Last value of the hour

            # Format the timestamp for clean output
            timestamp_str = hour.strftime('%Y-%m-%dT%H:%M:%SZ')

            print(
                f"{timestamp_str} | "
                f"Open: {open_price}%, High: {high_price}%, "
                f"Low: {low_price}%, Close: {close_price}%"
            )

    except requests.exceptions.RequestException as e:
        print(f"HTTP Error: {e}")
        sys.exit(1)
    except (ValueError, KeyError) as e:
        print(f"Data Processing Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fetch_btc_dominance_ohlc()

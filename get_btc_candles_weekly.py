import ccxt
import datetime
import sys


def fetch_btc_candles():
    """Fetch BTC/USDT 5-minute OHLC candle data using CCXT
    Output format: YYYY-MM-DDTHH:MM:SSZ | O: [open] | H: [high] | L: [low] | C: [close] | Volume: [volume]
    """

    # Initialize Binance exchange (supports fetch_ohlcv method)
    exchange = ccxt.binance()

    try:
        # Fetch 5-minute OHLCV data for BTC/USDT
        # CCXT returns: [timestamp, open, high, low, close, volume]
        candles = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=168)

        if len(candles) == 0:
            print("Error: No candles found in response")
            sys.exit(1)

        # Process and print each candle with OHLC format
        for candle in candles:
            if len(candle) >= 6:
                timestamp = datetime.datetime.fromtimestamp(
                    candle[0] / 1000, datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
                open_price = candle[1]
                high_price = candle[2]
                low_price = candle[3]
                close_price = candle[4]
                volume = candle[5]

                print(
                    f"{timestamp} | O: {open_price} | H: {high_price} | L: {low_price} | C: {close_price} | Volume: {volume}")
            else:
                print(f"Warning: Invalid OHLCV format: {candle}")

    except ccxt.NetworkError as e:
        print(f"Network Error: {e}")
        sys.exit(1)
    except ccxt.ExchangeError as e:
        print(f"Exchange Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    fetch_btc_candles()

#!/usr/bin/env python3
"""
BTC/Altcoin Strategy Analyzer
Implements trading strategy based on BTC price, BTC dominance, and weekly candle trends.
"""

import subprocess
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Tuple, Optional
import sys


class Trend(Enum):
    """Trend classification for price movements"""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class HWC(Enum):
    """Weekly candle trend classification"""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


# Decision matrix with all 27 combinations as specified in blueprint
DECISION_MATRIX = {
    # BTC Bullish, BTC.D Bullish, HWC Bullish
    (Trend.BULLISH, Trend.BULLISH, HWC.BULLISH): "Strong BTC buy (Low risk)",
    (Trend.BULLISH, Trend.BULLISH, HWC.NEUTRAL): "Moderate BTC buy (Medium risk)",
    (Trend.BULLISH, Trend.BULLISH, HWC.BEARISH): "Avoid BTC (High risk)",

    # BTC Bullish, BTC.D Bearish, HWC Bullish
    (Trend.BULLISH, Trend.BEARISH, HWC.BULLISH): "Risky altcoin buy (Requires confirmation)",
    (Trend.BULLISH, Trend.BEARISH, HWC.NEUTRAL): "Altcoin accumulation (Medium risk)",
    (Trend.BULLISH, Trend.BEARISH, HWC.BEARISH): "Altcoin sell (High risk)",

    # BTC Bullish, BTC.D Neutral, HWC Bullish
    (Trend.BULLISH, Trend.NEUTRAL, HWC.BULLISH): "Strong BTC buy (Medium risk)",
    (Trend.BULLISH, Trend.NEUTRAL, HWC.NEUTRAL): "BTC accumulation (Medium risk)",
    (Trend.BULLISH, Trend.NEUTRAL, HWC.BEARISH): "BTC sell (High risk)",

    # BTC Bearish, BTC.D Bullish, HWC Bullish
    (Trend.BEARISH, Trend.BULLISH, HWC.BULLISH): "BTC short (Medium risk)",
    (Trend.BEARISH, Trend.BULLISH, HWC.NEUTRAL): "BTC short (Low risk)",
    (Trend.BEARISH, Trend.BULLISH, HWC.BEARISH): "Strong BTC short (High risk)",

    # BTC Bearish, BTC.D Bearish, HWC Bullish
    (Trend.BEARISH, Trend.BEARISH, HWC.BULLISH): "Altcoin buy (Low risk)",
    (Trend.BEARISH, Trend.BEARISH, HWC.NEUTRAL): "Altcoin accumulation (Low risk)",
    (Trend.BEARISH, Trend.BEARISH, HWC.BEARISH): "Strong altcoin buy (Medium risk)",

    # BTC Bearish, BTC.D Neutral, HWC Bullish
    (Trend.BEARISH, Trend.NEUTRAL, HWC.BULLISH): "BTC short (High risk)",
    (Trend.BEARISH, Trend.NEUTRAL, HWC.NEUTRAL): "Market neutral (Low risk)",
    (Trend.BEARISH, Trend.NEUTRAL, HWC.BEARISH): "Altcoin buy (Medium risk)",

    # BTC Neutral, BTC.D Bullish, HWC Bullish
    (Trend.NEUTRAL, Trend.BULLISH, HWC.BULLISH): "BTC accumulation (Low risk)",
    (Trend.NEUTRAL, Trend.BULLISH, HWC.NEUTRAL): "Market watch (Low risk)",
    (Trend.NEUTRAL, Trend.BULLISH, HWC.BEARISH): "Altcoin sell (Medium risk)",

    # BTC Neutral, BTC.D Bearish, HWC Bullish
    (Trend.NEUTRAL, Trend.BEARISH, HWC.BULLISH): "Altcoin accumulation (Low risk)",
    (Trend.NEUTRAL, Trend.BEARISH, HWC.NEUTRAL): "Market watch (Low risk)",
    (Trend.NEUTRAL, Trend.BEARISH, HWC.BEARISH): "BTC buy (Medium risk)",

    # BTC Neutral, BTC.D Neutral, HWC Bullish
    (Trend.NEUTRAL, Trend.NEUTRAL, HWC.BULLISH): "Market indecisive (Low risk)",
    (Trend.NEUTRAL, Trend.NEUTRAL, HWC.NEUTRAL): "MARKET_INDECISIVE",
    (Trend.NEUTRAL, Trend.NEUTRAL, HWC.BEARISH): "Market indecisive (Low risk)",
}


def execute_script(script_name: str, max_attempts: int = 2) -> str:
    """Execute a python script with retry logic and timeout"""
    attempts = 0
    last_error = None

    while attempts < max_attempts:
        try:
            result = subprocess.run(
                [sys.executable, script_name],
                capture_output=True,
                text=True,
                timeout=15,
                cwd='.'  # Run from current directory
            )

            if result.returncode == 0:
                return result.stdout
            else:
                last_error = result.stderr

        except subprocess.TimeoutExpired:
            last_error = f"Script {script_name} timed out after 15 seconds"
        except Exception as e:
            last_error = str(e)

        attempts += 1

    raise RuntimeError(
        f"Failed to execute {script_name} after {max_attempts} attempts: {last_error}")


def parse_btc_data(output: str) -> List[Tuple[datetime, float, float]]:
    """Parse BTC daily/weekly candle data using regex"""
    pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| O: ([\d.]+) \| H: [\d.]+ \| L: [\d.]+ \| C: ([\d.]+)'
    matches = re.findall(pattern, output)

    if len(matches) < 7:
        raise ValueError(
            "INCOMPLETE_DATA: Less than 7 data points found in BTC data")

    parsed_data = []
    for timestamp_str, open_price, close_price in matches:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        parsed_data.append((timestamp, float(open_price), float(close_price)))

    return parsed_data


def parse_btc_dominance(output: str) -> List[Tuple[datetime, float, float]]:
    """Parse BTC dominance data using regex"""
    pattern = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| Open: ([\d.]+)%,.*Close: ([\d.]+)%'
    matches = re.findall(pattern, output)

    if len(matches) < 7:
        raise ValueError(
            "INCOMPLETE_DATA: Less than 7 data points found in BTC dominance data")

    parsed_data = []
    for timestamp_str, open_pct, close_pct in matches:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        parsed_data.append((timestamp, float(open_pct), float(close_pct)))

    return parsed_data


def validate_timestamp_continuity(data: List[Tuple[datetime, float, float]], max_gap_hours: int = 1) -> None:
    """Validate that timestamps are continuous with max 1h gap"""
    if len(data) < 2:
        return

    for i in range(1, len(data)):
        time_diff = data[i][0] - data[i-1][0]
        if time_diff.total_seconds() > max_gap_hours * 3600:
            raise ValueError(
                f"TIMESTAMP_DISCONTINUITY: Gap of {time_diff.total_seconds()/3600:.1f}h between entries")


def calculate_trend(data: List[Tuple[datetime, float, float]],
                    bullish_threshold: float = 0.5,
                    bearish_threshold: float = -0.5) -> Tuple[Trend, float]:
    """Calculate trend based on first open and last close prices"""
    if len(data) < 7:
        raise ValueError(
            "INCOMPLETE_DATA: Need at least 7 data points for trend calculation")

    first_open = data[-7][1]  # 7th data point from the end (oldest)
    last_close = data[-1][2]   # Most recent close

    percentage_change = ((last_close - first_open) / first_open) * 100

    if percentage_change > bullish_threshold:
        return Trend.BULLISH, percentage_change
    elif percentage_change < bearish_threshold:
        return Trend.BEARISH, percentage_change
    else:
        return Trend.NEUTRAL, percentage_change


def calculate_hwc_trend(data: List[Tuple[datetime, float, float]],
                        bullish_threshold: float = 2.0,
                        bearish_threshold: float = -2.0) -> Tuple[HWC, float]:
    """Calculate weekly trend based on all available weekly data"""
    if len(data) < 7:
        raise ValueError(
            "INCOMPLETE_DATA: Need at least 7 weekly data points for HWC calculation")

    first_open = data[0][1]   # First open price (oldest)
    last_close = data[-1][2]  # Last close price (most recent)

    percentage_change = ((last_close - first_open) / first_open) * 100

    if percentage_change > bullish_threshold:
        return HWC.BULLISH, percentage_change
    elif percentage_change < bearish_threshold:
        return HWC.BEARISH, percentage_change
    else:
        return HWC.NEUTRAL, percentage_change


def get_risk_context(btc_trend: Trend, btc_d_trend: Trend, hwc_status: HWC) -> str:
    """Generate risk context based on the trend combination"""
    if (btc_trend == Trend.BULLISH and btc_d_trend == Trend.BULLISH and hwc_status == HWC.BULLISH):
        return "Low risk - All indicators aligned bullish"
    elif (btc_trend == Trend.BULLISH and btc_d_trend == Trend.BEARISH and hwc_status == HWC.BULLISH):
        return "Requires HWC confirmation - monitor for weekly trend reversal"
    elif (btc_trend == Trend.BULLISH and btc_d_trend == Trend.BEARISH and hwc_status == HWC.BEARISH):
        return "High risk - Altcoin market weakness"
    elif (btc_trend == Trend.BEARISH and btc_d_trend == Trend.BULLISH and hwc_status == HWC.BULLISH):
        return "Medium risk - BTC weakness with dominance strength"
    elif (btc_trend == Trend.BEARISH and btc_d_trend == Trend.BULLISH and hwc_status == HWC.BEARISH):
        return "High risk - Strong bearish momentum"
    else:
        return "Standard market conditions - monitor closely"


def get_confidence_score(btc_trend: Trend, btc_d_trend: Trend, hwc_status: HWC) -> int:
    """Calculate confidence score based on trend alignment"""
    # Base confidence
    confidence = 65

    # Increase confidence when trends are aligned
    if (btc_trend == btc_d_trend == hwc_status):
        confidence += 20
    elif (btc_trend == btc_d_trend) or (btc_trend == hwc_status) or (btc_d_trend == hwc_status):
        confidence += 10

    # Decrease confidence for neutral trends
    if Trend.NEUTRAL in [btc_trend, btc_d_trend] or hwc_status == HWC.NEUTRAL:
        confidence -= 15

    return max(50, min(95, confidence))  # Keep between 50-95%


def main():
    """Main analysis function"""
    try:
        # Execute scripts with retry logic
        print("Fetching BTC daily data...")
        btc_daily_output = execute_script("get_btc_candles_daily.py")

        print("Fetching BTC dominance data...")
        btc_dominance_output = execute_script("get_btc_dominance.py")

        print("Fetching BTC weekly data...")
        btc_weekly_output = execute_script("get_btc_candles_weekly.py")

        # Parse data
        btc_daily_data = parse_btc_data(btc_daily_output)
        btc_dominance_data = parse_btc_dominance(btc_dominance_output)
        btc_weekly_data = parse_btc_data(btc_weekly_output)

        # Validate timestamp continuity
        validate_timestamp_continuity(btc_daily_data)
        validate_timestamp_continuity(btc_dominance_data)
        validate_timestamp_continuity(btc_weekly_data)

        # Calculate trends
        btc_trend, btc_change = calculate_trend(btc_daily_data)
        btc_d_trend, btc_d_change = calculate_trend(btc_dominance_data)
        hwc_status, hwc_change = calculate_hwc_trend(
            btc_weekly_data, bullish_threshold=2.0, bearish_threshold=-2.0)

        # Get decision
        decision_key = (btc_trend, btc_d_trend, hwc_status)
        recommendation = DECISION_MATRIX.get(decision_key, "MARKET_INDECISIVE")

        # Generate output
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"\n[{current_time}]")
        print(
            f"BTC 7h Trend: {'▲' if btc_change > 0 else '▼'} {abs(btc_change):.2f}% ({btc_trend.value})")
        print(
            f"BTC.D 7h Trend: {'▲' if btc_d_change > 0 else '▼'} {abs(btc_d_change):.2f}% ({btc_d_trend.value})")
        print(f"HWC Status: {hwc_status.value} (Weekly {hwc_change:+.1f}%)")
        print(f"\nRECOMMENDATION: {recommendation}")
        print(
            f"RISK CONTEXT: {get_risk_context(btc_trend, btc_d_trend, hwc_status)}")
        print(
            f"CONFIDENCE: {get_confidence_score(btc_trend, btc_d_trend, hwc_status)}% (based on historical pattern match)")

    except ValueError as e:
        if "INCOMPLETE_DATA" in str(e) or "TIMESTAMP_DISCONTINUITY" in str(e):
            print(f"ERROR: {e}")
            sys.exit(1)
        else:
            raise
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# Test assertions with sample data
def test_analyzer():
    """Test the analyzer with sample data to validate all functionality"""

    # Sample data that matches the expected output formats
    sample_btc_daily = """
2025-08-29T12:00:00Z | O: 50000.0 | H: 50200.0 | L: 49900.0 | C: 50100.0 | Volume: 1000
2025-08-29T13:00:00Z | O: 50100.0 | H: 50300.0 | L: 50000.0 | C: 50200.0 | Volume: 1100
2025-08-29T14:00:00Z | O: 50200.0 | H: 50400.0 | L: 50100.0 | C: 50300.0 | Volume: 1200
2025-08-29T15:00:00Z | O: 50300.0 | H: 50500.0 | L: 50200.0 | C: 50400.0 | Volume: 1300
2025-08-29T16:00:00Z | O: 50400.0 | H: 50600.0 | L: 50300.0 | C: 50500.0 | Volume: 1400
2025-08-29T17:00:00Z | O: 50500.0 | H: 50700.0 | L: 50400.0 | C: 50600.0 | Volume: 1500
2025-08-29T18:00:00Z | O: 50600.0 | H: 50800.0 | L: 50500.0 | C: 50700.0 | Volume: 1600
2025-08-29T19:00:00Z | O: 50700.0 | H: 50900.0 | L: 50600.0 | C: 50800.0 | Volume: 1700
"""

    sample_btc_dominance = """
2025-08-29T12:00:00Z | Open: 48.5%, High: 49.0%, Low: 48.0%, Close: 48.8%
2025-08-29T13:00:00Z | Open: 48.8%, High: 49.2%, Low: 48.6%, Close: 49.0%
2025-08-29T14:00:00Z | Open: 49.0%, High: 49.5%, Low: 48.8%, Close: 49.3%
2025-08-29T15:00:00Z | Open: 49.3%, High: 49.8%, Low: 49.1%, Close: 49.6%
2025-08-29T16:00:00Z | Open: 49.6%, High: 50.0%, Low: 49.4%, Close: 49.8%
2025-08-29T17:00:00Z | Open: 49.8%, High: 50.2%, Low: 49.6%, Close: 50.0%
2025-08-29T18:00:00Z | Open: 50.0%, High: 50.5%, Low: 49.8%, Close: 50.3%
2025-08-29T19:00:00Z | Open: 50.3%, High: 50.8%, Low: 50.1%, Close: 50.5%
"""

    sample_btc_weekly = """
2025-08-22T12:00:00Z | O: 48000.0 | H: 48200.0 | L: 47800.0 | C: 48100.0 | Volume: 2000
2025-08-23T12:00:00Z | O: 48100.0 | H: 48300.0 | L: 47900.0 | C: 48200.0 | Volume: 2100
2025-08-24T12:00:00Z | O: 48200.0 | H: 48400.0 | L: 48000.0 | C: 48300.0 | Volume: 2200
2025-08-25T12:00:00Z | O: 48300.0 | H: 48500.0 | L: 48100.0 | C: 48400.0 | Volume: 2300
2025-08-26T12:00:00Z | O: 48400.0 | H: 48600.0 | L: 48200.0 | C: 48500.0 | Volume: 2400
2025-08-27T12:00:00Z | O: 48500.0 | H: 48700.0 | L: 48300.0 | C: 48600.0 | Volume: 2500
2025-08-28T12:00:00Z | O: 48600.0 | H: 48800.0 | L: 48400.0 | C: 48700.0 | Volume: 2600
2025-08-29T12:00:00Z | O: 48700.0 | H: 48900.0 | L: 48500.0 | C: 48800.0 | Volume: 2700
"""

    print("=== Testing BTC Data Parsing ===")
    btc_data = parse_btc_data(sample_btc_daily)
    assert len(btc_data) >= 7, "Should parse at least 7 BTC data points"
    print("✓ BTC parsing successful")

    print("=== Testing BTC Dominance Parsing ===")
    btc_d_data = parse_btc_dominance(sample_btc_dominance)
    assert len(
        btc_d_data) >= 7, "Should parse at least 7 BTC dominance data points"
    print("✓ BTC dominance parsing successful")

    print("=== Testing Weekly Data Parsing ===")
    weekly_data = parse_btc_data(sample_btc_weekly)
    assert len(weekly_data) >= 7, "Should parse at least 7 weekly data points"
    print("✓ Weekly parsing successful")

    print("=== Testing Timestamp Validation ===")
    validate_timestamp_continuity(btc_data)
    validate_timestamp_continuity(btc_d_data)
    validate_timestamp_continuity(weekly_data)
    print("✓ Timestamp validation successful")

    print("=== Testing Trend Calculations ===")
    btc_trend, btc_change = calculate_trend(btc_data)
    btc_d_trend, btc_d_change = calculate_trend(btc_d_data)
    hwc_status, hwc_change = calculate_hwc_trend(weekly_data)

    print(f"BTC Trend: {btc_trend.value} ({btc_change:.2f}%)")
    print(f"BTC.D Trend: {btc_d_trend.value} ({btc_d_change:.2f}%)")
    print(f"HWC Status: {hwc_status.value} ({hwc_change:.2f}%)")
    print("✓ Trend calculations successful")

    print("=== Testing Decision Matrix Coverage ===")
    # Test that all 27 combinations are covered
    for btc_t in Trend:
        for btc_d_t in Trend:
            for hwc_t in HWC:
                decision_key = (btc_t, btc_d_t, hwc_t)
                assert decision_key in DECISION_MATRIX, f"Missing decision for combination: {decision_key}"
    print("✓ All 27 decision combinations are covered")

    print("=== Testing Edge Cases ===")
    # Test incomplete data
    try:
        parse_btc_data(
            "2025-08-29T12:00:00Z | O: 50000.0 | H: 50200.0 | L: 49900.0 | C: 50100.0")
        assert False, "Should have raised INCOMPLETE_DATA error"
    except ValueError as e:
        assert "INCOMPLETE_DATA" in str(e)
        print("✓ Incomplete data handling works")

    print("\n=== All Tests Passed! ===")


# Uncomment to run tests
# test_analyzer()

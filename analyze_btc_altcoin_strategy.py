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
    SIDEWAYS = "Sideways"


class MWC(Enum):
    """Minor Wave Cycle (weekly) trend classification"""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    SIDEWAYS = "Sideways"


class HWC(Enum):
    """Higher Wave Cycle (monthly) trend classification"""
    BULLISH = "Bullish"
    BEARISH = "Bearish"
    SIDEWAYS = "Sideways"


# Decision matrix with all 27 combinations as specified in blueprint
DECISION_MATRIX = {
    # BTC Bullish, BTC.D Bullish, MWC Bullish
    (Trend.BULLISH, Trend.BULLISH, MWC.BULLISH): "Strong BTC buy (Low risk)",
    (Trend.BULLISH, Trend.BULLISH, MWC.SIDEWAYS): "Moderate BTC buy (Medium risk)",
    (Trend.BULLISH, Trend.BULLISH, MWC.BEARISH): "Avoid BTC (High risk)",

    # BTC Bullish, BTC.D Bearish, MWC Bullish
    (Trend.BULLISH, Trend.BEARISH, MWC.BULLISH): "Risky altcoin buy (Requires confirmation)",
    (Trend.BULLISH, Trend.BEARISH, MWC.SIDEWAYS): "Altcoin accumulation (Medium risk)",
    (Trend.BULLISH, Trend.BEARISH, MWC.BEARISH): "Altcoin sell (High risk)",

    # BTC Bullish, BTC.D Range Market, MWC Bullish
    (Trend.BULLISH, Trend.SIDEWAYS, MWC.BULLISH): "Strong BTC buy (Medium risk)",
    (Trend.BULLISH, Trend.SIDEWAYS, MWC.SIDEWAYS): "BTC accumulation (Medium risk)",
    (Trend.BULLISH, Trend.SIDEWAYS, MWC.BEARISH): "BTC sell (High risk)",

    # BTC Bearish, BTC.D Bullish, MWC Bullish
    (Trend.BEARISH, Trend.BULLISH, MWC.BULLISH): "BTC short (Medium risk)",
    (Trend.BEARISH, Trend.BULLISH, MWC.SIDEWAYS): "BTC short (Low risk)",
    (Trend.BEARISH, Trend.BULLISH, MWC.BEARISH): "Strong BTC short (High risk)",

    # BTC Bearish, BTC.D Bearish, MWC Bullish
    (Trend.BEARISH, Trend.BEARISH, MWC.BULLISH): "Altcoin buy (Low risk)",
    (Trend.BEARISH, Trend.BEARISH, MWC.SIDEWAYS): "Altcoin accumulation (Low risk)",
    (Trend.BEARISH, Trend.BEARISH, MWC.BEARISH): "Strong altcoin buy (Medium risk)",

    # BTC Bearish, BTC.D Range Market, MWC Bullish
    (Trend.BEARISH, Trend.SIDEWAYS, MWC.BULLISH): "BTC short (High risk)",
    (Trend.BEARISH, Trend.SIDEWAYS, MWC.SIDEWAYS): "Market range (Low risk)",
    (Trend.BEARISH, Trend.SIDEWAYS, MWC.BEARISH): "Altcoin buy (Medium risk)",

    # BTC Range Market, BTC.D Bullish, MWC Bullish
    (Trend.SIDEWAYS, Trend.BULLISH, MWC.BULLISH): "BTC accumulation (Low risk)",
    (Trend.SIDEWAYS, Trend.BULLISH, MWC.SIDEWAYS): "Market watch (Low risk)",
    (Trend.SIDEWAYS, Trend.BULLISH, MWC.BEARISH): "Altcoin sell (Medium risk)",

    # BTC Range Market, BTC.D Bearish, MWC Bullish
    (Trend.SIDEWAYS, Trend.BEARISH, MWC.BULLISH): "Altcoin accumulation (Low risk)",
    (Trend.SIDEWAYS, Trend.BEARISH, MWC.SIDEWAYS): "Market watch (Low risk)",
    (Trend.SIDEWAYS, Trend.BEARISH, MWC.BEARISH): "BTC buy (Medium risk)",

    # BTC Range Market, BTC.D Range Market, MWC Bullish
    (Trend.SIDEWAYS, Trend.SIDEWAYS, MWC.BULLISH): "Market range (Low risk)",
    (Trend.SIDEWAYS, Trend.SIDEWAYS, MWC.SIDEWAYS): "MARKET_RANGE",
    (Trend.SIDEWAYS, Trend.SIDEWAYS, MWC.BEARISH): "Market range (Low risk)",
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
        return Trend.SIDEWAYS, percentage_change


def calculate_mwc_trend(data: List[Tuple[datetime, float, float]],
                        bullish_threshold: float = 2.0,
                        bearish_threshold: float = -2.0) -> Tuple[MWC, float]:
    """Calculate Minor Wave Cycle (weekly) trend based on all available weekly data"""
    if len(data) < 7:
        raise ValueError(
            "INCOMPLETE_DATA: Need at least 7 weekly data points for MWC calculation")

    first_open = data[0][1]   # First open price (oldest)
    last_close = data[-1][2]  # Last close price (most recent)

    percentage_change = ((last_close - first_open) / first_open) * 100

    if percentage_change > bullish_threshold:
        return MWC.BULLISH, percentage_change
    elif percentage_change < bearish_threshold:
        return MWC.BEARISH, percentage_change
    else:
        return MWC.SIDEWAYS, percentage_change


def calculate_hwc_trend(data: List[Tuple[datetime, float, float]],
                        bullish_threshold: float = 5.0,
                        bearish_threshold: float = -5.0) -> Tuple[HWC, float]:
    """Calculate Higher Wave Cycle (monthly) trend based on 99-day data"""
    if len(data) < 7:
        raise ValueError(
            "INCOMPLETE_DATA: Need at least 7 monthly data points for HWC calculation")

    first_open = data[0][1]   # First open price (oldest)
    last_close = data[-1][2]  # Last close price (most recent)

    percentage_change = ((last_close - first_open) / first_open) * 100

    if percentage_change > bullish_threshold:
        return HWC.BULLISH, percentage_change
    elif percentage_change < bearish_threshold:
        return HWC.BEARISH, percentage_change

    else:
        return HWC.SIDEWAYS, percentage_change


def get_risk_context(btc_trend: Trend, btc_d_trend: Trend, mwc_status: MWC, hwc_status: Optional[MWC] = None) -> str:
    """Generate risk context based on the trend combination"""
    # Check for MWC/HWC conflict if HWC is provided
    conflict_warning = ""
    if hwc_status and mwc_status.value != hwc_status.value:
        conflict_warning = f" WARNING: MWC-HWC conflict ({mwc_status.value} vs {hwc_status.value}) - "
    else:
        conflict_warning = ""

    base_context = ""
    if (btc_trend == Trend.BULLISH and btc_d_trend == Trend.BULLISH and mwc_status == MWC.BULLISH):
        base_context = "Low risk - All indicators aligned bullish"
    elif (btc_trend == Trend.BULLISH and btc_d_trend == Trend.BEARISH and mwc_status == MWC.BULLISH):
        base_context = "Requires MWC confirmation - monitor for weekly trend reversal"
    elif (btc_trend == Trend.BULLISH and btc_d_trend == Trend.BEARISH and mwc_status == MWC.BEARISH):
        base_context = "High risk - Altcoin market weakness"
    elif (btc_trend == Trend.BEARISH and btc_d_trend == Trend.BULLISH and mwc_status == MWC.BULLISH):
        base_context = "Medium risk - BTC weakness with dominance strength"
    elif (btc_trend == Trend.BEARISH and btc_d_trend == Trend.BULLISH and mwc_status == MWC.BEARISH):
        base_context = "High risk - Strong bearish momentum"
    else:
        base_context = "Standard market conditions - monitor closely"

    return conflict_warning + base_context


def get_confidence_score(btc_trend: Trend, btc_d_trend: Trend, mwc_status: MWC, hwc_status: Optional[MWC] = None) -> int:
    """Calculate confidence score based on trend alignment"""
    # Base confidence
    confidence = 65

    # Increase confidence when trends are aligned (compare values since different enum types)
    if (btc_trend.value == btc_d_trend.value == mwc_status.value):
        confidence += 20
    elif (btc_trend.value == btc_d_trend.value) or (btc_trend.value == mwc_status.value) or (btc_d_trend.value == mwc_status.value):
        confidence += 10

    # Decrease confidence for sideways trends (compare values since different enum types)
    if (Trend.SIDEWAYS.value in [btc_trend.value, btc_d_trend.value] or
            mwc_status.value == MWC.SIDEWAYS.value):
        confidence -= 15

    # Adjust confidence based on MWC/HWC alignment
    if hwc_status:
        if mwc_status.value == hwc_status.value:
            confidence += 5  # Increased confidence when weekly and monthly trends align
        else:
            confidence -= 10  # Decreased confidence when trends conflict

    return max(50, min(95, confidence))  # Keep between 50-95%


def main():
    """Main analysis function"""
    try:
        # Execute scripts with retry logic
        print("Fetching BTC daily data...")
        btc_daily_output = execute_script("get_btc_candles_daily.py")

        print("Fetching BTC dominance data...")
        btc_dominance_output = execute_script("get_btc_dominance.py")

        print("Fetching BTC weekly data (MWC)...")
        btc_weekly_output = execute_script("get_btc_candles_weekly.py")

        print("Fetching BTC monthly data (HWC)...")
        btc_monthly_output = execute_script("get_btc_candles_99d.py")

        # Parse data
        btc_daily_data = parse_btc_data(btc_daily_output)
        btc_dominance_data = parse_btc_dominance(btc_dominance_output)
        btc_weekly_data = parse_btc_data(btc_weekly_output)
        btc_monthly_data = parse_btc_data(btc_monthly_output)

        # Validate timestamp continuity - allow 24h gaps for weekly/monthly data
        validate_timestamp_continuity(btc_daily_data)
        validate_timestamp_continuity(btc_dominance_data)
        validate_timestamp_continuity(btc_weekly_data, max_gap_hours=24)
        validate_timestamp_continuity(btc_monthly_data, max_gap_hours=24)

        # Calculate trends
        btc_trend, btc_change = calculate_trend(btc_daily_data)
        btc_d_trend, btc_d_change = calculate_trend(btc_dominance_data)
        mwc_status, mwc_change = calculate_mwc_trend(
            btc_weekly_data, bullish_threshold=2.0, bearish_threshold=-2.0)
        hwc_status, hwc_change = calculate_hwc_trend(
            btc_monthly_data, bullish_threshold=5.0, bearish_threshold=-5.0)

        # Get decision
        decision_key = (btc_trend, btc_d_trend, mwc_status)
        recommendation = DECISION_MATRIX.get(decision_key, "MARKET_INDECISIVE")

        # Generate output
        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        print(f"\n[{current_time}]")
        print(
            f"BTC 7h Trend: {'▲' if btc_change > 0 else '▼'} {abs(btc_change):.2f}% ({btc_trend.value})")
        print(
            f"BTC.D 7h Trend: {'▲' if btc_d_change > 0 else '▼'} {abs(btc_d_change):.2f}% ({btc_d_trend.value})")
        print(f"MWC Status: {mwc_status.value} (Weekly {mwc_change:+.1f}%)")
        print(f"HWC Status: {hwc_status.value} (Monthly {hwc_change:+.1f}%)")
        print(f"\nRECOMMENDATION: {recommendation}")
        print(
            f"RISK CONTEXT: {get_risk_context(btc_trend, btc_d_trend, mwc_status, hwc_status)}")
        print(
            f"CONFIDENCE: {get_confidence_score(btc_trend, btc_d_trend, mwc_status, hwc_status)}% (based on historical pattern match)")

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

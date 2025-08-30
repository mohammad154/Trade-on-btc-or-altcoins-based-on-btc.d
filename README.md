# BTC/Altcoin Trading Strategy Analyzer

A sophisticated cryptocurrency trading strategy analyzer that implements a multi-timeframe approach using Bitcoin price data, Bitcoin dominance, and market cycle analysis to generate trading recommendations.

## 🎯 Project Overview

This project implements a comprehensive trading strategy based on three key factors:

1. **BTC Price Trend** - 7-hour trend analysis
2. **BTC Dominance Trend** - 7-hour trend of Bitcoin's market dominance
3. **Market Wave Cycles** - Weekly (MWC) and Monthly (HWC) trend analysis

The strategy uses a decision matrix with 27 possible combinations to provide specific trading recommendations for both Bitcoin and altcoins.

## 📊 Strategy Logic

### Trend Classifications

- **BTC Trend**: Bullish, Bearish, or Sideways (based on 7-hour price change)
- **BTC Dominance Trend**: Bullish, Bearish, or Sideways (based on 7-hour dominance change)
- **Minor Wave Cycle (MWC)**: Weekly trend analysis
- **Higher Wave Cycle (HWC)**: Monthly trend analysis (optional confirmation)

### Decision Matrix

The system uses a comprehensive decision matrix with 27 combinations:

- **Strong BTC buy** when BTC bullish, BTC.D bullish, MWC bullish
- **Altcoin opportunities** when BTC bearish, BTC.D bearish, MWC bullish
- **Risk management** with specific recommendations for each market condition

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd Trade-on-btc-or-altcoins-based-on-btc.d
   ```

2. **Create virtual environment** (optional but recommended)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with your API key:
   ```env
   API_KEY=your_api_key_here
   ```

## 📁 Project Structure

```
Trade-on-btc-or-altcoins-based-on-btc.d/
├── analyze_btc_altcoin_strategy.py  # Main analysis script
├── get_btc_candles_daily.py        # Fetch BTC daily/hourly data
├── get_btc_candles_weekly.py       # Fetch BTC weekly data (MWC)
├── get_btc_candles_99d.py          # Fetch BTC 99-day data (HWC)
├── get_btc_dominance.py            # Fetch BTC dominance data
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables
├── .gitignore                     # Git ignore file
└── README.md                      # This file
```

## 🔧 Dependencies

- **ccxt** - [Cryptocurrency exchange API library](https://docs.ccxt.com/#/)
- **requests** - HTTP requests for API calls
- **python-dotenv** - Environment variable management

## 🎮 Usage

### Run the Complete Analysis

```bash
python analyze_btc_altcoin_strategy.py
```

### Run Individual Components

```bash
# BTC Price Data
python get_btc_candles_daily.py    # 24 hours of hourly data
python get_btc_candles_weekly.py   # 168 hours (7 days) of hourly data
python get_btc_candles_99d.py      # 99 days of daily data

# BTC Dominance
python get_btc_dominance.py        # 24 hours of BTC dominance data
```

## 📈 Output Format

The main analysis script provides:

- **Current timestamp** in ISO format
- **BTC 7h Trend** with percentage change and direction (▲/▼ arrows)
- **BTC.D 7h Trend** with percentage change and direction (▲/▼ arrows)
- **MWC Status** (Weekly trend with percentage change)
- **HWC Status** (Monthly trend with percentage change)
- **Trading Recommendation** based on decision matrix
- **Risk Context** analysis including MWC-HWC conflict detection
- **Confidence Score** (50-95%) based on historical pattern match

### Example Output

```
[2025-08-30T22:08:39Z]
BTC 7h Trend: ▼ 0.34% (Sideways)
BTC.D 7h Trend: ▲ 0.02% (Sideways)
MWC Status: Bearish (Weekly -5.9%)
HWC Status: Sideways (Monthly +1.1%)

RECOMMENDATION: Market range (Low risk)
RISK CONTEXT: WARNING: MWC-HWC conflict (Bearish vs Sideways) - Standard market conditions - monitor closely
CONFIDENCE: 50% (based on historical pattern match)
```

The system automatically detects conflicts between weekly and monthly trends and provides appropriate risk context warnings.

## ⚙️ Configuration

### Environment Variables

- `API_KEY`: Required for BTC dominance data from [Coinstats API](https://openapi.coinstats.app/login/)

### Trend Thresholds

- **BTC/BTC.D Trends**: ±0.5% for 7-hour changes
- **MWC (Weekly)**: ±2.0% threshold
- **HWC (Monthly)**: ±5.0% threshold

## 🔄 Data Sources

- **Price Data**: Binance Exchange via CCXT library
- **Dominance Data**: Coinstats.app API (requires API key)
- **Timeframes**: Multiple timeframes for comprehensive analysis

## 🛡️ Risk Management

The system includes built-in risk management:

- **Data validation** with timestamp continuity checks
- **Confidence scoring** based on trend alignment
- **Risk context analysis** for each market condition
- **Error handling** for incomplete or inconsistent data

## 📋 Decision Matrix Examples

| BTC Trend | BTC.D Trend | MWC Trend | Recommendation                            |
| --------- | ----------- | --------- | ----------------------------------------- |
| Bullish   | Bullish     | Bullish   | Strong BTC buy (Low risk)                 |
| Bullish   | Bearish     | Bullish   | Risky altcoin buy (Requires confirmation) |
| Bearish   | Bearish     | Bullish   | Altcoin buy (Low risk)                    |
| Sideways  | Sideways    | Bullish   | Market range (Low risk)                   |
| Sideways  | Bearish     | Bullish   | Altcoin accumulation (Low risk)           |
| Bearish   | Bullish     | Bullish   | BTC short (Medium risk)                   |

_Note: The complete decision matrix contains 27 combinations, with recommendations tailored to each market condition including risk levels._

## 🚨 Error Handling

The system handles various error conditions:

- **INCOMPLETE_DATA**: When insufficient data points are available
- **TIMESTAMP_DISCONTINUITY**: When data gaps exceed thresholds
- **API errors**: Network and exchange-specific errors with retry logic

## 📊 Performance Metrics

- **Confidence Score**: 50-95% based on trend alignment
- **Risk Assessment**: Low/Medium/High risk classifications
- **Trend Alignment**: MWC-HWC conflict detection

## 🔮 Future Enhancements

Potential improvements:

- Real-time data streaming integration
- Additional technical indicators
- Backtesting framework
- Portfolio management features
- Alert system integration
- Web dashboard interface

## 📝 License

This project is for educational and research purposes. Use at your own risk for trading decisions.

## ⚠️ Disclaimer

**Trading involves significant risk of loss.** This software is provided for educational purposes only and should not be considered financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

---

**Note**: Ensure you have proper API access and comply with the terms of service for all data providers used in this project.

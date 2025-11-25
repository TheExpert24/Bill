# Advanced Hedge Fund Algorithm

## Overview

This is a sophisticated, institutional-style hedge fund algorithm that implements modern alpha signal generation using public financial data. The algorithm removes the dependency on fixed S&P 500 lists and dynamically selects the most profitable opportunities from a large, multi-factor screened universe.

## Key Features

### 🏦 **Institutional Architecture**
- Multi-factor signal generation (momentum, value, quality, volatility)
- Price-action predictors with trend-following indicators
- Cross-asset relationships and statistical arbitrage
- News sentiment analysis via NewsAPI integration
- Signal aggregation with normalization and historical weighting
- Volatility targeting and risk parity position sizing

### 📊 **Dynamic Stock Universe**
- **No fixed S&P 500 list** - algorithm searches for the best opportunities
- Multi-screen universe generation:
  - Large cap liquidity screening
  - High momentum identification
  - Value stock selection
  - Growth stock analysis
- Automatic filtering by market cap, volume, and data quality

### 🎯 **Alpha Signal Generation**
- **Factor Signals**: Value (P/E, P/B, dividend yield), Quality (ROE, ROA, debt ratios)
- **Price Action**: Trend strength, realized volatility, rolling skew, Bollinger Band positioning
- **Sentiment Analysis**: NewsAPI integration with NLP sentiment scoring
- **Statistical Arbitrage**: Cross-asset correlation and spread analysis

### 💰 **Advanced Risk Management**
- Volatility targeting (15% annual target)
- Risk parity position sizing
- Maximum 5% allocation per position
- Correlation-based diversification
- Signal quality filtering

## Files Structure

```
advanced_hedge_fund_engine.py    # Main algorithm engine
advanced_main.py                 # Standalone execution script
backtesting_engine.py            # Backtesting and optimization framework
demo_advanced_hedge_fund.py      # Demonstration script
test_advanced_algorithm.py       # Component testing script
config.py                        # Configuration parameters
```

## Quick Start

### 1. Test the Algorithm
```bash
python3 test_advanced_algorithm.py
```
This runs a quick test to verify all components work correctly.

### 2. Run Full Algorithm
```bash
python3 advanced_main.py
```
This executes the complete algorithm on a dynamic universe of ~300 stocks.

### 3. Run Demo
```bash
python3 demo_advanced_hedge_fund.py
```
This demonstrates the algorithm capabilities with sample outputs.

## Configuration

The algorithm is configured in `config.py` under `ADVANCED_CONFIG`:

```python
ADVANCED_CONFIG = {
    # Universe and positioning
    'universe_size': 300,          # Dynamic stock universe size
    'max_positions': 25,           # Maximum positions in portfolio
    
    # Risk management
    'target_volatility': 0.15,     # 15% annual volatility target
    'correlation_threshold': 0.7,  # Maximum correlation between positions
    
    # Signal weights (must sum to 1.0)
    'signal_weights': {
        'momentum_score': 0.25,    # Price momentum signals
        'value_score': 0.20,       # Value factor signals
        'quality_score': 0.20,     # Quality factor signals
        'volatility_score': 0.15,  # Volatility regime signals
        'sentiment_score': 0.10,   # News sentiment signals
        'stat_arb_score': 0.10     # Statistical arbitrage signals
    },
    
    # Position sizing
    'max_position_size': 0.05,     # 5% max per position
    'min_signal_quality': 0.3,     # Minimum signal confidence
    
    # Liquidity filters
    'liquidity_filter': {
        'min_volume': 100000,      # Minimum average volume
        'min_market_cap': 1e9      # $1B minimum market cap
    }
}
```

## Algorithm Pipeline

### 1. **Dynamic Universe Generation**
```
Major Stocks → Momentum Screening → Value Screening → Growth Screening
     ↓
Combined Universe (300 stocks)
```

### 2. **Signal Computation**
For each stock in the universe:
```
Price Data + Fundamentals → Factor Analysis → Price Action → Sentiment
                                     ↓              ↓          ↓
                              Value/Quality    Trend/Vol   News Score
```

### 3. **Signal Aggregation**
```
Individual Signals → Normalization → Weighted Combination → Quality Assessment
                                      ↓
                              Composite Alpha Score
```

### 4. **Portfolio Construction**
```
Qualified Signals → Risk Sizing → Correlation Check → Final Portfolio
                          ↓              ↓
                   Vol-adjusted     Diversification
```

## Signal Breakdown

### Factor Signals
- **Value Score**: P/E ratio, P/B ratio, dividend yield
- **Quality Score**: ROE, ROA, debt ratios, Sharpe ratio
- **Volatility Score**: Current volatility regime (low/normal/high)
- **Momentum Score**: Multi-timeframe price momentum

### Price Action Signals
- **Trend Strength**: Price above moving averages
- **Realized Volatility**: 20-day rolling volatility (annualized)
- **Rolling Skew**: Distribution asymmetry
- **Bollinger Band Position**: Mean reversion signals

### Sentiment Signals
- **News Sentiment**: NLP analysis of recent headlines
- **Sentiment Momentum**: Change in sentiment over time
- **Sentiment Strength**: Consistency of sentiment signals

## Backtesting Framework

The included backtesting engine (`backtesting_engine.py`) provides:

- **Historical Performance**: Test strategy on past data
- **Parameter Optimization**: Grid search for optimal settings
- **Risk Metrics**: Sharpe ratio, maximum drawdown, win rate
- **Benchmark Comparison**: Performance vs market indices

### Running Backtests
```python
from backtesting_engine import BacktestEngine
from datetime import datetime, timedelta

# Define backtest period
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

# Initialize backtest engine
backtest = BacktestEngine(start_date, end_date, initial_capital=100000)

# Run backtest
results = backtest.run_backtest(stock_universe, rebalance_frequency='M')
```

## Output Reports

The algorithm generates comprehensive reports including:

### Portfolio Recommendations
- Ranked position recommendations with shares and allocation
- Signal scores and quality metrics for each position
- Factor breakdown analysis for top positions

### Risk Analysis
- Portfolio-level risk metrics
- Correlation analysis between positions
- Volatility targeting effectiveness

### Statistical Arbitrage
- Identified pairs trading opportunities
- Correlation matrices
- Spread analysis with Z-scores

## Advantages Over Traditional Systems

### ✅ **No Fixed Universe**
- Searches across entire market for opportunities
- Dynamic adaptation to market conditions
- No bias toward specific sectors or indices

### ✅ **Institutional-Grade Signals**
- Multi-factor risk model
- Sophisticated signal aggregation
- Professional-grade risk management

### ✅ **Real-Time Adaptation**
- News sentiment integration
- Volatility regime detection
- Dynamic position sizing

### ✅ **Comprehensive Analysis**
- Cross-asset relationships
- Statistical arbitrage opportunities
- Factor-based stock selection

## Requirements

- Python 3.7+
- yfinance (stock data)
- NewsAPI key (for sentiment analysis)
- pandas, numpy, scipy, scikit-learn
- nltk (for sentiment analysis)

## Performance Expectations

Based on the institutional architecture design:
- **Target Return**: 15-25% annually (market dependent)
- **Target Volatility**: 15% (lower than typical equity portfolios)
- **Sharpe Ratio Target**: >1.0 (risk-adjusted performance focus)
- **Maximum Drawdown**: <20% (controlled risk exposure)

## Limitations

- Uses public data only (no proprietary datasets)
- No access to high-frequency tick data
- Limited by NewsAPI rate limits for sentiment
- Backtested performance may differ from live trading

## Support

For questions or improvements, the algorithm is designed to be:
- **Extensible**: Easy to add new signals or factors
- **Configurable**: All parameters adjustable via config
- **Testable**: Comprehensive test suite included

---

**Disclaimer**: This algorithm is for educational and research purposes. Past performance does not guarantee future results. Always conduct your own research and consider consulting with financial professionals before making investment decisions.
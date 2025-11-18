# Configuration settings for the market analysis engine

# Data ingestion
DATA_PERIOD = '1y'  # Period for historical data
NEWS_PAGE_SIZE = 10

# Indicators
SMA_SHORT_WINDOW = 20
SMA_LONG_WINDOW = 50
RSI_WINDOW = 14
BB_WINDOW = 20
BB_NUM_STD = 2
MOMENTUM_PERIOD = 10
VOLATILITY_WINDOW = 20
SENTIMENT_WINDOW = 5

# Rules
DEFAULT_RULES = [
    'bullish_crossover',
    'oversold_rsi',
    'low_pe_ratio',
    'positive_sentiment_shift',
    'overbought_rsi',
    'price_above_upper_band'
]

# Scoring
CRITERIA_WEIGHTS = {
    'bullish_crossover': 2.0,
    'oversold_rsi': 1.5,
    'low_pe_ratio': 1.0,
    'positive_sentiment_shift': 1.0,
    'overbought_rsi': -2.0,
    'price_above_upper_band': -1.5,
    'high_sharpe_ratio': 2.5,
    'attractive_sortino': 2.0,
    'low_value_at_risk': 1.5,
    'strong_momentum': 1.8,
    'reasonable_volatility': 1.2
}

# Position sizing
TOTAL_CAPITAL = 10000  # Example capital
RISK_TOLERANCE = 0.02  # 2%
MAX_ALLOCATION_PER_ASSET = 0.1  # 10%
DIVERSIFICATION_FACTOR = 0.5

# Output
OUTPUT_FORMAT = 'text'  # 'text', 'json', 'csv'

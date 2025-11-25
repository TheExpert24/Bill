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

# Advanced Hedge Fund Configuration
TOTAL_CAPITAL = 100000  # Increased capital for better diversification
RISK_TOLERANCE = 0.02 
MAX_ALLOCATION_PER_ASSET = 0.05  # Reduced for better diversification
DIVERSIFICATION_FACTOR = 0.5

# Advanced Algorithm Parameters - PROFIT MAXIMIZATION FOCUS
ADVANCED_CONFIG = {
    # Engine parameters - AGGRESSIVE for higher returns
    'universe_size': 500,  # Larger universe for more opportunities
    'max_positions': 30,   # More positions for diversification with profit focus
    'target_volatility': 0.20,  # Higher volatility tolerance for higher returns
    'correlation_threshold': 0.8,  # Looser correlation limits for more opportunities
    
    # Signal weights - PROFIT MAXIMIZED (momentum heavy)
    'signal_weights': {
        'momentum_score': 0.40,   # Increased - strongest predictor of returns
        'value_score': 0.15,      # Reduced - value can be slow
        'quality_score': 0.20,    # Maintained - important for risk management
        'volatility_score': 0.10, # Reduced - focus on returns over safety
        'sentiment_score': 0.10,  # Maintained - news can drive quick gains
        'stat_arb_score': 0.05    # Reduced - slower profit realization
    },
    
    # Risk management - MORE AGGRESSIVE
    'max_position_size': 0.08,   # 8% max per position (higher conviction)
    'min_signal_quality': 0.2,   # Lower threshold to capture more opportunities
    'signal_threshold': -0.1,    # Allow slightly negative signals if other factors strong
    
    # Universe generation - LOWER THRESHOLDS for more stocks
    'liquidity_filter': {
        'min_volume': 50000,     # Lower volume requirement
        'min_market_cap': 5e8    # $500M minimum (include more growth stocks)
    }
}

OUTPUT_FORMAT = 'text' 

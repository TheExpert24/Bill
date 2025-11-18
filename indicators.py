import pandas as pd
import numpy as np

def simple_moving_average(data, window=20):
    """Calculate Simple Moving Average."""
    return data.rolling(window=window).mean()

def exponential_moving_average(data, window=20):
    """Calculate Exponential Moving Average."""
    return data.ewm(span=window).mean()

def relative_strength_index(data, window=14):
    """Calculate RSI."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def bollinger_bands(data, window=20, num_std=2):
    """Calculate Bollinger Bands."""
    sma = data.rolling(window=window).mean()
    std = data.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, lower_band

def price_momentum_ratio(data, period=10):
    """Calculate price momentum ratio."""
    return (data - data.shift(period)) / data.shift(period)

def volatility(data, window=20):
    """Calculate rolling volatility (standard deviation)."""
    return data.rolling(window=window).std()

def earnings_flag(pe_ratio, threshold=15):
    """Flag for earnings-driven events based on P/E ratio."""
    return 1 if pe_ratio and pe_ratio < threshold else 0

def sentiment_shift_score(sentiment_scores, window=5):
    """Calculate sentiment shift score as recent average minus historical."""
    if len(sentiment_scores) < window * 2:
        return 0
    recent = np.mean(sentiment_scores[-window:])
    historical = np.mean(sentiment_scores[:-window])
    return recent - historical

def sharpe_ratio(data, risk_free_rate=0.00008):  # Daily risk free ~2%/252
    """Calculate Sharpe ratio."""
    returns = data.pct_change().dropna()
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    return excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

def sortino_ratio(data, risk_free_rate=0.00008):
    """Calculate Sortino ratio (downside deviation)."""
    returns = data.pct_change().dropna()
    if len(returns) < 2:
        return 0
    excess_returns = returns - risk_free_rate
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std() if len(downside_returns) > 0 else 0.001
    return excess_returns.mean() / downside_std

def value_at_risk(data, confidence=0.95):
    """Calculate Value at Risk."""
    returns = data.pct_change().dropna()
    if len(returns) < 10:
        return 0
    return np.percentile(returns, (1 - confidence) * 100)

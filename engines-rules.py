class RuleEngine:
    def __init__(self, rules=None):
        self.rules = rules or []

    def add_rule(self, rule_func):
        self.rules.append(rule_func)

    def evaluate(self, signals, fundamentals=None):
        """Evaluate all rules against signals and fundamentals."""
        results = {}
        for rule in self.rules:
            try:
                results[rule.__name__] = rule(signals, fundamentals)
            except Exception as e:
                results[rule.__name__] = False  # Default to False on error
        return results

# Example rule functions
def bullish_crossover(signals, fundamentals=None):
    """SMA 20 crosses above SMA 50."""
    sma_20 = signals.get('sma_20')
    sma_50 = signals.get('sma_50')
    if sma_20 is not None and sma_50 is not None:
        return sma_20.iloc[-1] > sma_50.iloc[-1] and sma_20.iloc[-2] <= sma_50.iloc[-2]
    return False

def oversold_rsi(signals, fundamentals=None):
    """RSI below 30."""
    rsi = signals.get('rsi')
    if rsi is not None:
        return rsi.iloc[-1] < 30
    return False

def overbought_rsi(signals, fundamentals=None):
    """RSI above 70."""
    rsi = signals.get('rsi')
    if rsi is not None:
        return rsi.iloc[-1] > 70
    return False

def price_above_upper_band(signals, fundamentals=None):
    """Price above upper Bollinger Band."""
    close = signals.get('close')
    upper_band = signals.get('upper_band')
    if close is not None and upper_band is not None:
        return close.iloc[-1] > upper_band.iloc[-1]
    return False

def low_pe_ratio(signals, fundamentals=None):
    """P/E ratio below 15."""
    if fundamentals and 'pe_ratio' in fundamentals:
        return fundamentals['pe_ratio'] < 15
    return False

def positive_sentiment_shift(signals, fundamentals=None):
    """Positive sentiment shift."""
    sentiment_shift = signals.get('sentiment_shift')
    if sentiment_shift is not None:
        return sentiment_shift > 0.1
    return False

def high_sharpe_ratio(signals, fundamentals=None):
    """Sharpe ratio above 1.0 (good risk-adjusted returns)."""
    sharpe = signals.get('sharpe')
    if sharpe is not None:
        return sharpe > 1.0
    return False

def attractive_sortino(signals, fundamentals=None):
    """Sortino ratio above 1.5 (good downside protection)."""
    sortino = signals.get('sortino')
    if sortino is not None:
        return sortino > 1.5
    return False

def low_value_at_risk(signals, fundamentals=None):
    """VaR better than -2% (low tail risk)."""
    var = signals.get('var')
    if var is not None:
        return var > -0.02  # Less than 2% loss at 95% confidence
    return False

def strong_momentum(signals, fundamentals=None):
    """Strong recent momentum."""
    momentum = signals.get('momentum')
    if momentum is not None:
        return momentum.iloc[-1] > 0.05  # 5% recent gain
    return False

def reasonable_volatility(signals, fundamentals=None):
    """Volatility in acceptable range (not too high, not too low)."""
    vol = signals.get('volatility')
    if vol is not None:
        return 0.1 < vol < 0.5  # 10-50% annual vol
    return False

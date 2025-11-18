import pandas as pd
import numpy as np

def normalize_price_data(df):
    """Normalize and clean price data."""
    # Fill missing values with forward fill, then backward
    df = df.ffill().bfill()
    # Ensure numeric types
    numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    # Remove rows with all NaN
    df = df.dropna(how='all')
    return df

def normalize_fundamentals(info):
    """Normalize fundamental data."""
    normalized = {}
    normalized['name'] = info.get('longName', info.get('shortName', ''))
    normalized['sector'] = info.get('sector', '')
    normalized['industry'] = info.get('industry', '')
    normalized['market_cap'] = info.get('marketCap', None)
    normalized['pe_ratio'] = info.get('trailingPE', None)
    normalized['dividend_yield'] = info.get('dividendYield', None)
    return normalized

def normalize_news_headlines(headlines):
    """Clean and normalize news headlines."""
    cleaned = []
    for h in headlines:
        # Basic cleaning: strip, lower, remove special chars
        clean = h.strip().lower()
        # Remove non-alphanumeric except spaces
        clean = ''.join(c for c in clean if c.isalnum() or c.isspace())
        cleaned.append(clean)
    return cleaned

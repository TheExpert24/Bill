#!/usr/bin/env python3
"""
Market Analysis and Trade-Sizing Engine
Main pipeline integrating all components.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from data_ingestion.api_client import MarketDataClient
from data_ingestion.scraper import NewsScraper
from preprocessing.normalize import normalize_price_data, normalize_fundamentals, normalize_news_headlines
from preprocessing.sentiment import batch_analyze_sentiment
from signals.indicators import (
    simple_moving_average, exponential_moving_average, relative_strength_index,
    bollinger_bands, price_momentum_ratio, volatility, sentiment_shift_score
)
from rules.engine import RuleEngine, bullish_crossover, oversold_rsi, overbought_rsi, price_above_upper_band, low_pe_ratio, positive_sentiment_shift
from scoring.engine import ScoringEngine
from sizing.engine import PositionSizer
from output.recommendations import RecommendationOutput
from database.db import get_session, save_asset, save_price_data, save_news
from config.config import *

def process_asset(ticker, client, scraper, session):
    """Process a single asset through the pipeline."""
    print(f"Processing {ticker}...")

    # Data ingestion
    price_df = client.get_price_data(ticker, period=DATA_PERIOD)
    fundamentals = client.get_fundamentals(ticker)
    news_headlines = client.get_company_news(ticker, page_size=NEWS_PAGE_SIZE)
    scraped_headlines = scraper.scrape_yahoo_news(ticker, num_headlines=NEWS_PAGE_SIZE)
    all_headlines = news_headlines + scraped_headlines

    # Normalization
    price_df = normalize_price_data(price_df)
    fundamentals_norm = normalize_fundamentals(fundamentals)
    headlines_norm = normalize_news_headlines(all_headlines)

    # Sentiment analysis
    sentiment_scores = batch_analyze_sentiment(headlines_norm)

    # Save to database
    asset_id = save_asset(session, ticker, **fundamentals_norm)
    save_price_data(session, asset_id, price_df)
    save_news(session, asset_id, headlines_norm, sentiment_score=sum(sentiment_scores)/len(sentiment_scores) if sentiment_scores else 0)

    # Signal extraction
    close_prices = price_df['Close']
    signals = {
        'close': close_prices,
        'sma_20': simple_moving_average(close_prices, SMA_SHORT_WINDOW),
        'sma_50': simple_moving_average(close_prices, SMA_LONG_WINDOW),
        'rsi': relative_strength_index(close_prices, RSI_WINDOW),
        'upper_band': bollinger_bands(close_prices, BB_WINDOW, BB_NUM_STD)[0],
        'momentum': price_momentum_ratio(close_prices, MOMENTUM_PERIOD),
        'volatility': volatility(close_prices, VOLATILITY_WINDOW),
        'sentiment_shift': sentiment_shift_score(sentiment_scores, SENTIMENT_WINDOW)
    }

    return signals, fundamentals_norm

def main(tickers):
    """Main pipeline execution."""
    client = MarketDataClient()
    scraper = NewsScraper()
    session = get_session()

    rule_engine = RuleEngine()
    rule_engine.add_rule(bullish_crossover)
    rule_engine.add_rule(oversold_rsi)
    rule_engine.add_rule(overbought_rsi)
    rule_engine.add_rule(price_above_upper_band)
    rule_engine.add_rule(low_pe_ratio)
    rule_engine.add_rule(positive_sentiment_shift)

    scoring_engine = ScoringEngine(CRITERIA_WEIGHTS)
    sizer = PositionSizer(TOTAL_CAPITAL, RISK_TOLERANCE, MAX_ALLOCATION_PER_ASSET, DIVERSIFICATION_FACTOR)
    output = RecommendationOutput(OUTPUT_FORMAT)

    asset_scores = {}
    current_prices = {}
    volatilities = {}

    for ticker in tickers:
        try:
            signals, fundamentals = process_asset(ticker, client, scraper, session)
            rule_results = rule_engine.evaluate(signals, fundamentals)
            score = scoring_engine.score_asset(rule_results)
            asset_scores[ticker] = score
            current_prices[ticker] = signals['close'].iloc[-1]
            volatilities[ticker] = signals['volatility'].iloc[-1] if not signals['volatility'].empty else 0.2
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    # Rank and size positions
    ranked = scoring_engine.rank_assets(asset_scores)
    positions = sizer.size_positions(ranked, current_prices, volatilities)

    # Generate output
    report = output.generate_report(positions, asset_scores, current_prices)
    print(report)

    # Save report
    filename = output.save_report(report)
    print(f"Report saved to {filename}")

if __name__ == "__main__":
    # Example tickers
    tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
    main(tickers)

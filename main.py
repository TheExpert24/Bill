#!/usr/bin/env python3
"""
Market Analysis and Trade-Sizing Engine
Main pipeline integrating all components including hedge fund-style analysis.
"""

import sys
import os
import importlib
sys.path.append(os.path.dirname(__file__))

from api_client import MarketDataClient
from scraper import NewsScraper
from normalize import normalize_price_data, normalize_fundamentals, normalize_news_headlines
from sentiment import batch_analyze_sentiment
from indicators import (
    simple_moving_average, exponential_moving_average, relative_strength_index,
    bollinger_bands, price_momentum_ratio, volatility, sentiment_shift_score
)
engines_rules = importlib.import_module('engines-rules')
RuleEngine = engines_rules.RuleEngine
bullish_crossover = engines_rules.bullish_crossover
oversold_rsi = engines_rules.oversold_rsi
overbought_rsi = engines_rules.overbought_rsi
price_above_upper_band = engines_rules.price_above_upper_band
low_pe_ratio = engines_rules.low_pe_ratio
positive_sentiment_shift = engines_rules.positive_sentiment_shift

from engine import ScoringEngine
engine_sizing = importlib.import_module('engine-sizing')
PositionSizer = engine_sizing.PositionSizer
from recommendations import RecommendationOutput
from db import get_session, save_asset, save_price_data, save_news
from hedge_fund_engine import HedgeFundEngine
from event_driven_engine import EventDrivenEngine
from config import *

def process_asset_with_hedge_fund_analysis(ticker, client, scraper, session, 
                                           hedge_engine, event_engine):
    """Process a single asset through the enhanced pipeline with hedge fund analysis."""
    print(f"Processing {ticker} with hedge fund-style analysis...")

    price_df = client.get_price_data(ticker, period=DATA_PERIOD)
    fundamentals = client.get_fundamentals(ticker)
    news_headlines = client.get_company_news(ticker, page_size=NEWS_PAGE_SIZE)
    scraped_headlines = scraper.scrape_yahoo_news(ticker, num_headlines=NEWS_PAGE_SIZE)
    all_headlines = news_headlines + scraped_headlines

    price_df = normalize_price_data(price_df)
    fundamentals_norm = normalize_fundamentals(fundamentals)
    headlines_norm = normalize_news_headlines(all_headlines)

    sentiment_scores = batch_analyze_sentiment(headlines_norm)

    asset_id = save_asset(session, ticker, **fundamentals_norm)
    save_price_data(session, asset_id, price_df)
    save_news(session, asset_id, headlines_norm, sentiment_score=sum(sentiment_scores)/len(sentiment_scores) if sentiment_scores else 0)

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

    hedge_analysis = hedge_engine.generate_composite_signal(
        price_df, fundamentals_norm, sentiment_scores
    )
    
    event_analysis = event_engine.generate_event_signal(
        headlines_norm, price_df
    )
    
    vol_regime = hedge_analysis['volatility_regime']['regime']
    event_signal_adjusted = event_engine.filter_by_market_regime(
        event_analysis['composite_signal'], vol_regime
    )
    
    return signals, fundamentals_norm, hedge_analysis, event_analysis, event_signal_adjusted

def process_asset(ticker, client, scraper, session):
    """Process a single asset through the pipeline."""
    print(f"Processing {ticker}...")

    price_df = client.get_price_data(ticker, period=DATA_PERIOD)
    fundamentals = client.get_fundamentals(ticker)
    news_headlines = client.get_company_news(ticker, page_size=NEWS_PAGE_SIZE)
    scraped_headlines = scraper.scrape_yahoo_news(ticker, num_headlines=NEWS_PAGE_SIZE)
    all_headlines = news_headlines + scraped_headlines

    price_df = normalize_price_data(price_df)
    fundamentals_norm = normalize_fundamentals(fundamentals)
    headlines_norm = normalize_news_headlines(all_headlines)

    sentiment_scores = batch_analyze_sentiment(headlines_norm)

    asset_id = save_asset(session, ticker, **fundamentals_norm)
    save_price_data(session, asset_id, price_df)
    save_news(session, asset_id, headlines_norm, sentiment_score=sum(sentiment_scores)/len(sentiment_scores) if sentiment_scores else 0)

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

def main_with_hedge_fund_analysis(tickers):
    """Enhanced main pipeline with hedge fund-style analysis."""
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
    
    hedge_engine = HedgeFundEngine()
    event_engine = EventDrivenEngine()

    asset_scores = {}
    current_prices = {}
    volatilities = {}
    hedge_signals = {}
    event_signals = {}
    all_price_data = {}

    for ticker in tickers:
        try:
            signals, fundamentals, hedge_analysis, event_analysis, event_adj = \
                process_asset_with_hedge_fund_analysis(ticker, client, scraper, session,
                                                      hedge_engine, event_engine)
            
            rule_results = rule_engine.evaluate(signals, fundamentals)
            base_score = scoring_engine.score_asset(rule_results)
            
            hedge_score = hedge_analysis['composite_score']
            event_score = event_adj
            
            combined_score = (base_score * 0.4) + (hedge_score * 0.4) + (event_score * 0.2)
            
            asset_scores[ticker] = combined_score
            current_prices[ticker] = signals['close'].iloc[-1]
            volatilities[ticker] = signals['volatility'].iloc[-1] if not signals['volatility'].empty else 0.2
            hedge_signals[ticker] = hedge_analysis
            event_signals[ticker] = event_analysis
            
            all_price_data[ticker] = {
                'Close': signals['close']
            }
            
            print(f"{ticker}: Base={base_score:.2f}, Hedge={hedge_score:.2f}, Event={event_score:.2f}, Combined={combined_score:.2f}")
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    stat_arb = hedge_engine.compute_statistical_arbitrage_signals(all_price_data)
    if stat_arb['pairs']:
        print(f"\nPair trading opportunities found: {len(stat_arb['pairs'])}")
        for pair in stat_arb['pairs'][:5]:
            print(f"  {pair['ticker1']}-{pair['ticker2']}: corr={pair['correlation']:.2f}, z={pair['spread_z_score']:.2f}, signal={pair['signal']}")

    ranked = scoring_engine.rank_assets(asset_scores)
    positions = sizer.size_positions(ranked, current_prices, volatilities)

    report = output.generate_report(positions, asset_scores, current_prices)
    print("\n" + "="*80)
    print("HEDGE FUND-STYLE ANALYSIS REPORT")
    print("="*80)
    print(report)

    filename = output.save_report(report)
    print(f"\nReport saved to {filename}")
    
    return positions, asset_scores, hedge_signals, event_signals

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

    ranked = scoring_engine.rank_assets(asset_scores)
    positions = sizer.size_positions(ranked, current_prices, volatilities)

    report = output.generate_report(positions, asset_scores, current_prices)
    print(report)

    filename = output.save_report(report)
    print(f"Report saved to {filename}")

if __name__ == "__main__":
    tickers = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'NVDA', 'META', 'JPM', 'V', 'WMT']
    main_with_hedge_fund_analysis(tickers)

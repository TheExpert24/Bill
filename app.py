from flask import Flask, request, render_template
import sys
import os
sys.path.append(os.path.dirname(__file__))

from tickers import get_sample_us_tickers, get_all_us_tickers
from main import main as run_engine
import config as cfg

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    print("Index route executed")
    if request.method == 'POST':
        capital = float(request.form['capital'])
        num_stocks = int(request.form['num_stocks'])
        risk_tolerance = float(request.form['risk_tolerance']) / 100
        goal = request.form['goal']
        time_horizon = request.form['time_horizon']

        cfg.TOTAL_CAPITAL = capital
        cfg.RISK_TOLERANCE = risk_tolerance

        if goal == 'conservative':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.20
            cfg.DIVERSIFICATION_FACTOR = 0.8
        elif goal == 'moderate':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.30
            cfg.DIVERSIFICATION_FACTOR = 1.0
        elif goal == 'aggressive':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.40
            cfg.DIVERSIFICATION_FACTOR = 1.2

        try:
            all_tickers = get_all_us_tickers()
            tickers = all_tickers
            print(f"Analyzing {len(tickers)} stocks from S&P 500...")
        except Exception as e:
            print(f"Error fetching tickers: {e}")
            return render_template('error.html', error="Failed to fetch stock tickers.")


        try:
            recommendations = run_engine_web(tickers, num_stocks)
            return render_template('results.html', recommendations=recommendations)
        except Exception as e:
            return render_template('error.html', error=str(e))

    return render_template('index.html')

def run_engine_web(tickers, num_stocks):
    """Modified version of main that returns recommendations as dict with hedge fund analysis."""
    from api_client import MarketDataClient
    from scraper import NewsScraper
    from normalize import normalize_price_data, normalize_fundamentals, normalize_news_headlines
    from sentiment import batch_analyze_sentiment
    from indicators import (
        simple_moving_average, exponential_moving_average, relative_strength_index,
        bollinger_bands, price_momentum_ratio, volatility, sentiment_shift_score,
        sharpe_ratio, sortino_ratio, value_at_risk
    )
    import importlib
    engines_rules = importlib.import_module('engines-rules')
    RuleEngine = engines_rules.RuleEngine
    bullish_crossover = engines_rules.bullish_crossover
    oversold_rsi = engines_rules.oversold_rsi
    overbought_rsi = engines_rules.overbought_rsi
    price_above_upper_band = engines_rules.price_above_upper_band
    low_pe_ratio = engines_rules.low_pe_ratio
    positive_sentiment_shift = engines_rules.positive_sentiment_shift
    high_sharpe_ratio = engines_rules.high_sharpe_ratio
    attractive_sortino = engines_rules.attractive_sortino
    low_value_at_risk = engines_rules.low_value_at_risk
    strong_momentum = engines_rules.strong_momentum
    reasonable_volatility = engines_rules.reasonable_volatility
    
    from engine import ScoringEngine
    engine_sizing = importlib.import_module('engine-sizing')
    PositionSizer = engine_sizing.PositionSizer
    from db import get_session, save_asset, save_price_data, save_news
    from hedge_fund_engine import HedgeFundEngine
    from event_driven_engine import EventDrivenEngine
    import config as cfg

    client = MarketDataClient()
    scraper = NewsScraper()
    session = get_session()
    
    hedge_engine = HedgeFundEngine()
    event_engine = EventDrivenEngine()

    rule_engine = RuleEngine()
    rule_engine.add_rule(bullish_crossover)
    rule_engine.add_rule(oversold_rsi)
    rule_engine.add_rule(overbought_rsi)
    rule_engine.add_rule(price_above_upper_band)
    rule_engine.add_rule(low_pe_ratio)
    rule_engine.add_rule(positive_sentiment_shift)
    rule_engine.add_rule(high_sharpe_ratio)
    rule_engine.add_rule(attractive_sortino)
    rule_engine.add_rule(low_value_at_risk)
    rule_engine.add_rule(strong_momentum)
    rule_engine.add_rule(reasonable_volatility)

    scoring_engine = ScoringEngine(cfg.CRITERIA_WEIGHTS)
    sizer = PositionSizer(cfg.TOTAL_CAPITAL, cfg.RISK_TOLERANCE, cfg.MAX_ALLOCATION_PER_ASSET, cfg.DIVERSIFICATION_FACTOR)

    asset_scores = {}
    current_prices = {}
    volatilities = {}
    rule_results_dict = {}
    fundamentals_dict = {}
    hedge_signals_dict = {}
    event_signals_dict = {}
    recommendations = []
    
    processed = 0
    failed = 0
    total = len(tickers)

    for ticker in tickers:
        try:
            processed += 1
            if processed % 10 == 0:
                print(f"Progress: {processed}/{total} stocks processed...")
                
            price_df = client.get_price_data(ticker, period=cfg.DATA_PERIOD)
            
            if price_df is None or len(price_df) < 50:
                failed += 1
                continue
                
            fundamentals = client.get_fundamentals(ticker)
            
            news_headlines = []
            try:
                news_headlines = client.get_company_news(ticker, page_size=cfg.NEWS_PAGE_SIZE)
            except:
                pass
                
            scraped_headlines = []
            try:
                scraped_headlines = scraper.scrape_yahoo_news(ticker, num_headlines=5)
            except:
                pass
                
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
                'sma_20': simple_moving_average(close_prices, cfg.SMA_SHORT_WINDOW),
                'sma_50': simple_moving_average(close_prices, cfg.SMA_LONG_WINDOW),
                'rsi': relative_strength_index(close_prices, cfg.RSI_WINDOW),
                'upper_band': bollinger_bands(close_prices, cfg.BB_WINDOW, cfg.BB_NUM_STD)[0],
                'momentum': price_momentum_ratio(close_prices, cfg.MOMENTUM_PERIOD),
                'volatility': volatility(close_prices, cfg.VOLATILITY_WINDOW),
                'sentiment_shift': sentiment_shift_score(sentiment_scores, cfg.SENTIMENT_WINDOW),
                'sharpe': sharpe_ratio(close_prices),
                'sortino': sortino_ratio(close_prices),
                'var': value_at_risk(close_prices)
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

            rule_results = rule_engine.evaluate(signals, fundamentals_norm)
            rule_results_dict[ticker] = rule_results
            fundamentals_dict[ticker] = fundamentals_norm
            
            base_score = scoring_engine.score_asset(rule_results)
            hedge_score = hedge_analysis['composite_score']
            event_score = event_signal_adjusted
            
            combined_score = (base_score * 0.4) + (hedge_score * 0.4) + (event_score * 0.2)
            
            asset_scores[ticker] = combined_score
            current_prices[ticker] = signals['close'].iloc[-1]
            volatilities[ticker] = signals['volatility'].iloc[-1] if not signals['volatility'].empty else 0.2
            hedge_signals_dict[ticker] = hedge_analysis
            event_signals_dict[ticker] = event_analysis
            
        except Exception as e:
            failed += 1
            continue
    
    print(f"Analysis complete: {processed} stocks processed, {failed} failed, {len(asset_scores)} scored successfully")

    ranked = scoring_engine.rank_assets(asset_scores)
    print(f"Ranked {len(ranked)} assets with scores")
    
    top_ranked = ranked[:num_stocks]
    print(f"Selecting top {num_stocks} stocks for investment")
    
    positions = sizer.size_positions(top_ranked, current_prices, volatilities)
    print(f"Generated {len(positions)} positions")

    if not positions:
        print("ERROR: No positions generated even after analysis")
        return []

    recommendations = []
    for ticker, shares in positions.items():
        cost = shares * current_prices[ticker]
        score = asset_scores.get(ticker, 0)
        
        expected_return_pct = min(max((score / 10.0) * 15, 3), 25)
        
        reasoning = []
        rules = rule_results_dict.get(ticker, {})
        
        if rules.get('bullish_crossover'):
            reasoning.append("Bullish crossover: Short-term MA above long-term MA")
        if rules.get('oversold_rsi'):
            reasoning.append("Oversold RSI: Price may be undervalued")
        if rules.get('low_pe_ratio'):
            reasoning.append("Low P/E ratio: Attractive valuation")
        if rules.get('positive_sentiment_shift'):
            reasoning.append("Positive sentiment shift in news")
        if rules.get('high_sharpe_ratio'):
            reasoning.append("High Sharpe ratio: Excellent risk-adjusted returns")
        if rules.get('attractive_sortino'):
            reasoning.append("Strong Sortino ratio: Good downside protection")
        if rules.get('low_value_at_risk'):
            reasoning.append("Low Value at Risk: Limited tail risk")
        if rules.get('strong_momentum'):
            reasoning.append("Strong momentum: Recent price strength")
        if rules.get('reasonable_volatility'):
            reasoning.append("Reasonable volatility: Balanced risk profile")
        
        hedge_sig = hedge_signals_dict.get(ticker, {})
        if hedge_sig:
            momentum_str = hedge_sig.get('momentum_signals', {}).get('momentum_strength', 0)
            if momentum_str >= 3:
                reasoning.append(f"Strong multi-timeframe momentum (score: {momentum_str}/4)")
            
            vol_regime = hedge_sig.get('volatility_regime', {}).get('regime', 'unknown')
            if vol_regime == 'low':
                reasoning.append("Low volatility regime: Favorable risk environment")
            
            factor_score = hedge_sig.get('factor_scores', {}).get('total_factor_score', 0)
            if factor_score >= 6:
                reasoning.append(f"High multi-factor score: {factor_score}")
        
        event_sig = event_signals_dict.get(ticker, {})
        if event_sig:
            if event_sig.get('earnings_event', {}).get('detected'):
                reasoning.append("Positive earnings catalyst detected")
            if event_sig.get('ma_event', {}).get('detected'):
                reasoning.append("M&A activity detected")
            if event_sig.get('product_event', {}).get('detected'):
                reasoning.append("Product launch catalyst")
        
        if not reasoning:
            reasoning.append("Meets configured criteria for potential opportunity")

        fund = fundamentals_dict.get(ticker, {})
        recommendations.append({
            'ticker': ticker,
            'company_name': fund.get('name', ticker),
            'sector': fund.get('sector', 'N/A'),
            'shares': shares,
            'price': round(current_prices[ticker], 2),
            'total_cost': round(cost, 2),
            'score': round(score, 2),
            'expected_return': f"{expected_return_pct:.1f}%",
            'reasoning': reasoning
        })

    return recommendations

if __name__ == '__main__':  # Ensure debug=True
    app.run(debug=True, port=5001)

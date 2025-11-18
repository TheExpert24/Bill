from flask import Flask, request, render_template
import sys
import os
sys.path.append(os.path.dirname(__file__))

from data_ingestion.tickers import get_sample_us_tickers, get_all_us_tickers
from main import main as run_engine
import config.config as cfg

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    print("Index route executed")  # Debugging print statement
    if request.method == 'POST':
        # Get user inputs
        capital = float(request.form['capital'])
        risk_tolerance = float(request.form['risk_tolerance']) / 100  # Convert % to decimal
        goal = request.form['goal']
        time_horizon = request.form['time_horizon']

        # Adjust config based on inputs
        cfg.TOTAL_CAPITAL = capital
        cfg.RISK_TOLERANCE = risk_tolerance

        if goal == 'conservative':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.05  # 5%
            cfg.DIVERSIFICATION_FACTOR = 0.3
        elif goal == 'moderate':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.1  # 10%
            cfg.DIVERSIFICATION_FACTOR = 0.5
        elif goal == 'aggressive':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.15  # 15%
            cfg.DIVERSIFICATION_FACTOR = 0.7

        # Get all available tickers
        try:
            all_tickers = get_all_us_tickers()  # Fetch all market tickers
        except:
            return render_template('error.html', error="Failed to fetch tickers.")
        tickers = all_tickers

        # Run engine (modified main to return results instead of print)
        try:
            recommendations = run_engine_web(tickers)
            return render_template('results.html', recommendations=recommendations)
        except Exception as e:
            return render_template('error.html', error=str(e))

    return render_template('index.html')

def run_engine_web(tickers):
    """Modified version of main that returns recommendations as dict."""
    from data_ingestion.api_client import MarketDataClient
    from data_ingestion.scraper import NewsScraper
    from preprocessing.normalize import normalize_price_data, normalize_fundamentals, normalize_news_headlines
    from preprocessing.sentiment import batch_analyze_sentiment
    from signals.indicators import (
        simple_moving_average, exponential_moving_average, relative_strength_index,
        bollinger_bands, price_momentum_ratio, volatility, sentiment_shift_score
    )
    from rules.engine import RuleEngine, bullish_crossover, oversold_rsi, overbought_rsi, price_above_upper_band, low_pe_ratio, positive_sentiment_shift, high_sharpe_ratio, attractive_sortino, low_value_at_risk, strong_momentum, reasonable_volatility
    from scoring.engine import ScoringEngine
    from sizing.engine import PositionSizer
    from database.db import get_session, save_asset, save_price_data, save_news
    import config.config as cfg

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
    rule_results_dict = {}  # Store rule results per ticker
    fundamentals_dict = {}  # Store fundamentals per ticker
    recommendations = []  # Initialize recommendations as an empty list

    for ticker in tickers:
        try:
            # Data ingestion
            price_df = client.get_price_data(ticker, period=cfg.DATA_PERIOD)
            fundamentals = client.get_fundamentals(ticker)
            try:
                news_headlines = client.get_company_news(ticker, page_size=cfg.NEWS_PAGE_SIZE)
            except:
                news_headlines = []
            try:
                scraped_headlines = scraper.scrape_yahoo_news(ticker, num_headlines=cfg.NEWS_PAGE_SIZE)
            except:
                scraped_headlines = []
            all_headlines = news_headlines + scraped_headlines

            # Normalization
            price_df = normalize_price_data(price_df)
            fundamentals_norm = normalize_fundamentals(fundamentals)
            headlines_norm = normalize_news_headlines(all_headlines)
            sentiment_scores = batch_analyze_sentiment(headlines_norm)

            # Save to database
            asset_id = save_asset(session, ticker, **fundamentals_norm)
            save_price_data(session, asset_id, price_df)
            save_news(session, asset_id, headlines_norm, sentiment_score=sum(sentiment_scores)/len(sentiment_scores) if sentiment_scores else 0)

            # Signal extraction
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

            rule_results = rule_engine.evaluate(signals, fundamentals_norm)
            rule_results_dict[ticker] = rule_results
            fundamentals_dict[ticker] = fundamentals_norm
            score = scoring_engine.score_asset(rule_results)
            asset_scores[ticker] = score
            current_prices[ticker] = signals['close'].iloc[-1]
            volatilities[ticker] = signals['volatility'].iloc[-1] if not signals['volatility'].empty else 0.2
        except Exception as e:
            print(f"Error processing {ticker}: {e}")
            continue

    # Rank and size positions
    ranked = scoring_engine.rank_assets(asset_scores)
    print(f"Ranked assets: {ranked}")  # Debugging: Check ranked assets
    positions = sizer.size_positions(ranked, current_prices, volatilities)
    print(f"Generated positions: {positions}")  # Debugging: Check generated positions

    # If no positions, force top 2 recommendations
    if not positions and ranked:
        print("No positions generated, and no fallback recommendations will be provided.")  # Debugging
        return []  # Return an empty list if no positions are generated

    # Format recommendations with reasoning
    recommendations = []
    for ticker, shares in positions.items():
        cost = shares * current_prices[ticker]
        # Generate reasoning based on actual rule results
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
            'score': round(asset_scores[ticker], 2),
            'reasoning': reasoning
        })

    return recommendations

if __name__ == '__main__':  # Ensure debug=True
    app.run(debug=True, port=5001)

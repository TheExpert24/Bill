from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(__file__))

from tickers import get_sample_us_tickers, get_all_us_tickers
from main import main as run_engine
import config as cfg
from auth import GoogleAuth
from db import get_session, is_first_time_user, get_user_portfolio, update_user_portfolio, save_user_recommendation
from models import User, UserRecommendation
import oauth_config

app = Flask(__name__)
app.secret_key = oauth_config.SECRET_KEY

# Initialize Google OAuth
google_auth = GoogleAuth(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page with authentication and recommendation form"""
    user = google_auth.get_current_user()
    
    if request.method == 'POST':
        # Check if user is logged in
        if not user:
            return redirect(url_for('login'))
        
        capital = float(request.form['capital'])
        risk_tolerance = float(request.form['risk_tolerance']) / 100
        goal = request.form['goal']
        time_horizon = request.form['time_horizon']

        # Store parameters in session for analysis
        session['analysis_capital'] = capital
        session['analysis_risk_tolerance'] = risk_tolerance
        session['analysis_goal'] = goal
        session['analysis_time_horizon'] = time_horizon
        
        # Initialize progress tracking
        session['analysis_progress'] = {
            'processed': 0,
            'total': 0,
            'percentage': 0,
            'status': 'Starting stock analysis...'
        }
        
        # Redirect to progress page which will trigger analysis
        return redirect(url_for('analyze_progress'))

    return render_template('index.html', user=user)

@app.route('/analyze_progress')
def analyze_progress():
    """Progress page that shows analysis in real-time"""
    user = google_auth.get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    progress = session.get('analysis_progress', {
        'processed': 0,
        'total': 0,
        'percentage': 0,
        'status': 'Initializing...'
    })
    
    return render_template('results.html', analysis_progress=progress)

@app.route('/start_analysis', methods=['POST'])
def start_analysis():
    """Start the analysis in background"""
    user = google_auth.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get parameters from session
        capital = session.get('analysis_capital')
        risk_tolerance = session.get('analysis_risk_tolerance')
        goal = session.get('analysis_goal')
        time_horizon = session.get('analysis_time_horizon')
        
        if not all([capital, risk_tolerance, goal, time_horizon]):
            return jsonify({'error': 'Missing analysis parameters'}), 400
        
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

        all_tickers = get_all_us_tickers()
        tickers = all_tickers
        print(f"Analyzing {len(tickers)} stocks from S&P 500...")
        
        # Update progress
        session['analysis_progress'] = {
            'processed': 0,
            'total': len(tickers),
            'percentage': 0,
            'status': 'Starting stock analysis...'
        }
        
        # Run analysis with progress tracking - pass Flask session to the function
        recommendations = run_engine_web(tickers, session)
        
        # Check if this is the user's first time
        session_db = get_session()
        is_first_time = is_first_time_user(session_db, user.id)
        
        # Generate combined recommendations (all actions in one table)
        combined_recommendations = generate_combined_recommendations(recommendations, user.id, is_first_time)
        
        # Save recommendations to user account
        save_user_recommendations(user.id, {
            'capital': capital,
            'risk_tolerance': risk_tolerance,
            'goal': goal,
            'time_horizon': time_horizon,
            'recommendations': recommendations,
            'predictions': combined_recommendations,
            'is_first_time': is_first_time
        })
        
        # Update user's portfolio with new recommendations
        if update_user_portfolio(session_db, user.id, recommendations):
            print("Portfolio updated successfully")
        
        session_db.close()
        
        # Update progress to completed
        session['analysis_progress'] = {
            'processed': len(tickers),
            'total': len(tickers),
            'percentage': 100,
            'status': 'Analysis complete!'
        }
        session['final_recommendations'] = combined_recommendations
        
        return jsonify({
            'status': 'completed',
            'combined_recommendations': combined_recommendations
        })
        
    except Exception as e:
        session['analysis_progress'] = {
            'processed': 0,
            'total': 0,
            'percentage': 0,
            'status': f'Error: {str(e)}'
        }
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress')
def get_progress():
    """API endpoint to get current analysis progress"""
    progress = session.get('analysis_progress', {
        'processed': 0,
        'total': 0,
        'percentage': 0,
        'status': 'Not started'
    })
    
    final_recs = session.get('final_recommendations')
    if final_recs:
        return jsonify({
            'status': 'completed',
            'progress': progress,
            'recommendations': final_recs
        })
    else:
        return jsonify({
            'status': 'in_progress',
            'progress': progress
        })

@app.route('/accounts')
def accounts():
    """User accounts page showing recommendation history"""
    user = google_auth.get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    session_db = get_session()
    try:
        # Get user's recommendation history
        recommendations = session_db.query(UserRecommendation).filter_by(user_id=user.id).order_by(UserRecommendation.created_at.desc()).all()
        
        # Convert JSON data back to objects for display
        recommendation_history = []
        for rec in recommendations:
            recommendation_history.append({
                'id': rec.id,
                'capital': rec.capital,
                'risk_tolerance': rec.risk_tolerance,
                'goal': rec.goal,
                'time_horizon': rec.time_horizon,
                'recommendations': json.loads(rec.recommendations_json),
                'predictions': json.loads(rec.prediction_json) if rec.prediction_json else {},
                'is_first_time': rec.is_first_time,
                'created_at': rec.created_at
            })
        
        return render_template('accounts.html', user=user, recommendation_history=recommendation_history)
    finally:
        session_db.close()

@app.route('/api/user_info')
def api_user_info():
    """API endpoint to get current user info"""
    user = google_auth.get_current_user()
    if not user:
        return jsonify({'logged_in': False})
    
    return jsonify({
        'logged_in': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_pic': user.profile_pic
        }
    })

def save_user_recommendations(user_id, data):
    """Save user recommendations to database"""
    session_db = get_session()
    try:
        recommendation = UserRecommendation(
            user_id=user_id,
            capital=data['capital'],
            risk_tolerance=data['risk_tolerance'],
            goal=data['goal'],
            time_horizon=data['time_horizon'],
            recommendations_json=json.dumps(data['recommendations']),
            prediction_json=json.dumps(data['predictions']),
            is_first_time=data['is_first_time']
        )
        session_db.add(recommendation)
        session_db.commit()
        return recommendation.id
    except Exception as e:
        session_db.rollback()
        raise e
    finally:
        session_db.close()

def generate_combined_recommendations(recommendations, user_id, is_first_time):
    """Generate combined recommendations (all actions in one table)"""
    combined = []
    
    # Get portfolio information for context
    session_db = get_session()
    current_portfolio = get_user_portfolio(session_db, user_id) if not is_first_time else []
    user_holdings = {pos.ticker: pos for pos in current_portfolio}
    session_db.close()
    
    if is_first_time:
        # For first-time users, show all recommendations as BUY actions
        for rec in recommendations:
            combined.append({
                'ticker': rec['ticker'],
                'action': 'BUY',
                'current_shares': 0,
                'suggested_quantity': rec['shares'],
                'investment_amount': rec['total_cost'],
                'confidence': 85,
                'score': rec['score'],
                'reasoning': f"Build your initial portfolio with {rec['ticker']}. " + "; ".join(rec['reasoning']),
                'is_new': True
            })
    else:
        # For returning users, combine new recommendations with portfolio analysis
        scores = [rec.get('score', 0) for rec in recommendations]
        avg_score = sum(scores) / len(scores) if scores else 5.0
        
        # Process each recommendation
        for rec in recommendations:
            ticker = rec['ticker']
            score = rec['score']
            price = rec['price']
            shares = rec['shares']
            
            if ticker in user_holdings:
                # User owns this stock - analyze what to do
                position = user_holdings[ticker]
                if score >= avg_score + 2:
                    action = 'BUY MORE'
                    confidence = min(95, 70 + (score - avg_score) * 5)
                    reasoning = f"Strong momentum. Consider adding {shares} more shares to your current {position.shares} share position."
                    investment = shares * price
                elif score >= avg_score - 1:
                    action = 'KEEP'
                    confidence = min(85, 70 + abs(score - avg_score) * 3)
                    reasoning = f"Hold your current {position.shares} shares. Stock performing as expected."
                    investment = 0
                else:
                    action = 'SELL'
                    confidence = min(90, 65 + (avg_score - score) * 4)
                    reasoning = f"Consider reducing your {position.shares} share position due to underperformance."
                    investment = -(shares * price)  # Negative for selling
            else:
                # New stock recommendation
                action = 'BUY'
                confidence = min(90, 65 + (score - avg_score) * 8)
                reasoning = f"New opportunity: Strong buy signal for diversification. " + "; ".join(rec['reasoning'])
                investment = rec['total_cost']
            
            combined.append({
                'ticker': ticker,
                'action': action,
                'current_shares': user_holdings.get(ticker, type('obj', (object,), {'shares': 0})).shares,
                'suggested_quantity': shares if action in ['BUY', 'BUY MORE'] else shares,
                'investment_amount': investment,
                'confidence': confidence,
                'score': score,
                'reasoning': reasoning,
                'is_new': ticker not in user_holdings
            })
    
    # Add some additional market opportunities
    if not is_first_time:
        market_ops = suggest_market_opportunities(avg_score)
        combined.extend(market_ops)
    
    return combined

def suggest_market_opportunities(avg_score):
    """Suggest additional market opportunities"""
    opportunities = []
    
    # Add some popular stocks for diversification
    market_stocks = [
        {'ticker': 'AAPL', 'score': avg_score + 1.5, 'price': 150.0, 'shares': 5},
        {'ticker': 'MSFT', 'score': avg_score + 1.2, 'price': 280.0, 'shares': 3},
    ]
    
    for stock in market_stocks:
        opportunities.append({
            'ticker': stock['ticker'],
            'action': 'BUY',
            'current_shares': 0,
            'suggested_quantity': stock['shares'],
            'investment_amount': stock['shares'] * stock['price'],
            'confidence': 80,
            'score': stock['score'],
            'reasoning': f"Market opportunity: Strong fundamentals with {stock['shares']} shares recommended.",
            'is_new': True
        })
    
    return opportunities

def run_engine_web(tickers, flask_session=None):
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
    db_session = get_session()  # Use different variable name to avoid Flask session conflict
    
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

    # Initialize progress tracking in Flask session if available
    if flask_session:
        flask_session['analysis_progress'] = {
            'processed': 0,
            'total': total,
            'percentage': 0,
            'status': f'Starting analysis of {total} stocks...'
        }

    for ticker in tickers:
        try:
            processed += 1
            # Update progress every 10 stocks but show cumulative count
            if processed % 10 == 0:
                percentage = int(processed/total*100)
                print(f"Progress: {processed}/{total} stocks processed... ({percentage}%)")
                
                # Update progress in Flask session for real-time display
                if flask_session:
                    flask_session['analysis_progress'] = {
                        'processed': processed,
                        'total': total,
                        'percentage': percentage,
                        'status': f'Analyzing stock {processed} of {total}...'
                    }
                else:
                    # Fallback: use globals
                    if 'analysis_progress' in globals():
                        globals()['analysis_progress'].update({
                            'processed': processed,
                            'total': total,
                            'percentage': percentage,
                            'status': f'Analyzing stock {processed} of {total}...'
                        })
                
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

            asset_id = save_asset(db_session, ticker, **fundamentals_norm)
            save_price_data(db_session, asset_id, price_df)
            save_news(db_session, asset_id, headlines_norm, sentiment_score=sum(sentiment_scores)/len(sentiment_scores) if sentiment_scores else 0)

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

    # Final progress update
    if flask_session:
        flask_session['analysis_progress'] = {
            'processed': processed,
            'total': total,
            'percentage': 100,
            'status': 'Generating recommendations...'
        }
    elif 'analysis_progress' in globals():
        globals()['analysis_progress'].update({
            'processed': processed,
            'total': total,
            'percentage': 100,
            'status': 'Generating recommendations...'
        })

    ranked = scoring_engine.rank_assets(asset_scores)
    print(f"Ranked {len(ranked)} assets with scores")
    
    # Use advanced hedge fund engine for automatic position determination
    from advanced_hedge_fund_engine import AdvancedHedgeFundEngine
    hedge_engine_web = AdvancedHedgeFundEngine(universe_size=len(tickers))
    
    # Create stock scores in the format expected by the algorithm
    stock_scores_for_auto = {}
    for ticker, score in asset_scores.items():
        stock_scores_for_auto[ticker] = {
            'composite_score': score / 10.0,  # Normalize to 0-1 range
            'signal_quality': min(abs(score / 10.0), 1.0),
            'current_price': current_prices.get(ticker, 50.0)
        }
    
    # Automatically determine optimal number of positions
    optimal_position_count = hedge_engine_web._determine_optimal_position_count(stock_scores_for_auto, cfg.TOTAL_CAPITAL)
    print(f"Algorithm automatically determined optimal position count: {optimal_position_count}")
    
    # Select top positions based on algorithm determination
    top_ranked = ranked[:optimal_position_count]
    print(f"Selecting top {optimal_position_count} stocks for investment")
    
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

    # Final progress update
    if flask_session:
        flask_session['analysis_progress'] = {
            'processed': processed,
            'total': total,
            'percentage': 100,
            'status': 'Analysis complete!'
        }
    elif 'analysis_progress' in globals():
        globals()['analysis_progress'].update({
            'status': 'Analysis complete!'
        })

    # Close database session
    db_session.close()

    return recommendations

if __name__ == '__main__':
    app.run(debug=True, port=9999)

from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sys
import os
import json
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
sys.path.append(os.path.dirname(__file__))

# Global progress tracking
global_analysis_progress = {
    'processed': 0,
    'total': 0,
    'percentage': 0,
    'status': 'Not started'
}
progress_lock = threading.Lock()

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
        
        # Debug: Print the raw form data
        print(f"DEBUG: Raw form data received:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
        
        capital = float(request.form['capital'])
        risk_tolerance = float(request.form['risk_tolerance']) / 100
        goal = request.form['goal']
        time_horizon = request.form['time_horizon']

        # Store parameters in session for analysis
        session['analysis_capital'] = capital
        session['analysis_risk_tolerance'] = risk_tolerance
        session['analysis_goal'] = goal
        session['analysis_time_horizon'] = time_horizon
        
        # Clear any old recommendations from session
        session.pop('final_recommendations', None)
        session.pop('analysis_progress', None)
        
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
        
        # Debug: Print the actual values being used
        print(f"DEBUG: User entered capital: ${capital}")
        print(f"DEBUG: After float conversion: ${capital}")
        print(f"DEBUG: Config TOTAL_CAPITAL before update: ${cfg.TOTAL_CAPITAL}")
        print(f"DEBUG: Config TOTAL_CAPITAL after update: ${cfg.TOTAL_CAPITAL}")
        print(f"DEBUG: Risk tolerance: {risk_tolerance}")
        
        if goal == 'conservative':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.20
            cfg.DIVERSIFICATION_FACTOR = 0.8
        elif goal == 'moderate':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.30
            cfg.DIVERSIFICATION_FACTOR = 1.0
        elif goal == 'aggressive':
            cfg.MAX_ALLOCATION_PER_ASSET = 0.40
            cfg.DIVERSIFICATION_FACTOR = 1.2

        all_tickers = get_all_us_tickers()  # Get full universe for comprehensive analysis
        tickers = all_tickers  # Analyze all available stocks
        print(f"Analyzing {len(tickers)} stocks for comprehensive recommendations...")
        
        # Update progress
        session['analysis_progress'] = {
            'processed': 0,
            'total': len(tickers),
            'percentage': 0,
            'status': 'Starting stock analysis...'
        }
        
        # Run analysis with progress tracking - pass Flask session to the function
        recommendations = run_engine_web(tickers, session, capital)
        
        # Make recommendations JSON-safe immediately
        recommendations = make_json_safe(recommendations)
        
        # Check if this is the user's first time
        session_db = get_session()
        is_first_time = is_first_time_user(session_db, user.id)
        
        # Generate combined recommendations (all actions in one table)
        combined_recommendations = generate_combined_recommendations(recommendations, user.id, is_first_time)
        
        # Debug: Print what we're actually returning
        print(f"DEBUG: Combined recommendations being returned:")
        for i, rec in enumerate(combined_recommendations):
            print(f"  {i+1}. {rec['ticker']}: {rec['action']} {rec['suggested_quantity']} shares @ ${rec.get('investment_amount', 0)}")
        
        total_investment = sum(rec.get('investment_amount', 0) for rec in combined_recommendations)
        print(f"DEBUG: Total investment amount: ${total_investment}")
        
        # Save recommendations to user account
        save_user_recommendations(user.id, make_json_safe({
            'capital': capital,
            'risk_tolerance': risk_tolerance,
            'goal': goal,
            'time_horizon': time_horizon,
            'recommendations': recommendations,
            'predictions': combined_recommendations,
            'is_first_time': is_first_time
        }))
        
        # Update user's portfolio with new recommendations
        if update_user_portfolio(session_db, user.id, recommendations):
            print("Portfolio updated successfully")
        
        session_db.close()
        
        # Update progress to completed in both global and session
        final_progress = {
            'processed': len(tickers),
            'total': len(tickers),
            'percentage': 100,
            'status': 'Analysis complete!'
        }
        global_analysis_progress.update(final_progress)
        session['analysis_progress'] = final_progress
        session['final_recommendations'] = make_json_safe(combined_recommendations)
        
        return jsonify({
            'status': 'completed',
            'combined_recommendations': make_json_safe(combined_recommendations)
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
    global global_analysis_progress
    
    # Use global progress first, fallback to session
    progress = global_analysis_progress if global_analysis_progress['total'] > 0 else session.get('analysis_progress', {
        'processed': 0,
        'total': 0,
        'percentage': 0,
        'status': 'Not started'
    })
    
    final_recs = session.get('final_recommendations')
    if final_recs:
        return jsonify({
            'status': 'completed',
            'progress': make_json_safe(progress),
            'recommendations': make_json_safe(final_recs),
            'total': len(final_recs)
        })
    else:
        return jsonify({
            'status': 'in_progress',
            'progress': make_json_safe(progress)
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
    
    # Helper function to build reasoning from recommendation data
    def build_reasoning(rec):
        reasoning = []
        rules = rec.get('rule_results', {})
        
        # Convert any non-JSON serializable values
        if isinstance(rules, dict):
            rules = make_json_safe(rules)
        
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
        
        # Add hedge fund signals
        hedge_sig = rec.get('hedge_signals', {})
        if hedge_sig:
            momentum_str = hedge_sig.get('momentum_signals', {}).get('momentum_strength', 0)
            if momentum_str >= 3:
                reasoning.append(f"Strong multi-timeframe momentum (score: {momentum_str}/4)")
            
            vol_regime = hedge_sig.get('volatility_regime', {}).get('regime', 'unknown')
            if vol_regime == 'low':
                reasoning.append("Low volatility regime: Favorable risk environment")
        
        # Add event signals
        event_sig = rec.get('event_signals', {})
        if event_sig:
            if event_sig.get('earnings_event', {}).get('detected'):
                reasoning.append("Positive earnings catalyst detected")
            if event_sig.get('ma_event', {}).get('detected'):
                reasoning.append("M&A activity detected")
            if event_sig.get('product_event', {}).get('detected'):
                reasoning.append("Product launch catalyst")
        
        if not reasoning:
            reasoning.append("Meets configured criteria for potential opportunity")
        
        return reasoning
    
    if is_first_time:
        # For first-time users, show all recommendations as BUY actions
        for rec in recommendations:
            reasoning = build_reasoning(rec)
            combined.append({
                'ticker': rec['ticker'],
                'action': 'BUY',
                'current_shares': 0,
                'suggested_quantity': rec['shares'],
                'investment_amount': rec['total_cost'],
                'confidence': 85,
                'score': rec['score'],
                'reasoning': f"Build your initial portfolio with {rec['ticker']}. " + "; ".join(reasoning),
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
            price = rec['current_price']
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
                reasoning_list = build_reasoning(rec)
                reasoning = f"New opportunity: Strong buy signal for diversification. " + "; ".join(reasoning_list)
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
                'is_new': bool(ticker not in user_holdings)  # Ensure it's a proper bool
            })
    
    return combined

def make_json_safe(obj):
    """Convert data structure to be JSON-safe by handling numpy and boolean types"""
    import numpy as np
    
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, tuple):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, (np.bool_, bool)):  # Handle both numpy and Python booleans
        return bool(obj)
    elif isinstance(obj, (np.integer, np.floating)):  # Handle numpy numbers
        return obj.item()
    elif isinstance(obj, np.ndarray):  # Handle numpy arrays
        return obj.tolist()
    elif hasattr(obj, 'item') and callable(getattr(obj, 'item')):  # Handle other numpy scalars
        try:
            return obj.item()
        except:
            return str(obj)
    elif hasattr(obj, 'tolist') and callable(getattr(obj, 'tolist')):  # Handle other numpy arrays
        try:
            return obj.tolist()
        except:
            return str(obj)
    elif obj is True or obj is False:  # Explicit boolean check
        return bool(obj)
    else:
        return obj

def analyze_single_stock(ticker, total_stocks, flask_session=None):
    """Analyze a single stock - optimized for parallel execution"""
    global global_analysis_progress
    
    try:
        from api_client import MarketDataClient
        from normalize import normalize_price_data, normalize_fundamentals, normalize_news_headlines
        from sentiment import batch_analyze_sentiment
        from indicators import (
            simple_moving_average, relative_strength_index,
            bollinger_bands, price_momentum_ratio, volatility, sentiment_shift_score,
            sharpe_ratio, sortino_ratio, value_at_risk
        )
        import importlib
        engines_rules = importlib.import_module('engines-rules')
        from hedge_fund_engine import HedgeFundEngine
        from event_driven_engine import EventDrivenEngine
        import config as cfg
        
        client = MarketDataClient()
        hedge_engine = HedgeFundEngine()
        event_engine = EventDrivenEngine()
        
        # Get price data
        price_df = client.get_price_data(ticker, period=cfg.DATA_PERIOD)
        if price_df is None or len(price_df) < 50:
            return None
            
        # Get fundamentals
        fundamentals = client.get_fundamentals(ticker)
        
        # Reduced news fetching for speed
        try:
            news_headlines = client.get_company_news(ticker, page_size=2)  # Reduced for speed
        except:
            news_headlines = []

        # Process data
        price_df = normalize_price_data(price_df)
        fundamentals_norm = normalize_fundamentals(fundamentals)
        headlines_norm = normalize_news_headlines(news_headlines)
        sentiment_scores = batch_analyze_sentiment(headlines_norm)

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

        # Generate analysis
        hedge_analysis = hedge_engine.generate_composite_signal(
            price_df, fundamentals_norm, sentiment_scores
        )
        event_analysis = event_engine.generate_event_signal(headlines_norm, price_df)
        vol_regime = hedge_analysis['volatility_regime']['regime']
        event_signal_adjusted = event_engine.filter_by_market_regime(
            event_analysis['composite_signal'], vol_regime
        )

        # Rule engine analysis
        from engine import ScoringEngine
        rule_engine = engines_rules.RuleEngine()
        rule_engine.add_rule(engines_rules.bullish_crossover)
        rule_engine.add_rule(engines_rules.oversold_rsi)
        rule_engine.add_rule(engines_rules.overbought_rsi)
        rule_engine.add_rule(engines_rules.low_pe_ratio)
        rule_engine.add_rule(engines_rules.positive_sentiment_shift)
        rule_engine.add_rule(engines_rules.high_sharpe_ratio)
        
        scoring_engine = ScoringEngine(cfg.CRITERIA_WEIGHTS)
        rule_results = rule_engine.evaluate(signals, fundamentals_norm)
        
        base_score = scoring_engine.score_asset(rule_results)
        hedge_score = hedge_analysis['composite_score']
        event_score = event_signal_adjusted
        combined_score = (base_score * 0.4) + (hedge_score * 0.4) + (event_score * 0.2)
        
        result = {
            'ticker': ticker,
            'score': combined_score,
            'price': signals['close'].iloc[-1],
            'volatility': signals['volatility'].iloc[-1] if not signals['volatility'].empty else 0.2,
            'rule_results': rule_results,
            'fundamentals': fundamentals_norm,
            'hedge_signals': hedge_analysis,
            'event_signals': event_analysis
        }
        
        # Thread-safe progress update
        with progress_lock:
            global_analysis_progress['processed'] += 1
            processed = global_analysis_progress['processed']
            percentage = int((processed / total_stocks) * 100)
            global_analysis_progress['percentage'] = percentage
            global_analysis_progress['status'] = f'Analyzed {ticker} ({processed}/{total_stocks})'
        
        return result
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {str(e)}")
        with progress_lock:
            global_analysis_progress['processed'] += 1
        return None

def run_engine_web(tickers, flask_session=None, user_capital=None):
    """Parallel processing version - much faster than sequential"""
    global global_analysis_progress
    
    # Use user-provided capital if available, otherwise use config
    actual_capital = user_capital if user_capital is not None else cfg.TOTAL_CAPITAL
    print(f"DEBUG: run_engine_web using capital: ${actual_capital}")
    
    total = len(tickers)
    
    # Reset progress
    with progress_lock:
        global_analysis_progress.update({
            'processed': 0,
            'total': total,
            'percentage': 0,
            'status': f'Starting parallel analysis of {total} stocks...'
        })
    
    print(f"Starting parallel analysis of {total} stocks with up to 8 threads...")
    
    # Parallel processing with ThreadPoolExecutor
    results = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_ticker = {executor.submit(analyze_single_stock, ticker, total, flask_session): ticker for ticker in tickers}
        
        for future in as_completed(future_to_ticker):
            result = future.result()
            if result:
                results.append(result)
    
    print(f"Parallel analysis complete: {len(results)} stocks analyzed successfully!")
    
    # Process results
    asset_scores = {r['ticker']: r['score'] for r in results}
    current_prices = {r['ticker']: r['price'] for r in results}
    volatilities = {r['ticker']: r['volatility'] for r in results}
    rule_results_dict = {r['ticker']: r['rule_results'] for r in results}
    fundamentals_dict = {r['ticker']: r['fundamentals'] for r in results}
    hedge_signals_dict = {r['ticker']: r['hedge_signals'] for r in results}
    event_signals_dict = {r['ticker']: r['event_signals'] for r in results}
    
    # Generate final recommendations
    import importlib
    engine_sizing = importlib.import_module('engine-sizing')
    PositionSizer = engine_sizing.PositionSizer
    
    # Debug: Print the capital being used for position sizing
    print(f"DEBUG: Creating PositionSizer with capital: ${actual_capital}")
    print(f"DEBUG: Risk tolerance: {cfg.RISK_TOLERANCE}")
    print(f"DEBUG: Max allocation per asset: {cfg.MAX_ALLOCATION_PER_ASSET}")
    
    sizer = PositionSizer(actual_capital, cfg.RISK_TOLERANCE, cfg.MAX_ALLOCATION_PER_ASSET, cfg.DIVERSIFICATION_FACTOR)
    
    # Filter stocks that meet the minimum score threshold
    qualified_assets = [(ticker, score) for ticker, score in asset_scores.items() if score > cfg.MIN_SCORE_THRESHOLD]
    qualified_assets.sort(key=lambda x: x[1], reverse=True)  # Sort by score descending
    
    print(f"Found {len(qualified_assets)} stocks above minimum score threshold ({cfg.MIN_SCORE_THRESHOLD})")
    
    # Use the position sizer to calculate actual positions
    positions = sizer.size_positions(qualified_assets, current_prices, volatilities)
    
    recommendations = []
    total_portfolio_cost = 0
    
    for ticker, shares in positions.items():
        score = asset_scores[ticker]
        cost = shares * current_prices[ticker]
        total_portfolio_cost += cost
        
        recommendation = {
            'ticker': ticker,
            'score': float(score),  # Use the score variable defined above
            'shares': int(shares),  # Ensure it's a Python int
            'current_price': float(current_prices[ticker]),  # Ensure it's a Python float
            'total_cost': float(cost),  # Ensure it's a Python float
            'volatility': float(volatilities[ticker]),  # Ensure it's a Python float
            'rule_results': make_json_safe(rule_results_dict[ticker]),
            'fundamentals': make_json_safe(fundamentals_dict[ticker]),
            'hedge_signals': make_json_safe(hedge_signals_dict[ticker]),
            'event_signals': make_json_safe(event_signals_dict[ticker])
        }
        recommendations.append(recommendation)
    
    print(f"DEBUG: Portfolio summary - {len(recommendations)} positions, Total cost: ${total_portfolio_cost:.2f}, Budget: ${actual_capital}")
    
    if total_portfolio_cost > actual_capital:
        print(f"WARNING: Portfolio cost (${total_portfolio_cost:.2f}) exceeds budget (${actual_capital})!")
    
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    with progress_lock:
        global_analysis_progress.update({
            'processed': total,
            'percentage': 100,
            'status': 'Analysis complete!'
        })
    
    return recommendations
if __name__ == '__main__':
    # For local development
    app.run(debug=True, port=9999)
else:
    # For production (Render)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))


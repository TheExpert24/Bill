from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Asset, PriceData, News, User, UserRecommendation, UserPortfolio
import pandas as pd
import os
from datetime import datetime

# Create database engine
engine = create_engine('sqlite:///market_data.db')

# Create all tables
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def init_database():
    """Initialize the database with all tables"""
    try:
        Base.metadata.create_all(engine)
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")

def save_asset(session, ticker, name=None, sector=None, industry=None, market_cap=None, pe_ratio=None, dividend_yield=None):
    asset = session.query(Asset).filter_by(ticker=ticker).first()
    if not asset:
        asset = Asset(ticker=ticker, name=name, sector=sector, industry=industry, market_cap=market_cap, pe_ratio=pe_ratio, dividend_yield=dividend_yield)
        session.add(asset)
        session.commit()
    return asset.id

def save_price_data(session, asset_id, df):
    """Save price data in bulk for better performance."""
    price_data = [
        PriceData(
            asset_id=asset_id,
            date=index,
            open_price=row['Open'],
            high_price=row['High'],
            low_price=row['Low'],
            close_price=row['Close'],
            volume=row['Volume'],
            adj_close=row.get('Adj Close', row['Close'])
        )
        for index, row in df.iterrows()
    ]
    session.bulk_save_objects(price_data)
    session.commit()

def save_news(session, asset_id, headlines, source='scraped', published_at=None, sentiment_score=None):
    for headline in headlines:
        news = News(
            asset_id=asset_id,
            headline=headline,
            source=source,
            published_at=published_at,
            sentiment_score=sentiment_score
        )
        session.add(news)
    session.commit()

def get_asset_data(session, ticker):
    asset = session.query(Asset).filter_by(ticker=ticker).first()
    if asset:
        price_data = session.query(PriceData).filter_by(asset_id=asset.id).all()
        news = session.query(News).filter_by(asset_id=asset.id).all()
        return asset, price_data, news
    return None, None, None

def get_user_recommendations(session, user_id):
    """Get all recommendations for a specific user"""
    try:
        recommendations = session.query(UserRecommendation).filter_by(user_id=user_id).order_by(UserRecommendation.created_at.desc()).all()
        return recommendations
    except Exception as e:
        print(f"Error fetching user recommendations: {e}")
        return []

def is_first_time_user(session, user_id):
    """Check if this is the user's first recommendation"""
    recommendations = session.query(UserRecommendation).filter_by(user_id=user_id).count()
    return recommendations == 0

def get_user_portfolio(session, user_id):
    """Get user's current portfolio positions"""
    try:
        positions = session.query(UserPortfolio).filter_by(user_id=user_id).all()
        return positions
    except Exception as e:
        print(f"Error fetching user portfolio: {e}")
        return []

def update_user_portfolio(session, user_id, recommendations):
    """Update user's portfolio based on new recommendations"""
    try:
        # Get current positions
        current_positions = {pos.ticker: pos for pos in get_user_portfolio(session, user_id)}
        
        # Update positions based on recommendations
        for rec in recommendations:
            ticker = rec['ticker']
            shares = rec['shares']
            price = rec.get('current_price', rec.get('price', 0))  # Handle both field names
            
            if ticker in current_positions:
                # Update existing position
                position = current_positions[ticker]
                # Simple average cost calculation
                total_shares = position.shares + shares
                total_cost = (position.shares * position.avg_price) + (shares * price)
                position.avg_price = total_cost / total_shares
                position.shares = total_shares
                position.updated_at = datetime.utcnow()
            else:
                # Add new position
                new_position = UserPortfolio(
                    user_id=user_id,
                    ticker=ticker,
                    shares=shares,
                    avg_price=price
                )
                session.add(new_position)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating user portfolio: {e}")
        return False

def save_user_recommendation(session, user_id, capital, risk_tolerance, goal, time_horizon, recommendations_json, prediction_json, is_first_time):
    """Save a new user recommendation"""
    try:
        recommendation = UserRecommendation(
            user_id=user_id,
            capital=capital,
            risk_tolerance=risk_tolerance,
            goal=goal,
            time_horizon=time_horizon,
            recommendations_json=recommendations_json,
            prediction_json=prediction_json,
            is_first_time=is_first_time
        )
        session.add(recommendation)
        session.commit()
        return recommendation.id
    except Exception as e:
        session.rollback()
        print(f"Error saving user recommendation: {e}")
        return None

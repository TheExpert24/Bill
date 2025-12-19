from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    google_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    profile_pic = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    recommendations = relationship("UserRecommendation", back_populates="user")
    portfolio_positions = relationship("UserPortfolio", back_populates="user")

class Asset(Base):
    __tablename__ = 'assets'
    id = Column(Integer, primary_key=True)
    ticker = Column(String, unique=True, nullable=False)
    name = Column(String)
    sector = Column(String)
    industry = Column(String)
    market_cap = Column(Float)
    pe_ratio = Column(Float)
    dividend_yield = Column(Float)

    price_data = relationship("PriceData", back_populates="asset")
    news = relationship("News", back_populates="asset")

class PriceData(Base):
    __tablename__ = 'price_data'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    date = Column(DateTime, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    adj_close = Column(Float)

    asset = relationship("Asset", back_populates="price_data")

class News(Base):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)
    asset_id = Column(Integer, ForeignKey('assets.id'))
    headline = Column(Text, nullable=False)
    source = Column(String)
    published_at = Column(DateTime)
    url = Column(String)
    sentiment_score = Column(Float)

    asset = relationship("Asset", back_populates="news")

class UserPortfolio(Base):
    __tablename__ = 'user_portfolio'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    ticker = Column(String, nullable=False)
    shares = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="portfolio_positions")

class UserRecommendation(Base):
    __tablename__ = 'user_recommendations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    capital = Column(Float)
    risk_tolerance = Column(Float)
    goal = Column(String)
    time_horizon = Column(String)
    recommendations_json = Column(Text)  # Store recommendations as JSON
    prediction_json = Column(Text)  # Store buy/sell/keep predictions as JSON
    is_first_time = Column(Boolean, default=True)  # Track if this is first recommendation
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")

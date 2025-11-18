from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

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

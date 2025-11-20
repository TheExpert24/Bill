from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Asset, PriceData, News
import pandas as pd

engine = create_engine('sqlite:///market_data.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

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

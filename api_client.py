import yfinance as yf
from newsapi import NewsApiClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class MarketDataClient:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

    def get_price_data(self, ticker, period='1y'):
        """Fetch historical price data for a ticker."""
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        if data.empty:
            raise ValueError(f"No price data found for {ticker}")
        return data

    def get_price_data_batch(self, tickers, period='1y'):
        """Fetch historical price data for multiple tickers."""
        data = yf.download(tickers, period=period, group_by='ticker', threads=True)
        return data

    def get_fundamentals(self, ticker):
        """Fetch fundamental data for a ticker."""
        stock = yf.Ticker(ticker)
        info = stock.info
        return info

    def get_news_headlines(self, query='finance', language='en', page_size=10):
        """Fetch recent news headlines."""
        top_headlines = self.newsapi.get_top_headlines(q=query, language=language, page_size=page_size)
        return top_headlines['articles']

    def get_company_news(self, ticker, page_size=10):
        """Fetch news specific to a company."""
        query = ticker
        return self.get_news_headlines(query=query, page_size=page_size)

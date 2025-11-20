import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

def get_sp500_tickers():
    """Fetch list of S&P 500 tickers from Wikipedia."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'class': 'wikitable'})
    tickers = []
    if table:
        rows = table.find_all('tr')[1:]
        for row in rows:
            cols = row.find_all('td')
            if cols:
                ticker = cols[0].text.strip()
                tickers.append(ticker)
    return tickers

def get_all_us_tickers():
    """Fetch all US tickers from S&P 500."""
    return get_sp500_tickers()

def get_sample_us_tickers(limit=50):
    """Get a sample of US tickers for faster processing."""
    all_tickers = get_all_us_tickers()
    return all_tickers[:limit]

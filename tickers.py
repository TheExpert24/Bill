import requests
from bs4 import BeautifulSoup
import yfinance as yf
import pandas as pd

def get_sp500_tickers():
    """Fetch list of S&P 500 tickers from Wikipedia."""
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    table = soup.find('table', {'id': 'constituents'})
    tickers = []
    if table:
        rows = table.find_all('tr')[1:]  # Skip header
        for row in rows:
            cols = row.find_all('td')
            if cols:
                ticker = cols[0].text.strip()
                tickers.append(ticker)
    return tickers

def get_all_us_tickers():
    """Fetch all US tickers from a static dataset."""
    # Replace 'path_to_tickers.csv' with the actual path to your dataset
    tickers_df = pd.read_csv('path_to_tickers.csv')  # Ensure the CSV contains a 'ticker' column
    return tickers_df['ticker'].tolist()

def get_sample_us_tickers(limit=50):
    """Get a sample of US tickers for faster processing."""
    all_tickers = get_all_us_tickers()
    return all_tickers[:limit]

import requests
from bs4 import BeautifulSoup

class NewsScraper:
    def __init__(self):
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

    def scrape_yahoo_news(self, ticker, num_headlines=10):
        """Scrape recent news headlines from Yahoo Finance for a ticker."""
        url = f'https://finance.yahoo.com/quote/{ticker}/news'
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')
        headlines = []
        for item in soup.find_all('h3', class_='Mb(5px)'):
            if len(headlines) < num_headlines:
                headlines.append(item.text.strip())
        return headlines

    def scrape_general_news(self, query, site='news.google.com', num_headlines=10):
        """Basic scraper for general news - placeholder for more complex scraping."""
        # This is a simplified example; real scraping might need more logic
        url = f'https://news.google.com/search?q={query}'
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'lxml')
        headlines = []
        for item in soup.find_all('h3'):
            if len(headlines) < num_headlines:
                headlines.append(item.text.strip())
        return headlines

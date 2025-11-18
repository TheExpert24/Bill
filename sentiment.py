import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download VADER lexicon if not already
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

sia = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """Analyze sentiment of text using VADER."""
    scores = sia.polarity_scores(text)
    return scores['compound']  # -1 to 1

def batch_analyze_sentiment(texts):
    """Analyze sentiment for a list of texts."""
    return [analyze_sentiment(text) for text in texts]

def average_sentiment(sentiment_scores):
    """Calculate average sentiment score."""
    return sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0

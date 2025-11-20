import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sentiment import analyze_sentiment

class EventDrivenEngine:
    """
    Event-driven analysis engine for hedge fund-style trading.
    Monitors news, earnings, and market events to generate trading signals.
    """
    
    def __init__(self, event_window=5):
        self.event_window = event_window
        self.event_keywords = {
            'positive': [
                'beat', 'exceed', 'growth', 'profit', 'surge', 'gain', 'rise',
                'upgrade', 'bullish', 'acquisition', 'partnership', 'innovation',
                'breakthrough', 'strong', 'outperform', 'record', 'expansion'
            ],
            'negative': [
                'miss', 'decline', 'loss', 'fall', 'drop', 'downgrade', 'bearish',
                'lawsuit', 'scandal', 'weak', 'underperform', 'layoff', 'closure',
                'warning', 'concern', 'investigation', 'fine', 'penalty'
            ],
            'earnings': [
                'earnings', 'eps', 'revenue', 'quarter', 'q1', 'q2', 'q3', 'q4',
                'fiscal', 'guidance', 'forecast'
            ],
            'merger': [
                'merger', 'acquisition', 'takeover', 'buyout', 'deal', 'offer'
            ],
            'product': [
                'launch', 'release', 'product', 'service', 'unveil', 'announce'
            ],
            'management': [
                'ceo', 'cfo', 'executive', 'board', 'director', 'resign', 'appoint'
            ]
        }
    
    def classify_event_type(self, headline):
        """
        Classify news headline into event categories.
        """
        headline_lower = headline.lower()
        events = []
        
        for category, keywords in self.event_keywords.items():
            if category not in ['positive', 'negative']:
                if any(keyword in headline_lower for keyword in keywords):
                    events.append(category)
        
        if not events:
            events.append('general')
        
        return events
    
    def score_event_sentiment(self, headline):
        """
        Score event sentiment with enhanced category detection.
        """
        sentiment = analyze_sentiment(headline)
        headline_lower = headline.lower()
        
        positive_count = sum(1 for word in self.event_keywords['positive'] 
                           if word in headline_lower)
        negative_count = sum(1 for word in self.event_keywords['negative'] 
                           if word in headline_lower)
        
        if positive_count > negative_count:
            sentiment_score = min(sentiment + 0.2, 1.0)
        elif negative_count > positive_count:
            sentiment_score = max(sentiment - 0.2, -1.0)
        else:
            sentiment_score = sentiment
        
        return sentiment_score
    
    def detect_earnings_event(self, headlines, price_data):
        """
        Detect earnings-related events and price reactions.
        Returns signal based on earnings surprise + price momentum.
        """
        earnings_headlines = [h for h in headlines 
                             if any(kw in h.lower() for kw in self.event_keywords['earnings'])]
        
        if not earnings_headlines:
            return {'detected': False, 'signal': 0, 'sentiment': 0}
        
        sentiments = [self.score_event_sentiment(h) for h in earnings_headlines]
        avg_sentiment = np.mean(sentiments)
        
        if len(price_data) >= self.event_window:
            close = price_data['Close']
            recent_return = (close.iloc[-1] - close.iloc[-self.event_window]) / close.iloc[-self.event_window]
            
            if avg_sentiment > 0.3 and recent_return > 0.03:
                signal = 2
            elif avg_sentiment > 0 and recent_return > 0:
                signal = 1
            elif avg_sentiment < -0.3 and recent_return < -0.03:
                signal = -2
            elif avg_sentiment < 0 and recent_return < 0:
                signal = -1
            else:
                signal = 0
        else:
            signal = 1 if avg_sentiment > 0.3 else (-1 if avg_sentiment < -0.3 else 0)
        
        return {
            'detected': True,
            'signal': signal,
            'sentiment': avg_sentiment,
            'headlines': earnings_headlines
        }
    
    def detect_ma_event(self, headlines):
        """
        Detect merger & acquisition events.
        M&A typically creates price jumps and arbitrage opportunities.
        """
        ma_headlines = [h for h in headlines 
                       if any(kw in h.lower() for kw in self.event_keywords['merger'])]
        
        if not ma_headlines:
            return {'detected': False, 'signal': 0}
        
        sentiments = [self.score_event_sentiment(h) for h in ma_headlines]
        avg_sentiment = np.mean(sentiments)
        
        signal = 2 if avg_sentiment > 0.2 else 1
        
        return {
            'detected': True,
            'signal': signal,
            'sentiment': avg_sentiment,
            'headlines': ma_headlines
        }
    
    def detect_product_launch(self, headlines):
        """
        Detect product launch events.
        Major product launches can drive momentum.
        """
        product_headlines = [h for h in headlines 
                            if any(kw in h.lower() for kw in self.event_keywords['product'])]
        
        if not product_headlines:
            return {'detected': False, 'signal': 0}
        
        sentiments = [self.score_event_sentiment(h) for h in product_headlines]
        avg_sentiment = np.mean(sentiments)
        
        signal = 1 if avg_sentiment > 0.2 else 0
        
        return {
            'detected': True,
            'signal': signal,
            'sentiment': avg_sentiment,
            'headlines': product_headlines
        }
    
    def detect_management_change(self, headlines):
        """
        Detect management change events.
        Leadership changes can signal strategic shifts.
        """
        mgmt_headlines = [h for h in headlines 
                         if any(kw in h.lower() for kw in self.event_keywords['management'])]
        
        if not mgmt_headlines:
            return {'detected': False, 'signal': 0}
        
        sentiments = [self.score_event_sentiment(h) for h in mgmt_headlines]
        avg_sentiment = np.mean(sentiments)
        
        if 'resign' in ' '.join(mgmt_headlines).lower():
            signal = -1
        else:
            signal = 1 if avg_sentiment > 0.2 else 0
        
        return {
            'detected': True,
            'signal': signal,
            'sentiment': avg_sentiment,
            'headlines': mgmt_headlines
        }
    
    def compute_momentum_after_event(self, price_data, event_date_index=-1, 
                                     lookback=5, lookforward=5):
        """
        Compute price momentum before and after an event.
        Used to validate if event had real price impact.
        """
        close = price_data['Close']
        
        if abs(event_date_index) > len(close) - lookback - lookforward:
            return {'pre_event_return': 0, 'post_event_return': 0}
        
        event_idx = event_date_index if event_date_index >= 0 else len(close) + event_date_index
        
        if event_idx - lookback < 0 or event_idx + lookforward >= len(close):
            return {'pre_event_return': 0, 'post_event_return': 0}
        
        pre_price = close.iloc[event_idx - lookback]
        event_price = close.iloc[event_idx]
        post_price = close.iloc[min(event_idx + lookforward, len(close) - 1)]
        
        pre_return = (event_price - pre_price) / pre_price if pre_price > 0 else 0
        post_return = (post_price - event_price) / event_price if event_price > 0 else 0
        
        return {
            'pre_event_return': pre_return,
            'post_event_return': post_return,
            'momentum_shift': post_return - pre_return
        }
    
    def analyze_news_flow(self, headlines, timestamps=None):
        """
        Analyze news flow intensity and sentiment trends.
        Increasing news flow often precedes price moves.
        """
        if not headlines:
            return {
                'flow_intensity': 0,
                'sentiment_trend': 0,
                'recent_sentiment': 0
            }
        
        sentiments = [self.score_event_sentiment(h) for h in headlines]
        
        recent_window = min(self.event_window, len(headlines))
        recent_sentiments = sentiments[-recent_window:]
        historical_sentiments = sentiments[:-recent_window] if len(sentiments) > recent_window else sentiments
        
        recent_avg = np.mean(recent_sentiments)
        historical_avg = np.mean(historical_sentiments) if historical_sentiments else recent_avg
        
        sentiment_trend = recent_avg - historical_avg
        
        flow_intensity = len(headlines) / max(1, len(set(headlines)))
        
        return {
            'flow_intensity': flow_intensity,
            'sentiment_trend': sentiment_trend,
            'recent_sentiment': recent_avg,
            'total_news': len(headlines)
        }
    
    def generate_event_signal(self, headlines, price_data):
        """
        Generate composite event-driven signal combining all event types.
        """
        earnings = self.detect_earnings_event(headlines, price_data)
        ma = self.detect_ma_event(headlines)
        product = self.detect_product_launch(headlines)
        mgmt = self.detect_management_change(headlines)
        news_flow = self.analyze_news_flow(headlines)
        
        total_signal = 0
        total_signal += earnings['signal']
        total_signal += ma['signal']
        total_signal += product['signal']
        total_signal += mgmt['signal']
        
        if news_flow['sentiment_trend'] > 0.2:
            total_signal += 1
        elif news_flow['sentiment_trend'] < -0.2:
            total_signal -= 1
        
        if news_flow['flow_intensity'] > 2:
            total_signal += 1
        
        total_signal = max(-5, min(5, total_signal))
        
        return {
            'composite_signal': total_signal,
            'earnings_event': earnings,
            'ma_event': ma,
            'product_event': product,
            'management_event': mgmt,
            'news_flow': news_flow
        }
    
    def filter_by_market_regime(self, signal, volatility_regime):
        """
        Adjust event signals based on broader market volatility regime.
        In high volatility, reduce position sizes even with strong signals.
        """
        if volatility_regime == 'high':
            adjusted_signal = signal * 0.5
        elif volatility_regime == 'low':
            adjusted_signal = signal * 1.2
        else:
            adjusted_signal = signal
        
        return adjusted_signal

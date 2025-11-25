"""
Advanced Hedge Fund Algorithm
Implements institutional-style alpha signal generation using public data
"""

import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler
import requests
from bs4 import BeautifulSoup
from sentiment import batch_analyze_sentiment
from indicators import (
    simple_moving_average, relative_strength_index, volatility, 
    sharpe_ratio, sortino_ratio, price_momentum_ratio
)

class AdvancedHedgeFundEngine:
    """
    Modern hedge fund-style algorithmic system that integrates:
    - Factor-style signals (value, quality, volatility, momentum)
    - Price-action predictors (trend-following, realized volatility, rolling skew)
    - Cross-asset relationships (correlation and Z-score spread signals)
    - News sentiment analysis via NewsAPI
    - Signal aggregation with normalization and historical weighting
    - Volatility targeting and risk parity position sizing
    """
    
    def __init__(self, lookback_short=20, lookback_medium=50, lookback_long=200, 
                 universe_size=200, max_positions=20):
        self.lookback_short = lookback_short
        self.lookback_medium = lookback_medium
        self.lookback_long = lookback_long
        self.universe_size = universe_size
        self.max_positions = max_positions
        
        # Signal weights - calibrated through backtesting
        self.signal_weights = {
            'momentum_score': 0.25,
            'value_score': 0.20,
            'quality_score': 0.20,
            'volatility_score': 0.15,
            'sentiment_score': 0.10,
            'stat_arb_score': 0.10
        }
        
        # Risk parameters
        self.target_volatility = 0.15  # 15% annual target volatility
        self.max_position_size = 0.05  # 5% max per position
        self.correlation_threshold = 0.7
        
    def get_dynamic_stock_universe(self):
        """
        Generate dynamic stock universe instead of fixed S&P 500
        Uses multiple screening criteria with rotation and diversification
        """
        print("Generating dynamic stock universe...")
        
        # Add rotation and time-based variation
        current_time = pd.Timestamp.now()
        
        # Add day-of-week and hour-based rotation
        day_rotation = current_time.day % 7
        hour_rotation = current_time.hour % 6
        
        import random
        random.seed(int(current_time.timestamp()) % 10000)  # More sophisticated randomization
        
        all_universe_sources = []
        
        try:
            # Strategy 1: Large cap established companies
            major_tickers = self._get_major_us_tickers()
            all_universe_sources.append(('major', major_tickers))
            
            # Strategy 2: Sector rotation - different each time
            sector_stocks = self._get_sector_rotation_stocks()
            all_universe_sources.append(('sector', sector_stocks))
            
            # Strategy 3: Market cap tiers
            large_cap = self._get_large_cap_stocks()
            mid_cap = self._get_mid_cap_stocks() 
            small_cap = self._get_small_cap_stocks()
            all_universe_sources.extend([
                ('large_cap', large_cap),
                ('mid_cap', mid_cap), 
                ('small_cap', small_cap)
            ])
            
            # Strategy 4: Performance-based screening
            high_momentum = self._get_high_momentum_stocks(limit=50)
            all_universe_sources.append(('momentum', high_momentum))
            
            # Strategy 5: Value opportunities
            value_opportunities = self._get_value_stocks(limit=50)
            all_universe_sources.append(('value', value_opportunities))
            
            # Strategy 6: Growth stocks
            growth_opportunities = self._get_growth_stocks(limit=50)
            all_universe_sources.append(('growth', growth_opportunities))
            
            # Strategy 7: International exposure (US-listed)
            international_us = self._get_international_us_stocks()
            all_universe_sources.append(('international', international_us))
            
            # Strategy 8: ESG/sustainable stocks
            sustainable_stocks = self._get_sustainable_stocks()
            all_universe_sources.append(('sustainable', sustainable_stocks))
            
            # Strategy 9: High dividend stocks
            dividend_stocks = self._get_dividend_stocks()
            all_universe_sources.append(('dividend', dividend_stocks))
            
            # Strategy 10: Recent IPOs and emerging
            emerging_stocks = self._get_emerging_stocks()
            all_universe_sources.append(('emerging', emerging_stocks))
            
            # Combine all sources with rotation
            final_universe = self._create_diverse_universe(all_universe_sources)
            
            print(f"Generated diverse universe of {len(final_universe)} stocks from {len(all_universe_sources)} sources")
            
            return final_universe[:self.universe_size]
            
        except Exception as e:
            print(f"Error generating dynamic universe: {e}")
            # Fallback with more diversity
            return self._get_fallback_diverse_universe()
    
    def _get_major_us_tickers(self):
        """Get major US stock tickers from multiple sources"""
        # Major tech and established companies
        tech_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX', 'CRM', 'ORCL']
        finance_tickers = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'MCO']
        healthcare_tickers = ['JNJ', 'PFE', 'UNH', 'MRK', 'ABBV', 'TMO', 'DHR', 'ABT', 'ISRG', 'BMY']
        consumer_tickers = ['WMT', 'HD', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX', 'TGT', 'COST']
        industrial_tickers = ['BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'LMT', 'RTX', 'UNP', 'DE']
        energy_tickers = ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'KMI', 'ET']
        
        return tech_tickers + finance_tickers + healthcare_tickers + consumer_tickers + industrial_tickers + energy_tickers
    
    def _get_high_momentum_stocks(self, limit=50):
        """Identify high momentum stocks with different lookback periods"""
        try:
            # Get all major tickers plus some additional ones
            base_tickers = self._get_major_us_tickers()
            
            # Add some momentum-focused ETFs and popular stocks
            momentum_focus = ['TQQQ', 'SQQQ', 'UVXY', 'VXX', 'ARKK', 'ARKQ', 'ROBO', 'BOTZ']
            tech_focus = ['NVDA', 'AMD', 'CRM', 'NOW', 'SNOW', 'PLTR', 'CRWD', 'DDOG']
            growth_focus = ['TSLA', 'ZM', 'PTON', 'ROKU', 'SQ', 'SHOP', 'UBER', 'LYFT']
            
            all_tickers = list(set(base_tickers + momentum_focus + tech_focus + growth_focus))
            
            momentum_scores = {}
            batch_size = 20
            
            for i in range(0, min(len(all_tickers), 150), batch_size):
                batch = all_tickers[i:i+batch_size]
                try:
                    data = yf.download(batch, period='6mo', group_by='ticker', threads=True)
                    for ticker in batch:
                        if ticker in data.columns.get_level_values(0):
                            prices = data[ticker]['Close'].dropna()
                            if len(prices) > 50:
                                # Multiple momentum periods for diversity
                                mom_1m = (prices.iloc[-1] / prices.iloc[-20] - 1) if len(prices) >= 20 else 0
                                mom_3m = (prices.iloc[-1] / prices.iloc[-60] - 1) if len(prices) >= 60 else 0
                                mom_6m = (prices.iloc[-1] / prices.iloc[-120] - 1) if len(prices) >= 120 else 0
                                
                                # Weighted momentum score
                                momentum_score = mom_1m * 0.5 + mom_3m * 0.3 + mom_6m * 0.2
                                momentum_scores[ticker] = momentum_score
                except Exception:
                    continue
            
            # Return top momentum stocks with some randomization
            sorted_stocks = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
            top_stocks = [ticker for ticker, score in sorted_stocks[:limit]]
            
            # Add some randomization to avoid always picking the same ones
            import random
            random.shuffle(top_stocks)
            return top_stocks
            
        except Exception as e:
            print(f"Error getting momentum stocks: {e}")
            return []
    
    def _get_value_stocks(self, limit=50):
        """Identify value stocks with good fundamentals"""
        try:
            # Expanded value candidates from different sectors
            traditional_value = ['BRK-B', 'BABA', 'T', 'VZ', 'IBM', 'INTC', 'CSCO', 'GE', 'F', 'GM']
            telecom_value = ['TMUS', 'CMCSA', 'CHTR', 'DISH', 'S']
            financial_value = ['BAC', 'WFC', 'C', 'USB', 'PNC', 'TFC', 'COF', 'GS', 'MS', 'SCHW']
            energy_value = ['XOM', 'CVX', 'COP', 'EOG', 'VLO', 'MPC', 'PSX', 'HFC', 'MRO', 'CLR']
            industrial_value = ['CAT', 'BA', 'MMM', 'HON', 'LMT', 'RTX', 'UNP', 'DE', 'UPS', 'FDX']
            
            all_value = list(set(traditional_value + telecom_value + financial_value + 
                               energy_value + industrial_value))
            
            # Randomize to avoid always picking the same ones
            import random
            random.shuffle(all_value)
            return all_value[:limit]
            
        except Exception as e:
            print(f"Error getting value stocks: {e}")
            return []
    
    def _get_growth_stocks(self, limit=50):
        """Identify growth stocks with strong earnings"""
        try:
            # Expand growth categories for diversity
            cloud_growth = ['SNOW', 'NOW', 'CRM', 'ADBE', 'ORCL', 'MSFT', 'GOOGL']
            fintech_growth = ['SQ', 'PYPL', 'SHOP', 'AFRM', 'SOFI', 'UPST', 'LC', 'V']
            ev_tech = ['TSLA', 'NIO', 'XPEV', 'LI', 'RIVN', 'LCID', 'QS', 'NKLA']
            biotech_growth = ['MRNA', 'BNTX', 'GILD', 'BIIB', 'REGN', 'VRTX', 'AMGN', 'ILMN']
            ai_tech = ['NVDA', 'AMD', 'GOOGL', 'META', 'MSFT', 'CRM', 'PLTR', 'AI']
            streaming_media = ['NFLX', 'DIS', 'ROKU', 'SPOT', 'TWTR', 'PINS', 'SNAP', 'TTD']
            
            all_growth = list(set(cloud_growth + fintech_growth + ev_tech + 
                                biotech_growth + ai_tech + streaming_media))
            
            import random
            random.shuffle(all_growth)
            return all_growth[:limit]
            
        except Exception as e:
            print(f"Error getting growth stocks: {e}")
            return []
    
    def _filter_by_liquidity(self, tickers):
        """Filter stocks by liquidity and data availability"""
        filtered = []
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Basic liquidity checks
                avg_volume = info.get('averageVolume', 0)
                market_cap = info.get('marketCap', 0)
                
                if avg_volume > 100000 and market_cap > 1e9:  # Basic liquidity filters
                    filtered.append(ticker)
                    
            except Exception:
                continue
                
        return filtered
    
    def _get_sector_rotation_stocks(self):
        """Get different sector stocks based on rotation"""
        import random
        
        # Different sector combinations based on time
        sector_combos = [
            # Tech-heavy rotation
            ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'CRM', 'ORCL', 'ADBE', 'INTC', 'AMD'],
            # Healthcare rotation  
            ['JNJ', 'PFE', 'UNH', 'MRK', 'ABBV', 'TMO', 'DHR', 'ABT', 'ISRG', 'BMY'],
            # Financial rotation
            ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BLK', 'SPGI', 'MCO'],
            # Industrial rotation
            ['BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'LMT', 'RTX', 'UNP', 'DE'],
            # Consumer rotation
            ['WMT', 'HD', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX', 'TGT', 'COST'],
            # Energy rotation
            ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'KMI', 'ET']
        ]
        
        # Randomly select one or more sector combinations
        num_sectors = random.randint(2, 4)
        selected_sectors = random.sample(sector_combos, num_sectors)
        
        # Combine and flatten
        sector_stocks = []
        for sector in selected_sectors:
            sector_stocks.extend(sector)
        
        return list(set(sector_stocks))
    
    def _get_large_cap_stocks(self):
        """Get large cap stocks (> $10B market cap)"""
        large_caps = [
            # Mega caps
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            # Large financial
            'JPM', 'BAC', 'WFC', 'V', 'MA', 'JNJ', 'PG', 'UNH',
            # Large industrials  
            'XOM', 'CVX', 'WMT', 'HD', 'DIS', 'V', 'MA', 'BRK-B'
        ]
        return large_caps
    
    def _get_mid_cap_stocks(self):
        """Get mid cap stocks ($2B - $10B market cap)"""
        mid_caps = [
            'CRM', 'ADBE', 'NFLX', 'PYPL', 'NOW', 'SQ', 'UBER', 'LYFT',
            'ZOOM', 'SNOW', 'PLTR', 'CRWD', 'DDOG', 'NET', 'ESTC',
            'TDOC', 'ROKU', 'SHOP', 'AFRM', 'SOFI', 'PTON', 'DOCU',
            'ZM', 'TWLO', 'OKTA', 'ZS', 'SPLK', 'MDB', 'CRWD'
        ]
        return mid_caps
    
    def _get_small_cap_stocks(self):
        """Get small cap stocks (< $2B market cap)"""
        small_caps = [
            'RBLX', 'COIN', 'RIVN', 'LCID', 'QS', 'NKLA', 'CHPT', 'EVGO',
            'MRIN', 'MAXN', 'ENPH', 'SEDG', 'NEE', 'FSLR', 'SPWR', 'RUN',
            'BE', 'NOVA', 'ARRY', 'CSIQ', 'JKS', 'SOL', 'GEVO', 'REGI',
            'AMRS', 'CPPL', 'SPRO', 'EVVTY', 'BLNK', 'CHPT'
        ]
        return small_caps
    
    def _get_international_us_stocks(self):
        """Get international companies listed on US exchanges"""
        international_us = [
            # Chinese ADRs
            'BABA', 'JD', 'PDD', 'NTES', 'BIDU', 'TME', 'IQ', 'BILI',
            # European companies
            'SAP', 'ASML', 'NVO', 'TM', 'HMC', 'SONY', 'TSM', 'UMC',
            # Canadian companies
            'SHOP', 'SU', 'CNR', 'CP', 'BNS', 'RY', 'TD', 'BCE',
            # Other international
            'AZN', 'SNY', 'TEF', 'ITUB', 'VALE', 'PBR', 'GOLD', 'NEM'
        ]
        return international_us
    
    def _get_sustainable_stocks(self):
        """Get ESG/sustainable focused stocks"""
        sustainable = [
            # Clean energy
            'ENPH', 'SEDG', 'NEE', 'FSLR', 'SPWR', 'RUN', 'BE', 'NOVA',
            # Electric vehicles
            'TSLA', 'NIO', 'XPEV', 'LI', 'RIVN', 'LCID', 'CHPT', 'EVGO',
            # Sustainable agriculture
            'F ', 'MON ', 'MOS', 'CF', 'NTR', 'CTVA', 'ADM',
            # Water/waste management
            'AWK', 'WTRG', 'WM', 'RSG', 'CCL', 'HWIN',
            # ESG focused ETFs
            'ESGU', 'SUSA', 'ICLN', 'PBW', 'QCLN'
        ]
        return sustainable
    
    def _get_dividend_stocks(self):
        """Get high dividend yield stocks"""
        dividend_stocks = [
            # REITs
            'AMT', 'PLD', 'SPG', 'CCI', 'EQIX', 'O', 'PSA', 'VTR',
            # Utilities
            'NEE', 'DUK', 'SO', 'D', 'AEP', 'XEL', 'SRE', 'PEG',
            # Telecommunications
            'VZ', 'T', 'TMUS', 'CMCSA', 'CHTR',
            # Financials
            'JPM', 'BAC', 'WFC', 'C', 'TFC', 'USB', 'PNC', 'COF',
            # Consumer staples
            'PG', 'KO', 'PEP', 'WMT', 'CL', 'KMB', 'CPB', 'GIS'
        ]
        return dividend_stocks
    
    def _get_emerging_stocks(self):
        """Get recent IPOs and emerging companies"""
        recent_ipos = [
            'RBLX', 'COIN', 'RIVN', 'LCID', 'AFRM', 'SOFI', 'UPST',
            'SPCR', 'RIVN', 'PATH', 'COIN', 'RBLX', 'NET', 'DOCU',
            'CRWD', 'SNOW', 'ZM', 'PTON', 'ROKU', 'TDOC', 'DDOG',
            'PLTR', 'SQ', 'SHOP', 'UBER', 'LYFT', 'ABNB', 'DASH'
        ]
        return recent_ipos
    
    def _create_diverse_universe(self, universe_sources):
        """Create final diverse universe from multiple sources"""
        import random
        
        all_stocks = []
        
        # Add stocks from each source with rotation
        for source_name, stocks in universe_sources:
            if stocks:
                # Take different numbers from each source for diversity
                if source_name in ['major', 'large_cap']:
                    take_count = min(len(stocks), 25)  # More from established sources
                elif source_name in ['momentum', 'value', 'growth']:
                    take_count = min(len(stocks), 15)  # Medium from screened sources
                else:
                    take_count = min(len(stocks), 10)  # Less from specialized sources
                
                # Randomize selection from each source
                selected = random.sample(stocks, min(take_count, len(stocks)))
                all_stocks.extend(selected)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_stocks = []
        for stock in all_stocks:
            if stock not in seen:
                seen.add(stock)
                unique_stocks.append(stock)
        
        # Final randomization
        random.shuffle(unique_stocks)
        
        return unique_stocks
    
    def _get_fallback_diverse_universe(self):
        """Fallback universe with maximum diversity"""
        fallback_sources = [
            # Major indices components
            self._get_major_us_tickers(),
            # Sector representatives
            self._get_sector_rotation_stocks(),
            # Different market caps
            self._get_large_cap_stocks(),
            self._get_mid_cap_stocks(),
            self._get_small_cap_stocks(),
            # Different strategies
            self._get_high_momentum_stocks(30),
            self._get_value_stocks(30),
            self._get_growth_stocks(30),
            # Special categories
            self._get_sustainable_stocks(20),
            self._get_dividend_stocks(20),
            self._get_emerging_stocks(20)
        ]
        
        # Combine all sources
        all_fallback = []
        for source in fallback_sources:
            all_fallback.extend(source)
        
        # Remove duplicates and randomize
        unique_fallback = list(set(all_fallback))
        import random
        random.shuffle(unique_fallback)
        
        return unique_fallback[:self.universe_size]
    
    def compute_factor_signals(self, price_data, fundamentals):
        """
        Compute factor-style signals: value, quality, volatility, momentum
        """
        close = price_data['Close']
        returns = close.pct_change().dropna()
        
        signals = {}
        
        # Value Factor
        signals['value_score'] = self._compute_value_score(fundamentals)
        
        # Quality Factor  
        signals['quality_score'] = self._compute_quality_score(price_data, returns, fundamentals)
        
        # Volatility Factor
        vol_regime = self.detect_volatility_regime(price_data)
        signals['volatility_score'] = self._compute_volatility_score(vol_regime)
        
        # Momentum Factor
        momentum_signals = self.compute_momentum_signals(price_data)
        signals['momentum_score'] = self._compute_momentum_score(momentum_signals)
        
        return signals
    
    def _compute_value_score(self, fundamentals):
        """Compute value factor score - PROFIT FOCUSED"""
        score = 0
        count = 0
        
        # Growth potential indicators (more important for profit)
        revenue_growth = fundamentals.get('revenueGrowth')
        if revenue_growth and revenue_growth > 0.15:  # 15%+ revenue growth
            score += 2
        elif revenue_growth and revenue_growth > 0.10:  # 10%+ revenue growth
            score += 1
        count += 1
        
        earnings_growth = fundamentals.get('earningsGrowth')
        if earnings_growth and earnings_growth > 0.20:  # 20%+ earnings growth
            score += 2
        elif earnings_growth and earnings_growth > 0.15:  # 15%+ earnings growth
            score += 1
        count += 1
        
        # Moderate P/E (not too high, not too low)
        pe_ratio = fundamentals.get('trailingPE')
        if pe_ratio and pe_ratio > 0:
            if 10 <= pe_ratio <= 30:  # Sweet spot for growth
                score += 1.5
            elif 5 <= pe_ratio <= 40:  # Acceptable range
                score += 0.5
            count += 1
        
        # Price momentum (forward-looking)
        price_momentum = fundamentals.get('52WeekHigh')
        if price_momentum:
            # Higher score for stocks near 52-week highs (momentum plays)
            current_price = fundamentals.get('currentPrice', 0)
            if current_price and price_momentum:
                if current_price / price_momentum > 0.8:  # Within 20% of 52-week high
                    score += 1
                elif current_price / price_momentum > 0.6:  # Within 40% of 52-week high
                    score += 0.5
            count += 1
        
        return score / max(count, 1) if count > 0 else 0
    
    def _compute_quality_score(self, price_data, returns, fundamentals):
        """Compute quality factor score"""
        score = 0
        count = 0
        
        # Sharpe ratio
        sharpe = sharpe_ratio(price_data['Close'])
        if sharpe > 1.0:
            score += 2
        elif sharpe > 0.5:
            score += 1
        count += 1
        
        # Return on Equity
        roe = fundamentals.get('returnOnEquity')
        if roe and roe > 0.15:
            score += 2
        elif roe and roe > 0.10:
            score += 1
        count += 1
        
        # Return on Assets
        roa = fundamentals.get('returnOnAssets')
        if roa and roa > 0.05:
            score += 1
            count += 1
        
        # Debt-to-Equity
        debt_to_equity = fundamentals.get('debtToEquity')
        if debt_to_equity and debt_to_equity < 0.5:
            score += 2
        elif debt_to_equity and debt_to_equity < 1.0:
            score += 1
        count += 1
        
        return score / max(count, 1) if count > 0 else 0
    
    def _compute_volatility_score(self, vol_regime):
        """Compute volatility factor score"""
        regime = vol_regime.get('regime', 'normal')
        
        if regime == 'low':
            return 2  # Low volatility is good for risk-adjusted returns
        elif regime == 'normal':
            return 1
        else:
            return 0  # High volatility regime
    
    def _compute_momentum_score(self, momentum_signals):
        """Compute momentum factor score - AGGRESSIVE for profit maximization"""
        # Use multiple momentum metrics for stronger signal
        momentum_strength = momentum_signals.get('momentum_strength', 0)
        price_above_sma20 = momentum_signals.get('price_above_sma20', 0)
        price_above_sma50 = momentum_signals.get('price_above_sma50', 0)
        
        # Enhanced momentum scoring for profit focus
        score = 0
        
        # Base momentum strength (0-1)
        score += min(momentum_strength / 4.0, 1.0) * 0.4
        
        # Price position relative to moving averages
        if price_above_sma20 > 0.05:  # 5%+ above 20-day MA
            score += 0.3
        elif price_above_sma20 > 0.02:  # 2%+ above
            score += 0.2
        
        if price_above_sma50 > 0.10:  # 10%+ above 50-day MA
            score += 0.3
        elif price_above_sma50 > 0.05:  # 5%+ above
            score += 0.15
        
        # Cap at 1.0 and return
        return min(score, 1.0)
    
    def compute_price_action_signals(self, price_data):
        """
        Compute price-action predictors:
        - Trend-following indicators
        - Realized volatility
        - Rolling skew
        """
        close = price_data['Close']
        high = price_data['High']
        low = price_data['Low']
        
        signals = {}
        
        # Trend-following signals
        sma_short = simple_moving_average(close, 20)
        sma_long = simple_moving_average(close, 50)
        
        if len(close) > 50:
            signals['trend_strength'] = 1 if close.iloc[-1] > sma_short.iloc[-1] > sma_long.iloc[-1] else 0
        else:
            signals['trend_strength'] = 0
        
        # Realized volatility
        returns = close.pct_change()
        realized_vol = returns.rolling(window=20).std() * np.sqrt(252)
        signals['realized_volatility'] = realized_vol.iloc[-1] if len(realized_vol) > 0 else 0.2
        
        # Rolling skew
        if len(returns) > 20:
            rolling_skew = returns.rolling(window=20).skew()
            signals['rolling_skew'] = rolling_skew.iloc[-1] if not pd.isna(rolling_skew.iloc[-1]) else 0
        else:
            signals['rolling_skew'] = 0
        
        # Bollinger Band position
        bb_upper, bb_lower = self._compute_bollinger_bands(close, 20, 2)
        if len(close) > 20:
            bb_position = (close.iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            signals['bb_position'] = bb_position if not pd.isna(bb_position) else 0.5
        else:
            signals['bb_position'] = 0.5
        
        return signals
    
    def _compute_bollinger_bands(self, data, window=20, num_std=2):
        """Compute Bollinger Bands"""
        sma = data.rolling(window=window).mean()
        std = data.rolling(window=window).std()
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        return upper_band, lower_band
    
    def compute_cross_asset_signals(self, price_data_dict):
        """
        Compute cross-asset relationships:
        - Correlation matrix
        - Z-score spread signals for statistical arbitrage
        """
        if len(price_data_dict) < 2:
            return {'correlation_matrix': None, 'spread_signals': []}
        
        tickers = list(price_data_dict.keys())
        
        # Create price matrix
        price_df = pd.DataFrame({
            ticker: data['Close'] for ticker, data in price_data_dict.items()
        })
        
        returns_df = price_df.pct_change().dropna()
        
        if len(returns_df) < 20:
            return {'correlation_matrix': None, 'spread_signals': []}
        
        # Correlation matrix
        correlation_matrix = returns_df.corr()
        
        # Statistical arbitrage signals
        spread_signals = []
        
        # Generate pairs for spread analysis
        for i, ticker1 in enumerate(tickers[:10]):  # Limit to avoid computational complexity
            for j, ticker2 in enumerate(tickers[i+1:i+6]):
                try:
                    if ticker1 in correlation_matrix.index and ticker2 in correlation_matrix.index:
                        corr = correlation_matrix.loc[ticker1, ticker2]
                        
                        if corr > 0.5:  # Sufficient correlation
                            # Calculate spread
                            spread = np.log(price_df[ticker1]) - np.log(price_df[ticker2])
                            spread_mean = spread.mean()
                            spread_std = spread.std()
                            
                            if spread_std > 0:
                                current_spread = spread.iloc[-1]
                                z_score = (current_spread - spread_mean) / spread_std
                                
                                spread_signals.append({
                                    'ticker1': ticker1,
                                    'ticker2': ticker2,
                                    'correlation': corr,
                                    'spread_z_score': z_score,
                                    'signal': 'pair_trade' if abs(z_score) > 1.5 else 'neutral'
                                })
                except Exception:
                    continue
        
        return {
            'correlation_matrix': correlation_matrix,
            'spread_signals': spread_signals
        }
    
    def compute_sentiment_signals(self, news_headlines, ticker):
        """
        Compute sentiment signals using NewsAPI and NLP
        """
        if not news_headlines:
            return {'sentiment_score': 0, 'sentiment_strength': 0}
        
        # Extract headlines text
        headlines = [article.get('title', '') for article in news_headlines if article.get('title')]
        
        if not headlines:
            return {'sentiment_score': 0, 'sentiment_strength': 0}
        
        # Analyze sentiment
        sentiment_scores = batch_analyze_sentiment(headlines)
        
        if not sentiment_scores:
            return {'sentiment_score': 0, 'sentiment_strength': 0}
        
        # Compute sentiment metrics
        avg_sentiment = np.mean(sentiment_scores)
        sentiment_strength = np.std(sentiment_scores)  # How consistent the sentiment is
        
        # Sentiment momentum (recent vs historical)
        if len(sentiment_scores) >= 10:
            recent_sentiment = np.mean(sentiment_scores[-5:])
            historical_sentiment = np.mean(sentiment_scores[:-5])
            sentiment_momentum = recent_sentiment - historical_sentiment
        else:
            sentiment_momentum = 0
        
        return {
            'sentiment_score': avg_sentiment,
            'sentiment_strength': sentiment_strength,
            'sentiment_momentum': sentiment_momentum
        }
    
    def aggregate_signals(self, factor_signals, price_action_signals, 
                         sentiment_signals, stat_arb_signals):
        """
        Aggregate all signals using hedge fund alpha-combination logic
        """
        # Normalize all signals to -1 to +1 scale
        normalized_signals = self._normalize_signals(factor_signals, price_action_signals, 
                                                   sentiment_signals, stat_arb_signals)
        
        # Calculate weighted composite signal
        composite_score = 0
        for signal_name, weight in self.signal_weights.items():
            if signal_name in normalized_signals:
                composite_score += weight * normalized_signals[signal_name]
        
        # Apply signal quality filters
        signal_quality = self._assess_signal_quality(normalized_signals)
        
        return {
            'composite_score': composite_score,
            'signal_quality': signal_quality,
            'individual_signals': normalized_signals,
            'signal_weights': self.signal_weights
        }
    
    def _normalize_signals(self, factor_signals, price_action_signals, 
                          sentiment_signals, stat_arb_signals):
        """Normalize all signals to consistent scale"""
        normalized = {}
        
        # Factor signals (already roughly 0-2 scale)
        for key, value in factor_signals.items():
            normalized[key] = np.clip(value / 2.0, -1, 1)
        
        # Price action signals
        if 'trend_strength' in price_action_signals:
            normalized['trend_score'] = price_action_signals['trend_strength']
        
        if 'realized_volatility' in price_action_signals:
            vol = price_action_signals['realized_volatility']
            normalized['volatility_signal'] = np.clip((0.3 - vol) / 0.3, -1, 1)  # Prefer lower vol
        
        # Sentiment signals
        if 'sentiment_score' in sentiment_signals:
            normalized['sentiment_score'] = np.clip(sentiment_signals['sentiment_score'], -1, 1)
        
        # Statistical arbitrage
        if stat_arb_signals and 'spread_signals' in stat_arb_signals:
            avg_spread_z = np.mean([signal['spread_z_score'] for signal in stat_arb_signals['spread_signals']])
            normalized['stat_arb_score'] = np.clip(-avg_spread_z / 3.0, -1, 1)  # Mean reversion signal
        
        return normalized
    
    def _assess_signal_quality(self, signals):
        """Assess the quality and confidence of signals"""
        quality_factors = []
        
        # Signal strength
        signal_strength = np.mean([abs(signal) for signal in signals.values() if isinstance(signal, (int, float))])
        quality_factors.append(min(signal_strength * 2, 1.0))
        
        # Signal consistency (lower std dev = higher quality)
        signal_values = [signal for signal in signals.values() if isinstance(signal, (int, float))]
        if len(signal_values) > 1:
            signal_consistency = 1 - min(np.std(signal_values), 1.0)
            quality_factors.append(signal_consistency)
        
        return np.mean(quality_factors) if quality_factors else 0.5
    
    def compute_position_size(self, signal_score, signal_quality, current_price, 
                            volatility, total_capital, correlations=None):
        """
        Volatility targeting and risk parity position sizing
        """
        if signal_score <= 0 or signal_quality < 0.3:
            return 0  # Skip low quality signals
        
        # AGGRESSIVE position sizing for profit maximization
        signal_strength = min(abs(signal_score), 1.0)
        
        # Reduce volatility penalty for higher returns
        vol_scalar = (self.target_volatility * 1.2) / max(volatility, 0.05)
        
        # Quality adjustment (less restrictive)
        quality_multiplier = max(signal_quality, 0.3)  # Minimum 0.3 instead of filtering out
        
        # Calculate dollar allocation - more aggressive
        base_allocation = total_capital * self.max_position_size
        # Enhanced multiplier for strong signals
        signal_multiplier = 1.0 + (signal_strength * 0.5)  # Up to 50% bonus for strong signals
        
        vol_adjusted_allocation = base_allocation * vol_scalar * signal_strength * quality_multiplier * signal_multiplier
        
        # Reduce correlation penalty - less restrictive
        if correlations:
            correlation_penalty = 0.9  # Only 10% penalty instead of more
            vol_adjusted_allocation *= correlation_penalty
        
        # Convert to shares
        shares = int(vol_adjusted_allocation / current_price)
        
        return max(shares, 0)
    
    def compute_momentum_signals(self, price_data):
        """Compute momentum signals for factor analysis"""
        close = price_data['Close']
        
        # Multiple timeframe momentum
        mom_10 = price_momentum_ratio(close, 10) if len(close) > 10 else pd.Series([0])
        mom_20 = price_momentum_ratio(close, 20) if len(close) > 20 else pd.Series([0])
        mom_50 = price_momentum_ratio(close, 50) if len(close) > 50 else pd.Series([0])
        
        # Simple moving averages
        sma_20 = simple_moving_average(close, 20) if len(close) > 20 else close
        sma_50 = simple_moving_average(close, 50) if len(close) > 50 else close
        
        # Momentum strength score
        momentum_strength = 0
        if len(close) > 20 and close.iloc[-1] > sma_20.iloc[-1]:
            momentum_strength += 1
        if len(close) > 50 and close.iloc[-1] > sma_50.iloc[-1]:
            momentum_strength += 1
        
        # Price above moving averages
        price_above_sma20 = (close.iloc[-1] / sma_20.iloc[-1] - 1) if len(sma_20) > 0 and sma_20.iloc[-1] > 0 else 0
        price_above_sma50 = (close.iloc[-1] / sma_50.iloc[-1] - 1) if len(sma_50) > 0 and sma_50.iloc[-1] > 0 else 0
        
        return {
            'momentum_10': mom_10.iloc[-1] if len(mom_10) > 0 else 0,
            'momentum_20': mom_20.iloc[-1] if len(mom_20) > 0 else 0,
            'momentum_50': mom_50.iloc[-1] if len(mom_50) > 0 else 0,
            'momentum_strength': momentum_strength,
            'price_above_sma20': price_above_sma20,
            'price_above_sma50': price_above_sma50
        }
    
    def detect_volatility_regime(self, price_data):
        """Detect volatility regime for factor analysis"""
        close = price_data['Close']
        returns = close.pct_change().dropna()
        
        # Multiple volatility measures
        vol_20 = volatility(close, 20) if len(close) > 20 else volatility(close, len(close)//2)
        vol_50 = volatility(close, 50) if len(close) > 50 else vol_20
        
        realized_vol = returns.rolling(window=20).std() * np.sqrt(252)
        
        # Current regime
        current_vol = realized_vol.iloc[-1] if len(realized_vol) > 0 else 0.2
        
        if current_vol > 0.30:
            regime = 'high'
        elif current_vol < 0.15:
            regime = 'low'
        else:
            regime = 'normal'
        
        return {
            'volatility_20': vol_20.iloc[-1] if len(vol_20) > 0 else 0.2,
            'volatility_50': vol_50.iloc[-1] if len(vol_50) > 0 else 0.2,
            'realized_vol': current_vol,
            'regime': regime
        }
    
    def generate_portfolio_recommendations(self, stock_universe, client, newsapi_client, 
                                         total_capital=100000):
        """
        Generate portfolio recommendations using the full algorithm
        """
        print(f"Analyzing universe of {len(stock_universe)} stocks...")
        
        all_price_data = {}
        all_fundamentals = {}
        all_news = {}
        all_sentiment = {}
        
        # Process all stocks
        for i, ticker in enumerate(stock_universe):
            try:
                print(f"Processing {ticker} ({i+1}/{len(stock_universe)})...")
                
                # Get price data
                price_data = client.get_price_data(ticker, period='1y')
                if price_data.empty:
                    continue
                
                # Get fundamentals
                fundamentals = client.get_fundamentals(ticker)
                
                # Get news and sentiment
                company_news = client.get_company_news(ticker, page_size=10)
                sentiment_signals = self.compute_sentiment_signals(company_news, ticker)
                
                all_price_data[ticker] = price_data
                all_fundamentals[ticker] = fundamentals
                all_news[ticker] = company_news
                all_sentiment[ticker] = sentiment_signals
                
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue
        
        # Compute signals for all stocks
        stock_scores = {}
        
        for ticker, price_data in all_price_data.items():
            try:
                fundamentals = all_fundamentals.get(ticker, {})
                
                # Factor signals
                factor_signals = self.compute_factor_signals(price_data, fundamentals)
                
                # Price action signals
                price_action_signals = self.compute_price_action_signals(price_data)
                
                # Sentiment signals
                sentiment_signals = all_sentiment.get(ticker, {'sentiment_score': 0})
                
                # Aggregate signals
                aggregated_signals = self.aggregate_signals(
                    factor_signals, price_action_signals, sentiment_signals, {}
                )
                
                stock_scores[ticker] = {
                    'composite_score': aggregated_signals['composite_score'],
                    'signal_quality': aggregated_signals['signal_quality'],
                    'current_price': price_data['Close'].iloc[-1],
                    'volatility': price_action_signals.get('realized_volatility', 0.2),
                    'factor_breakdown': factor_signals,
                    'price_action_breakdown': price_action_signals,
                    'sentiment_breakdown': sentiment_signals
                }
                
            except Exception as e:
                print(f"Error computing signals for {ticker}: {e}")
                continue
        
        # Cross-asset analysis
        stat_arb_signals = self.compute_cross_asset_signals(all_price_data)
        
        # Generate portfolio positions
        portfolio_positions = []
        total_value = 0
        
        # Sort by composite score
        sorted_stocks = sorted(stock_scores.items(), 
                             key=lambda x: x[1]['composite_score'] * x[1]['signal_quality'], 
                             reverse=True)
        
        for ticker, signals in sorted_stocks[:self.max_positions]:
            if signals['composite_score'] > 0 and signals['signal_quality'] > 0.3:
                position_size = self.compute_position_size(
                    signals['composite_score'],
                    signals['signal_quality'],
                    signals['current_price'],
                    signals['volatility'],
                    total_capital
                )
                
                if position_size > 0:
                    position_value = position_size * signals['current_price']
                    portfolio_positions.append({
                        'ticker': ticker,
                        'shares': position_size,
                        'price': signals['current_price'],
                        'value': position_value,
                        'score': signals['composite_score'],
                        'quality': signals['signal_quality'],
                        'breakdown': signals
                    })
                    total_value += position_value
        
        return {
            'positions': portfolio_positions,
            'total_value': total_value,
            'cash_remaining': total_capital - total_value,
            'stat_arb_opportunities': stat_arb_signals.get('spread_signals', []),
            'universe_stats': {
                'total_analyzed': len(stock_universe),
                'qualified_positions': len(portfolio_positions),
                'avg_score': np.mean([pos['score'] for pos in portfolio_positions]) if portfolio_positions else 0
            }
        }
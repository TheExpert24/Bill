import pandas as pd
import numpy as np
from indicators import (
    simple_moving_average, relative_strength_index, volatility,
    sharpe_ratio, sortino_ratio, value_at_risk, bollinger_bands,
    price_momentum_ratio
)

class HedgeFundEngine:
    """
    Hedge fund-style multi-factor analysis engine combining:
    - Momentum signals
    - Mean reversion signals
    - Volatility regime detection
    - Factor analysis
    - Statistical arbitrage indicators
    - Risk-adjusted metrics
    """
    
    def __init__(self, lookback_short=20, lookback_medium=50, lookback_long=200):
        self.lookback_short = lookback_short
        self.lookback_medium = lookback_medium
        self.lookback_long = lookback_long
    
    def compute_momentum_signals(self, price_data):
        """
        Compute momentum signals - hedge funds look for persistent price trends.
        Returns multiple momentum indicators across different timeframes.
        """
        close = price_data['Close']
        
        mom_10 = price_momentum_ratio(close, 10)
        mom_20 = price_momentum_ratio(close, 20)
        mom_50 = price_momentum_ratio(close, 50)
        
        roc_5 = (close - close.shift(5)) / close.shift(5)
        roc_10 = (close - close.shift(10)) / close.shift(10)
        
        sma_20 = simple_moving_average(close, 20)
        sma_50 = simple_moving_average(close, 50)
        sma_200 = simple_moving_average(close, 200)
        
        momentum_strength = 0
        if len(close) > 20 and close.iloc[-1] > sma_20.iloc[-1]:
            momentum_strength += 1
        if len(close) > 50 and close.iloc[-1] > sma_50.iloc[-1]:
            momentum_strength += 1
        if len(close) > 200 and close.iloc[-1] > sma_200.iloc[-1]:
            momentum_strength += 1
        if len(sma_20) > 50 and len(sma_50) > 50 and sma_20.iloc[-1] > sma_50.iloc[-1]:
            momentum_strength += 1
        
        return {
            'momentum_10': mom_10,
            'momentum_20': mom_20,
            'momentum_50': mom_50,
            'roc_5': roc_5,
            'roc_10': roc_10,
            'momentum_strength': momentum_strength,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'sma_200': sma_200
        }
    
    def compute_mean_reversion_signals(self, price_data):
        """
        Compute mean reversion signals - identify when prices deviate significantly
        from their historical average (z-score approach).
        """
        close = price_data['Close']
        
        sma_20 = simple_moving_average(close, 20)
        std_20 = close.rolling(window=20).std()
        
        z_score = (close - sma_20) / std_20
        
        upper_band, lower_band = bollinger_bands(close, 20, 2)
        
        bb_position = (close - lower_band) / (upper_band - lower_band)
        
        rsi = relative_strength_index(close, 14)
        
        oversold = (z_score.iloc[-1] < -2) if len(z_score) > 0 and not pd.isna(z_score.iloc[-1]) else False
        overbought = (z_score.iloc[-1] > 2) if len(z_score) > 0 and not pd.isna(z_score.iloc[-1]) else False
        
        return {
            'z_score': z_score,
            'bb_position': bb_position,
            'upper_band': upper_band,
            'lower_band': lower_band,
            'rsi': rsi,
            'oversold': oversold,
            'overbought': overbought
        }
    
    def detect_volatility_regime(self, price_data):
        """
        Detect volatility regime - hedge funds adjust strategies based on
        whether market is in low, normal, or high volatility regime.
        """
        close = price_data['Close']
        
        vol_20 = volatility(close, 20)
        vol_50 = volatility(close, 50)
        
        returns = close.pct_change()
        realized_vol = returns.rolling(window=20).std() * np.sqrt(252)
        
        atr = self._compute_atr(price_data, 14)
        atr_normalized = atr / close
        
        if len(vol_20) > 50:
            recent_vol = vol_20.iloc[-1]
            historical_vol = vol_50.iloc[-1]
            vol_expansion = recent_vol > historical_vol * 1.5 if historical_vol > 0 else False
            vol_compression = recent_vol < historical_vol * 0.7 if historical_vol > 0 else False
        else:
            vol_expansion = False
            vol_compression = False
        
        if len(realized_vol) > 0 and not pd.isna(realized_vol.iloc[-1]):
            current_vol = realized_vol.iloc[-1]
            if current_vol > 0.30:
                regime = 'high'
            elif current_vol < 0.15:
                regime = 'low'
            else:
                regime = 'normal'
        else:
            regime = 'unknown'
        
        return {
            'volatility_20': vol_20,
            'volatility_50': vol_50,
            'realized_vol': realized_vol,
            'atr': atr,
            'atr_normalized': atr_normalized,
            'vol_expansion': vol_expansion,
            'vol_compression': vol_compression,
            'regime': regime
        }
    
    def _compute_atr(self, price_data, period=14):
        """Compute Average True Range."""
        high = price_data['High']
        low = price_data['Low']
        close = price_data['Close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def compute_factor_scores(self, price_data, fundamentals):
        """
        Compute factor scores - hedge funds use factor models to identify
        stocks with favorable characteristics.
        """
        close = price_data['Close']
        
        value_score = 0
        if fundamentals.get('pe_ratio'):
            pe = fundamentals['pe_ratio']
            if 0 < pe < 15:
                value_score = 2
            elif 15 <= pe < 25:
                value_score = 1
        
        momentum_signals = self.compute_momentum_signals(price_data)
        momentum_score = momentum_signals['momentum_strength']
        
        sharpe = sharpe_ratio(close)
        quality_score = 2 if sharpe > 1.5 else (1 if sharpe > 0.8 else 0)
        
        vol_regime = self.detect_volatility_regime(price_data)
        risk_score = 2 if vol_regime['regime'] == 'low' else (1 if vol_regime['regime'] == 'normal' else 0)
        
        return {
            'value_score': value_score,
            'momentum_score': momentum_score,
            'quality_score': quality_score,
            'risk_score': risk_score,
            'total_factor_score': value_score + momentum_score + quality_score + risk_score
        }
    
    def compute_statistical_arbitrage_signals(self, asset_prices_dict):
        """
        Compute statistical arbitrage signals - identify pairs of stocks
        with mean-reverting spread relationships.
        Returns correlation matrix and cointegration candidates.
        """
        if len(asset_prices_dict) < 2:
            return {'correlation_matrix': None, 'pairs': []}
        
        tickers = list(asset_prices_dict.keys())
        price_df = pd.DataFrame({ticker: asset_prices_dict[ticker]['Close'] 
                                for ticker in tickers})
        
        returns_df = price_df.pct_change().dropna()
        
        if len(returns_df) < 20:
            return {'correlation_matrix': None, 'pairs': []}
        
        correlation_matrix = returns_df.corr()
        
        pairs = []
        for i, ticker1 in enumerate(tickers):
            for j, ticker2 in enumerate(tickers):
                if i < j:
                    corr = correlation_matrix.loc[ticker1, ticker2]
                    if corr > 0.7:
                        spread = price_df[ticker1] / price_df[ticker2]
                        spread_mean = spread.mean()
                        spread_std = spread.std()
                        z_score = (spread.iloc[-1] - spread_mean) / spread_std if spread_std > 0 else 0
                        
                        pairs.append({
                            'ticker1': ticker1,
                            'ticker2': ticker2,
                            'correlation': corr,
                            'spread_z_score': z_score,
                            'signal': 'long_short' if z_score > 2 else ('short_long' if z_score < -2 else 'neutral')
                        })
        
        return {
            'correlation_matrix': correlation_matrix,
            'pairs': pairs
        }
    
    def compute_risk_adjusted_metrics(self, price_data):
        """
        Compute comprehensive risk-adjusted performance metrics.
        """
        close = price_data['Close']
        
        sharpe = sharpe_ratio(close)
        sortino = sortino_ratio(close)
        var_95 = value_at_risk(close, 0.95)
        var_99 = value_at_risk(close, 0.99)
        
        returns = close.pct_change().dropna()
        
        if len(returns) > 0:
            max_drawdown = self._compute_max_drawdown(close)
            positive_returns = returns[returns > 0]
            negative_returns = returns[returns < 0]
            win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0
            avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0
            avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        else:
            max_drawdown = 0
            win_rate = 0
            profit_factor = 0
        
        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'var_95': var_95,
            'var_99': var_99,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor
        }
    
    def _compute_max_drawdown(self, prices):
        """Compute maximum drawdown."""
        cummax = prices.cummax()
        drawdown = (prices - cummax) / cummax
        return drawdown.min()
    
    def generate_composite_signal(self, price_data, fundamentals, sentiment_scores):
        """
        Generate composite trading signal combining all factors.
        Returns score from -10 to +10.
        """
        momentum_signals = self.compute_momentum_signals(price_data)
        mean_reversion_signals = self.compute_mean_reversion_signals(price_data)
        vol_regime = self.detect_volatility_regime(price_data)
        factor_scores = self.compute_factor_scores(price_data, fundamentals)
        risk_metrics = self.compute_risk_adjusted_metrics(price_data)
        
        signal_score = 0
        
        signal_score += momentum_signals['momentum_strength']
        
        if mean_reversion_signals['oversold']:
            signal_score += 2
        if mean_reversion_signals['overbought']:
            signal_score -= 2
        
        if vol_regime['regime'] == 'low':
            signal_score += 1
        elif vol_regime['regime'] == 'high':
            signal_score -= 1
        
        signal_score += factor_scores['value_score']
        signal_score += factor_scores['quality_score']
        
        if risk_metrics['sharpe_ratio'] > 1.0:
            signal_score += 2
        elif risk_metrics['sharpe_ratio'] < 0:
            signal_score -= 2
        
        if risk_metrics['max_drawdown'] < -0.3:
            signal_score -= 2
        
        if sentiment_scores and len(sentiment_scores) > 0:
            avg_sentiment = np.mean(sentiment_scores)
            if avg_sentiment > 0.3:
                signal_score += 1
            elif avg_sentiment < -0.3:
                signal_score -= 1
        
        signal_score = max(-10, min(10, signal_score))
        
        return {
            'composite_score': signal_score,
            'momentum_signals': momentum_signals,
            'mean_reversion_signals': mean_reversion_signals,
            'volatility_regime': vol_regime,
            'factor_scores': factor_scores,
            'risk_metrics': risk_metrics
        }
    
    def compute_position_size_with_risk_controls(self, signal_score, current_price, 
                                                   volatility, total_capital, 
                                                   max_position_pct=0.1, 
                                                   risk_per_trade=0.02):
        """
        Calculate position size with strict risk controls:
        - Volatility-adjusted sizing
        - Maximum position limits
        - Risk per trade limits
        - Kelly criterion optional
        """
        if signal_score <= 0:
            return 0
        
        signal_strength = signal_score / 10.0
        
        base_allocation = total_capital * max_position_pct * signal_strength
        
        risk_amount = total_capital * risk_per_trade
        
        if volatility > 0:
            vol_adjusted_shares = risk_amount / (volatility * current_price)
        else:
            vol_adjusted_shares = base_allocation / current_price
        
        max_shares = base_allocation / current_price
        
        final_shares = min(vol_adjusted_shares, max_shares)
        
        return int(final_shares)

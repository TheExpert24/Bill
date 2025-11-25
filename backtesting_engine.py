"""
Backtesting Engine for Advanced Hedge Fund Algorithm
Validates signal performance and optimizes parameters
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from advanced_hedge_fund_engine import AdvancedHedgeFundEngine

class BacktestEngine:
    """
    Backtesting framework for hedge fund algorithm validation
    """
    
    def __init__(self, start_date, end_date, initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.engine = AdvancedHedgeFundEngine()
        
        # Performance tracking
        self.trades = []
        self.portfolio_history = []
        self.returns_history = []
        
    def run_backtest(self, stock_universe, rebalance_frequency='M'):
        """
        Run complete backtest on stock universe
        """
        print(f"Running backtest from {self.start_date} to {self.end_date}")
        print(f"Universe: {len(stock_universe)} stocks")
        print(f"Rebalance frequency: {rebalance_frequency}")
        
        # Generate rebalancing dates
        rebalance_dates = self._generate_rebalance_dates(rebalance_frequency)
        
        portfolio_value = self.initial_capital
        cash = self.initial_capital
        positions = {}
        
        for i, date in enumerate(rebalance_dates):
            if date >= self.end_date:
                break
                
            print(f"\nRebalance {i+1}/{len(rebalance_dates)}: {date.strftime('%Y-%m-%d')}")
            
            # Get historical data up to this date
            end_date_for_data = date + timedelta(days=5)  # Small buffer for data availability
            
            # Run strategy at this point in time
            current_portfolio = self._run_strategy_point(
                stock_universe, date, end_date_for_data, positions, portfolio_value
            )
            
            # Calculate performance
            portfolio_value = current_portfolio['total_value']
            cash = current_portfolio['cash']
            positions = current_portfolio['positions']
            
            # Record portfolio state
            self.portfolio_history.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': cash,
                'num_positions': len(positions),
                'positions': list(positions.keys())
            })
        
        # Calculate final performance metrics
        results = self._calculate_performance_metrics()
        
        return {
            'trades': self.trades,
            'portfolio_history': self.portfolio_history,
            'performance_metrics': results,
            'final_portfolio_value': portfolio_value,
            'total_return': (portfolio_value - self.initial_capital) / self.initial_capital
        }
    
    def _generate_rebalance_dates(self, frequency):
        """Generate rebalancing dates based on frequency"""
        dates = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            dates.append(current_date)
            
            if frequency == 'W':
                current_date += timedelta(weeks=1)
            elif frequency == 'M':
                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            elif frequency == 'Q':
                # Move to next quarter
                month = current_date.month
                if month <= 3:
                    next_month = 4
                elif month <= 6:
                    next_month = 7
                elif month <= 9:
                    next_month = 10
                else:
                    next_month = 1
                    current_date = current_date.replace(year=current_date.year + 1)
                
                if next_month <= 12:
                    current_date = current_date.replace(month=next_month)
            else:  # Annual
                current_date = current_date.replace(year=current_date.year + 1)
        
        return dates
    
    def _run_strategy_point(self, stock_universe, analysis_date, data_end_date, 
                          existing_positions, portfolio_value):
        """
        Run strategy at a specific point in time (historical backtest)
        """
        # Download historical data up to analysis date
        try:
            price_data = {}
            fundamentals_data = {}
            
            # Get price data for all stocks
            for ticker in stock_universe:
                try:
                    # Get data from analysis_date onwards (but we need past data for indicators)
                    data = yf.download(ticker, 
                                     start=analysis_date - timedelta(days=300), 
                                     end=data_end_date, 
                                     progress=False)
                    
                    if not data.empty and len(data) > 50:  # Need sufficient data
                        price_data[ticker] = data
                        
                        # Get basic fundamentals (simplified for backtest)
                        fundamentals_data[ticker] = self._get_historical_fundamentals(ticker, data)
                        
                except Exception as e:
                    continue
            
            if len(price_data) < 10:  # Need minimum stocks
                return {
                    'positions': existing_positions,
                    'cash': portfolio_value,
                    'total_value': portfolio_value
                }
            
            # Run algorithm on historical data
            portfolio_recommendations = self.engine.generate_portfolio_recommendations(
                stock_universe=list(price_data.keys()),
                client=self._create_mock_client(price_data, fundamentals_data),
                newsapi_client=None,  # No news for backtest
                total_capital=portfolio_value
            )
            
            # Extract new positions
            new_positions = {}
            total_allocation = 0
            
            for position in portfolio_recommendations['positions']:
                ticker = position['ticker']
                shares = position['shares']
                price = position['price']
                
                if ticker in price_data:
                    cost = shares * price
                    if cost <= portfolio_value * 0.95:  # Leave some cash
                        new_positions[ticker] = {
                            'shares': shares,
                            'price': price,
                            'cost': cost,
                            'entry_date': analysis_date,
                            'score': position['score']
                        }
                        total_allocation += cost
            
            cash = portfolio_value - total_allocation
            
            return {
                'positions': new_positions,
                'cash': cash,
                'total_value': portfolio_value
            }
            
        except Exception as e:
            print(f"Error in strategy point: {e}")
            return {
                'positions': existing_positions,
                'cash': portfolio_value,
                'total_value': portfolio_value
            }
    
    def _get_historical_fundamentals(self, ticker, price_data):
        """Generate simplified historical fundamentals for backtest"""
        # This is a simplified approach - in practice you'd use historical financial data
        close_prices = price_data['Close']
        
        # Simulate some fundamental metrics based on price behavior
        return {
            'trailingPE': np.random.uniform(10, 30),  # Random P/E for simulation
            'priceToBook': np.random.uniform(1, 5),
            'priceToSalesTrailing12Months': np.random.uniform(1, 10),
            'dividendYield': np.random.uniform(0, 0.05),
            'returnOnEquity': np.random.uniform(0.05, 0.25),
            'returnOnAssets': np.random.uniform(0.02, 0.15),
            'debtToEquity': np.random.uniform(0.1, 1.5),
            'marketCap': close_prices.iloc[-1] * np.random.uniform(1e6, 1e9)  # Rough market cap
        }
    
    def _create_mock_client(self, price_data, fundamentals_data):
        """Create mock client for backtesting"""
        class MockClient:
            def __init__(self, price_data, fundamentals_data):
                self.price_data = price_data
                self.fundamentals_data = fundamentals_data
            
            def get_price_data(self, ticker, period='1y'):
                return self.price_data.get(ticker, pd.DataFrame())
            
            def get_fundamentals(self, ticker):
                return self.fundamentals_data.get(ticker, {})
            
            def get_company_news(self, ticker, page_size=10):
                return []  # No news in backtest
        
        return MockClient(price_data, fundamentals_data)
    
    def _calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        if not self.portfolio_history:
            return {}
        
        # Convert to DataFrame for easier analysis
        portfolio_df = pd.DataFrame(self.portfolio_history)
        portfolio_df['date'] = pd.to_datetime(portfolio_df['date'])
        portfolio_df = portfolio_df.sort_values('date')
        
        # Calculate returns
        portfolio_df['portfolio_return'] = portfolio_df['portfolio_value'].pct_change()
        
        # Basic metrics
        total_return = (portfolio_df['portfolio_value'].iloc[-1] / self.initial_capital) - 1
        annualized_return = ((1 + total_return) ** (252 / len(portfolio_df))) - 1
        
        # Risk metrics
        returns = portfolio_df['portfolio_return'].dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualized
        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0
        
        # Drawdown
        peak = portfolio_df['portfolio_value'].expanding().max()
        drawdown = (portfolio_df['portfolio_value'] - peak) / peak
        max_drawdown = drawdown.min()
        
        # Win rate
        positive_returns = returns[returns > 0]
        win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'avg_trade_return': np.mean([trade.get('return', 0) for trade in self.trades]) if self.trades else 0,
            'best_trade': max([trade.get('return', 0) for trade in self.trades]) if self.trades else 0,
            'worst_trade': min([trade.get('return', 0) for trade in self.trades]) if self.trades else 0
        }
    
    def optimize_parameters(self, stock_universe, parameter_ranges):
        """
        Optimize algorithm parameters using grid search
        """
        print("Running parameter optimization...")
        
        best_params = None
        best_sharpe = -np.inf
        optimization_results = []
        
        # Generate parameter combinations
        param_combinations = self._generate_parameter_combinations(parameter_ranges)
        print(f"Testing {len(param_combinations)} parameter combinations...")
        
        for i, params in enumerate(param_combinations):
            try:
                # Update engine parameters
                self.engine.signal_weights = params['signal_weights']
                self.engine.universe_size = params['universe_size']
                self.engine.max_positions = params['max_positions']
                
                # Run shortened backtest for optimization
                backtest_results = self.run_backtest(
                    stock_universe[:50],  # Use smaller universe for speed
                    rebalance_frequency='M'
                )
                
                sharpe = backtest_results['performance_metrics'].get('sharpe_ratio', -np.inf)
                
                optimization_results.append({
                    'params': params,
                    'sharpe_ratio': sharpe,
                    'total_return': backtest_results['performance_metrics'].get('total_return', 0)
                })
                
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = params
                
                if (i + 1) % 10 == 0:
                    print(f"Completed {i+1}/{len(param_combinations)} combinations. Best Sharpe: {best_sharpe:.3f}")
                    
            except Exception as e:
                print(f"Error testing parameters {params}: {e}")
                continue
        
        print(f"Optimization complete. Best Sharpe ratio: {best_sharpe:.3f}")
        
        return {
            'best_parameters': best_params,
            'best_sharpe': best_sharpe,
            'all_results': optimization_results
        }
    
    def _generate_parameter_combinations(self, parameter_ranges):
        """Generate all combinations of parameters for optimization"""
        import itertools
        
        signal_weight_keys = ['momentum_score', 'value_score', 'quality_score', 'volatility_score', 'sentiment_score', 'stat_arb_score']
        
        combinations = []
        
        # Generate signal weight combinations
        for momentum_w in parameter_ranges.get('momentum_weights', [0.2, 0.25, 0.3]):
            for value_w in parameter_ranges.get('value_weights', [0.15, 0.2, 0.25]):
                for quality_w in parameter_ranges.get('quality_weights', [0.15, 0.2, 0.25]):
                    for vol_w in parameter_ranges.get('vol_weights', [0.1, 0.15, 0.2]):
                        for sent_w in parameter_ranges.get('sent_weights', [0.05, 0.1, 0.15]):
                            for stat_w in parameter_ranges.get('stat_weights', [0.05, 0.1, 0.15]):
                                
                                # Normalize weights to sum to 1
                                total_weight = momentum_w + value_w + quality_w + vol_w + sent_w + stat_w
                                if abs(total_weight - 1.0) < 0.01:  # Close enough to 1
                                    combinations.append({
                                        'signal_weights': {
                                            'momentum_score': momentum_w,
                                            'value_score': value_w,
                                            'quality_score': quality_w,
                                            'volatility_score': vol_w,
                                            'sentiment_score': sent_w,
                                            'stat_arb_score': stat_w
                                        },
                                        'universe_size': parameter_ranges.get('universe_sizes', [200])[0],
                                        'max_positions': parameter_ranges.get('max_positions', [20])[0]
                                    })
        
        return combinations[:50]  # Limit to avoid excessive computation
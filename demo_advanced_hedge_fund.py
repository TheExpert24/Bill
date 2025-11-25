#!/usr/bin/env python3
"""
Advanced Hedge Fund Algorithm Demo
Demonstrates the complete pipeline with dynamic stock selection and backtesting
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import our advanced components
from advanced_hedge_fund_engine import AdvancedHedgeFundEngine
from backtesting_engine import BacktestEngine
from api_client import MarketDataClient
from config import ADVANCED_CONFIG, TOTAL_CAPITAL

def demo_basic_usage():
    """Demonstrate basic usage of the advanced hedge fund algorithm"""
    
    print("="*80)
    print("ADVANCED HEDGE FUND ALGORITHM DEMO")
    print("="*80)
    
    # Initialize the advanced engine
    print("\n1. Initializing Advanced Hedge Fund Engine...")
    engine = AdvancedHedgeFundEngine(
        universe_size=ADVANCED_CONFIG['universe_size'],
        max_positions=ADVANCED_CONFIG['max_positions']
    )
    
    # Configure signal weights
    engine.signal_weights = ADVANCED_CONFIG['signal_weights']
    print(f"✓ Engine initialized with {engine.universe_size} stock universe")
    
    # Generate dynamic stock universe
    print("\n2. Generating Dynamic Stock Universe...")
    stock_universe = engine.get_dynamic_stock_universe()
    print(f"✓ Generated universe: {len(stock_universe)} stocks")
    print(f"Sample: {stock_universe[:10]}")
    
    # Initialize market data client
    print("\n3. Initializing Market Data Client...")
    client = MarketDataClient()
    print("✓ Market data client ready")
    
    # Generate portfolio recommendations
    print("\n4. Running Advanced Portfolio Generation...")
    print("This will analyze all stocks and generate recommendations...")
    
    try:
        portfolio = engine.generate_portfolio_recommendations(
            stock_universe=stock_universe,
            client=client,
            newsapi_client=client.newsapi,
            total_capital=TOTAL_CAPITAL
        )
        
        # Display results
        display_demo_results(portfolio)
        
    except Exception as e:
        print(f"Error during portfolio generation: {e}")
        import traceback
        traceback.print_exc()

def demo_backtesting():
    """Demonstrate backtesting capabilities"""
    
    print("\n" + "="*80)
    print("BACKTESTING DEMO")
    print("="*80)
    
    # Define backtest period (2 years)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)
    
    print(f"Backtest period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Initialize backtesting engine
    backtest_engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000
    )
    
    # Use a smaller universe for faster backtesting
    engine = AdvancedHedgeFundEngine(universe_size=50, max_positions=10)
    stock_universe = engine.get_dynamic_stock_universe()
    
    print(f"Backtesting with {len(stock_universe)} stocks...")
    
    # Run backtest with monthly rebalancing
    print("Running backtest (this may take a few minutes)...")
    try:
        results = backtest_engine.run_backtest(
            stock_universe=stock_universe,
            rebalance_frequency='M'
        )
        
        # Display backtest results
        display_backtest_results(results)
        
    except Exception as e:
        print(f"Error during backtesting: {e}")

def demo_parameter_optimization():
    """Demonstrate parameter optimization"""
    
    print("\n" + "="*80)
    print("PARAMETER OPTIMIZATION DEMO")
    print("="*80)
    
    # Define parameter ranges to test
    parameter_ranges = {
        'momentum_weights': [0.20, 0.25, 0.30],
        'value_weights': [0.15, 0.20, 0.25],
        'quality_weights': [0.15, 0.20, 0.25],
        'vol_weights': [0.10, 0.15, 0.20],
        'sent_weights': [0.05, 0.10, 0.15],
        'stat_weights': [0.05, 0.10, 0.15],
        'universe_sizes': [100],
        'max_positions': [15]
    }
    
    # Initialize backtesting engine for optimization
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # 1 year for speed
    
    backtest_engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000
    )
    
    # Small universe for optimization
    engine = AdvancedHedgeFundEngine(universe_size=30, max_positions=10)
    stock_universe = engine.get_dynamic_stock_universe()
    
    print("Running parameter optimization...")
    print("Testing multiple signal weight combinations...")
    
    try:
        optimization_results = backtest_engine.optimize_parameters(
            stock_universe=stock_universe,
            parameter_ranges=parameter_ranges
        )
        
        # Display optimization results
        display_optimization_results(optimization_results)
        
    except Exception as e:
        print(f"Error during optimization: {e}")

def display_demo_results(portfolio):
    """Display portfolio generation results"""
    
    positions = portfolio['positions']
    
    print(f"\n✓ Portfolio generated successfully!")
    print(f"Positions found: {len(positions)}")
    print(f"Total value: ${portfolio['total_value']:,.2f}")
    print(f"Cash remaining: ${portfolio['cash_remaining']:,.2f}")
    
    if positions:
        print(f"\nTop 5 Recommendations:")
        print("-" * 60)
        for i, pos in enumerate(positions[:5], 1):
            print(f"{i}. {pos['ticker']}: {pos['shares']} shares @ ${pos['price']:.2f} "
                  f"(Value: ${pos['value']:,.2f}, Score: {pos['score']:.3f})")
    
    # Show factor breakdown for top position
    if positions:
        top_pos = positions[0]
        breakdown = top_pos['breakdown']
        
        print(f"\nFactor Analysis for {top_pos['ticker']}:")
        print(f"  Value Score: {breakdown['factor_breakdown'].get('value_score', 0):.3f}")
        print(f"  Quality Score: {breakdown['factor_breakdown'].get('quality_score', 0):.3f}")
        print(f"  Momentum Score: {breakdown['factor_breakdown'].get('momentum_score', 0):.3f}")
        print(f"  Volatility Score: {breakdown['factor_breakdown'].get('volatility_score', 0):.3f}")
        print(f"  Sentiment Score: {breakdown['sentiment_breakdown'].get('sentiment_score', 0):.3f}")

def display_backtest_results(results):
    """Display backtesting results"""
    
    print(f"\n✓ Backtest completed successfully!")
    
    perf_metrics = results['performance_metrics']
    
    print(f"\nBacktest Performance:")
    print(f"  Total Return: {perf_metrics.get('total_return', 0):.2%}")
    print(f"  Annualized Return: {perf_metrics.get('annualized_return', 0):.2%}")
    print(f"  Volatility: {perf_metrics.get('volatility', 0):.2%}")
    print(f"  Sharpe Ratio: {perf_metrics.get('sharpe_ratio', 0):.3f}")
    print(f"  Maximum Drawdown: {perf_metrics.get('max_drawdown', 0):.2%}")
    print(f"  Win Rate: {perf_metrics.get('win_rate', 0):.2%}")
    
    # Compare to simple benchmark (S&P 500 approximation)
    print(f"\nBenchmark Comparison:")
    print("  Note: This would typically compare to S&P 500 or other benchmarks")
    print("  The algorithm aims to outperform with lower volatility and better risk-adjusted returns")

def display_optimization_results(optimization_results):
    """Display parameter optimization results"""
    
    print(f"\n✓ Parameter optimization completed!")
    
    best_params = optimization_results['best_parameters']
    best_sharpe = optimization_results['best_sharpe']
    
    print(f"\nBest Parameters Found:")
    print(f"  Best Sharpe Ratio: {best_sharpe:.3f}")
    
    if best_params:
        print(f"  Optimal Signal Weights:")
        for signal, weight in best_params['signal_weights'].items():
            print(f"    {signal}: {weight:.3f}")
        
        print(f"  Optimal Universe Size: {best_params['universe_size']}")
        print(f"  Optimal Max Positions: {best_params['max_positions']}")
    
    print(f"\nOptimization suggests focusing on:")
    print("  - Higher momentum weights for trending markets")
    print("  - Quality factors for stable returns")
    print("  - Diversified position sizing")

def main():
    """Main demo function"""
    
    print("ADVANCED HEDGE FUND ALGORITHM")
    print("Institutional-Style Alpha Generation with Dynamic Universe")
    print()
    
    # Demo 1: Basic usage
    print("Starting demo with basic portfolio generation...")
    try:
        demo_basic_usage()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        return
    
    # Demo 2: Backtesting (commented out by default as it takes time)
    # demo_backtesting()
    
    # Demo 3: Parameter optimization (commented out by default)
    # demo_parameter_optimization()
    
    print(f"\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nTo run the full algorithm:")
    print("  python advanced_main.py")
    print("\nTo run backtesting:")
    print("  Uncomment the backtesting demo in this script")
    print("\nTo run parameter optimization:")
    print("  Uncomment the optimization demo in this script")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Profit-Focused Hedge Fund Algorithm
Streamlined for maximum return generation
"""

import sys
import os
from datetime import datetime
import pandas as pd
import numpy as np

# Import components
from advanced_hedge_fund_engine import AdvancedHedgeFundEngine
from api_client import MarketDataClient
from config import ADVANCED_CONFIG, TOTAL_CAPITAL

def run_profit_optimized_algorithm():
    """Run the algorithm focused purely on profit maximization"""
    
    print("="*80)
    print("PROFIT-FOCUSED HEDGE FUND ALGORITHM")
    print("Optimized for Maximum Return Generation")
    print("="*80)
    
    # Initialize with profit-focused settings
    print("\nInitializing profit-optimized engine...")
    engine = AdvancedHedgeFundEngine(
        universe_size=ADVANCED_CONFIG['universe_size']  # 500 stocks
    )
    
    # Apply profit-focused signal weights
    engine.signal_weights = ADVANCED_CONFIG['signal_weights']
    print(f"✓ Engine initialized")
    print(f"  Universe: {engine.universe_size} stocks")
    print(f"  Positions: Auto-determined by algorithm")
    print(f"  Momentum weight: {engine.signal_weights['momentum_score']:.1%} (highest)")
    
    # Generate universe
    print("\nGenerating profit-focused stock universe...")
    stock_universe = engine.get_dynamic_stock_universe()
    print(f"✓ Generated {len(stock_universe)} stocks for analysis")
    
    # Initialize market data client
    client = MarketDataClient()
    
    # Run algorithm
    print(f"\nRunning profit maximization algorithm...")
    print(f"Capital allocation: ${TOTAL_CAPITAL:,}")
    
    try:
        portfolio = engine.generate_portfolio_recommendations(
            stock_universe=stock_universe,
            client=client,
            newsapi_client=client.newsapi,
            total_capital=TOTAL_CAPITAL
        )
        
        # Display results
        display_profit_results(portfolio)
        
        # Save results
        save_profit_results(portfolio)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def display_profit_results(portfolio):
    """Display results optimized for profit analysis"""
    
    positions = portfolio['positions']
    
    print(f"\n" + "="*80)
    print("PROFIT MAXIMIZATION RESULTS")
    print("="*80)
    
    if not positions:
        print("❌ No profitable opportunities found")
        print("Consider:")
        print("- Lowering signal quality thresholds")
        print("- Expanding universe size")
        print("- Adjusting risk parameters")
        return
    
    print(f"✅ Found {len(positions)} profit opportunities")
    print(f"💰 Total allocation: ${portfolio['total_value']:,.2f}")
    print(f"💵 Cash remaining: ${portfolio['cash_remaining']:,.2f}")
    print(f"📊 Capital utilization: {(portfolio['total_value']/TOTAL_CAPITAL)*100:.1f}%")
    
    # Top opportunities
    print(f"\n🔥 TOP PROFIT OPPORTUNITIES:")
    print("-" * 80)
    print(f"{'Rank':<4} {'Ticker':<8} {'Shares':<8} {'Price':<10} {'Allocation':<12} {'Score':<8} {'ROI Potential':<12}")
    print("-" * 80)
    
    for i, pos in enumerate(positions[:15], 1):
        allocation_pct = (pos['value'] / portfolio['total_value']) * 100 if portfolio['total_value'] > 0 else 0
        
        # Estimate ROI potential based on signal score
        roi_potential = pos['score'] * 50  # Rough estimate: score * 50% potential
        
        print(f"{i:<4} {pos['ticker']:<8} {pos['shares']:<8} "
              f"${pos['price']:<9.2f} ${pos['value']:<11,.2f} "
              f"{pos['score']:<7.3f} {roi_potential:<11.1f}%")
    
    # Portfolio stats
    if positions:
        scores = [pos['score'] for pos in positions]
        avg_score = np.mean(scores)
        top_score = max(scores)
        
        print(f"\n📈 PORTFOLIO METRICS:")
        print(f"  Average signal score: {avg_score:.3f}")
        print(f"  Highest conviction: {top_score:.3f}")
        print(f"  Score range: {min(scores):.3f} to {max(scores):.3f}")
        
        # Allocation distribution
        values = [pos['value'] for pos in positions]
        total_value = sum(values)
        weights = [v/total_value for v in values]
        concentration = max(weights) if weights else 0
        
        print(f"  Position concentration: {concentration:.1%}")
        print(f"  Effective diversification: {1/concentration:.1f} positions")

def save_profit_results(portfolio):
    """Save profit-focused results"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"profit_optimized_portfolio_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("PROFIT-FOCUSED PORTFOLIO RECOMMENDATIONS\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Capital: ${TOTAL_CAPITAL:,}\n\n")
        
        positions = portfolio['positions']
        
        f.write("TOP 20 POSITIONS BY PROFIT POTENTIAL\n")
        f.write("-"*60 + "\n")
        f.write(f"{'Rank':<4} {'Ticker':<8} {'Shares':<10} {'Price':<10} {'Value':<12} {'Score':<8}\n")
        f.write("-"*60 + "\n")
        
        for i, pos in enumerate(positions[:20], 1):
            f.write(f"{i:<4} {pos['ticker']:<8} {pos['shares']:<10} "
                   f"${pos['price']:<9.2f} ${pos['value']:<11,.2f} {pos['score']:<7.3f}\n")
        
        # Summary stats
        f.write(f"\nPORTFOLIO SUMMARY\n")
        f.write("-"*30 + "\n")
        f.write(f"Total positions: {len(positions)}\n")
        f.write(f"Total allocation: ${portfolio['total_value']:,.2f}\n")
        f.write(f"Average score: {np.mean([p['score'] for p in positions]):.3f}\n")
        f.write(f"Best opportunity: {max([p['score'] for p in positions]):.3f}\n")
    
    print(f"\n💾 Results saved to: {filename}")

def main():
    """Main execution"""
    print("🚀 PROFIT MAXIMIZATION MODE ACTIVATED")
    print("Algorithm configured for highest return potential\n")
    
    run_profit_optimized_algorithm()
    
    print(f"\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print("\n💡 Key Features for Profit Maximization:")
    print("• 40% weight on momentum (strongest return predictor)")
    print("• Higher volatility tolerance (20% vs 15%)")
    print("• Larger position sizes (8% vs 5% max)")
    print("• Broader universe (500 vs 300 stocks)")
    print("• Aggressive signal thresholds")
    print("• Growth-focused value scoring")

if __name__ == "__main__":
    main()

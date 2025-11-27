#!/usr/bin/env python3
"""
Advanced Hedge Fund Algorithm - Main Pipeline
Uses institutional-style alpha signal generation with dynamic stock universe selection
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Import our advanced engine
from advanced_hedge_fund_engine import AdvancedHedgeFundEngine
from api_client import MarketDataClient
from config import *

def main():
    """Main execution of the advanced hedge fund algorithm"""
    
    print("="*80)
    print("ADVANCED HEDGE FUND ALGORITHM")
    print("Institutional-Style Alpha Signal Generation")
    print("="*80)
    
    # Initialize components
    print("Initializing market data client...")
    client = MarketDataClient()
    
    print("Initializing advanced hedge fund engine...")
    # Configure engine for aggressive alpha generation
    engine = AdvancedHedgeFundEngine(
        lookback_short=20,
        lookback_medium=50, 
        lookback_long=200,
        universe_size=300  # Large universe for better opportunities
    )
    
    # Generate dynamic stock universe
    print("\nGenerating dynamic stock universe...")
    stock_universe = engine.get_dynamic_stock_universe()
    
    if not stock_universe:
        print("ERROR: Could not generate stock universe. Exiting.")
        return
    
    print(f"Selected universe: {len(stock_universe)} stocks")
    print(f"Sample tickers: {stock_universe[:10]}")
    
    # Set capital allocation
    total_capital = TOTAL_CAPITAL
    print(f"\nPortfolio capital: ${total_capital:,}")
    
    # Generate portfolio recommendations
    print("\nGenerating portfolio recommendations...")
    print("This may take several minutes due to comprehensive analysis...")
    
    try:
        portfolio = engine.generate_portfolio_recommendations(
            stock_universe=stock_universe,
            client=client,
            newsapi_client=client.newsapi,
            total_capital=total_capital
        )
        
        # Display results
        display_portfolio_results(portfolio, total_capital)
        
        # Generate detailed report
        generate_detailed_report(portfolio, engine, stock_universe)
        
    except Exception as e:
        print(f"Error during portfolio generation: {e}")
        import traceback
        traceback.print_exc()

def display_portfolio_results(portfolio, total_capital):
    """Display portfolio results in a formatted way"""
    
    print("\n" + "="*80)
    print("PORTFOLIO RECOMMENDATIONS")
    print("="*80)
    
    positions = portfolio['positions']
    
    if not positions:
        print("No qualifying positions found. Consider:")
        print("- Reducing signal quality thresholds")
        print("- Expanding stock universe")
        print("- Adjusting risk parameters")
        return
    
    print(f"Total Positions: {len(positions)}")
    print(f"Capital Allocated: ${portfolio['total_value']:,.2f}")
    print(f"Cash Remaining: ${portfolio['cash_remaining']:,.2f}")
    print(f"Capital Utilization: {(portfolio['total_value']/total_capital)*100:.1f}%")
    
    print("\nTop 10 Position Recommendations:")
    print("-" * 100)
    print(f"{'Rank':<4} {'Ticker':<8} {'Shares':<8} {'Price':<10} {'Value':<12} {'Score':<8} {'Quality':<8}")
    print("-" * 100)
    
    for i, position in enumerate(positions[:10], 1):
        print(f"{i:<4} {position['ticker']:<8} {position['shares']:<8} "
              f"${position['price']:<9.2f} ${position['value']:<11,.2f} "
              f"{position['score']:<7.3f} {position['quality']:<7.3f}")
    
    # Portfolio statistics
    if positions:
        scores = [pos['score'] for pos in positions]
        qualities = [pos['quality'] for pos in positions]
        values = [pos['value'] for pos in positions]
        
        print(f"\nPortfolio Statistics:")
        print(f"Average Signal Score: {np.mean(scores):.3f}")
        print(f"Average Signal Quality: {np.mean(qualities):.3f}")
        print(f"Largest Position: ${max(values):,.2f} ({max(values)/sum(values)*100:.1f}% of portfolio)")
        print(f"Most Diversified: {len(positions)} positions")
    
    # Statistical arbitrage opportunities
    stat_arb = portfolio.get('stat_arb_opportunities', [])
    if stat_arb:
        print(f"\nStatistical Arbitrage Opportunities: {len(stat_arb)}")
        for signal in stat_arb[:5]:
            print(f"  {signal['ticker1']}-{signal['ticker2']}: "
                  f"Correlation={signal['correlation']:.2f}, "
                  f"Z-Score={signal['spread_z_score']:.2f}")

def generate_detailed_report(portfolio, engine, stock_universe):
    """Generate comprehensive analysis report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"advanced_hedge_fund_report_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("ADVANCED HEDGE FUND ALGORITHM REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Stock Universe: {len(stock_universe)} stocks\n\n")
        
        # Portfolio summary
        positions = portfolio['positions']
        f.write("PORTFOLIO SUMMARY\n")
        f.write("-"*30 + "\n")
        f.write(f"Total Positions: {len(positions)}\n")
        f.write(f"Capital Allocated: ${portfolio['total_value']:,.2f}\n")
        f.write(f"Cash Remaining: ${portfolio['cash_remaining']:,.2f}\n")
        f.write(f"Capital Utilization: {(portfolio['total_value']/(portfolio['total_value']+portfolio['cash_remaining']))*100:.1f}%\n\n")
        
        # Detailed positions
        f.write("DETAILED POSITIONS\n")
        f.write("-"*50 + "\n")
        f.write(f"{'Ticker':<8} {'Shares':<8} {'Price':<10} {'Value':<12} {'Score':<8} {'Quality':<8} {'Value%':<8}\n")
        f.write("-"*50 + "\n")
        
        total_value = sum(pos['value'] for pos in positions)
        for position in positions:
            value_pct = (position['value'] / total_value * 100) if total_value > 0 else 0
            f.write(f"{position['ticker']:<8} {position['shares']:<8} "
                   f"${position['price']:<9.2f} ${position['value']:<11,.2f} "
                   f"{position['score']:<7.3f} {position['quality']:<7.3f} "
                   f"{value_pct:<7.1f}%\n")
        
        # Factor breakdown for top positions
        f.write("\n\nFACTOR ANALYSIS (Top 5 Positions)\n")
        f.write("-"*60 + "\n")
        
        for i, position in enumerate(positions[:5], 1):
            f.write(f"\n{i}. {position['ticker']} (Score: {position['score']:.3f})\n")
            
            breakdown = position['breakdown']
            
            # Factor signals
            factors = breakdown['factor_breakdown']
            f.write(f"   Value Score: {factors.get('value_score', 0):.3f}\n")
            f.write(f"   Quality Score: {factors.get('quality_score', 0):.3f}\n")
            f.write(f"   Momentum Score: {factors.get('momentum_score', 0):.3f}\n")
            f.write(f"   Volatility Score: {factors.get('volatility_score', 0):.3f}\n")
            
            # Price action
            price_action = breakdown['price_action_breakdown']
            f.write(f"   Trend Strength: {price_action.get('trend_strength', 0):.3f}\n")
            f.write(f"   Realized Volatility: {price_action.get('realized_volatility', 0):.3f}\n")
            
            # Sentiment
            sentiment = breakdown['sentiment_breakdown']
            f.write(f"   Sentiment Score: {sentiment.get('sentiment_score', 0):.3f}\n")
            f.write(f"   Sentiment Strength: {sentiment.get('sentiment_strength', 0):.3f}\n")
        
        # Statistical arbitrage
        stat_arb = portfolio.get('stat_arb_opportunities', [])
        if stat_arb:
            f.write(f"\n\nSTATISTICAL ARBITRAGE OPPORTUNITIES\n")
            f.write("-"*40 + "\n")
            for signal in stat_arb[:10]:
                f.write(f"{signal['ticker1']}-{signal['ticker2']}: "
                       f"Correlation={signal['correlation']:.3f}, "
                       f"Z-Score={signal['spread_z_score']:.3f}, "
                       f"Signal={signal['signal']}\n")
        
        # Risk metrics
        if positions:
            f.write(f"\n\nPORTFOLIO RISK METRICS\n")
            f.write("-"*30 + "\n")
            
            scores = [pos['score'] for pos in positions]
            qualities = [pos['quality'] for pos in positions]
            
            f.write(f"Average Signal Score: {np.mean(scores):.3f}\n")
            f.write(f"Score Standard Deviation: {np.std(scores):.3f}\n")
            f.write(f"Average Signal Quality: {np.mean(qualities):.3f}\n")
            f.write(f"Quality Standard Deviation: {np.std(qualities):.3f}\n")
            
            # Concentration metrics
            values = [pos['value'] for pos in positions]
            total_portfolio_value = sum(values)
            if total_portfolio_value > 0:
                weights = [v/total_portfolio_value for v in values]
                hhi = sum(w**2 for w in weights)  # Herfindahl-Hirschman Index
                f.write(f"Concentration (HHI): {hhi:.3f}\n")
                f.write(f"Effective Positions: {1/hhi:.1f}\n")
        
        # Universe statistics
        universe_stats = portfolio.get('universe_stats', {})
        if universe_stats:
            f.write(f"\n\nUNIVERSE STATISTICS\n")
            f.write("-"*25 + "\n")
            f.write(f"Total Stocks Analyzed: {universe_stats.get('total_analyzed', 0)}\n")
            f.write(f"Qualified Positions: {universe_stats.get('qualified_positions', 0)}\n")
            f.write(f"Selection Rate: {(universe_stats.get('qualified_positions', 0) / max(universe_stats.get('total_analyzed', 1), 1))*100:.1f}%\n")
            f.write(f"Average Score of Qualified: {universe_stats.get('avg_score', 0):.3f}\n")
    
    print(f"\nDetailed report saved to: {filename}")

if __name__ == "__main__":
    main()
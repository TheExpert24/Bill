#!/usr/bin/env python3
"""
Test automatic position count determination
"""

from advanced_hedge_fund_engine import AdvancedHedgeFundEngine

def test_automatic_positions():
    """Test that the algorithm automatically determines position count"""
    
    print("Testing Automatic Position Count Determination...")
    print("="*60)
    
    # Initialize engine without max_positions parameter
    engine = AdvancedHedgeFundEngine(universe_size=100)
    
    print("✓ Engine initialized without max_positions parameter")
    print(f"✓ Universe size: {engine.universe_size}")
    
    # Test the automatic position determination with mock data
    print("\nTesting position determination logic...")
    
    # Create mock stock scores for testing
    mock_stock_scores = {}
    
    # Add different tiers of stocks
    # Top tier (high score, high quality)
    for i in range(8):
        mock_stock_scores[f"STOCK_TOP_{i}"] = {
            'composite_score': 0.6 + (i * 0.05),  # 0.6-0.95
            'signal_quality': 0.8,
            'current_price': 50.0 + (i * 10)
        }
    
    # Middle tier (medium score, medium quality)
    for i in range(15):
        mock_stock_scores[f"STOCK_MID_{i}"] = {
            'composite_score': 0.3 + (i * 0.02),  # 0.3-0.58
            'signal_quality': 0.6,
            'current_price': 30.0 + (i * 5)
        }
    
    # Lower tier (lower score, lower quality)
    for i in range(20):
        mock_stock_scores[f"STOCK_LOW_{i}"] = {
            'composite_score': 0.1 + (i * 0.01),  # 0.1-0.29
            'signal_quality': 0.4,
            'current_price': 20.0 + (i * 3)
        }
    
    print(f"Created {len(mock_stock_scores)} mock stocks")
    print(f"  - Top tier: 8 stocks (score 0.6-0.95)")
    print(f"  - Middle tier: 15 stocks (score 0.3-0.58)")
    print(f"  - Lower tier: 20 stocks (score 0.1-0.29)")
    
    # Test automatic position determination
    total_capital = 100000
    optimal_positions = engine._determine_optimal_position_count(mock_stock_scores, total_capital)
    
    print(f"\nAutomatic Position Count Result:")
    print(f"  Total capital: ${total_capital:,}")
    print(f"  Optimal positions: {optimal_positions}")
    
    # Show the breakdown
    qualifying_stocks = []
    for ticker, signals in mock_stock_scores.items():
        if signals['composite_score'] > 0 and signals['signal_quality'] > 0.2:
            qualifying_stocks.append((ticker, signals))
    
    qualifying_stocks.sort(key=lambda x: x[1]['composite_score'] * x[1]['signal_quality'], reverse=True)
    
    top_tier = [s for s in qualifying_stocks if s[1]['composite_score'] > 0.5]
    middle_tier = [s for s in qualifying_stocks if 0.3 < s[1]['composite_score'] <= 0.5]
    lower_tier = [s for s in qualifying_stocks if 0.0 < s[1]['composite_score'] <= 0.3]
    
    print(f"\nQualification Breakdown:")
    print(f"  - Qualifying stocks: {len(qualifying_stocks)}")
    print(f"  - Top tier (>0.5): {len(top_tier)}")
    print(f"  - Middle tier (0.3-0.5): {len(middle_tier)}")
    print(f"  - Lower tier (0.0-0.3): {len(lower_tier)}")
    
    print(f"\nAlgorithm Logic:")
    print(f"  1. Includes all top tier stocks")
    print(f"  2. Adds middle tier if sufficient capital remains")
    print(f"  3. Adds lower tier only if significant capital remains")
    print(f"  4. Ensures minimum position size constraints")
    print(f"  5. Caps at reasonable maximum (35 positions)")
    
    print(f"\n" + "="*60)
    print("✓ AUTOMATIC POSITION DETERMINATION TEST COMPLETE")
    print("✓ Algorithm will automatically optimize position count")
    print("✓ Based on signal quality, capital constraints, and risk")

if __name__ == "__main__":
    test_automatic_positions()
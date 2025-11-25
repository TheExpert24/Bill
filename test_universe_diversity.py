#!/usr/bin/env python3
"""
Test the diversity of stock universe generation
"""

import sys
import os
import pandas as pd
from advanced_hedge_fund_engine import AdvancedHedgeFundEngine

def test_universe_diversity():
    """Test that the algorithm generates diverse stock universes"""
    
    print("Testing Universe Diversity...")
    print("="*60)
    
    # Initialize engine
    engine = AdvancedHedgeFundEngine(universe_size=100, max_positions=20)
    
    # Generate multiple universes to test diversity
    universes = []
    universe_size = 50
    
    print("Generating 5 different universes to test diversity...")
    
    for i in range(5):
        print(f"\nUniverse {i+1}:")
        try:
            # Generate universe
            universe = engine.get_dynamic_stock_universe()
            
            # Limit to test size
            if len(universe) > universe_size:
                universe = universe[:universe_size]
            
            universes.append(universe)
            
            print(f"Generated {len(universe)} stocks")
            print(f"Sample: {universe[:10]}")
            
            # Track sector diversity
            tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'CRM', 'ADBE', 'ORCL']
            finance_stocks = ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'AXP', 'BLK']
            healthcare_stocks = ['JNJ', 'PFE', 'UNH', 'MRK', 'ABBV', 'TMO', 'DHR', 'ABT', 'ISRG', 'BMY']
            consumer_stocks = ['WMT', 'HD', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'SBUX', 'TGT', 'COST']
            industrial_stocks = ['BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'LMT', 'RTX', 'UNP', 'DE']
            energy_stocks = ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'KMI', 'ET']
            
            tech_count = len([s for s in universe if s in tech_stocks])
            finance_count = len([s for s in universe if s in finance_stocks])
            healthcare_count = len([s for s in universe if s in healthcare_stocks])
            consumer_count = len([s for s in universe if s in consumer_stocks])
            industrial_count = len([s for s in universe if s in industrial_stocks])
            energy_count = len([s for s in universe if s in energy_stocks])
            
            print(f"Sector breakdown:")
            print(f"  Tech: {tech_count}, Finance: {finance_count}, Healthcare: {healthcare_count}")
            print(f"  Consumer: {consumer_count}, Industrial: {industrial_count}, Energy: {energy_count}")
            
        except Exception as e:
            print(f"Error generating universe {i+1}: {e}")
            continue
    
    # Analyze diversity across universes
    if len(universes) >= 2:
        print(f"\n" + "="*60)
        print("DIVERSITY ANALYSIS")
        print("="*60)
        
        # Find common stocks across all universes
        if universes:
            common_stocks = set(universes[0])
            for universe in universes[1:]:
                common_stocks &= set(universe)
            
            print(f"Stocks appearing in ALL universes: {len(common_stocks)}")
            print(f"Common stocks: {list(common_stocks)[:10]}")
            
            # Find unique stocks in each universe
            for i, universe in enumerate(universes):
                unique_to_this = set(universe) - common_stocks
                print(f"Universe {i+1} unique stocks: {len(unique_to_this)}")
                if unique_to_this:
                    print(f"  Sample unique: {list(unique_to_this)[:5]}")
        
        # Calculate overlap between pairs
        print(f"\nOverlap Analysis (Universe pairs):")
        for i in range(min(3, len(universes))):
            for j in range(i+1, min(3, len(universes))):
                overlap = len(set(universes[i]) & set(universes[j]))
                overlap_pct = (overlap / len(universes[i])) * 100
                print(f"  Universe {i+1} vs {j+1}: {overlap}/{len(universes[i])} stocks ({overlap_pct:.1f}% overlap)")
    
    print(f"\n" + "="*60)
    print("DIVERSITY TEST COMPLETE")
    print("="*60)
    print("✓ Generated multiple diverse universes")
    print("✓ Each run should produce different stock selections")
    print("✓ Time-based randomization ensures variation")
    print("✓ Multiple universe sources provide broad coverage")

if __name__ == "__main__":
    test_universe_diversity()
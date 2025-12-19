class PositionSizer:
    def __init__(self, total_capital, risk_tolerance=0.02, max_allocation_per_asset=0.1, diversification_factor=0.5):
        """
        Initialize position sizer.
        - total_capital: Total available capital
        - risk_tolerance: Max risk per position (e.g., 0.02 for 2%)
        - max_allocation_per_asset: Max capital allocation per asset (e.g., 0.1 for 10%)
        - diversification_factor: Factor to adjust for diversification (0-1)
        """
        self.total_capital = total_capital
        self.risk_tolerance = risk_tolerance
        self.max_allocation_per_asset = max_allocation_per_asset
        self.diversification_factor = diversification_factor

    def size_positions(self, ranked_assets, current_prices, volatilities=None):
        """Size positions for top N assets, ensuring allocation even for small capital."""
        positions = {}
        
        if not ranked_assets:
            return positions
        
        positive_assets = [(t, s) for t, s in ranked_assets if s > 0 and t in current_prices]
        
        if not positive_assets:
            print("Warning: No assets with positive scores. Taking top assets regardless of score.")
            positive_assets = [(t, s) for t, s in ranked_assets if t in current_prices]
            if not positive_assets:
                return positions
        
        total_score = sum(score for _, score in positive_assets)
        if total_score <= 0:
            total_score = len(positive_assets)
            positive_assets = [(t, 1.0) for t, _ in positive_assets]
        
        print(f"Position sizing for {len(positive_assets)} stocks with positive signals...")

        allocations = []
        for ticker, score in positive_assets:
            price = current_prices[ticker]
            volatility = volatilities.get(ticker, 0.2) if volatilities else 0.2

            score_allocation = (score / total_score) * self.total_capital * self.diversification_factor

            risk_adjusted_allocation = min(score_allocation, self.risk_tolerance * self.total_capital / max(volatility, 0.05))

            allocation = min(risk_adjusted_allocation, self.max_allocation_per_asset * self.total_capital)

            if allocation >= price * 0.5:
                allocations.append((ticker, allocation, price, score))
        
        allocations.sort(key=lambda x: x[3], reverse=True)
        
        print(f"DEBUG: Starting position sizing with ${self.total_capital} capital")
        remaining_capital = self.total_capital
        total_allocated = 0
        
        for ticker, allocation, price, score in allocations:
            if remaining_capital <= 0:
                print(f"DEBUG: Breaking - no remaining capital")
                break
                
            actual_allocation = min(allocation, remaining_capital)
            
            if actual_allocation >= price:
                shares = int(actual_allocation // price)
                if shares > 0:
                    cost = shares * price
                    positions[ticker] = shares
                    remaining_capital -= cost
                    total_allocated += cost
                    print(f"DEBUG: {ticker}: {shares} shares @ ${price:.2f} = ${cost:.2f} (remaining: ${remaining_capital:.2f})")
        
        print(f"DEBUG: Final allocation - Used: ${total_allocated:.2f}, Remaining: ${remaining_capital:.2f}")
        
        if not positions and allocations:
            print(f"Warning: Capital too small for regular allocation. Using equal-weight for affordable stocks...")
            affordable = [(t, p) for t, a, p, s in allocations if p <= self.total_capital / len(allocations[:10])]
            if not affordable:
                affordable = [(t, p) for t, a, p, s in allocations if p <= self.total_capital]
            
            equal_weight = self.total_capital / max(len(affordable), 1)
            remaining_capital = self.total_capital
            
            for ticker, price in affordable:
                if remaining_capital < price:
                    continue
                allocation = min(equal_weight, remaining_capital)
                shares = int(allocation // price)
                if shares > 0:
                    positions[ticker] = shares
                    remaining_capital -= shares * price
        
        print(f"Generated {len(positions)} positions using ${self.total_capital - remaining_capital:.2f} of ${self.total_capital:.2f}")
        return positions

    def get_portfolio_value(self, positions, current_prices):
        """Calculate total portfolio value."""
        return sum(shares * current_prices.get(ticker, 0) for ticker, shares in positions.items())

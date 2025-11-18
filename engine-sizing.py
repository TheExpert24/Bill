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
        """Size positions based on scores, prices, and constraints."""
        positions = {}
        remaining_capital = self.total_capital
        total_score = sum(score for _, score in ranked_assets if score > 0)

        for ticker, score in ranked_assets:
            if score <= 0 or ticker not in current_prices:
                continue

            price = current_prices[ticker]
            volatility = volatilities.get(ticker, 0.2) if volatilities else 0.2  # Default 20% vol

            # Base allocation proportional to score
            base_allocation = (score / total_score) * self.total_capital * self.diversification_factor

            # Adjust for risk tolerance
            risk_adjusted_allocation = min(base_allocation, self.risk_tolerance * self.total_capital / volatility)

            # Cap at max allocation
            allocation = min(risk_adjusted_allocation, self.max_allocation_per_asset * self.total_capital)

            # Ensure within remaining capital
            allocation = min(allocation, remaining_capital)

            if allocation > 0:
                shares = int(allocation // price)
                if shares > 0:
                    positions[ticker] = shares
                    remaining_capital -= shares * price

        return positions

    def get_portfolio_value(self, positions, current_prices):
        """Calculate total portfolio value."""
        return sum(shares * current_prices.get(ticker, 0) for ticker, shares in positions.items())

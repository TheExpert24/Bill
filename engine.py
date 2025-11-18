class ScoringEngine:
    def __init__(self, criteria_weights=None):
        """Initialize with configurable criteria weights."""
        self.criteria_weights = criteria_weights or {
            'bullish_crossover': 2.0,
            'oversold_rsi': 1.5,
            'low_pe_ratio': 1.0,
            'positive_sentiment_shift': 1.0,
            'overbought_rsi': -2.0,  # Negative for sell signals
            'price_above_upper_band': -1.5
        }

    def score_asset(self, rule_results):
        """Score an asset based on rule evaluation results."""
        score = 0.0
        for rule_name, result in rule_results.items():
            if rule_name in self.criteria_weights:
                weight = self.criteria_weights[rule_name]
                score += weight * (1 if result else 0)
        # Add randomness to break ties between assets with identical scores
        import random
        score += random.uniform(-0.1, 0.1)
        return score

    def rank_assets(self, asset_scores):
        """Rank assets by their scores."""
        return sorted(asset_scores.items(), key=lambda x: x[1], reverse=True)

# Example usage: asset_scores = {'AAPL': 3.5, 'GOOGL': 2.0, ...}

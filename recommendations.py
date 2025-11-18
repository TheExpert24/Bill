import json
from datetime import datetime

class RecommendationOutput:
    def __init__(self, output_format='text'):
        self.output_format = output_format  # 'text', 'json', 'csv'

    def generate_report(self, positions, scores, prices, additional_info=None):
        """Generate trade recommendations report."""
        timestamp = datetime.now().isoformat()
        report_data = {
            'timestamp': timestamp,
            'positions': positions,
            'scores': scores,
            'prices': prices,
            'additional_info': additional_info or {}
        }

        if self.output_format == 'json':
            return json.dumps(report_data, indent=4)
        elif self.output_format == 'csv':
            return self._to_csv(report_data)
        else:
            return self._to_text(report_data)

    def _to_text(self, data):
        """Generate text report."""
        report = f"Trade Recommendations - {data['timestamp']}\n\n"
        total_value = 0
        for ticker, shares in data['positions'].items():
            price = data['prices'].get(ticker, 0)
            cost = shares * price
            score = data['scores'].get(ticker, 0)
            total_value += cost
            report += f"• {ticker}: Buy {shares} shares at ${price:.2f} each. Total cost: ${cost:.2f}. Score: {score:.2f}\n"
        report += f"\nTotal Portfolio Value: ${total_value:.2f}\n"
        if data['additional_info']:
            report += f"\nAdditional Info: {data['additional_info']}\n"
        return report

    def _to_csv(self, data):
        """Generate CSV report."""
        lines = ["Ticker,Shares,Price per Share,Total Cost,Score"]
        for ticker, shares in data['positions'].items():
            price = data['prices'].get(ticker, 0)
            cost = shares * price
            score = data['scores'].get(ticker, 0)
            lines.append(f"{ticker},{shares},{price:.2f},{cost:.2f},{score:.2f}")
        return "\n".join(lines)

    def save_report(self, report, filename=None):
        """Save report to file."""
        if not filename:
            filename = f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{self.output_format}"
        with open(filename, 'w') as f:
            f.write(report)
        return filename

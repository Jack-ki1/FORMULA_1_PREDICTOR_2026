"""
Share card generator - creates shareable text/image summary cards.
Generates social media-friendly summary cards.
"""
from typing import Dict, Any, List
import json
from reports.csv_excel_report import extract_predictions_list


class ShareCardGenerator:
    """Generates shareable summary cards for social media."""
    
    def generate_card(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate shareable summary card.
        
        Args:
            data: Prediction data dictionary
        
        Returns:
            Share card data with text and HTML representations
        """
        predictions = extract_predictions_list(data)
        if not predictions:
            return {
                'error': 'No predictions available',
                'summary': 'Unable to generate share card',
            }
        
        # Extract top prediction
        top_prediction = predictions[0] if predictions else None
        top_driver = top_prediction.get('driver_code', 'Unknown') if top_prediction else 'Unknown'
        top_probability = top_prediction.get('probability', 0.0) if top_prediction else 0.0
        
        # Generate text summary
        text_summary = self._generate_text_summary(data, top_driver, top_probability)
        
        # Generate HTML card
        html_card = self._generate_html_card(data, top_driver, top_probability)
        
        # Generate markdown card
        markdown_card = self._generate_markdown_card(data, top_driver, top_probability)
        
        return {
            'summary': text_summary,
            'html': html_card,
            'markdown': markdown_card,
            'top_driver': top_driver,
            'top_probability': top_probability,
            'confidence': data.get('confidence', 0.0),
            'race_id': data.get('race_id', 'Unknown'),
            'target': data.get('target_id', 'Unknown'),
        }
    
    def _generate_text_summary(self, data: Dict[str, Any], top_driver: str, top_probability: float) -> str:
        """Generate text summary for sharing."""
        race_id = data.get('race_id', 'Unknown')
        target = data.get('target_id', 'winner')
        
        summary = f"🏎️ F1 Predictor 2026 Prediction\n"
        summary += f"🏁 Grand Prix: {race_id.title()}\n"
        summary += f"🥇 Top Pick: {top_driver} ({top_probability * 100:.1f}% for {target.upper()})\n"
        summary += f"⚡ Powered by ML & Monte Carlo Simulation"
        return summary
    
    def _generate_html_card(self, data: Dict[str, Any], top_driver: str, top_probability: float) -> str:
        """Generate HTML card for rendering."""
        race_id = data.get('race_id', 'Unknown')
        target = data.get('target_id', 'winner')
        return f"""
        <div class="f1-share-card" style="background:#16233F;color:#FFF;padding:24px;border-radius:12px;border-top:4px solid #E10600;max-width:400px;">
            <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;color:#9AA0AC;">F1 PREDICTOR 2026</div>
            <div style="font-size:20px;font-weight:bold;margin:8px 0;">{race_id.title()} GP</div>
            <div style="font-size:28px;font-weight:900;color:#E10600;">{top_driver}</div>
            <div style="font-size:14px;color:#D8DAE0;">{top_probability * 100:.1f}% Projected {target.title()} Chance</div>
        </div>
        """
    
    def _generate_markdown_card(self, data: Dict[str, Any], top_driver: str, top_probability: float) -> str:
        """Generate Markdown card."""
        race_id = data.get('race_id', 'Unknown')
        target = data.get('target_id', 'winner')
        return f"""### 🏎️ F1 2026: {race_id.title()} Prediction
**Top Projected Driver:** `{top_driver}` ({top_probability * 100:.1f}% for {target})
*Generated with F1 Predictor 2026*"""

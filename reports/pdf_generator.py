"""
PDF generator using WeasyPrint or fallback HTML renderer.
Generates professional PDF reports from prediction data.
"""
from typing import Dict, Any, List
import io
from datetime import datetime
from reports.csv_excel_report import extract_predictions_list


class PDFGenerator:
    """Generates PDF reports using WeasyPrint or fallback renderer."""
    
    def generate_pdf(self, data: Dict[str, Any]) -> bytes:
        """
        Generate PDF report from prediction data.
        
        Args:
            data: Prediction data dictionary
        
        Returns:
            PDF file bytes
        """
        try:
            from weasyprint import HTML
            html_content = self._generate_html_template(data)
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except Exception:
            return self._generate_fallback_pdf(data)
    
    def _generate_html_template(self, data: Dict[str, Any]) -> str:
        """Generate HTML template for PDF conversion."""
        predictions = extract_predictions_list(data)
        
        rows = ""
        for i, pred in enumerate(predictions, 1):
            code = pred.get('driver_code', 'Unknown')
            prob = pred.get('probability', 0.0)
            pct = pred.get('percentage', prob * 100)
            rows += f"""
            <tr>
                <td><strong>{i}</strong></td>
                <td><strong>{code}</strong></td>
                <td>{prob:.4f}</td>
                <td><div class="pct-bar"><div class="pct-fill" style="width:{min(100, pct)}%"></div></div> {pct:.1f}%</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>F1 Predictor 2026 - Predictions</title>
            <style>
                body {{ font-family: 'Helvetica Neue', Arial, sans-serif; margin: 40px; color: #15151E; background: #FFF; }}
                .header {{ border-bottom: 3px solid #E10600; padding-bottom: 15px; margin-bottom: 25px; }}
                .logo {{ font-size: 32px; font-weight: 900; color: #E10600; }}
                .meta {{ background: #F4F5F7; padding: 15px; border-radius: 8px; margin-bottom: 25px; font-size: 13px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }}
                th {{ background: #16233F; color: #FFF; padding: 10px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #E3E5EA; }}
                .pct-bar {{ display: inline-block; width: 100px; height: 8px; background: #E3E5EA; border-radius: 4px; overflow: hidden; vertical-align: middle; margin-right: 8px; }}
                .pct-fill {{ height: 100%; background: #E10600; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">FORMULA 1 PREDICTOR 2026</div>
                <h2>Session Prediction Report — {data.get('race_id', 'Race').title()}</h2>
            </div>
            <div class="meta">
                <div><strong>Race ID:</strong> {data.get('race_id', 'Unknown')} &nbsp;|&nbsp; <strong>Session:</strong> {data.get('session', data.get('session_type', 'race'))} &nbsp;|&nbsp; <strong>Target:</strong> {data.get('target_id', 'winner').upper()}</div>
                <div><strong>Generated:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
            </div>
            <table>
                <thead>
                    <tr><th>#</th><th>Driver</th><th>Probability</th><th>Percentage</th></tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        return html
    
    def _generate_fallback_pdf(self, data: Dict[str, Any]) -> bytes:
        """Fallback to basic text-based PDF or raw HTML bytes."""
        html_content = self._generate_html_template(data)
        return html_content.encode('utf-8')

"""
Reports blueprint - CSV/JSON/PDF/share-card exports.
All export functionality is now integrated into the dashboard.
This blueprint only provides API endpoints for export functionality.
"""
from flask import Blueprint, jsonify, request, send_file
from reports.csv_excel_report import CSVExcelReportGenerator
from reports.pdf_generator import PDFGenerator
from reports.share_card_generator import ShareCardGenerator
import io

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/export', methods=['POST'])
def api_export():
    """Unified export endpoint for dashboard predictions."""
    data = request.json

    try:
        format = data.get('format', 'csv')
        predictions = data.get('predictions', {})

        # Format the predictions data for the generators
        export_data = {
            'race_id': data.get('race_id'),
            'session': data.get('session'),
            'sub_session': data.get('sub_session'),
            'target_id': data.get('target_id'),
            'include_charts': data.get('include_charts', False),
            'detail_level': data.get('detail_level', 'summary'),
            'predictions': predictions
        }

        if format == 'csv':
            generator = CSVExcelReportGenerator()
            csv_data = generator.generate_csv(export_data)
            return send_file(
                io.BytesIO(csv_data.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'f1_prediction_{data.get("race_id", "race")}.csv'
            )

        elif format == 'json':
            generator = CSVExcelReportGenerator()
            json_data = generator.generate_json(export_data)
            return jsonify({'data': json_data, 'download_url': None})

        elif format == 'pdf':
            generator = PDFGenerator()
            pdf_data = generator.generate_pdf(export_data)
            return send_file(
                io.BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'f1_prediction_{data.get("race_id", "race")}.pdf'
            )

        elif format == 'share':
            generator = ShareCardGenerator()
            card_data = generator.generate_card(export_data)
            return jsonify({'data': card_data, 'download_url': None})

        else:
            return jsonify({'error': f'Unsupported format: {format}'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

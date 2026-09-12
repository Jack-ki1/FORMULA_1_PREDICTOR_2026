from reports.csv_excel_report import CSVExcelReportGenerator
from reports.pdf_generator import PDFGenerator
from reports.share_card_generator import ShareCardGenerator
import io
class ReportService:
    def export(self, data: dict):
        fmt = data.get("format","csv")
        predictions = data.get("predictions",{})
        export_data = {
            "race_id": data.get("race_id"),
            "session": data.get("session"),
            "sub_session": data.get("sub_session"),
            "target_id": data.get("target_id"),
            "include_charts": data.get("include_charts", False),
            "detail_level": data.get("detail_level","summary"),
            "predictions": predictions
        }
        if fmt=="csv":
            gen = CSVExcelReportGenerator()
            csv_data = gen.generate_csv(export_data)
            return ("csv", csv_data.encode("utf-8"), "text/csv", f'f1_prediction_{data.get("race_id","race")}.csv')
        elif fmt=="json":
            gen = CSVExcelReportGenerator()
            json_data = gen.generate_json(export_data)
            return ("json", json_data, "application/json", None)
        elif fmt=="pdf":
            gen = PDFGenerator()
            pdf_data = gen.generate_pdf(export_data)
            return ("pdf", pdf_data, "application/pdf", f'f1_prediction_{data.get("race_id","race")}.pdf')
        elif fmt=="share":
            gen = ShareCardGenerator()
            card_data = gen.generate_card(export_data)
            return ("share", card_data, "application/json", None)
        else:
            raise ValueError(f"Unsupported format: {fmt}")
report_service = ReportService()

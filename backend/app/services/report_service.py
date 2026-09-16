from backend.app.reports.csv_excel_report import CSVExcelReportGenerator
from backend.app.reports.pdf_generator import PDFGenerator
from backend.app.reports.share_card_generator import ShareCardGenerator
class ReportService:
    def export(self, data: dict):
        fmt = data.get("format","csv")
        predictions = data.get("predictions",{})
        # NOTE: use `or <default>` rather than `.get(key, default)` below.
        # `.get` only applies its default when the key is ABSENT, but every key
        # here is always present (constructed right here) — so a caller that
        # omits `target_id` produced a literal None that flowed into the
        # generators, where `data.get('target_id','winner').upper()` crashed with
        # "'NoneType' object has no attribute 'upper'" and returned HTTP 500.
        # See modify.md section 1.4.
        export_data = {
            "race_id": data.get("race_id") or "race",
            "session": data.get("session") or data.get("session_type") or "race",
            "sub_session": data.get("sub_session") or "",
            "target_id": data.get("target_id") or "winner",
            "include_charts": data.get("include_charts", False),
            "detail_level": data.get("detail_level") or "summary",
            "predictions": predictions or {}
        }
        if not isinstance(export_data["predictions"], (dict, list)):
            raise ValueError("predictions must be an object or list")
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

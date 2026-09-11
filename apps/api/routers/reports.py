"""Reports router — ports dashboard/blueprints/reports.py."""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from reports.csv_excel_report import CSVExcelReportGenerator
from reports.pdf_generator import PDFGenerator
from reports.share_card_generator import ShareCardGenerator

logger = logging.getLogger(__name__)
router = APIRouter()


class ExportRequest(BaseModel):
    format: str = "csv"
    race_id: str | None = None
    session: str | None = None
    sub_session: str | None = None
    target_id: str | None = None
    include_charts: bool = False
    detail_level: str = "summary"
    predictions: dict = {}


@router.post("/export")
def export(body: ExportRequest):
    export_data = body.model_dump()
    race_id = body.race_id or "race"

    try:
        if body.format == "csv":
            csv_data = CSVExcelReportGenerator().generate_csv(export_data)
            return Response(
                content=csv_data.encode("utf-8"),
                media_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="f1_prediction_{race_id}.csv"'},
            )

        if body.format == "json":
            json_data = CSVExcelReportGenerator().generate_json(export_data)
            return {"data": json_data, "download_url": None}

        if body.format == "pdf":
            pdf_data = PDFGenerator().generate_pdf(export_data)
            return Response(
                content=pdf_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="f1_prediction_{race_id}.pdf"'},
            )

        if body.format == "share":
            card_data = ShareCardGenerator().generate_card(export_data)
            return {"data": card_data, "download_url": None}

        raise HTTPException(status_code=400, detail=f"Unsupported format: {body.format}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

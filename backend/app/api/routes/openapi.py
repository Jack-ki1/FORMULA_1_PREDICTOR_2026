from fastapi import APIRouter

router = APIRouter()

# FastAPI auto-generates /api/v1/openapi.json from routers (3.1.0) — no custom spec needed
# Keep only alias for legacy docs pointer

@router.get("/api/docs", tags=["openapi"], include_in_schema=False)
async def docs():
    return {"message": "OpenAPI available at /api/v1/openapi.json", "swagger_ui": "/docs (FastAPI auto-docs)"}

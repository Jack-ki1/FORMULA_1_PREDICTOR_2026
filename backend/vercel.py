"""
Vercel serverless entry point for F1 Predictor 2026 (Vercel Services, service root = backend/).
"""
import importlib.util
import os
import sys
import traceback
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _ensure_backend_package() -> None:
    """Make `import backend.app` work whether or not the bundle keeps a backend/ folder."""
    try:
        spec = importlib.util.find_spec("backend.app")
    except ModuleNotFoundError:
        spec = None
    if spec is not None:
        return
    pkg = types.ModuleType("backend")
    pkg.__path__ = [_HERE]
    pkg.__file__ = os.path.join(_HERE, "__init__.py")
    pkg.__package__ = "backend"
    sys.modules["backend"] = pkg


try:
    _ensure_backend_package()
    import backend.app as _backend_app

    # backend/app/__init__.py already builds `app` (and initialises the DB schema) at import.
    app = getattr(_backend_app, "app", None) or _backend_app.create_app()
    print("F1 Predictor 2026 - Vercel serverless app ready", flush=True)
except Exception as exc:  # keep the function alive so the failure is visible
    _tb = traceback.format_exc()
    print("F1 Predictor boot failure:\n" + _tb, flush=True)
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    _message = f"{type(exc).__name__}: {exc}"
    _tail = _tb[-2000:]
    app = FastAPI(title="F1 Predictor 2026 API (boot failed)")

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    )
    async def _boot_failed(path: str):
        return JSONResponse(
            {"error": {"code": "BOOT_FAILED", "message": _message, "traceback_tail": _tail}},
            status_code=503,
        )

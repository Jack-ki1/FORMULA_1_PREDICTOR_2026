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


def _build_app():
    try:
        _ensure_backend_package()
        import backend.app as backend_app

        built = getattr(backend_app, "app", None) or backend_app.create_app()
        print("F1 Predictor 2026 - Vercel serverless app ready", flush=True)
        return built
    except Exception as exc:  # keep the function alive so the failure is visible
        tb = traceback.format_exc()
        print("F1 Predictor boot failure:\n" + tb, flush=True)
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse

        message = f"{type(exc).__name__}: {exc}"
        tail = tb[-2000:]
        fallback = FastAPI(title="F1 Predictor 2026 API (boot failed)")

        @fallback.api_route(
            "/{path:path}",
            methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
        )
        async def _boot_failed(path: str):
            return JSONResponse(
                {"error": {"code": "BOOT_FAILED", "message": message, "traceback_tail": tail}},
                status_code=503,
            )

        return fallback


app = _build_app()

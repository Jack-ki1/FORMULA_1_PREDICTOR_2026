"""
Vercel serverless entry point for F1 Predictor 2026 (Vercel Services, service root = backend/).

TEMPORARY DIAGNOSTICS: unknown URLs return a JSON report (404) describing what the
function sees. Remove the `_add_debug_catch_all` call once the deployment is verified.
"""
import importlib.util
import logging
import os
import sys
import traceback
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for _p in (_PARENT, _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class _CaptureWarnings(logging.Handler):
    """Remember recent WARNING+ log lines (e.g. 'Failed to register v1 routers: ...')."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.lines: list = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.lines.append(self.format(record)[:600])
            del self.lines[:-30]
        except Exception:
            pass


_capture = _CaptureWarnings()
logging.getLogger().addHandler(_capture)


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


def _listdir(path: str):
    try:
        return sorted(os.listdir(path))[:80]
    except Exception as exc:  # pragma: no cover
        return [f"<{type(exc).__name__}: {exc}>"]


def _add_debug_catch_all(application) -> None:
    from fastapi import Request
    from fastapi.responses import JSONResponse

    @application.api_route("/{full_path:path}", methods=["GET"], include_in_schema=False)
    async def _debug_catch_all(full_path: str, request: Request):
        try:
            route_paths = sorted(application.openapi().get("paths", {}).keys())
        except Exception as exc:  # pragma: no cover
            route_paths = [f"<openapi failed: {type(exc).__name__}: {exc}>"]
        return JSONResponse(
            {
                "debug": "temporary catch-all: no route matched this URL",
                "path_seen_by_app": request.url.path,
                "scope_path": request.scope.get("path"),
                "scope_root_path": request.scope.get("root_path"),
                "route_count": len(route_paths),
                "has_races_route": any("/races" in p for p in route_paths),
                "sample_routes": route_paths[:40],
                "captured_warnings": _capture.lines[-15:],
                "bundle_dir": _HERE,
                "bundle_listing": _listdir(_HERE),
                "app_listing": _listdir(os.path.join(_HERE, "app")),
                "app_cache_listing": _listdir(os.path.join(_HERE, "app", "cache")),
                "cwd": os.getcwd(),
                "vercel_env": os.environ.get("VERCEL"),
            },
            status_code=404,
        )


def _build_app():
    try:
        _ensure_backend_package()
        import backend.app as backend_app

        built = getattr(backend_app, "app", None) or backend_app.create_app()
        _add_debug_catch_all(built)
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

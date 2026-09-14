"""
Deprecated entrypoint — use `python backend/main.py` instead.
Kept as thin shim for backward compatibility (`python main.py` at repo root).
"""
import sys, os
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
from backend.main import main as _backend_main

if __name__ == "__main__":
    import warnings
    warnings.warn("`python main.py` is deprecated — use `python backend/main.py` or `python -m backend.main`", DeprecationWarning, stacklevel=1)
    _backend_main()

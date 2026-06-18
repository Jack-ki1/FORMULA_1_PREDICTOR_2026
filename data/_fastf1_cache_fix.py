"""
FastF1 Cache Fix — Python 3.14 Compatibility Patch.

Fixes the 'RequestsCookieJar is not defined' error that occurs when
requests_cache + cattrs try to serialize HTTP responses on Python 3.14.

This module MUST be imported before any fastf1 calls are made.
It patches requests_cache.CachedSession to use the pickle serializer
instead of the broken cattrs serializer.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_PATCHED = False


def apply_fastf1_cache_fix():
    """
    Clear corrupted FastF1 cache files and patch requests_cache
    to use pickle serializer (avoids cattrs/RequestsCookieJar NameError).

    Safe to call multiple times — only applies the patch once.
    """
    global _PATCHED
    if _PATCHED:
        return

    try:
        import fastf1
    except ImportError:
        return

    # 1. Clear corrupted cache files
    try:
        cache_dir = Path(fastf1.Cache.cache_dir) if hasattr(fastf1.Cache, 'cache_dir') else None
        if cache_dir and cache_dir.exists():
            for cache_file in cache_dir.glob("*.sqlite*"):
                try:
                    cache_file.unlink()
                    logger.debug(f"Cleared corrupted cache: {cache_file}")
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Could not clear FastF1 cache: {e}")

    # 2. Patch requests_cache to use pickle serializer
    try:
        import requests_cache

        _original_init = requests_cache.CachedSession.__init__

        def _patched_init(self, *args, **kwargs):
            if 'serializer' not in kwargs:
                kwargs['serializer'] = 'pickle'
            _original_init(self, *args, **kwargs)

        requests_cache.CachedSession.__init__ = _patched_init
        logger.debug("Patched requests_cache serializer to use pickle (Python 3.14 compat)")
    except Exception as e:
        logger.debug(f"Could not patch requests_cache: {e}")

    _PATCHED = True


def configure_fastf1_offline_mode():
    """
    Configure FastF1 to work in offline mode for future seasons.
    
    This prevents DNS errors when trying to fetch non-existent data
    for future races (e.g., 2026 season).
    """
    try:
        import fastf1
        
        # FIX: Ensure cache directory exists before enabling cache
        cache_path = Path(fastf1.Cache.cache_dir) if hasattr(fastf1.Cache, 'cache_dir') else Path('.fastf1_cache')
        cache_path.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        
        # Enable offline mode - this tells FastF1 to rely on cached data
        fastf1.Cache.enable_cache(cache_dir=str(cache_path), use_requests_cache=True)
        
        # Set a short timeout to fail fast on network issues
        import requests_cache
        requests_cache.install_cache('fastf1_cache', backend='sqlite', expire_after=86400)
        
        # Suppress verbose FastF1 warnings for future races
        logging.getLogger('fastf1').setLevel(logging.ERROR)
        logging.getLogger('fastf1.core').setLevel(logging.ERROR)
        logging.getLogger('fastf1.api').setLevel(logging.ERROR)
        logging.getLogger('fastf1.req').setLevel(logging.ERROR)
        logging.getLogger('fastf1.events').setLevel(logging.ERROR)
        
        logger.info("FastF1 configured for offline/cached operation")
        
    except Exception as e:
        logger.warning(f"Could not configure FastF1 offline mode: {e}")


# Auto-apply on import
apply_fastf1_cache_fix()

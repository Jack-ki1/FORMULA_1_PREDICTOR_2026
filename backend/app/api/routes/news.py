import asyncio
import time
import logging
import xml.etree.ElementTree as ET
from fastapi import APIRouter
from typing import List, Dict, Any, Tuple
router = APIRouter(prefix="/api/v1/news", tags=["news"])
logger = logging.getLogger(__name__)

# --- TTL cache ---------------------------------------------------------------
# The two upstream feeds were fetched sequentially with a 4s timeout each on
# EVERY request, so /api/v1/news took ~5-8s cold and repeated that cost for every
# visitor and every page load. Now the result is memoised for NEWS_TTL seconds,
# so only the first request pays network latency.
NEWS_TTL = 300.0
_FEED_TIMEOUT = 3.0
_news_cache: Dict[str, Any] = {"payload": None, "fetched_at": 0.0}
_news_lock = asyncio.Lock()


def _parse_rss(xml_text: str, source_label: str, default_image: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Parse an RSS document into the news shape. Never raises."""
    out: List[Dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
        for it in root.findall(".//item")[:limit]:
            title = (it.findtext("title", "") or "").strip()
            if not title:
                continue
            enc = it.find("enclosure")
            img = enc.get("url", "") if enc is not None else ""
            out.append({
                "title": title,
                "source": source_label,
                "date": (it.findtext("pubDate", "") or "")[:16],
                "url": (it.findtext("link", "") or "").strip() or "https://www.formula1.com",
                "image": img or default_image,
                "summary": (it.findtext("description", "") or "")[:180],
            })
    except Exception as e:
        logger.debug("RSS parse failed for %s: %s", source_label, e)
    return out
async def _fetch_feed(client, url: str, source_label: str, default_image: str) -> Tuple[str, List[Dict[str, Any]]]:
    try:
        resp = await client.get(url)
        if resp.status_code == 200:
            items = _parse_rss(resp.text, source_label, default_image)
            if items:
                return source_label, items
    except Exception as e:
        logger.debug("feed %s failed: %s", url, e)
    return source_label, []

# Fallback curated news (used when live RSS blocked or no key)
FALLBACK_NEWS: List[Dict[str, Any]] = [
  {"title":"Verstappen tops final testing in Bahrain — 2026 active aero in focus","source":"Formula1.com","date":"2026-03-02","url":"https://www.formula1.com","image":"/media/f1_simulation.png","summary":"Red Bull's RB22 shows strong straight-mode efficiency as teams debut 2026 regs with 30kg lighter cars."},
  {"title":"Audi makes official grid debut — German marque joins 2026","source":"Motorsport","date":"2026-03-01","url":"https://www.motorsport.com","image":"/media/car_parts.png","summary":"Audi A1 completes 100 laps on day one, Seidl calls it 'a solid baseline for a Works PU'."},
  {"title":"Cadillac cleared for 2026 entry — American team at 11","source":"Autosport","date":"2026-02-28","url":"https://www.autosport.com","image":"/media/f1_cartoon.png","summary":"Cadillac C1 passes crash tests, joins as 11th team with GM 2029 PU plan."},
  {"title":"FIA tweaks Overtake Mode deployment zones for Melbourne","source":"FIA","date":"2026-03-04","url":"https://www.fia.com","image":"/media/circuit2.png","summary":"Within 1s → +0.5MJ to 337 km/h, boost button adds strategic deploy — replaces DRS."},
  {"title":"Sustainable fuel era begins — 100% advanced biofuel mandated","source":"F1 Technical","date":"2026-03-03","url":"https://www.racefans.net","image":"/media/pit_stop.jpg","summary":"Non-food biomass fuel, no refuelling — tyre deg re-tuned for 2026."},
]

@router.get("", summary="Latest F1 news — live RSS via Formula1.com, fallback curated (TTL-cached)")
async def get_news(force: bool = False):
    """Latest F1 news — live RSS else curated fallback. Cached for NEWS_TTL."""
    now = time.time()
    cached = _news_cache.get("payload")
    if cached and not force and (now - _news_cache.get("fetched_at", 0.0)) < NEWS_TTL:
        return {**cached, "cached": True, "age_seconds": round(now - _news_cache["fetched_at"], 1)}

    # Serialise concurrent refreshes: without this, N simultaneous first-hits
    # would each fire their own upstream requests.
    async with _news_lock:
        cached = _news_cache.get("payload")
        if cached and not force and (time.time() - _news_cache.get("fetched_at", 0.0)) < NEWS_TTL:
            return {**cached, "cached": True, "age_seconds": round(time.time() - _news_cache["fetched_at"], 1)}

        live: List[Dict[str, Any]] = []
        source = "fallback"
        try:
            import httpx
            # Fetched CONCURRENTLY with a short timeout. Previously these two
            # feeds were awaited one after the other at 4s each, so a slow or
            # blocked upstream cost up to 8s on the request path.
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(_FEED_TIMEOUT, connect=2.0),
                headers={"User-Agent": "F1-Predictor/2026"},
            ) as client:
                results = await asyncio.gather(
                    _fetch_feed(client, "https://www.formula1.com/en/rss.xml",
                                "Formula1.com (RSS)", "/media/circuit1.png"),
                    _fetch_feed(client, "https://feeds.bbci.co.uk/sport/formula1/rss.xml",
                                "BBC Sport F1", "/media/sunset_race.png"),
                    return_exceptions=True,
                )
            for res in results:
                if isinstance(res, Exception):
                    continue
                label, items = res
                if items:
                    live = items
                    source = "live-rss" if "Formula1" in label else "live-bbc"
                    break
        except Exception as e:
            logger.debug("news fetch unavailable, fallback: %s", e)

        news = live if live else FALLBACK_NEWS
        payload = {
            "news": news,
            "source": source,
            "count": len(news),
            "note": ("Live RSS when reachable, otherwise curated fallback — "
                     f"cached for {int(NEWS_TTL)}s. Pass ?force=true to refresh."),
            "fetched_at": time.time(),
        }
        _news_cache["payload"] = payload
        _news_cache["fetched_at"] = time.time()
        return {**payload, "cached": False, "age_seconds": 0.0}

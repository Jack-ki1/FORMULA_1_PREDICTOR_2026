import time
import logging
import xml.etree.ElementTree as ET
from fastapi import APIRouter
from typing import List, Dict, Any
import asyncio

router = APIRouter(prefix="/api/v1/news", tags=["news"])
logger = logging.getLogger(__name__)

# Fallback curated news (used when live RSS blocked or no key)
FALLBACK_NEWS: List[Dict[str, Any]] = [
  {"title":"Verstappen tops final testing in Bahrain — 2026 active aero in focus","source":"Formula1.com","date":"2026-03-02","url":"https://www.formula1.com","image":"/media/f1_simulation.png","summary":"Red Bull's RB22 shows strong straight-mode efficiency as teams debut 2026 regs with 30kg lighter cars."},
  {"title":"Audi makes official grid debut — German marque joins 2026","source":"Motorsport","date":"2026-03-01","url":"https://www.motorsport.com","image":"/media/car_parts.png","summary":"Audi A1 completes 100 laps on day one, Seidl calls it 'a solid baseline for a Works PU'."},
  {"title":"Cadillac cleared for 2026 entry — American team at 11","source":"Autosport","date":"2026-02-28","url":"https://www.autosport.com","image":"/media/f1_cartoon.png","summary":"Cadillac C1 passes crash tests, joins as 11th team with GM 2029 PU plan."},
  {"title":"FIA tweaks Overtake Mode deployment zones for Melbourne","source":"FIA","date":"2026-03-04","url":"https://www.fia.com","image":"/media/circuit2.png","summary":"Within 1s → +0.5MJ to 337 km/h, boost button adds strategic deploy — replaces DRS."},
  {"title":"Sustainable fuel era begins — 100% advanced biofuel mandated","source":"F1 Technical","date":"2026-03-03","url":"https://www.racefans.net","image":"/media/pit_stop.jpg","summary":"Non-food biomass fuel, no refuelling — tyre deg re-tuned for 2026."},
]

@router.get("", summary="Latest F1 news — live RSS via Formula1.com, fallback curated (non-blocking)")
async def get_news():
    live: List[Dict[str, Any]] = []
    source = "fallback"
    # Use httpx AsyncClient so we don't block the event loop (fixes transformation.md §4)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=4, headers={"User-Agent":"F1-Predictor/2026"}) as client:
            try:
                resp = await client.get("https://www.formula1.com/en/rss.xml")
                if resp.status_code==200 and resp.text.strip().startswith("<?xml"):
                    root = ET.fromstring(resp.text)
                    items = root.findall(".//item")[:6]
                    for it in items:
                        title = it.findtext("title","").strip()
                        link = it.findtext("link","").strip()
                        pub = it.findtext("pubDate","").strip()
                        desc = it.findtext("description","").strip()
                        img = ""
                        enc = it.find("enclosure")
                        if enc is not None: img = enc.get("url","")
                        if title:
                            live.append({"title":title,"source":"Formula1.com (RSS)","date":pub[:16] if pub else "","url":link or "https://www.formula1.com","image":img or "/media/circuit1.png","summary":desc[:180]})
                    if live:
                        source="live-rss"
            except Exception as e:
                logger.debug(f"RSS Formula1 failed: {e}")
            if not live:
                try:
                    resp2 = await client.get("https://feeds.bbci.co.uk/sport/formula1/rss.xml")
                    if resp2.status_code==200:
                        root = ET.fromstring(resp2.text)
                        items = root.findall(".//item")[:6]
                        for it in items:
                            title = it.findtext("title","").strip()
                            link = it.findtext("link","").strip()
                            pub = it.findtext("pubDate","").strip()
                            desc = it.findtext("description","").strip()
                            if title:
                                live.append({"title":title,"source":"BBC Sport F1","date":pub[:16] if pub else "","url":link,"image":"/media/sunset_race.png","summary":desc[:180]})
                        if live: source="live-bbc"
                except Exception as e:
                    logger.debug(f"RSS BBC failed: {e}")
    except Exception as e:
        logger.debug(f"httpx not available, fallback: {e}")
        # Fallback to sync if httpx not available — still return curated
        pass

    news = live if live else FALLBACK_NEWS
    return {"news": news, "source": source, "count": len(news), "note": "Live RSS when available (async, non-blocking), otherwise curated fallback — always via /api/v1/news", "fetched_at": time.time()}

from __future__ import annotations
from datetime import datetime, timedelta
import random
import requests
from app.settings import settings

SYMBOL_MAP = {
    "TSLA": "TSLA", "META": "META", "SPY": "SPY", "QQQ": "QQQ",
    "VIX": "VIXY", "OIL": "USO", "NQ": "QQQ", "COMP": "QQQ", "DXY": "UUP", "US10Y": "TLT"
}

def get_quote(symbol: str) -> dict:
    mapped = SYMBOL_MAP.get(symbol.upper(), symbol.upper())
    if not settings.finnhub_api_key:
        # Safe demo fallback so app still works before API setup.
        base = {"TSLA": 390, "META": 715, "SPY": 620, "QQQ": 555}.get(symbol.upper(), 100)
        pct = random.uniform(-1.2, 1.2)
        return {"symbol": symbol.upper(), "price": round(base * (1 + pct/100), 2), "pct": round(pct, 2), "demo": True}
    url = "https://finnhub.io/api/v1/quote"
    r = requests.get(url, params={"symbol": mapped, "token": settings.finnhub_api_key}, timeout=10)
    r.raise_for_status()
    data = r.json()
    c, pc = float(data.get("c") or 0), float(data.get("pc") or 0)
    pct = ((c-pc)/pc*100) if pc else float(data.get("dp") or 0)
    return {"symbol": symbol.upper(), "price": round(c, 2), "pct": round(pct, 2), "demo": False}

def get_candles(symbol: str, minutes: int = 45) -> list[dict]:
    # Finnhub candle endpoint can be added here. Demo fallback simulates 1m candles.
    q = get_quote(symbol)
    price = q["price"] or 100
    candles = []
    now = datetime.utcnow()
    for i in range(minutes):
        drift = random.uniform(-0.0025, 0.0025)
        o = price
        c = max(1, price * (1 + drift))
        h = max(o, c) * (1 + random.uniform(0, 0.0018))
        l = min(o, c) * (1 - random.uniform(0, 0.0018))
        v = int(random.uniform(80_000, 500_000))
        candles.append({"t": (now - timedelta(minutes=minutes-i)).isoformat(), "o": round(o,2), "h": round(h,2), "l": round(l,2), "c": round(c,2), "v": v})
        price = c
    return candles

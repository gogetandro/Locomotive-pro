import os, math, random, datetime as dt
from typing import Dict, List, Literal
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="LOCOMOTIVE PRO X API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ScanRequest(BaseModel):
    symbol: Literal["TSLA","META","BOTH"] = "BOTH"

WEIGHTS = {"NQ":20,"SPY":18,"QQQ":18,"COMP":12,"VIX":-12,"OIL":-8,"DXY":-6,"US10Y":-6}

@app.get("/")
def root():
    return {"app":"LOCOMOTIVE PRO X","status":"online","endpoints":["/morning-scan","/health"]}

@app.get("/health")
def health():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat()}

def mock_market() -> Dict[str,float]:
    # Sprint 1 fallback. Later this is replaced by Finnhub candles/quotes.
    return {"NQ": random.uniform(-0.8,0.9), "SPY": random.uniform(-0.7,0.8), "QQQ": random.uniform(-0.8,0.9),
            "COMP": random.uniform(-0.7,0.8), "VIX": random.uniform(-5,5), "OIL": random.uniform(-2,2),
            "DXY": random.uniform(-0.4,0.4), "US10Y": random.uniform(-0.7,0.7)}

def market_balance(m: Dict[str,float]):
    raw = 0
    comps = {}
    for k,w in WEIGHTS.items():
        v = m.get(k,0)
        # Positive SPY/QQQ/NQ is bullish; positive VIX/OIL/DXY/Yield is bearish because weights are negative.
        c = max(-12, min(12, v * w / 2))
        comps[k] = round(c,2)
        raw += c
    score = int(max(0, min(100, 50 + raw)))
    return {"score": score, "components": comps}

def scan_symbol(symbol: str, market_score: int):
    own_momentum = random.uniform(-1.4,1.5)
    tech = random.uniform(-14,14)
    base = market_score - 50 + own_momentum*12 + tech
    call = int(max(5, min(95, 50 + base)))
    put = int(max(5, min(95, 100 - call)))
    wait = int(max(0, 100 - max(call,put)))
    if call >= 75: action="CALL"
    elif put >= 75: action="PUT"
    else: action="WAIT"
    confidence = max(call, put) if action != "WAIT" else 100 - abs(call-put)
    price = 390 if symbol=="TSLA" else 720
    atr = 4.8 if symbol=="TSLA" else 6.2
    direction = 1 if action=="CALL" else -1
    if action=="WAIT": direction=0
    entry = price + direction*0.25*atr
    stop = entry - direction*0.45*atr if direction else None
    tp1 = entry + direction*0.8*atr if direction else None
    tp2 = entry + direction*1.35*atr if direction else None
    reasons = [
        f"Market Balance = {market_score}%",
        f"{symbol} momentum = {own_momentum:+.2f}%",
        "Trade Gate: " + ("OPEN" if action!="WAIT" else "WAIT - pa gen ase konfimasyon"),
        "Opening Bell Mode: preferans 9:35 apre premye range la konfime"
    ]
    return {"symbol":symbol,"action":action,"confidence":int(confidence),"quality": quality(confidence),
            "call_probability":call,"put_probability":put,"wait_probability":wait,
            "entry":round(entry,2) if direction else None,"stop":round(stop,2) if stop else None,
            "tp1":round(tp1,2) if tp1 else None,"tp2":round(tp2,2) if tp2 else None,"reasons":reasons}

def quality(conf):
    return "A+" if conf>=92 else "A" if conf>=85 else "B" if conf>=75 else "C" if conf>=60 else "NO TRADE"

@app.post("/morning-scan")
def morning_scan(req: ScanRequest):
    m = mock_market()
    market = market_balance(m)
    symbols = ["TSLA","META"] if req.symbol=="BOTH" else [req.symbol]
    scans = [scan_symbol(s, market["score"]) for s in symbols]
    tradable = [s for s in scans if s["action"] != "WAIT"]
    best = max(tradable or scans, key=lambda x: x["confidence"])
    return {"time": dt.datetime.now().isoformat(), "mode":"Opening Bell", "market":market, "scans":scans, "best_trade":best,
            "note":"Sprint 1 uses fallback market simulation if Finnhub is not connected yet. Next sprint replaces it with live quotes/candles."}

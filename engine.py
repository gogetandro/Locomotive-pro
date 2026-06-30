from __future__ import annotations
from datetime import datetime
from app.market_data import get_quote, get_candles
from app.indicators import ema, rsi, macd, vwap, atr, rvol

MARKET_ITEMS = [
    ("NQ", "nq", False, "Nasdaq futures proxy"),
    ("SPY", "spy", False, "S&P 500 confirmation"),
    ("QQQ", "qqq", False, "Nasdaq ETF confirmation"),
    ("COMP", "comp", False, "Nasdaq Composite proxy"),
    ("VIX", "vix_inverse", True, "Fear gauge inverse"),
    ("OIL", "oil_inverse", True, "Oil pressure inverse"),
    ("DXY", "dxy_inverse", True, "Dollar strength inverse"),
    ("US10Y", "us10y_inverse", True, "Yield pressure inverse"),
]


def score_direction(value, threshold=0.1, inverse=False):
    if inverse:
        value = -value
    if value > threshold:
        return 1
    if value < -threshold:
        return -1
    return 0


def _label_from_dir(direction: int) -> str:
    if direction > 0:
        return "bullish"
    if direction < 0:
        return "bearish"
    return "neutral"


def market_snapshot(weights: dict) -> dict:
    quotes = {name: get_quote(name) for name, _, _, _ in MARKET_ITEMS}
    checklist = []
    agreement = 0
    weighted_score = 0.0
    total_weight = 0.0

    for name, key, inverse, description in MARKET_ITEMS:
        pct = quotes[name]["pct"]
        direction = score_direction(pct, inverse=inverse)
        weight = float(weights.get(key, 0))
        contribution = direction * weight
        weighted_score += contribution
        total_weight += abs(weight)
        if direction > 0:
            agreement += 1
        checklist.append({
            "symbol": name,
            "key": key,
            "description": description,
            "pct": pct,
            "direction": direction,
            "status": _label_from_dir(direction),
            "weight": round(weight, 4),
            "contribution": round(contribution, 4),
            "pass": direction > 0,
        })

    normalized = weighted_score / total_weight if total_weight else 0
    market_score = max(0, min(100, 50 + normalized * 50))
    if agreement >= 6:
        bias = "strong bullish"
    elif agreement >= 5:
        bias = "bullish"
    elif agreement <= 2:
        bias = "bearish"
    else:
        bias = "mixed"
    return {
        "quotes": quotes,
        "checklist": checklist,
        "agreement": f"{agreement}/{len(MARKET_ITEMS)}",
        "agreement_count": agreement,
        "market_score": round(market_score, 1),
        "bias": bias,
    }


def analyze_symbol(symbol: str, weights: dict, mode="safe") -> dict:
    symbol = symbol.upper()
    market = market_snapshot(weights)
    quotes = dict(market["quotes"])
    quotes[symbol] = get_quote(symbol)

    candles = get_candles(symbol, 45)
    closes = [c["c"] for c in candles]
    price = closes[-1]
    ind = {
        "ema9": ema(closes, 9),
        "ema20": ema(closes, 20),
        "ema50": ema(closes, 50),
        "ema200": ema(closes, 200),
        "rsi": rsi(closes, 14),
        "macd": macd(closes),
        "vwap": vwap(candles),
        "atr": atr(candles),
        "rvol": rvol(candles),
    }
    or_candles = candles[:5]
    or_high = max(c["h"] for c in or_candles)
    or_low = min(c["l"] for c in or_candles)

    features = {}
    breakdown = {}

    # Market layer from shared snapshot.
    for item in market["checklist"]:
        key = item["key"]
        direction = item["direction"]
        features[key] = direction
        breakdown[key] = round(direction * weights.get(key, 0), 4)

    # Technical layer.
    features["vwap"] = 1 if price > ind["vwap"] else -1
    features["ema"] = 1 if ind["ema9"] > ind["ema20"] else -1
    features["rsi"] = 1 if 52 <= ind["rsi"] <= 70 else (-1 if 30 <= ind["rsi"] < 48 else 0)
    features["macd"] = 1 if ind["macd"]["hist"] > 0 else -1
    features["rvol"] = 1 if ind["rvol"] >= 1.4 else 0
    features["orb"] = 1 if price > or_high else (-1 if price < or_low else 0)
    for k in ["vwap", "ema", "rsi", "macd", "rvol", "orb"]:
        breakdown[k] = round(features[k] * weights.get(k, 0), 4)

    raw = sum(breakdown.values())
    bullish = max(0, min(1, 0.5 + raw / 1.6))
    put = 1 - bullish
    confidence = max(bullish, put)
    threshold = 0.78 if mode == "safe" else 0.68
    decision = "WAIT"
    blockers = []

    if market["agreement_count"] < (5 if mode == "safe" else 4):
        blockers.append(f"Market agreement only {market['agreement']}.")
    if features["rvol"] <= 0 and mode == "safe":
        blockers.append("RVOL is not strong enough yet.")
    if features["orb"] == 0 and mode == "safe":
        blockers.append("Opening range has not broken yet.")

    if confidence >= threshold and not blockers:
        decision = "CALL" if bullish > put else "PUT"

    # Trade levels.
    a = max(ind["atr"], price * 0.003)
    if decision == "CALL":
        entry = price
        stop = price - a * 0.8
        target1 = price + a * 1.2
        target2 = price + a * 2.0
    elif decision == "PUT":
        entry = price
        stop = price + a * 0.8
        target1 = price - a * 1.2
        target2 = price - a * 2.0
    else:
        entry = stop = target1 = target2 = None

    reasons = []
    for item in market["checklist"]:
        if item["direction"] > 0:
            reasons.append(f"{item['symbol']} supports bullish pressure")
        elif item["direction"] < 0:
            reasons.append(f"{item['symbol']} warns against bullish pressure")
    if features["vwap"] > 0:
        reasons.append(f"{symbol} is above VWAP")
    else:
        reasons.append(f"{symbol} is below VWAP")
    if features["ema"] > 0:
        reasons.append("EMA 9 is above EMA 20")
    else:
        reasons.append("EMA 9 is below EMA 20")
    if features["orb"] > 0:
        reasons.append("Price broke above opening range")
    elif features["orb"] < 0:
        reasons.append("Price broke below opening range")

    return {
        "symbol": symbol,
        "decision": decision,
        "call_probability": round(bullish * 100, 1),
        "put_probability": round(put * 100, 1),
        "confidence": round(confidence * 100, 1),
        "entry": round(entry, 2) if entry else None,
        "stop": round(stop, 2) if stop else None,
        "target1": round(target1, 2) if target1 else None,
        "target2": round(target2, 2) if target2 else None,
        "quotes": quotes,
        "market": {k: v for k, v in market.items() if k != "quotes"},
        "indicators": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in ind.items()},
        "opening_range": {"high": round(or_high, 2), "low": round(or_low, 2)},
        "features": features,
        "breakdown": breakdown,
        "blockers": blockers,
        "reasons": reasons,
    }


def morning_scan(weights: dict, mode="safe") -> dict:
    """Run the full 9:25–9:35 scan for TSLA and META and select one best trade."""
    tsla = analyze_symbol("TSLA", weights, mode)
    meta = analyze_symbol("META", weights, mode)
    candidates = [tsla, meta]

    tradable = [x for x in candidates if x["decision"] in {"CALL", "PUT"}]
    if tradable:
        best = sorted(tradable, key=lambda x: (x["confidence"], max(x["call_probability"], x["put_probability"])), reverse=True)[0]
        best_trade = {
            "symbol": best["symbol"],
            "decision": best["decision"],
            "confidence": best["confidence"],
            "entry": best["entry"],
            "stop": best["stop"],
            "target1": best["target1"],
            "target2": best["target2"],
        }
        scan_decision = f"{best['symbol']} {best['decision']}"
    else:
        best = sorted(candidates, key=lambda x: x["confidence"], reverse=True)[0]
        best_trade = {
            "symbol": None,
            "decision": "WAIT",
            "confidence": best["confidence"],
            "entry": None,
            "stop": None,
            "target1": None,
            "target2": None,
        }
        scan_decision = "WAIT"

    shared_market = tsla["market"]
    pre_bell_checklist = []
    for item in shared_market["checklist"]:
        pre_bell_checklist.append({
            "name": item["symbol"],
            "status": item["status"],
            "pass": item["pass"],
            "pct": item["pct"],
            "note": item["description"],
        })

    technical_checklist = []
    for result in candidates:
        technical_checklist.append({
            "symbol": result["symbol"],
            "decision": result["decision"],
            "confidence": result["confidence"],
            "call_probability": result["call_probability"],
            "put_probability": result["put_probability"],
            "orb": result["features"].get("orb"),
            "vwap": result["features"].get("vwap"),
            "ema": result["features"].get("ema"),
            "rvol": result["indicators"].get("rvol"),
            "blockers": result["blockers"],
        })

    return {
        "scan_name": "Morning Scan",
        "timestamp_utc": datetime.utcnow().isoformat(),
        "mode": mode,
        "scan_decision": scan_decision,
        "best_trade": best_trade,
        "market_score": shared_market["market_score"],
        "market_bias": shared_market["bias"],
        "market_agreement": shared_market["agreement"],
        "pre_bell_checklist": pre_bell_checklist,
        "technical_checklist": technical_checklist,
        "symbols": {"TSLA": tsla, "META": meta},
        "next_step": "After 10:05 AM ET, run Auto Evaluate Latest so the Learning Engine can update weights.",
    }

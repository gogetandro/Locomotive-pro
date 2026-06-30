from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models import init_db, SessionLocal, Prediction
from app.learning import get_state, update_learning, performance
from app.engine import analyze_symbol, morning_scan
from app.market_data import get_candles
from app.telegram import send_telegram

app = FastAPI(title="LOCOMOTIVE PRO X API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup(): init_db()

def get_db():
    db=SessionLocal()
    try: yield db
    finally: db.close()

class AnalyzeRequest(BaseModel):
    symbol: str = "TSLA"
    mode: str = "safe"
    save: bool = True

class VerdictRequest(BaseModel):
    prediction_id: int
    result: str
    note: str | None = None

@app.get("/")
def root(): return {"ok": True, "name": "LOCOMOTIVE PRO X API"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    state=get_state(db)
    res=analyze_symbol(req.symbol.upper(), state.weights, req.mode)
    if req.save:
        p=Prediction(symbol=req.symbol.upper(), decision=res["decision"], confidence=res["confidence"], entry=res["entry"], stop=res["stop"], target1=res["target1"], target2=res["target2"], features=res["features"], breakdown=res["breakdown"])
        db.add(p); db.commit(); db.refresh(p)
        res["prediction_id"]=p.id
        if res["decision"] != "WAIT":
            send_telegram(f"LOCOMOTIVE PRO X\n{req.symbol.upper()} {res['decision']}\nConfidence: {res['confidence']}%\nEntry: {res['entry']} Stop: {res['stop']} T1: {res['target1']}")
    return res


class MorningScanRequest(BaseModel):
    mode: str = "safe"
    save: bool = True

@app.post("/morning-scan")
def run_morning_scan(req: MorningScanRequest, db: Session = Depends(get_db)):
    state = get_state(db)
    scan = morning_scan(state.weights, req.mode)
    saved_ids = []
    if req.save:
        for symbol, res in scan["symbols"].items():
            p = Prediction(
                symbol=symbol,
                decision=res["decision"],
                confidence=res["confidence"],
                entry=res["entry"],
                stop=res["stop"],
                target1=res["target1"],
                target2=res["target2"],
                features={**res["features"], "scan_type": "morning_scan"},
                breakdown=res["breakdown"],
            )
            db.add(p)
            db.commit()
            db.refresh(p)
            saved_ids.append({"symbol": symbol, "prediction_id": p.id})
        scan["saved_predictions"] = saved_ids
        bt = scan["best_trade"]
        send_telegram(
            f"🚂 LOCOMOTIVE PRO X — Morning Scan\n"
            f"Decision: {scan['scan_decision']}\n"
            f"Market: {scan['market_bias']} ({scan['market_score']}%)\n"
            f"Agreement: {scan['market_agreement']}\n"
            f"Best: {bt['decision']} {bt['symbol'] or ''} Conf: {bt['confidence']}%\n"
            f"Entry: {bt['entry']} Stop: {bt['stop']} T1: {bt['target1']}"
        )
    return scan

@app.post("/verdict")
def verdict(req: VerdictRequest, db: Session = Depends(get_db)):
    p=db.get(Prediction, req.prediction_id)
    if not p: raise HTTPException(404, "Prediction not found")
    p.status="evaluated"; p.result=req.result; p.result_note=req.note
    db.add(p); db.commit(); db.refresh(p)
    state=update_learning(db, p, req.result)
    return {"updated": True, "weights": state.weights, "calibration": state.calibration}

@app.post("/tasks/evaluate-latest")
def evaluate_latest(db: Session = Depends(get_db)):
    p=db.query(Prediction).filter(Prediction.status=="open").order_by(Prediction.created_at.desc()).first()
    if not p: return {"evaluated": False, "reason": "No open prediction"}
    if p.decision == "WAIT":
        result="wait_ok"; note="WAIT evaluated as safe by default. Replace with candle logic after live data setup."
    else:
        candles=get_candles(p.symbol, 35)
        highs=[c['h'] for c in candles]; lows=[c['l'] for c in candles]
        if p.decision == "CALL":
            result="correct" if p.target1 and max(highs)>=p.target1 else ("wrong" if p.stop and min(lows)<=p.stop else "wrong")
        else:
            result="correct" if p.target1 and min(lows)<=p.target1 else ("wrong" if p.stop and max(highs)>=p.stop else "wrong")
        note=f"Auto evaluated with 9:30-10:00 candle window. Decision={p.decision}."
    p.status="evaluated"; p.result=result; p.result_note=note
    db.add(p); db.commit(); db.refresh(p)
    state=update_learning(db,p,result)
    return {"evaluated": True, "prediction_id": p.id, "result": result, "weights": state.weights}

@app.get("/performance")
def perf(db: Session = Depends(get_db)): return performance(db)

@app.get("/weights")
def weights(db: Session = Depends(get_db)):
    s=get_state(db); return {"weights": s.weights, "calibration": s.calibration}

@app.get("/predictions")
def predictions(db: Session = Depends(get_db)):
    rows=db.query(Prediction).order_by(Prediction.created_at.desc()).limit(50).all()
    return [{"id":p.id,"created_at":p.created_at.isoformat(),"symbol":p.symbol,"decision":p.decision,"confidence":p.confidence,"result":p.result,"status":p.status} for p in rows]

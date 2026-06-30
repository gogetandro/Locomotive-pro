from __future__ import annotations
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import WeightState, Prediction

POSITIVE = {"correct", "wait_ok"}
NEGATIVE = {"wrong", "wait_bad"}

def get_state(db: Session) -> WeightState:
    return db.get(WeightState, 1)

def update_learning(db: Session, prediction: Prediction, result: str):
    state = get_state(db)
    weights = dict(state.weights)
    features = prediction.features or {}
    delta = 0.015 if result in POSITIVE else -0.015
    for key, value in features.items():
        if key in weights and isinstance(value, (int,float)):
            strength = min(1.0, abs(float(value)))
            weights[key] = max(0.01, min(0.35, weights[key] + delta*strength))
    # normalize market weights groups lightly, keep interpretable
    total = sum(weights.values())
    if total > 0:
        weights = {k: round(v/total*2.0, 4) for k,v in weights.items()}  # sums ~2 across market+technical groups
    state.weights = weights
    state.updated_at = datetime.utcnow()

    preds = db.query(Prediction).filter(Prediction.status == "evaluated").all()
    if preds:
        correct = sum(1 for p in preds if p.result in POSITIVE)
        rate = correct / len(preds)
        cal = dict(state.calibration or {})
        cal["accuracy"] = round(rate, 3)
        cal["confidence_cap"] = round(max(0.65, min(0.95, 0.70 + rate*0.25)), 3)
        state.calibration = cal
    db.add(state)
    db.commit()
    db.refresh(state)
    return state

def performance(db: Session):
    rows = db.query(Prediction).filter(Prediction.status == "evaluated").order_by(Prediction.created_at.desc()).all()
    def calc(n):
        r=rows[:n]
        if not r: return {"count":0,"accuracy":0}
        ok=sum(1 for x in r if x.result in POSITIVE)
        return {"count":len(r),"accuracy":round(ok/len(r)*100,1)}
    return {"last7":calc(7),"last30":calc(30),"last90":calc(90)}

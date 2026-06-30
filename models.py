from __future__ import annotations
from datetime import datetime
from sqlalchemy import create_engine, String, Float, Integer, DateTime, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.settings import settings

class Base(DeclarativeBase):
    pass

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    symbol: Mapped[str] = mapped_column(String(12), index=True)
    decision: Mapped[str] = mapped_column(String(12))  # CALL, PUT, WAIT
    confidence: Mapped[float] = mapped_column(Float)
    entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    stop: Mapped[float | None] = mapped_column(Float, nullable=True)
    target1: Mapped[float | None] = mapped_column(Float, nullable=True)
    target2: Mapped[float | None] = mapped_column(Float, nullable=True)
    features: Mapped[dict] = mapped_column(JSON)
    breakdown: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open/evaluated
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)  # correct/wrong/wait_ok/wait_bad
    result_note: Mapped[str | None] = mapped_column(Text, nullable=True)

class WeightState(Base):
    __tablename__ = "weight_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    weights: Mapped[dict] = mapped_column(JSON)
    calibration: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        state = db.get(WeightState, 1)
        if not state:
            state = WeightState(id=1, weights={
                "nq": 0.20, "spy": 0.18, "qqq": 0.18, "comp": 0.12,
                "vix_inverse": 0.12, "oil_inverse": 0.08, "dxy_inverse": 0.06, "us10y_inverse": 0.06,
                "orb": 0.12, "vwap": 0.10, "ema": 0.10, "rsi": 0.06, "macd": 0.08, "rvol": 0.10
            }, calibration={"bias": 0.0, "confidence_cap": 0.92})
            db.add(state)
            db.commit()

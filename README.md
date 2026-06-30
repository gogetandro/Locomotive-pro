# LOCOMOTIVE PRO X — Full Stack Opening Bell

A trading decision-support system for TSLA/META between 9:30–10:00 AM ET.

It includes:
- FastAPI backend
- SQLite database (local) with SQLAlchemy
- Learning engine v1
- Auto result evaluator
- Adaptive weights
- Confidence calibration
- Pattern library
- React/Vite frontend
- Telegram alert endpoint

> Educational tool only. It does not guarantee market results.

## Run backend locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend API: http://localhost:8000
API docs: http://localhost:8000/docs

## Run frontend locally

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Deploy idea

- Frontend: Netlify
- Backend: Render/Railway/Fly.io
- Database: PostgreSQL later; SQLite is included for local testing.

## Daily workflow

1. At 9:25–9:35 AM ET, open dashboard.
2. Click **Run Opening Bell Analysis**.
3. System saves prediction.
4. After 10:05 AM ET, click **Evaluate Latest Prediction** or schedule `/tasks/evaluate-latest` on backend.
5. Learning engine updates weights and calibration.


## Morning Scan

The dashboard now includes **🚀 Morning Scan**.

What it does:
1. Scans TSLA and META together.
2. Checks SPY, QQQ, NQ, COMP, VIX, OIL, DXY, and US10Y.
3. Builds a pre-bell checklist and market agreement score.
4. Runs the Trade Gate for each symbol.
5. Returns one best decision: `TSLA CALL`, `META PUT`, or `WAIT`.
6. Saves both TSLA and META predictions so the learning engine can evaluate them later.

API endpoint:

```bash
POST /morning-scan
{
  "mode": "safe",
  "save": true
}
```

After 10:05 AM ET, run:

```bash
POST /tasks/evaluate-latest
```

That updates the prediction result and adjusts adaptive weights.

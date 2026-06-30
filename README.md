# LOCOMOTIVE PRO X — Sprint 1

One Decision. Maximum Confirmation.

## Structure

```text
frontend/  -> React + Vite app for Netlify
backend/   -> FastAPI app for Render
```

## Frontend Netlify settings

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `frontend/dist`

Environment variable on Netlify:

```text
VITE_API_BASE=https://YOUR-RENDER-BACKEND.onrender.com
```

## Backend Render settings

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Sprint 1 features

- Morning Scan endpoint: `/morning-scan`
- TSLA/META CALL/PUT/WAIT
- Market Balance: NQ, SPY, QQQ, COMP, VIX, OIL, DXY, US10Y
- Trade Quality Score
- Entry / Stop / TP1 / TP2
- Why breakdown

## Important

Sprint 1 uses fallback simulated market values if live data is not connected yet. Sprint 2 replaces mock market values with real Finnhub quote/candle data.

from __future__ import annotations

def sma(values, n):
    if len(values) < n: return sum(values)/len(values) if values else 0
    return sum(values[-n:])/n

def ema(values, n):
    if not values: return 0
    k = 2/(n+1)
    e = values[0]
    for v in values[1:]: e = v*k + e*(1-k)
    return e

def rsi(values, n=14):
    if len(values) < n+1: return 50
    gains, losses = [], []
    for a,b in zip(values[-n-1:-1], values[-n:]):
        diff=b-a; gains.append(max(diff,0)); losses.append(abs(min(diff,0)))
    avg_gain=sum(gains)/n; avg_loss=sum(losses)/n
    if avg_loss == 0: return 100
    rs=avg_gain/avg_loss
    return 100 - (100/(1+rs))

def macd(values):
    m = ema(values,12)-ema(values,26)
    # simple signal proxy
    signal = m*0.8
    hist = m - signal
    return {"macd": m, "signal": signal, "hist": hist}

def vwap(candles):
    pv=sum(((x['h']+x['l']+x['c'])/3)*x['v'] for x in candles)
    vol=sum(x['v'] for x in candles)
    return pv/vol if vol else 0

def atr(candles, n=14):
    if len(candles)<2: return 0
    trs=[]
    for i in range(1,len(candles)):
        h,l,pc=candles[i]['h'],candles[i]['l'],candles[i-1]['c']
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    return sma(trs, min(n,len(trs)))

def rvol(candles, lookback=20):
    if len(candles)<2: return 1
    current=candles[-1]['v']
    avg=sum(x['v'] for x in candles[-lookback-1:-1])/min(lookback, len(candles)-1)
    return current/avg if avg else 1

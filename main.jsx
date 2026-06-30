import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App(){
  const [symbol,setSymbol]=useState('TSLA');
  const [mode,setMode]=useState('safe');
  const [res,setRes]=useState(null);
  const [scan,setScan]=useState(null);
  const [perf,setPerf]=useState(null);
  const [weights,setWeights]=useState(null);
  const [preds,setPreds]=useState([]);
  const [loading,setLoading]=useState(false);
  const [scanLoading,setScanLoading]=useState(false);

  async function refresh(){
    setPerf(await (await fetch(API+'/performance')).json());
    setWeights(await (await fetch(API+'/weights')).json());
    setPreds(await (await fetch(API+'/predictions')).json());
  }
  useEffect(()=>{refresh()},[]);

  async function analyze(){
    setLoading(true);
    const r=await fetch(API+'/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol,mode,save:true})});
    setRes(await r.json());
    setLoading(false);
    refresh();
  }

  async function morningScan(){
    setScanLoading(true);
    const r=await fetch(API+'/morning-scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode,save:true})});
    setScan(await r.json());
    setScanLoading(false);
    refresh();
  }

  async function evalLatest(){await fetch(API+'/tasks/evaluate-latest',{method:'POST'}); refresh();}
  async function mark(id,result){await fetch(API+'/verdict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prediction_id:id,result,note:'Manual verdict from dashboard'})}); refresh();}

  return <div className="app">
    <header>
      <h1>🚂 LOCOMOTIVE PRO X</h1>
      <p>One Decision. Maximum Confirmation. · Opening Bell AI · TSLA/META · 9:30–10:00 ET</p>
    </header>

    <section className="card controls hero">
      <div>
        <h2>🚀 Morning Scan</h2>
        <p>Run this around 9:25–9:35 AM. It scans TSLA + META, checks SPY/QQQ/NQ/COMP/VIX/OIL/DXY/US10Y, then gives one best decision.</p>
      </div>
      <select value={mode} onChange={e=>setMode(e.target.value)}><option value="safe">Safe Mode</option><option value="fast">Fast Mode</option></select>
      <button className="primary" onClick={morningScan} disabled={scanLoading}>{scanLoading?'Scanning...':'🚀 Run Morning Scan'}</button>
      <button onClick={evalLatest}>Auto Evaluate Latest After 10:05</button>
    </section>

    {scan && <section className={'card scan '+(scan.best_trade.decision||'wait').toLowerCase()}>
      <h2>Morning Scan Result: {scan.scan_decision}</h2>
      <div className="prob">
        <span>Market {scan.market_score}%</span>
        <span>{scan.market_bias}</span>
        <span>Agreement {scan.market_agreement}</span>
        <span>Best Confidence {scan.best_trade.confidence}%</span>
      </div>
      <div className="levels"><b>Best:</b> {scan.best_trade.decision} {scan.best_trade.symbol||''} <b>Entry:</b> {scan.best_trade.entry||'—'} <b>Stop:</b> {scan.best_trade.stop||'—'} <b>T1:</b> {scan.best_trade.target1||'—'} <b>T2:</b> {scan.best_trade.target2||'—'}</div>
      <h3>Pre-Bell Checklist</h3>
      <div className="grid">{scan.pre_bell_checklist.map(x=><div key={x.name} className={'pill '+(x.pass?'good':'bad')}><b>{x.name}</b><span>{x.status} {x.pct}%</span></div>)}</div>
      <h3>TSLA / META Technical Checklist</h3>
      <div className="grid2">{scan.technical_checklist.map(x=><div key={x.symbol} className="miniCard"><h3>{x.symbol}: {x.decision}</h3><p>Confidence {x.confidence}% · CALL {x.call_probability}% · PUT {x.put_probability}%</p><p>ORB {x.orb} · VWAP {x.vwap} · EMA {x.ema} · RVOL {x.rvol}</p>{x.blockers?.length>0 && <ul>{x.blockers.map((b,i)=><li key={i}>{b}</li>)}</ul>}</div>)}</div>
      <p className="muted">{scan.next_step}</p>
    </section>}

    <section className="card controls">
      <select value={symbol} onChange={e=>setSymbol(e.target.value)}><option>TSLA</option><option>META</option></select>
      <select value={mode} onChange={e=>setMode(e.target.value)}><option value="safe">Safe Mode</option><option value="fast">Fast Mode</option></select>
      <button onClick={analyze} disabled={loading}>{loading?'Analyzing...':'Run Single Symbol Analysis'}</button>
    </section>

    {res && <section className={'card result '+res.decision.toLowerCase()}>
      <h2>{res.symbol}: {res.decision}</h2>
      <div className="prob"><span>CALL {res.call_probability}%</span><span>PUT {res.put_probability}%</span><span>CONF {res.confidence}%</span></div>
      <div className="levels"><b>Entry:</b> {res.entry||'—'} <b>Stop:</b> {res.stop||'—'} <b>T1:</b> {res.target1||'—'} <b>T2:</b> {res.target2||'—'}</div>
      {res.blockers?.length>0 && <><h3>Trade Gate Blockers</h3><ul>{res.blockers.map((b,i)=><li key={i}>{b}</li>)}</ul></>}
      <h3>Confidence Breakdown</h3>
      <div className="grid">{Object.entries(res.breakdown).map(([k,v])=><div key={k} className="pill"><b>{k}</b><span>{v}</span></div>)}</div>
      <h3>Indicators</h3><pre>{JSON.stringify(res.indicators,null,2)}</pre>
    </section>}

    <section className="grid2"><div className="card"><h2>Performance</h2><pre>{JSON.stringify(perf,null,2)}</pre></div><div className="card"><h2>Adaptive Weights</h2><pre>{JSON.stringify(weights,null,2)}</pre></div></section>
    <section className="card"><h2>Recent Predictions</h2>{preds.map(p=><div className="row" key={p.id}><span>#{p.id} {p.symbol} {p.decision} {p.confidence}% · {p.status} {p.result||''}</span><span><button onClick={()=>mark(p.id,'correct')}>Correct</button><button onClick={()=>mark(p.id,'wrong')}>Wrong</button><button onClick={()=>mark(p.id,'wait_ok')}>Wait OK</button></span></div>)}</section>
  </div>
}

createRoot(document.getElementById('root')).render(<App/>);

import React, {useState} from 'react';
import { createRoot } from 'react-dom/client';
import { Train, Rocket, Shield, Target, Brain } from 'lucide-react';
import './style.css';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function fmt(n){return typeof n==='number'? n.toFixed(2): n}
function App(){
  const [loading,setLoading]=useState(false);
  const [result,setResult]=useState(null);
  const [symbol,setSymbol]=useState('BOTH');
  const [error,setError]=useState('');
  async function morningScan(){
    setLoading(true); setError('');
    try{
      const r = await fetch(`${API_BASE}/morning-scan`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({symbol})});
      if(!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    }catch(e){setError('API pa reponn: '+e.message)} finally{setLoading(false)}
  }
  return <main>
    <header className="hero"><div><h1><Train/> LOCOMOTIVE <span>PRO X</span></h1><p>One Decision. Maximum Confirmation. Opening Bell Mode 9:30–10:00</p></div><div className="badge">v1.0 Sprint 1</div></header>
    <section className="panel scan"><div><h2><Rocket/> Morning Scan</h2><p>Analize TSLA/META avèk SPY, QQQ, NQ, COMP, VIX, OIL, DXY, US10Y.</p></div><select value={symbol} onChange={e=>setSymbol(e.target.value)}><option>BOTH</option><option>TSLA</option><option>META</option></select><button onClick={morningScan} disabled={loading}>{loading?'Scanning...':'🚀 Run Morning Scan'}</button></section>
    {error && <section className="error">{error}<br/>Asire backend Render/FastAPI a ap mache epi mete VITE_API_BASE sou Netlify.</section>}
    {result && <Dashboard result={result}/>} 
    {!result && <section className="grid"><Info icon={<Brain/>} title="Market Balance" text="Score mache jeneral la pou wè si bulls/bears gen avantaj."/><Info icon={<Target/>} title="CALL / PUT / WAIT" text="Sistèm nan pa fòse trade; si kondisyon yo pa fò li montre WAIT."/><Info icon={<Shield/>} title="Risk Engine" text="Entry, stop loss, TP1, TP2 baze sou volatilite ak confidence."/></section>}
  </main>
}
function Info({icon,title,text}){return <div className="card"><h3>{icon}{title}</h3><p>{text}</p></div>}
function Dashboard({result}){
 return <>
  <section className="panel verdict"><div><p className="small">Best Trade Today</p><h2 className={result.best_trade.action.toLowerCase()}>{result.best_trade.symbol} {result.best_trade.action}</h2><p>Confidence: <b>{result.best_trade.confidence}%</b> · Quality: <b>{result.best_trade.quality}</b></p></div><div className="levels"><span>Entry {fmt(result.best_trade.entry)}</span><span>Stop {fmt(result.best_trade.stop)}</span><span>TP1 {fmt(result.best_trade.tp1)}</span><span>TP2 {fmt(result.best_trade.tp2)}</span></div></section>
  <section className="grid two">{result.scans.map(s=><div className="card big" key={s.symbol}><h3>{s.symbol}</h3><div className="decision"><b className={s.action.toLowerCase()}>{s.action}</b><span>{s.confidence}%</span></div><div className="bars"><div style={{width:s.call_probability+'%'}}>CALL {s.call_probability}%</div><div style={{width:s.put_probability+'%'}}>PUT {s.put_probability}%</div><div style={{width:s.wait_probability+'%'}}>WAIT {s.wait_probability}%</div></div><h4>Why?</h4><ul>{s.reasons.map((r,i)=><li key={i}>{r}</li>)}</ul></div>)}</section>
  <section className="panel"><h2>Market Balance: {result.market.score}%</h2><div className="marketgrid">{Object.entries(result.market.components).map(([k,v])=><div key={k}><b>{k}</b><span className={v>=0?'green':'red'}>{v>0?'+':''}{fmt(v)}</span></div>)}</div></section>
 </>
}
createRoot(document.getElementById('root')).render(<App/>);

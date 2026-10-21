import { useEffect, useState } from 'react';
import BracketBoard from './BracketBoard';

export default function KnockoutResults({job,label,busy,anyRunning,onDecision}:{job:any;label:(id:string)=>string;busy:boolean;anyRunning:boolean;onDecision:(body:any)=>void}){
  const [winner,setWinner]=useState('');
  const [reason,setReason]=useState('');
  const tied=job.report?.series.find((n:any)=>n.status==='awaiting_decision');
  useEffect(()=>{setWinner('');setReason('')},[job.id,tied?.id]);
  return <>
    <section className="panel knockout-bracket-panel"><div className="section-header"><span>SINGLE-ELIMINATION BRACKET</span><span className="tiny">{job.report?.seeded_roster.length} ENTRANTS</span></div><BracketBoard report={job.report} label={label}/></section>
    {job.status==='awaiting_decision'&&tied&&<form className="panel bracket-ruling" onSubmit={e=>{e.preventDefault();onDecision({series_id:tied.id,winner,reason:reason.trim()})}}>
      <h3>Still tied after two tiebreak blocks</h3><p>{tied.title} · {tied.played} games · {tied.participants.map(label).join(' vs ')}. The runner will not pick a winner silently. Apply your announced tie policy and record the ruling below. This advances the selected entrant; it does not alter match scores.</p>
      <label htmlFor="ruling-winner">ADVANCING ENTRANT</label><select id="ruling-winner" required value={winner} onChange={e=>setWinner(e.target.value)}><option value="">Choose entrant…</option>{tied.participants.map((id:string)=><option key={id} value={id}>{label(id)}</option>)}</select>
      <label htmlFor="ruling-reason">RULING REASON · SAVED IN PRIVATE ADMIN REPORT</label><textarea id="ruling-reason" required minLength={5} maxLength={500} value={reason} onChange={e=>setReason(e.target.value)} placeholder="Record the announced policy and how it was applied."/>
      <button className="button primary small" disabled={busy||anyRunning||!winner||reason.trim().length<5}>Record ruling & continue</button>
    </form>}
    {job.decisions?.length>0&&<section className="panel bracket-ruling"><h3>Organizer rulings</h3>{job.decisions.map((d:any)=><p key={d.series_id}><strong>{d.series_id} → {label(d.winner)}</strong><br/>{d.reason}</p>)}</section>}
  </>;
}

import { useEffect, useState } from 'react';
import { ArrowUpRight, Download, MonitorPlay, Pause, Play, Trophy, Users } from 'lucide-react';
import CompetitionStage from './CompetitionStage';
import KnockoutResults from './KnockoutResults';
import './competition.css';

type BotInfo={id:string;name:string;version?:string;color:string};
type Props={format?:string;bots:BotInfo[];jobs:any[];anyRunning:boolean;request:(path:string,options?:RequestInit)=>Promise<any>;onJob:(job:any)=>void;onReplay:(id:string,names?:string[])=>void;onError:(error:any)=>void};
const f=(n:number)=>Number.isFinite(n)?n.toFixed(1):'—';

export default function RoundRobinLab({format='round_robin',bots,jobs,anyRunning,request,onJob,onReplay,onError}:Props){
  const knockout=format==='knockout';
  const endpoint=knockout?'/knockouts':'/round-robins';
  const [roster,setRoster]=useState(['survivor','hunter','bomber']);
  const [games,setGames]=useState(8);
  const [seed,setSeed]=useState(10000);
  const [mode,setMode]=useState('elimination');
  const [name,setName]=useState(knockout?'Finals tournament':'Weekly round robin');
  const [shuffle,setShuffle]=useState(true);
  const [individualPacks,setIndividualPacks]=useState(false);
  const [selected,setSelected]=useState<string|null>(null);
  const [busy,setBusy]=useState(false);
  const [page,setPage]=useState(0);
  const [presenting,setPresenting]=useState(false);
  const job=jobs.find(j=>j.id===selected)||jobs[0];
  const report=job?.report;
  const pairs=knockout?Math.max(0,roster.length-1):roster.length*(roster.length-1)/2;
  const total=pairs*games;
  const label=(id:string)=>job?.entries?.[id]?.name||bots.find(b=>b.id===id)?.name||id;
  const flagged=job?.rows?.filter((r:any)=>Object.keys(r.errors||{}).length).length||0;
  const lastPage=Math.max(0,Math.ceil((job?.rows?.length||0)/25)-1);
  useEffect(()=>setPage(0),[job?.id]);
  async function action(path:string,body:any={}){
    setBusy(true);
    try{const result=await request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});onJob(result);setSelected(result.id);}
    catch(e){onError(e)}finally{setBusy(false)}
  }
  function exportAdmin(){
    const url=URL.createObjectURL(new Blob([JSON.stringify(job,null,2)],{type:'application/json'}));
    const a=document.createElement('a');a.href=url;a.download='private-competition-'+job.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  return <div className="round-robin-lab">
    <div className="competition-intro"><Users size={22}/><div><h2>{knockout?'One bracket. One champion.':'One roster. Every pairing.'}</h2><p>Two-player matches, frozen submissions and a replay for every game. This runs the competition; it does not train bots between matches.</p></div><span className="chip">ORGANIZER MODE</span></div>
    <div className="lab-layout">
      <section className="panel"><div className="section-header"><span>{knockout?'KNOCKOUT SETUP':'ROUND-ROBIN SETUP'}</span></div><div className="panel-body lab-form">
        <label htmlFor="competition-name">RUN NAME</label><input id="competition-name" maxLength={60} value={name} onChange={e=>setName(e.target.value)}/>
        <fieldset className="competition-roster" disabled={busy||anyRunning}><legend>ROSTER · {roster.length} / 16</legend>{bots.map(b=><label key={b.id}><input type="checkbox" checked={roster.includes(b.id)} onChange={e=>setRoster(r=>e.target.checked?[...r,b.id]:r.filter(id=>id!==b.id))}/><span>{b.name}<small>{b.version||'Reference bot'}</small></span></label>)}</fieldset>
        {knockout&&<><label htmlFor="competition-seeding">BRACKET SEEDING</label><select id="competition-seeding" value={String(shuffle)} onChange={e=>setShuffle(e.target.value==='true')}><option value="true">Shuffle reproducibly using seed start</option><option value="false">Selection order · first selected is seed 1</option></select><p className="field-help">{roster.map((id,i)=>`${i+1}. ${bots.find(b=>b.id===id)?.name||id}`).join(' → ')}. Byes go to the highest seeds in a standard power-of-two bracket.</p></>}
        <label htmlFor="competition-games">{knockout?'BASE GAMES PER SERIES':'GAMES PER PAIR'}</label><select id="competition-games" value={games} onChange={e=>setGames(+e.target.value)}>{[8,16,24,40,80].map(n=><option key={n}>{n}</option>)}</select>
        <p className="field-help">Every block of 8 covers both seats at all four map rotations, using the same map for all pairs.</p>
        <label htmlFor="competition-seed">SEED START</label><input id="competition-seed" type="number" value={seed} onChange={e=>setSeed(+e.target.value)}/>
        <label htmlFor="competition-mode">GAME MODE</label><select id="competition-mode" value={mode} onChange={e=>setMode(e.target.value)}><option value="elimination">Elimination</option><option value="deathmatch">Deathmatch</option></select>
        {!knockout&&<label className="individual-pack-toggle"><input type="checkbox" checked={individualPacks} onChange={e=>setIndividualPacks(e.target.checked)}/><span><strong>Prepare a separate feedback ZIP for each bot</strong><small>After the run, download one per team with anonymous opponent aliases, replays and a per-opponent performance report.</small></span></label>}
        <div className="competition-budget"><strong>{pairs} {knockout?'series':'pairs'} × {games} games</strong><span>{total} {knockout?`base matches · up to ${pairs*(games+16)} with tiebreaks`:'total matches · 2–16 bots · limit 2,000'}</span></div>
        <button className="button primary launch" disabled={busy||anyRunning||roster.length<2||roster.length>16||total>2000||!Number.isSafeInteger(seed)} onClick={()=>action(endpoint,{roster,games_per_pair:games,seed,mode,name:name.trim()||(knockout?'Knockout tournament':'Round robin'),...(knockout?{shuffle}:{individual_packs:individualPacks})})}><Play size={15}/>{busy?'Preparing…':anyRunning?'Another experiment is running':knockout?'Run knockout tournament':'Run round robin'}</button>
        <p className="field-help">{knockout?'Most game wins in a series advances. A tied series plays up to two extra 8-game blocks, then pauses for a recorded organizer ruling. Publish the ruling policy before play.':'Win 3 points · draw 1 · loss 0. Equal scores share a rank. Use Knockout for a separate elimination bracket.'}</p>
      </div></section>
      <section className="results-area">{!job?<div className="empty-results"><Trophy size={43}/><h2>Bring the whole field.</h2><p>{knockout?'Select bot versions to build an elimination bracket.':'Select bot versions and run every pair.'} Results and completed-match checkpoints are saved locally.</p></div>:<>
        <div className="results-header"><span className="eyebrow">{knockout?'KNOCKOUT HISTORY':'ROUND-ROBIN HISTORY'}</span><select aria-label={knockout?'Knockout history':'Round-robin history'} value={job.id} onChange={e=>setSelected(e.target.value)}>{jobs.map(j=><option key={j.id} value={j.id}>{j.config.name} · {j.config.roster.length} bots · {new Date(j.created_at*1000).toLocaleString()} · {j.status}</option>)}</select></div>
        <div className="experiment-progress"><span>{job.status==='running'?(job.pause_requested?'Pausing after this match…':knockout?'Playing through the bracket…':'Running all pairings…'):job.status==='complete'?(knockout?'Tournament complete':'Round robin complete'):job.status==='awaiting_decision'?'Tied series — organizer ruling required':job.status==='interrupted'?'Interrupted — completed matches are saved':job.status==='paused'?'Paused — ready to resume':'Run failed — inspect the error'}</span><b>{job.completed} / {job.total}</b><div><i style={{width:(job.completed/job.total*100)+'%'}}/></div></div>
        <div className="competition-controls"><div>{job.status==='running'?<button className="button secondary small" disabled={busy||job.pause_requested} onClick={()=>action(`${endpoint}/${job.id}/pause`)}><Pause size={14}/> Pause after match</button>:['paused','interrupted','failed'].includes(job.status)&&<button className="button primary small" disabled={busy||anyRunning} onClick={()=>action(`${endpoint}/${job.id}/resume`)}><Play size={14}/> Resume saved run</button>}<button className="button secondary small" onClick={()=>setPresenting(true)}><MonitorPlay size={15}/> Audience view</button></div><span>{job.rules_version?`Rules ${job.rules_version} · `:''}{job.config.games_per_pair} {knockout?'base games per series':'games per pair'}</span></div>
        {job.error&&<div className="error-banner" role="alert">{job.error}</div>}
        {flagged>0&&<div className="competition-warning">{flagged} matches have bot errors/timeouts. Review them before treating these standings as official; errored bots follow the normal wait behavior, not an automatic forfeit.</div>}
        {knockout&&report&&<>
          {job.status==='complete'&&<div className="competition-leader"><Trophy size={24}/><div><span>{flagged?'CHAMPION · REVIEW FLAGGED MATCHES':'TOURNAMENT CHAMPION'}</span><strong>{label(report.winner)}</strong><small>Single elimination · series results determine advancement, not cumulative points.</small></div></div>}
          <KnockoutResults job={job} label={label} busy={busy} anyRunning={anyRunning} onDecision={body=>action(`${endpoint}/${job.id}/decision`,body)}/>
        </>}
        {report&&!knockout&&<>
          <div className="competition-leader"><Trophy size={24}/><div><span>{job.status==='complete'?(flagged?'POINTS LEADERS · REVIEW FLAGGED MATCHES':report.winner?'ROUND-ROBIN WINNER':'SHARED FIRST PLACE'):'PROVISIONAL LEADERS'}</span><strong>{report.leaders.map(label).join(' · ')}</strong><small>Points only; tied scores stay tied. This is a round robin, not a knockout bracket.</small></div></div>
          <section className="panel competition-table"><div className="section-header"><span>STANDINGS</span><span className="tiny">W 3 / D 1 / L 0</span></div><div className="competition-scroll"><table><thead><tr><th>RANK</th><th>BOT / VERSION</th><th>PLAYED</th><th>W / D / L</th><th>POINTS</th><th>DAMAGE + / −</th><th>SURVIVAL</th></tr></thead><tbody>{report.standings.map((r:any)=><tr key={r.bot}><td>{r.rank}</td><td><strong>{label(r.bot)}</strong><small>{job.entries?.[r.bot]?.version?.slice(0,12)}</small></td><td>{r.played}</td><td>{r.wins} / {r.draws} / {r.losses}</td><td className="mint">{r.points}</td><td>{f(r.averages.damage_dealt)} / {f(r.averages.damage_taken)}</td><td>{f(r.averages.survival_ticks*.2)}s</td></tr>)}</tbody></table></div></section>
          <section className="panel competition-table"><div className="section-header"><span>PAIRINGS</span><span className="tiny">A WINS / DRAWS / B WINS</span></div><div className="competition-scroll"><table><thead><tr><th>BOT A</th><th>BOT B</th><th>A / D / B</th><th>PLAYED</th></tr></thead><tbody>{report.pairings.map((p:any)=><tr key={p.participants.join(':')}><td>{label(p.participants[0])}</td><td>{label(p.participants[1])}</td><td>{p.wins[p.participants[0]]} / {p.draws} / {p.wins[p.participants[1]]}</td><td>{p.played} / {job.config.games_per_pair}</td></tr>)}</tbody></table></div></section>
        </>}
        <section className="panel competition-table"><div className="section-header"><span>MATCH HISTORY</span><span className="tiny">{job.rows?.length||0} SAVED</span></div><div className="competition-scroll"><table><thead><tr><th># / SEED</th><th>MATCHUP</th><th>WINNER</th><th>FLAGS</th><th/></tr></thead><tbody>{job.rows?.slice(page*25,(page+1)*25).map((r:any,i:number)=><tr key={r.index}><td>{page*25+i+1}<small>{r.seed}{r.series_id?` · ${r.series_id}`:''}</small></td><td>{r.bots.map(label).join(' vs ')}</td><td>{r.winner?label(r.winner):'Draw'}</td><td>{Object.keys(r.errors||{}).length?'Review':'—'}</td><td><button className="text-button" onClick={()=>onReplay(r.replay_id,r.bots.map(label))}>Replay <ArrowUpRight size={13}/></button></td></tr>)}</tbody></table></div><div className="competition-pagination"><button className="button secondary small" disabled={!page} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {page+1} / {lastPage+1}</span><button className="button secondary small" disabled={page>=lastPage} onClick={()=>setPage(p=>p+1)}>Next</button></div></section>
        <section className="panel competition-exports"><h3>Keep admin records private. Share the release pack.</h3><p>The anonymous ZIP includes identity-redacted replays and per-match metrics, with shuffled file order. It omits names, global IDs, event text and errors. Behavior/maps may still identify a bot; this is not a security sandbox.</p><div><button className="button secondary small" onClick={exportAdmin}><Download size={14}/> Private admin JSON</button>{job.status==='complete'?<a className="button primary small" href={`/api${endpoint}/${job.id}/release`}><Download size={14}/> Anonymous replay pack</a>:<button className="button primary small" disabled>Replay pack after completion</button>}</div><p className="field-help">{!knockout&&job.config.individual_packs?'The shared ZIP is still available. Individual participant ZIPs below contain a report and only that bot’s matches.':'Download once and share the same ZIP with all teams.'} Unzip a pack, then load its replays folder in the Replay Library. Admin reports contain real identities.</p>
          {!knockout&&job.config.individual_packs&&<div className="participant-packs"><h4>Participant feedback ZIPs</h4><p>Each ZIP has one consistent set of anonymous opponent aliases. Names and original seeds are omitted. Map or behavior clues can still reveal opponents.</p>{job.status==='complete'?<div className="participant-pack-list">{job.config.roster.map((id:string)=><a className="button secondary small" key={id} href={`/api/round-robins/${job.id}/participants/${encodeURIComponent(id)}/release`}><Download size={14}/> {label(id)} feedback ZIP</a>)}</div>:<p className="field-help">Downloads will be ready when the round robin is complete.</p>}</div>}
        </section>
      </>}</section>
    </div>
    {job&&<CompetitionStage key={job.id} job={job} open={presenting} onClose={()=>setPresenting(false)}/>}
  </div>;
}

import { useEffect, useRef, useState } from 'react';
import { ChevronRight, Expand, Eye, Trophy, X } from 'lucide-react';
import BracketBoard, { seriesTitle } from './BracketBoard';

type Props = { job: any; open: boolean; onClose: () => void };

// Presentation is deliberately separate from scoring: no reveal changes a result.
export default function CompetitionStage({ job, open, onClose }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [slide, setSlide] = useState(-1);
  const [phase, setPhase] = useState<'ready' | 'building' | 'revealed'>('ready');
  const [reducedMotion, setReducedMotion] = useState(false);
  const [fullscreenError, setFullscreenError] = useState('');
  const [revealed, setRevealed] = useState<string[]>([]);
  const knockout = job.config.kind === 'knockout';
  const pairings = knockout ? (job.report?.series || []).filter((n: any) => n.status !== 'bye') : job.config.roster.flatMap((a: string, i: number) => job.config.roster.slice(i + 1).map((b: string) =>
    job.report?.pairings.find((p: any) => p.participants[0] === a && p.participants[1] === b) ||
    { participants: [a, b], played: 0, wins: { [a]: 0, [b]: 0 }, draws: 0 }));
  const finale = !knockout && slide === pairings.length && slide >= 0;
  const overview = knockout && slide === -2;
  const pairing = pairings[slide];
  const nextUnrevealed = pairings.findIndex((p: any) => !revealed.includes(p.id));
  const grandFinal = knockout && pairing?.title === 'Final';
  const bigReveal = finale || grandFinal;
  const sourcesVisible = !knockout || !pairing || pairing.sources.every((id: string) => revealed.includes(id) || job.report.series.find((n: any) => n.id === id)?.status === 'bye');
  const ready = finale ? job.status === 'complete' : knockout ? pairing?.status === 'complete' && sourcesVisible : pairing?.played === job.config.games_per_pair;
  const label = (id: string) => job.entries?.[id]?.name || id;
  const winners: string[] = finale ? job.report?.leaders || [] : knockout ? (pairing?.winner ? [pairing.winner] : []) : pairing
    ? pairing.wins[pairing.participants[0]] === pairing.wins[pairing.participants[1]] ? []
      : [pairing.participants[pairing.wins[pairing.participants[0]] > pairing.wins[pairing.participants[1]] ? 0 : 1]]
    : [];
  const flagged = (job.rows || []).filter((r: any) => Object.keys(r.errors || {}).length &&
    (bigReveal || pairing?.participants.every((id: string) => r.bots.includes(id)))).length;

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReducedMotion(preference.matches);
    update(); preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);
  useEffect(() => {
    const element = dialog.current;
    if (open && element && !element.open) element.showModal();
    if (!open && element?.open) element.close();
    if (!open) setPhase(p => p === 'building' ? 'ready' : p);
  }, [open]);
  useEffect(() => {
    if (phase !== 'building' || !open) return;
    const timer = window.setTimeout(() => setPhase('revealed'), reducedMotion ? 0 : 2200);
    return () => window.clearTimeout(timer);
  }, [phase, open, reducedMotion]);
  useEffect(() => {
    if (knockout && phase === 'revealed' && pairing?.id) setRevealed(old => old.includes(pairing.id) ? old : [...old, pairing.id]);
  }, [knockout, phase, pairing?.id]);
  function contender(id: string | null, seat: number) {
    const source = knockout && pairing.sources[seat] && job.report.series.find((n: any) => n.id === pairing.sources[seat]);
    if (source && !revealed.includes(source.id) && source.status !== 'bye') return `Winner of ${seriesTitle(source)}`;
    return id ? label(id) : 'To be decided';
  }
  function move(next: number) {
    setSlide(next); setPhase('ready');
  }
  function close() {
    if (document.fullscreenElement === dialog.current) void document.exitFullscreen().catch(() => {});
    onClose();
  }
  async function fullscreen() {
    try {
      if (!dialog.current?.requestFullscreen) throw new Error('Unavailable');
      await dialog.current.requestFullscreen(); setFullscreenError('');
    } catch { setFullscreenError('Fullscreen unavailable here. Maximize the window for your audience.'); }
  }
  return <dialog ref={dialog} className={`competition-stage ${bigReveal ? 'stage-finale' : ''} stage-${phase} ${reducedMotion ? 'stage-still' : ''}`}
    aria-labelledby="stage-title" onCancel={e => { e.preventDefault(); close(); }}>
    <div className="stage-grid" aria-hidden="true"/><div className="stage-glow" aria-hidden="true"/>
    <header className="stage-topbar"><span>BOT ARENA <i>/</i> LIVE</span><div><button className="stage-icon" aria-label="Enter fullscreen" onClick={fullscreen}><Expand size={18}/></button><button className="stage-icon" aria-label="Close audience view" onClick={close}><X size={20}/></button></div></header>
    <div className="stage-content">
      <p className="stage-kicker">{job.config.name} <span>· {knockout ? 'KNOCKOUT' : 'ROUND ROBIN'}</span></p>
      {overview ? <>
        <h2 id="stage-title">The road to the crown.</h2>
        <p className="stage-subtitle">Only revealed results advance on this screen.</p>
        <BracketBoard report={job.report} label={label} audience revealed={revealed}/>
      </> : slide < 0 ? <>
        <div className="stage-emblem"><Trophy size={58} strokeWidth={1.2}/></div>
        <h2 id="stage-title">Built to think.<br/><em>Ready to battle.</em></h2>
        <p className="stage-subtitle">{job.config.roster.length} contenders. {pairings.length} {knockout ? 'series. One champion.' : 'rivalries. One leaderboard.'}</p>
        <div className="stage-roster">{job.config.roster.map((id: string, i: number) => <span key={id}><small>{String(i + 1).padStart(2, '0')}</small>{label(id)}</span>)}</div>
        <p className="stage-note">Results stay hidden until the host reveals them.</p>
        {knockout && <button className="stage-outline" onClick={() => move(-2)}>View the bracket</button>}
      </> : <>
        <p className="stage-round">{finale ? 'THE CHAMPIONSHIP REVEAL' : knockout ? grandFinal ? 'THE GRAND FINAL' : seriesTitle(pairing).toUpperCase() : `PAIRING ${String(slide + 1).padStart(2, '0')} / ${String(pairings.length).padStart(2, '0')}`}</p>
        <h2 id="stage-title" className="stage-match-title">{bigReveal ? 'Who takes the crown?' : 'The matchup'}</h2>
        {!finale && pairing && <div className="stage-matchup">{pairing.participants.map((id: string | null, i: number) => <div key={i} className={`stage-contender ${phase === 'revealed' && id && winners.includes(id) ? 'is-winner' : ''} ${phase === 'revealed' && id && winners.length && !winners.includes(id) ? 'is-runner-up' : ''}`}>
          <span className="stage-seat">{grandFinal ? 'FINALIST' : 'CONTENDER'} {i + 1}</span><strong>{contender(id, i)}</strong>
          {phase === 'revealed' && id ? <span className="stage-score">{pairing.wins[id]} <small>WINS</small></span> : <span className="stage-score stage-hidden-score">?</span>}
        </div>)}<span className="stage-versus">VS</span></div>}
        <div className="stage-result" role="status" aria-live="polite" aria-atomic="true">
          {phase === 'ready' && <><div className="stage-emblem"><Trophy size={bigReveal ? 72 : 36} strokeWidth={1.2}/></div><p>{!sourcesVisible ? 'Reveal the feeder series first.' : ready ? bigReveal ? 'The field has spoken.' : 'Strategy meets its verdict.' : pairing?.status === 'awaiting_decision' ? 'Tied series — awaiting organizer ruling.' : 'Waiting for completed matches…'}</p></>}
          {phase === 'building' && <div className="stage-suspense"><span/>{bigReveal ? 'A champion is about to rise…' : 'And the result is…'}</div>}
          {phase === 'revealed' && <div className="stage-verdict">
            {bigReveal && <Trophy size={80} strokeWidth={1.3}/>}
            <p>{grandFinal ? 'TOURNAMENT CHAMPION' : finale ? winners.length === 1 ? 'ROUND-ROBIN CHAMPION' : 'SHARED FIRST PLACE' : winners.length ? knockout ? 'ADVANCING TO THE NEXT ROUND' : 'SERIES WINNER' : 'SERIES TIED'}</p>
            <strong>{winners.length ? winners.map(label).join(' & ') : 'Honors even.'}</strong>
            <span>{finale ? `${job.report.standings[0]?.points ?? 0} points · ${job.completed} matches` : `${pairing.played} games · ${pairing.draws} drawn`}</span>
            {pairing?.ruling && <small>Advanced by recorded organizer ruling after an unresolved tie.</small>}
            {flagged > 0 && <small>Provisional: {flagged} flagged matches need organizer review.</small>}
          </div>}
        </div>
        {bigReveal && phase === 'revealed' && <div className="stage-confetti" aria-hidden="true">{Array.from({ length: 36 }, (_, i) => <i key={i} style={{ left: `${(i * 29) % 100}%`, animationDelay: `${(i % 8) * .12}s`, background: i % 2 ? '#f0cf79' : '#8ae8c4' }}/>)}</div>}
        <p className="stage-note">{knockout ? 'Single elimination · balanced series · two tiebreak blocks, then recorded ruling.' : finale ? 'Champion decided by total points. Equal points share first place.' : 'Round-robin series · every contender plays every other contender.'}</p>
        {knockout && phase !== 'building' && <button className="stage-outline" onClick={() => move(-2)}>Bracket overview</button>}
      </>}
    </div>
    <footer className="stage-host-controls"><div className="stage-host-navigation"><label htmlFor="stage-slide">HOST CONTROLS</label><select id="stage-slide" value={slide} disabled={phase === 'building'} onChange={e => move(+e.target.value)}><option value={-1}>Opening screen</option>{knockout && <option value={-2}>Bracket overview</option>}{pairings.map((p: any, i: number) => <option key={p.id || p.participants.join(':')} value={i}>{knockout ? seriesTitle(p) : `${i + 1}. ${p.participants.map(label).join(' vs ')}`}</option>)}{!knockout && <option value={pairings.length}>Championship reveal</option>}</select></div>
      {slide < 0 ? <button className="stage-action" onClick={() => move(overview ? nextUnrevealed < 0 ? -1 : nextUnrevealed : 0)}>{overview ? nextUnrevealed < 0 ? 'Back to opening' : 'Next unrevealed series' : 'Introduce first matchup'}<ChevronRight size={18}/></button>
        : phase !== 'revealed' ? <button className="stage-action" disabled={!ready || phase === 'building'} onClick={() => setPhase('building')}><Eye size={18}/>{phase === 'building' ? 'Revealing…' : bigReveal ? 'Reveal champion' : 'Reveal series result'}</button>
        : finale || grandFinal ? <button className="stage-action" onClick={() => move(knockout ? -2 : -1)}>{knockout ? 'The completed bracket' : 'Back to opening'}</button>
        : <button className="stage-action" onClick={() => move(slide + 1)}>{slide + 1 === pairings.length ? 'To the championship reveal' : knockout ? 'Next series' : 'Next matchup'}<ChevronRight size={18}/></button>}
      {fullscreenError && <p className="stage-fullscreen-note" role="status">{fullscreenError}</p>}
    </footer>
  </dialog>;
}

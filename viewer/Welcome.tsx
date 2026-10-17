import { useEffect, useRef, useState } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ArrowRight, ArrowUpRight, BookOpen, Bot, Check, ChevronRight, Download, FlaskConical, GitBranch, Lightbulb, ShieldCheck, SlidersHorizontal, Swords, Target, X } from 'lucide-react';
import './welcome.css';

type Guide = {id:string;path:string;title:string;content?:string};
type Props = {onNavigate:(tab:string)=>void;onUpload:()=>void};
const steps = [
  ['Make a prediction', 'Write down your strategy and what you expect it to do. “Retreating earlier should reduce deaths against Deadeye.”'],
  ['Meet several opponents', 'Run development matches against different styles. Keep the seeds, rules and versions in your experiment notes.'],
  ['Look beyond the win', 'Compare each opponent separately. Inspect damage, survival, draws and a replay where your plan failed.'],
  ['Change one thing', 'Tweak one parameter, rule or learned component. If the algorithm changes, record that as a separate experiment.'],
  ['Compare like for like', 'Upload a new version and repeat the same development matches, including spawn rotations and opponent versions.'],
  ['Test something new', 'Freeze your final bot, then try held-out seeds and an opponent you have not tuned against. Report the limits of your result.'],
];
const reading = [
  ['project-brief','01 / THE BIG PICTURE','Why Bot Arena?','A shared introduction for participants, mentors and the team.'],
  ['workflow','02 / YOUR NEXT STEPS','The experiment playbook','The six-step loop, fair comparisons and a held-out final check.'],
  ['parameters','03 / BUILD YOUR BOT','A strategy with knobs','Understand the starter, its parameters and the code that stays fixed.'],
  ['context','04 / WORK WITH INTENT','Context for your assistant','Keep AI-assisted changes grounded in your hypothesis and the rules.'],
];

export default function Welcome({onNavigate,onUpload}:Props){
  const [guides,setGuides]=useState<Guide[]>([]);
  const [selected,setSelected]=useState<string|null>(null);
  const [guideError,setGuideError]=useState('');
  useEffect(()=>{
    const controller=new AbortController();
    fetch('/api/guides',{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('Guides could not be loaded. Try refreshing after the server starts.');return r.json();}).then(setGuides).catch(e=>{if(e.name!=='AbortError')setGuideError(e.message)});
    return()=>controller.abort();
  },[]);
  return <div className="welcome">
    <section className="welcome-hero" aria-labelledby="welcome-title">
      <div className="welcome-intro">
        <div className="welcome-kicker"><span/> YOUR STRATEGY. REAL EVIDENCE.</div>
        <h1 id="welcome-title">Build a bot.<br/><span>Learn from every battle.</span></h1>
        <p>Turn a Python strategy into a repeatable experiment. Write your rules, expose a few parameters, and discover what holds up against more than one opponent.</p>
        <div className="welcome-actions"><a className="button primary" href="/api/examples/parameter_bot.py"><Download size={16}/> Get the starter bot</a><button className="button secondary" onClick={()=>onNavigate('Arena')}><Swords size={16}/> Explore the arena</button></div>
        <div className="welcome-meta"><span><Check size={13}/> Python basics</span><span><Check size={13}/> 2–4 hour workshop</span><span><Check size={13}/> Local-first prototype</span></div>
      </div>
      <aside className="strategy-note" aria-label="An example experiment, not live results">
        <div className="note-top"><span><Lightbulb size={15}/> EXPERIMENT 001</span><span className="chip">EXAMPLE</span></div>
        <div className="note-bot"><Bot size={37}/><div><strong>Your bot. Your hypothesis.</strong><span>One change. Several opponents.</span></div></div>
        <blockquote>“If my bot seeks health earlier, it should survive longer—without giving up too many attacks.”</blockquote>
        <div className="note-change"><span>retreat_health</span><code>1 <ArrowRight size={14}/> <b>2</b></code></div>
        <div className="note-opponents"><span>CHECK AGAINST</span><div><i>W</i> Wanderer <i>D</i> Deadeye <i>F</i> Fuse</div></div>
        <p><GitBranch size={15}/> A win against one style is a clue.<br/>A fair comparison is the next step.</p>
      </aside>
    </section>

    <section className="welcome-objectives" aria-labelledby="objectives-title">
      <div className="welcome-section-heading"><div><span className="eyebrow">THE POINT IS MORE THAN WINNING</span><h2 id="objectives-title">Build the habits behind better decisions.</h2></div><button className="text-button" onClick={()=>setSelected('project-brief')}>Read the project brief <ArrowUpRight size={15}/></button></div>
      <div className="objective-grid">
        <article><GitBranch size={21}/><h3>Think in algorithms</h3><p>Design a strategy you can explain. Separate its decision rules from the parameters you want to investigate.</p></article>
        <article><FlaskConical size={21}/><h3>Experiment with evidence</h3><p>Make a prediction, change one variable, and compare versions. A result that disproves your idea is useful too.</p></article>
        <article><ShieldCheck size={21}/><h3>Test generalization</h3><p>Learn why a bot can overfit one rival. Check several opponents, then try maps and a rival you did not tune against.</p></article>
      </div>
    </section>

    <section className="welcome-process" aria-labelledby="process-title">
      <div className="welcome-section-heading"><div><span className="eyebrow">YOUR PROCESS / REPEAT WITH INTENT</span><h2 id="process-title">From an idea to a defensible result.</h2></div><button className="text-button" onClick={()=>setSelected('experiment')}><BookOpen size={15}/> Open experiment notebook</button></div>
      <ol className="process-grid">{steps.map(([title,body],i)=><li key={title}><span className="process-number">0{i+1}</span><div><h3>{title}</h3><p>{body}</p></div></li>)}</ol>
      <div className="process-next"><span>Ready for your first development run?</span><div><button className="button secondary small" onClick={onUpload}>Upload your version <ArrowUpRight size={14}/></button><button className="button primary small" onClick={()=>onNavigate('Experiment Lab')}>Open Experiment Lab <ArrowRight size={14}/></button></div></div>
    </section>

    <section className="welcome-parameters" aria-labelledby="parameters-title">
      <div><span className="eyebrow">START SMALL. KEEP OWNERSHIP.</span><h2 id="parameters-title">Your algorithm.<br/>A few meaningful knobs.</h2><p>The parameter starter chooses between attacking, seeking supplies and exploring, with a fixed hazard-escape helper. You can replace the strategy as you learn.</p><button className="text-button" onClick={()=>setSelected('parameters')}>Understand each parameter <ChevronRight size={15}/></button></div>
      <div className="parameter-example"><div><SlidersHorizontal size={15}/> parameter_bot.py <span>MANUALLY CHOSEN</span></div><pre><code>{`PARAMETERS = {\n    "retreat_health": 1,\n    "aggression": 0.7,\n    "pickup_priority": 0.4,\n}`}</code></pre><p>These control preferences, not game physics. Change one value and save a new version before comparing.</p></div>
    </section>

    <section className="learning-boundary" aria-labelledby="ml-title"><Target size={24}/><div><h2 id="ml-title">Where does machine learning fit?</h2><p>Manual tuning teaches experimentation, overfitting and generalization. It is not automatically ML. Learning begins when a procedure fits decisions or parameters from data. An optional imitation-learning example is available now; automated parameter search for your own bot is a future extension.</p><div className="welcome-learning-links"><button className="text-button" onClick={()=>setSelected('concepts')}>Understand the distinction <ArrowUpRight size={14}/></button><button className="text-button" onClick={()=>setSelected('learning-league')}>Proposed: learn over 100 matches <ArrowUpRight size={14}/></button></div></div><span className="chip">LEARNING, EXPLAINED</span></section>

    <section className="welcome-reading" aria-labelledby="reading-title"><div className="welcome-section-heading"><div><span className="eyebrow">KEEP THE CONTEXT CLOSE</span><h2 id="reading-title">A shared starting point.</h2></div><button className="text-button" onClick={()=>setSelected('resources')}>Browse learning resources <ArrowUpRight size={15}/></button></div><div className="reading-grid">{reading.map(([id,kicker,title,body])=><button key={id} className="reading-card" onClick={()=>setSelected(id)}><span className="eyebrow">{kicker}</span><h3>{title} <ArrowUpRight size={16}/></h3><p>{body}</p><small>READ THE REPOSITORY GUIDE <ChevronRight size={12}/></small></button>)}</div></section>
    <p className="welcome-safety">Python uploads run on your computer. Only upload code you trust. The local runner is not a security sandbox.</p>
    {guideError&&<p role="status" className="welcome-safety">{guideError}</p>}
    {selected&&<GuideReader id={selected} guides={guides} onRead={setSelected} onClose={()=>setSelected(null)}/>}
  </div>;
}

function GuideReader({id,guides,onRead,onClose}:{id:string;guides:Guide[];onRead:(id:string)=>void;onClose:()=>void}){
  const dialog=useRef<HTMLDialogElement>(null);
  const body=useRef<HTMLDivElement>(null);
  const [guide,setGuide]=useState<Guide|null>(null);
  const [error,setError]=useState('');
  useEffect(()=>{dialog.current?.showModal();},[]);
  useEffect(()=>{
    const controller=new AbortController();setGuide(null);setError('');body.current?.scrollTo(0,0);
    fetch('/api/guides/'+id,{signal:controller.signal}).then(r=>{if(!r.ok)throw new Error('This guide could not be loaded. Restart the updated server or try again.');return r.json();}).then(setGuide).catch(e=>{if(e.name!=='AbortError')setError(e.message)});
    return()=>controller.abort();
  },[id]);
  return <dialog className="guide-dialog" ref={dialog} onCancel={onClose} onClick={e=>{if(e.target===e.currentTarget)onClose()}} aria-labelledby="guide-title">
    <header><div><span className="eyebrow">THE REPOSITORY, WITH YOU</span><h2 id="guide-title">{guide?.title||guides.find(g=>g.id===id)?.title||'Learning guide'}</h2></div><button className="icon-button" aria-label="Close learning guide" onClick={onClose}><X size={21}/></button></header>
    <div className="guide-document" ref={body} aria-busy={!guide&&!error}>
      {error?<p role="alert">{error}</p>:!guide?<p role="status">Loading guide…</p>:<Markdown remarkPlugins={[remarkGfm]} components={{
        a:({href,children})=>{
          if(!href)return <span>{children}</span>;
          if(href.startsWith('#'))return <a href={href} onClick={e=>{e.preventDefault();const heading=Array.from(body.current?.querySelectorAll('h1,h2,h3')||[]).find(el=>el.textContent?.toLowerCase().replace(/[^\w\s-]/g,'').trim().replace(/\s+/g,'-')===href.slice(1));heading?.scrollIntoView({block:'start'});}}>{children}</a>;
          if(/^https?:\/\//.test(href))return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;
          const path=new URL(href,'https://arena.invalid/'+guide.path).pathname.slice(1);
          const linked=guides.find(g=>g.path===path);
          if(linked)return <button className="guide-link" onClick={()=>onRead(linked.id)}>{children}</button>;
          if(path.startsWith('examples/')&&['parameter_bot.py','starter_bot.py','learned_bot.py'].includes(path.slice(9)))return <a href={'/api/examples/'+path.slice(9)}>{children}</a>;
          return <span>{children}</span>;
        },
      }}>{guide.content||''}</Markdown>}
    </div>
    <footer><span>{guide?.path||'Markdown guide'}</span><a className="text-button" href={`/api/guides/${id}?download=true`}><Download size={14}/> Download Markdown</a></footer>
  </dialog>;
}

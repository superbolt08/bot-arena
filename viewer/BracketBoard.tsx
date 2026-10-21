export const seriesTitle = (node: any) => node.title + (node.title === 'Final' ? '' : ` · ${node.slot}`);

export default function BracketBoard({ report, label, audience = false, revealed = [] }: {
  report: any; label: (id: string) => string; audience?: boolean; revealed?: string[];
}) {
  if (!report?.rounds) return null;
  const visible = (node: any) => !audience || node.status === 'bye' || revealed.includes(node.id);
  function entrant(node: any, id: string | null, seat: number) {
    const source = report.series.find((n: any) => n.id === node.sources[seat]);
    if (source && !visible(source)) return `Winner of ${seriesTitle(source)}`;
    return id ? label(id) : source ? `Winner of ${seriesTitle(source)}` : 'Bye';
  }
  return <div className={`bracket-board ${audience ? 'bracket-audience' : ''}`} role="region" aria-label="Knockout bracket" tabIndex={0}>
    {report.rounds.map((round: any, r: number) => <section className="bracket-round" key={r} aria-label={round.title}>
      <h3>{round.title}</h3><div className="bracket-series-list">{round.series.map((node: any) => <article key={node.id} className={`bracket-series ${node.title === 'Final' ? 'bracket-final' : ''}`}>
        <p>{seriesTitle(node)} <span>{node.status === 'bye' ? 'BYE' : !visible(node) ? 'UNREVEALED' : node.ruling ? 'RULING' : node.status === 'complete' ? 'FINAL' : node.status === 'awaiting_decision' ? 'TIED' : `${node.played} / ${node.target}`}</span></p>
        {node.participants.map((id: string | null, seat: number) => <div key={seat} className={visible(node) && id && node.winner === id ? 'bracket-winner' : ''}><strong>{entrant(node, id, seat)}</strong><b>{node.status === 'bye' ? '—' : visible(node) && id ? node.wins[id] ?? '—' : '?'}</b></div>)}
      </article>)}</div>
    </section>)}
  </div>;
}

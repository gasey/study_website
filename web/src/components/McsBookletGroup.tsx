import { useState } from 'react'
import type { BookletGroup } from '../lib/mcsBooklets'
import { bookletLabel } from '../lib/mcsBooklets'
import ExamPaperCard from './ExamPaperCard'

export default function McsBookletGroup({ group }: { group: BookletGroup }) {
  const [selected, setSelected] = useState(group.papers[0].id)
  const paper = group.papers.find(p => p.id === selected) || group.papers[0]
  return <section className="min-w-0" aria-label={group.title}>
    <h3 className="mb-2 text-[15px] font-semibold">{group.title}</h3>
    {group.papers.length > 1 && <div className="mb-2 flex flex-wrap gap-2" role="group" aria-label={`Choose booklet for ${group.title}`}>
      {group.papers.map(p => <button key={p.id} type="button" aria-pressed={paper.id === p.id}
        onClick={() => setSelected(p.id)} className={'min-h-11 rounded-pill border px-3 text-[12px] font-semibold ' +
          (paper.id === p.id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card text-ink')}>
        {bookletLabel(p)}
      </button>)}
    </div>}
    <ExamPaperCard key={paper.id} paper={paper} examId="combined-prelims" />
  </section>
}

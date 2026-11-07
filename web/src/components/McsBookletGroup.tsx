import { useState } from 'react'
import {representativeBooklet} from '../lib/sourceBooklets'
import type { BookletGroup } from '../lib/mcsBooklets'
import { bookletLabel } from '../lib/mcsBooklets'
import ExamPaperCard from './ExamPaperCard'

export default function McsBookletGroup({ group, examId = 'combined-prelims' }: { group: BookletGroup; examId?: string }) {
  const [selected, setSelected] = useState(()=>representativeBooklet(group).id)
  const paper = group.papers.find(p => p.id === selected) || representativeBooklet(group)
  return <section className="flex min-w-0 flex-col" aria-label={group.title}>
    <h3 className="mb-2 text-[15px] font-semibold">{group.title}</h3>
    {group.papers.length > 1 && <details className="exam-booklet-disclosure mb-2 rounded-[12px] border border-hairline bg-card px-4">
      <summary className="flex min-h-11 cursor-pointer items-center text-[12px] font-semibold text-secondary">Booklet series &amp; original sources</summary>
      <p className="mb-2 text-[12px] text-secondary">One booklet is shown for study. Other originals retain their printed order and answer mapping.</p>
      <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label={`Choose booklet for ${group.title}`}>
      {group.papers.map(p => <button key={p.id} type="button" aria-pressed={paper.id === p.id}
        onClick={() => setSelected(p.id)} className={'min-h-11 rounded-pill border px-3 text-[12px] font-semibold ' +
          (paper.id === p.id ? 'border-ink bg-ink text-paper' : 'border-hairline bg-card text-ink')}>
        {bookletLabel(p)}
      </button>)}
    </div></details>}
    <ExamPaperCard key={paper.id} paper={paper} examId={examId} hideSeriesInTitle />
  </section>
}

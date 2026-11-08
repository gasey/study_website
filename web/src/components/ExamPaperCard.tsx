import {withoutBooklet} from '../lib/sourceBooklets'
import {paperIdentity} from '../lib/paperIdentity'
import { Link } from 'react-router-dom'
import type { CollectionPaper } from '../lib/api'

/** Shared across exam modules. Printed identity and test eligibility remain separate. */
export default function ExamPaperCard({ paper: p, examId, hideSeriesInTitle=false }: { paper: CollectionPaper; examId: string; hideSeriesInTitle?: boolean }) {
  const {title:sourceTitle,exam,filename}=paperIdentity(p)
  const title = hideSeriesInTitle ? withoutBooklet(sourceTitle) : sourceTitle
  const compactSource = examId==='udc'||examId==='combined-prelims'
  const count = (n: number) => n.toLocaleString('en-IN')
  const base = `/exams/${examId}`
  const paper = encodeURIComponent(p.id)
  const filtered = (status: string) => `${base}?view=browse&pool=all&paper=${paper}&answer_status=${status}#exam-question-browser`
  const keyTest = p.allow_timed_test && p.scorable >= 20
  const reviewedTest = p.allow_practice && p.practice_count > 0 && !keyTest
  const button = 'inline-flex min-h-11 items-center justify-center rounded-pill border px-4 py-2 text-[13px] font-semibold'
  return <article className="exam-paper-card min-w-0 rounded-[12px] border border-hairline bg-card p-4 sm:p-5">
    <div className="exam-paper-body flex flex-1 flex-col gap-4">
      <div className="min-w-0 flex-1">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <span className="rounded-md border border-hairline bg-canvas px-2 py-1 font-mono text-[11px] font-semibold tracking-[0.04em] text-secondary">{p.year || 'Past paper'}</span>
          {!compactSource && p.source_pdf_url && <a href={p.source_pdf_url} target="_blank" rel="noreferrer" className="exam-paper-source inline-flex min-h-11 items-center gap-1 text-[12px] font-semibold text-link">Source PDF <span aria-hidden="true">↗</span></a>}
        </div>
        <h3 className="exam-paper-title break-words font-display text-[21px] font-medium leading-snug">{title}</h3>
        <p className="mt-2 break-words text-[13px] leading-relaxed text-secondary">{exam}</p>
        <p className="mt-1 text-[13px] text-secondary">{count(p.questions)} questions{p.descriptive > 0 ? ` · ${count(p.descriptive)} written` : ''}{!p.questions ? ' · PDF only' : ''}</p>
        {examId==='combined-prelims'&&p.year!==null&&p.year>=2023&&p.questions>0&&p.questions<100&&<p className="mt-2 text-[12px] text-[#80520a]">Fewer than 100 questions available · check source coverage</p>}
        {examId==='combined-prelims'&&p.instructions?.startsWith('Recovered Chase')&&<p className="mt-2 text-[12px] text-[#80520a]">Recovered copy · transcription and answer review pending</p>}
        <div className="exam-paper-coverage mt-4 flex flex-col items-start gap-1 text-[12px] leading-relaxed" aria-label="Answer coverage">
          {p.scorable > 0 && <Link to={filtered('official')} className="exam-paper-status font-semibold text-[#17613e]"><span aria-hidden="true">▪</span> {count(p.scorable)} official keys</Link>}
          {p.verified_solutions > 0 && <Link to={filtered('verified')} className="exam-paper-status font-semibold text-[#245f91]"><span aria-hidden="true">✓</span> {count(p.verified_solutions)} verified solutions · unofficial</Link>}
          <div className="flex flex-wrap gap-x-4 gap-y-1">
          {p.needs_review > 0 && <Link to={filtered('needs-review')} className="exam-paper-status text-[#80520a]">{count(p.needs_review)} {p.needs_review === 1 ? 'needs' : 'need'} review</Link>}
          {p.unsolved > 0 && <Link to={filtered('unsolved')} className="exam-paper-status text-secondary">{count(p.unsolved)} unanswered</Link>}
          {p.blocked_count > 0 && <span className="text-mypick">{count(p.blocked_count)} source/key issues</span>}
          </div>
        </div>
      </div>
      {p.questions===0&&<p className="mt-3 text-[12px] text-secondary">{p.source_pdf_url?'Original PDF available · questions not yet extracted.':'Questions not yet extracted; no original PDF is linked.'}</p>}
      <div className="exam-paper-actions mt-auto flex shrink-0 flex-wrap items-center gap-2">
        {p.questions > 0 && <Link to={`${base}/paper?paper=${paper}`} className={`${button} border-ink bg-ink text-paper`}>Browse paper</Link>}
        {p.allow_practice && p.answerable_count > 0 && <Link to={`${base}?view=practice&paper=${paper}#exam-question-browser`} className={`${button} border-hairline`}>Practise · {count(p.answerable_count)}</Link>}
      </div>
    </div>
    <details className="group mt-3 border-t border-hairline pt-1">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-2 text-[12px] font-semibold text-secondary"><span>Paper details{keyTest || reviewedTest ? ' & tests' : ''}</span><span aria-hidden="true" className="exam-paper-expand transition-transform group-open:rotate-45">＋</span></summary>
      <div className="space-y-3 pb-1 pt-1 text-[13px] leading-relaxed text-secondary">
        {hideSeriesInTitle && <p className="break-words">Selected source: {sourceTitle}</p>}
        <p className="break-words">{p.paper_label || p.title}</p>
        <p className="break-words text-[12px]">Source file: {filename}</p>
        {compactSource && p.source_pdf_url && <a href={p.source_pdf_url} target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center text-[12px] font-semibold text-link">Source PDF ↗</a>}
        {!!p.missing_explanations && <p>{count(p.missing_explanations)} {p.missing_explanations === 1 ? 'question has' : 'questions have'} no explanation yet.</p>}
        {!!p.blocked_count && <p>Questions with source/key issues are excluded from scoring.</p>}
        {(keyTest || reviewedTest) && <div className="rounded-[8px] border border-hairline bg-canvas p-3">
          <p className="font-semibold text-ink">Timed practice</p>
          <p className="mt-1">{p.rule_source === 'platform-default' ? 'Uses practice timing and marks. Original paper rules are not confirmed.' : `Configured paper rules${p.duration_minutes !== null ? ` · ${p.duration_minutes} minutes` : ''}${p.marks_correct !== null ? ` · +${p.marks_correct} correct` : ''}${p.marks_wrong !== null ? ` · ${p.marks_wrong > 0 ? '-' : ''}${p.marks_wrong} incorrect` : ''}.`} Only eligible questions are included.</p>
          {reviewedTest && <p className="mt-1">The reviewed estimate uses verified answers alongside available official keys.</p>}
          <div className="mt-3 flex flex-wrap gap-2">
            {keyTest && <Link to={`${base}/mock?paper=${paper}`} className={`${button} border-hairline bg-card text-ink`}>Official-key practice · {count(p.scorable)}</Link>}
            {reviewedTest && <Link to={`${base}/mock?paper=${paper}&mode=derived`} className={`${button} border-hairline bg-card text-ink`}>Reviewed estimate · {count(p.practice_count)}</Link>}
          </div>
        </div>}
        {p.rule_source !== 'platform-default' && !(keyTest || reviewedTest) && (p.duration_minutes !== null || p.marks_correct !== null) && <p>Configured paper rules{p.duration_minutes !== null ? ` · ${p.duration_minutes} minutes` : ''}{p.marks_correct !== null ? ` · +${p.marks_correct} correct` : ''}{p.marks_wrong !== null ? ` · ${p.marks_wrong > 0 ? '-' : ''}${p.marks_wrong} incorrect` : ''}.</p>}
      </div>
    </details>
  </article>
}

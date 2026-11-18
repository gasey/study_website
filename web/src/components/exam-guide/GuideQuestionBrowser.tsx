import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { listQuestions, listTaxonomy, submitAnswer, type AnswerResult, type ListParams, type Question, type QuestionPage, type TaxonomyFacet } from '../../lib/api';
import { selectGuidePaper, sourcePaperId, type ArchivedExamPaper } from '../../lib/examGuides';
import { nextBrowseOffset, readStudyStatus, studyStatusOptions } from '../../lib/questionBrowse';
import { AnswerLayoutControl } from '../AnswerLayout';
import StudyQuestionCard from '../StudyQuestionCard';
import Pagination from '../Pagination';

const FILTER_KEYS = ['paper', 'paper_type', 'paper_year', 'q', 'subject_id', 'topic_id', 'subtopic_id', 'status', 'answer_status', 'pool', 'order', 'seed', 'offset'];
const ANSWER_STATUSES = [['official', 'Official keys'], ['verified', 'Verified answers'], ['needs-review', 'Needs review'], ['unsolved', 'No answer yet'], ['written', 'Written questions']] as const;
const paperType = (paper: ArchivedExamPaper) => paper.branchId ? 'branch' : `common:${paper.subject}`;
function questionFilters(params: URLSearchParams, practice: boolean) {
  const pool: ListParams['pool'] = practice ? 'practice' : params.get('pool') === 'scorable' ? 'scorable' : params.get('pool') === 'practice' ? 'practice' : 'all';
  const answerStatus = ANSWER_STATUSES.find(([id]) => id === params.get('answer_status'))?.[0];
  return { pool, answerStatus, studyStatus: readStudyStatus(params.get('status')), subjectId: params.get('subject_id') || '', topicId: params.get('topic_id') || '', search: (params.get('q') || '').slice(0, 120) };
}

export function GuideQuestionBrowser({ papers, guideId, practice = false }: { papers: ArchivedExamPaper[]; guideId: string; practice?: boolean }) {
  const [params, setParams] = useSearchParams();
  const types = useMemo(() => [...new Set(papers.map(paperType))], [papers]);
  const type = types.includes(params.get('paper_type') || '') ? params.get('paper_type')! : '';
  const typedPapers = papers.filter((p) => !type || paperType(p) === type);
  const years = [...new Set(typedPapers.map((p) => String(p.year)))];
  const year = years.includes(params.get('paper_year') || '') ? params.get('paper_year')! : '';
  const available = typedPapers.filter((p) => !year || String(p.year) === year);
  const selected = selectGuidePaper(available, params.get('paper'));
  const position = available.findIndex((p) => p.id === selected?.id);
  const { pool, answerStatus, studyStatus, subjectId, topicId, search } = questionFilters(params, practice);
  const [taxonomy, setTaxonomy] = useState<TaxonomyFacet[]>([]);
  const [taxonomyError, setTaxonomyError] = useState('');
  const [taxonomyRetry, setTaxonomyRetry] = useState(0);
  const hasSource = !!selected && !!sourcePaperId(selected);
  useEffect(() => {
    if (!hasSource) return;
    let current = true;
    setTaxonomyError('');
    // Approved bank labels only; global taxonomy counts are not presented as paper counts.
    void listTaxonomy('all', true).then((value) => { if (current) setTaxonomy(value); }).catch(() => { if (current) setTaxonomyError('Subject and topic choices could not load.'); });
    return () => { current = false; };
  }, [hasSource, taxonomyRetry]);
  const subjects = [...new Map(taxonomy.map((row) => [row.subject_id, row.subject])).entries()];
  const topics = [...new Map(taxonomy.filter((row) => row.subject_id === subjectId && row.topic_id).map((row) => [row.topic_id!, row.topic || row.topic_id!])).entries()];
  function change(key: string, value: string) {
    setParams((previous) => {
      const next = new URLSearchParams(previous);
      if (value) next.set(key, value); else next.delete(key);
      next.delete('offset');
      if (key === 'subject_id') { next.delete('topic_id'); next.delete('subtopic_id'); }
      if (key === 'topic_id') next.delete('subtopic_id');
      if (['paper', 'paper_type', 'paper_year'].includes(key)) {
        next.delete('subject_id'); next.delete('topic_id'); next.delete('subtopic_id'); next.delete('seed');
        if (key !== 'paper') next.delete('paper');
        if (key === 'paper_type') next.delete('paper_year');
      }
      return next;
    }, { replace: key !== 'paper' });
  }
  function reset() {
    setParams((previous) => { const next = new URLSearchParams(previous); FILTER_KEYS.forEach((key) => next.delete(key)); return next; }, { replace: true });
  }
  function status(value: string) {
    setParams((previous) => {
      const next = new URLSearchParams(previous);
      next.delete('status'); next.delete('answer_status'); next.delete('offset');
      if (value.startsWith('study:')) next.set('status', value.slice(6));
      if (value.startsWith('answer:')) { next.set('answer_status', value.slice(7)); if (!practice) next.set('pool', 'all'); }
      return next;
    }, { replace: true });
  }
  if (!selected) return <p className="eg-empty">No source papers are available for this branch and scheme.</p>;
  const archive = new URLSearchParams(params);
  FILTER_KEYS.forEach((key) => archive.delete(key)); archive.delete('tab'); archive.set('view', 'papers');
  return <section id="exam-question-browser" className="exam-module-content" tabIndex={-1}>
    <div className="mb-3 flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-display text-[22px]">{practice ? 'Study practice' : 'Browse questions'}</h2><p className="text-[12px] text-secondary">Filters apply within your selected branch and source paper.</p></div><button type="button" onClick={reset} className="min-h-11 rounded-pill border border-hairline px-4 text-[12px] font-semibold">Reset filters</button></div>
    <div className="browse-filter-row eg-browse-filters" aria-label="Question filters">
      <label>Paper type<select aria-label="Paper type" value={type} onChange={(e) => change('paper_type', e.target.value)}><option value="">All paper types</option>{types.map((id) => <option key={id} value={id}>{id === 'branch' ? 'Branch papers' : id.slice(7)}</option>)}</select></label>
      <label>Specific paper<select aria-label="Specific paper" value={selected.id} onChange={(e) => change('paper', e.target.value)}>{available.map((p) => <option key={p.id} value={p.id}>{p.year} · {p.subject}{p.paperNumber ? ` · ${p.paperNumber}` : ''} · {p.sitting}{!sourcePaperId(p) ? ' · PDF only' : ''}</option>)}</select></label>
      <label>Subject<select aria-label="Subject" value={subjectId} disabled={!hasSource} onChange={(e) => change('subject_id', e.target.value)}><option value="">All subjects</option>{subjectId && !subjects.some(([id]) => id === subjectId) && <option value={subjectId}>Selected subject</option>}{subjects.map(([id, title]) => <option key={id} value={id}>{title}</option>)}</select></label>
      <label>Topic<select aria-label="Topic" value={topicId} disabled={!hasSource || !subjectId} onChange={(e) => change('topic_id', e.target.value)}><option value="">All topics</option>{topicId && !topics.some(([id]) => id === topicId) && <option value={topicId}>Selected topic</option>}{topics.map(([id, title]) => <option key={id} value={id}>{title}</option>)}</select></label>
      <label>Status<select aria-label="Question status" disabled={!hasSource} value={answerStatus ? `answer:${answerStatus}` : studyStatus !== 'all' ? `study:${studyStatus}` : ''} onChange={(e) => status(e.target.value)}><option value="">All questions</option><optgroup label="Your study">{studyStatusOptions.filter(([id]) => id !== 'all').map(([id, title]) => <option key={id} value={`study:${id}`}>{title}</option>)}</optgroup><optgroup label="Answer source">{ANSWER_STATUSES.map(([id, title]) => <option key={id} value={`answer:${id}`}>{title}</option>)}</optgroup></select></label>
      <label>Search<input aria-label="Search questions" type="search" maxLength={120} value={search} disabled={!hasSource} onChange={(e) => change('q', e.target.value)} placeholder="Question or option text" /></label>
    </div>
    {taxonomyError && <p role="status" className="eg-muted">{taxonomyError} <button className="min-h-11 text-link underline" onClick={() => setTaxonomyRetry((n) => n + 1)}>Retry subject choices</button></p>}
    <nav aria-label="Paper navigation" className="browse-paper-navigation">
      <button type="button" disabled={position <= 0} onClick={() => change('paper', available[position - 1].id)} className="min-h-11 text-link disabled:opacity-40">← Previous paper</button>
      <span className="min-w-0 flex-1 truncate text-center" title={selected.title}>{selected.year} · {selected.subject}{selected.paperNumber ? ` · Paper ${selected.paperNumber}` : ''}</span>
      <button type="button" disabled={position < 0 || position >= available.length - 1} onClick={() => change('paper', available[position + 1].id)} className="min-h-11 text-link disabled:opacity-40">Next paper →</button>
      <Link className="inline-flex min-h-11 items-center text-link" to={`?${archive}`}>All papers</Link><a className="inline-flex min-h-11 items-center text-link underline" href={selected.url} target="_blank" rel="noreferrer">PDF ↗</a>
    </nav>
    <details className="rounded-[12px] border border-hairline bg-card px-3 py-1">
      <summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">More filters &amp; answer layout</summary>
      <p className="py-3 text-[13px] text-secondary">Questions follow the order printed in this paper.</p>
      <AnswerLayoutControl />
      <div className="grid gap-3 py-3 sm:grid-cols-2">
        <label className="text-[12px] font-semibold">Year<select aria-label="Paper year" value={year} onChange={(e) => change('paper_year', e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="">All years</option>{years.map((y) => <option key={y} value={y}>{y}</option>)}</select></label>
        <label className="text-[12px] font-semibold">Answer pool<select aria-label="Answer pool" value={pool} disabled={practice || !hasSource} onChange={(e) => change('pool', e.target.value)} className="mt-1 block min-h-11 w-full rounded-[8px] border border-hairline bg-canvas p-2 text-[13px]"><option value="all">All questions</option><option value="scorable">Official answer keys</option><option value="practice">Questions with an answer</option></select></label>
      </div>
    </details>
    <p className="mt-2 text-[11px] text-muted">{selected.schemeBasis === 'inferred' ? 'Scheme inferred from sitting year; check the recruitment notification.' : 'Legacy sitting.'}</p>
    {hasSource ? <SourceQuestions key={`${selected.id}:${practice}`} paper={selected} guideId={guideId} practice={practice} /> : <p className="eg-empty">This paper is available as an original PDF. Its questions are not linked to the question bank here yet. Open the source above to read it.</p>}
  </section>;
}

function SourceQuestions({ paper, guideId, practice }: { paper: ArchivedExamPaper; guideId: string; practice: boolean }) {
  const [params, setParams] = useSearchParams();
  const size = practice ? 1 : 25;
  const rawOffset = Number(params.get('offset'));
  const offset = Number.isFinite(rawOffset) ? Math.min(100000, Math.max(0, Math.floor(rawOffset / size) * size)) : 0;
  const { pool, answerStatus, studyStatus, subjectId, topicId, search } = questionFilters(params, practice);
  const sourceId = sourcePaperId(paper)!;
  const requestKey = JSON.stringify([sourceId, pool, answerStatus, studyStatus, subjectId, topicId, offset, search]);
  const [resolved, setResolved] = useState<{ key: string; page: QuestionPage } | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [results, setResults] = useState<Record<string, AnswerResult>>({});
  const [picks, setPicks] = useState<Record<string, number>>({});
  const [viewed, setViewed] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const checking = useRef(new Set<string>());
  const live = useRef(true);
  useEffect(() => { live.current = true; return () => { live.current = false; }; }, []);
  const page = resolved?.key === requestKey ? resolved.page : null;
  useEffect(() => {
    let current = true;
    setError('');
    const timer = window.setTimeout(() => {
      if (search.trim().length === 1) { setError('Enter at least two characters to search.'); return; }
      void listQuestions({ paper_id: sourceId, pool, order: 'paper', subject_id: subjectId || undefined, topic_id: topicId || undefined, study_status: studyStatus, answer_status: answerStatus, q: search.trim() || undefined, limit: size, offset })
        .then((value) => { if (current) setResolved({ key: requestKey, page: value }); })
        .catch((e: Error) => { if (current) setError(e.message); });
    }, search.trim() ? 250 : 0);
    return () => { current = false; window.clearTimeout(timer); };
  }, [requestKey, sourceId, pool, answerStatus, studyStatus, subjectId, topicId, search, size, offset, retry]);
  function goPage(nextPage: number) {
    const currentPage = Math.floor(offset / size) + 1;
    const nextOffset = nextPage === currentPage + 1 ? nextBrowseOffset(offset, size, studyStatus, page?.items.map((q) => results[q.id]) || []) : (nextPage - 1) * size;
    if (nextOffset === offset) setRetry((n) => n + 1);
    else setParams((previous) => { const next = new URLSearchParams(previous); if (nextOffset) next.set('offset', String(nextOffset)); else next.delete('offset'); return next; });
  }
  async function answer(q: Question, index: number) {
    if (!page || checking.current.has(q.id) || results[q.id] || viewed[q.id] || busy[q.id] || q.type !== 'mcq' || q.held || q.key_disputed || q.answer_source === 'none' || ['duplicate-options', 'unresolved-source'].includes(q.source_defect || '')) return;
    checking.current.add(q.id); setBusy((old) => ({ ...old, [q.id]: true })); setPicks((old) => ({ ...old, [q.id]: index }));
    try {
      const result = await submitAnswer(q.id, index, 'practice', undefined, sourceId);
      if (live.current) setResults((old) => ({ ...old, [q.id]: result }));
    } catch (e) {
      if (live.current) { setError((e as Error).message); setPicks((old) => { const next = { ...old }; delete next[q.id]; return next; }); }
    } finally {
      checking.current.delete(q.id);
      if (live.current) setBusy((old) => ({ ...old, [q.id]: false }));
    }
  }
  const pagination = page && <Pagination page={Math.floor(offset / size) + 1} pages={Math.max(Math.floor(offset / size) + 1, Math.ceil(page.total / size))} label={practice ? 'Practice questions' : 'Source question pages'} onPageChange={goPage} />;
  return <>
    {error && <p role="alert" className="eg-notice">{error} <button type="button" onClick={() => setRetry((n) => n + 1)}>Retry questions</button></p>}
    {!page && !error && <p role="status" className="eg-muted">Loading source questions…</p>}
    {page && <>
      <div className="mt-4 flex justify-between gap-3 text-[13px] text-secondary"><span role="status">{page.total} {practice ? 'practice-ready MCQs' : 'questions'}{search || subjectId || topicId || answerStatus || studyStatus !== 'all' ? ' match these filters' : ' in this paper'}.</span><span>{page.total ? offset + 1 : 0}–{Math.min(offset + page.items.length, page.total)} of {page.total}</span></div>
      {practice && <p className="eg-muted">Untimed practice; this is not a full exam simulation.</p>}
      {pagination}
      {!page.items.length && <p className="eg-empty">{practice ? 'No eligible MCQs match. Use Browse for written or unanswered questions, or change your filters.' : 'No questions match these filters. Reset the filters, read the original PDF or choose another source paper.'}{offset > 0 && <button onClick={() => goPage(1)}>Return to the first page</button>}</p>}
      <div className="eg-bank-list">{page.items.map((q) => <StudyQuestionCard key={q.id} q={q} collectionId={guideId} contextCollectionId={null} paperId={sourceId} result={results[q.id]} pick={picks[q.id]} viewed={viewed[q.id]} busy={busy[q.id]} onPick={(i) => void answer(q, i)} onViewed={(value) => setViewed((old) => ({ ...old, [q.id]: value }))} onBusy={(value) => setBusy((old) => ({ ...old, [q.id]: value }))} onRetry={() => setRetry((n) => n + 1)} onNext={() => goPage(Math.floor(offset / size) + 2)} showPanelNext={false} />)}</div>
      {pagination}
    </>}
  </>;
}

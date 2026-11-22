import { lazy, Suspense, useEffect, useState, useSyncExternalStore } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getDeskSync, subscribeDesk } from '@/lib/desk';
import { archiveFor, branchesForScheme, examGuideViews, guideView, progressKey, readStudyProgress, resolveSelection, sourcePaperId, syllabusFor } from '@/lib/examGuides';
import type { ArchivedExamPaper, ExamGuide, ExamGuideView, StudyProgress, SyllabusPaper, SyllabusUnit } from '@/lib/examGuides';
import ExamOverview from '../ExamOverview';
import { GuideQuestionBrowser } from './GuideQuestionBrowser';
import '../../styles/exam-guide.css';

const STORAGE = 'ism.exam-guides.progress.v1';
const PaperPdf = lazy(() => import('../PaperPdf'));
function loadProgress(key: string | null) {
  try { return key ? readStudyProgress(JSON.parse(localStorage.getItem(key) || '{}')) : {}; } catch { return {}; }
}
function SourceLink({ guide, id, page }: { guide: ExamGuide; id: string; page?: number | null }) {
  const source = guide.sources.find((s) => s.id === id);
  return source ? <a href={`${source.url}${page ? `#page=${page}` : ''}`} target="_blank" rel="noreferrer">Official source ↗</a> : null;
}

function Recall({ cards, isDone, record }: {
  cards: { paper: SyllabusPaper; unit: SyllabusUnit }[];
  isDone: (paper: string, unit: string) => boolean;
  record: (paper: string, unit: string, done: boolean) => void;
}) {
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [visits, setVisits] = useState(0);
  const card = cards[index];
  const move = (next: number) => { setIndex(next); setRevealed(false); };
  if (!card) return <div className="eg-empty">A source-verified topic checklist is not available for this scheme. Use its original past papers for revision.</div>;
  function mark(done: boolean) {
    record(card.paper.id, card.unit.id, done);
    setVisits((n) => n + 1);
    move((index + 1) % cards.length);
  }
  return <>
    <p className="eg-muted">Self-assessed recall from the syllabus. These are revision prompts; no exam score is awarded.</p>
    <article className="eg-recall">
      <div className="eg-line"><span className="eg-kicker">{card.paper.title}</span><span>{index + 1} / {cards.length}</span></div>
      <h2>{card.unit.title}</h2>
      <p>Without looking, outline this topic’s key ideas. Recall the methods, assumptions and one application where relevant.</p>
      {isDone(card.paper.id, card.unit.id) && <span className="eg-pill">Previously revised</span>}
      {!revealed ? <button className="eg-button eg-primary" onClick={() => setRevealed(true)}>Show syllabus checklist</button> : <>
        <div className="eg-reference"><strong>Compare your recall with the syllabus</strong><p>{card.unit.description}</p></div>
        <div className="eg-actions"><button className="eg-button" onClick={() => mark(false)}>Needs revision</button><button className="eg-button eg-primary" onClick={() => mark(true)}>Mark revised & next</button></div>
      </>}
      <div className="eg-line eg-recall-nav"><button className="eg-button" disabled={index === 0} onClick={() => move(index - 1)}>← Previous</button><span>{visits} reviewed this session</span><button className="eg-button" disabled={index === cards.length - 1} onClick={() => move(index + 1)}>Next →</button></div>
    </article>
  </>;
}

export function ExamGuidePage({ guide }: { guide: ExamGuide }) {
  const identity = useSyncExternalStore(subscribeDesk, getDeskSync);
  const storageKey = identity.userId ? `${STORAGE}:${identity.userId}` : null;
  return <GuideContent key={storageKey || 'pending'} guide={guide} storageKey={storageKey} />;
}

function GuideContent({ guide, storageKey }: { guide: ExamGuide; storageKey: string | null }) {
  const [params, setParams] = useSearchParams();
  const { schemeId, branchId } = resolveSelection(guide, params.get('scheme'), params.get('branch'));
  const view = guideView(params.get('view'), params.get('tab'));
  const recall = params.get('practice_mode') === 'recall' || (!params.get('view') && params.get('tab') === 'Recall');
  const scheme = guide.schemes.find((s) => s.id === schemeId)!;
  const branch = guide.branches.find((b) => b.id === branchId)!;
  const plans = syllabusFor(guide, schemeId, branchId);
  const papers = archiveFor(guide, schemeId, branchId);
  const cards = plans.flatMap((paper) => paper.units.map((unit) => ({ paper, unit })));
  const [progress, setProgress] = useState<StudyProgress>(() => loadProgress(storageKey));
  const [storageError, setStorageError] = useState('');
  const [query, setQuery] = useState('');
  const [year, setYear] = useState('all');
  const [kind, setKind] = useState('all');
  const [openId, setOpenId] = useState<string | null>(null);
  useEffect(() => {
    setYear('all'); setKind('all'); setQuery(''); setOpenId(null);
  }, [schemeId, branchId]);
  function viewUrl(nextView: ExamGuideView, paper?: string, mode?: string) {
    const next = new URLSearchParams(params);
    next.set('scheme', schemeId); next.set('branch', branchId); next.set('view', nextView);
    next.delete('tab'); next.delete('offset'); next.delete('q');
    if (paper) {
      for (const key of ['paper_type', 'paper_year', 'subject_id', 'topic_id', 'subtopic_id', 'status', 'answer_status', 'pool', 'order', 'seed']) next.delete(key);
      next.set('paper', paper);
    }
    if (mode) next.set('practice_mode', mode); else next.delete('practice_mode');
    return `?${next}`;
  }
  function navigate(changes: { scheme?: string; branch?: string }) {
    const selection = resolveSelection(guide, changes.scheme || schemeId, changes.branch || branchId);
    setParams({ scheme: selection.schemeId, branch: selection.branchId, view, ...(recall ? { practice_mode: 'recall' } : {}) });
  }
  const key = (paper: string, unit: string) => progressKey(guide.id, schemeId, branchId, paper, unit);
  const isDone = (paper: string, unit: string) => progress[key(paper, unit)] === true;
  function record(paper: string, unit: string, done: boolean) {
    const next = { ...progress, [key(paper, unit)]: done };
    setProgress(next);
    if (!storageKey) { setStorageError('Account context is unavailable. Your checklist is kept for this session.'); return; }
    try { localStorage.setItem(storageKey, JSON.stringify(next)); setStorageError(''); }
    catch { setStorageError('Your progress is available this session, but this browser could not save it.'); }
  }
  const completed = cards.filter((c) => isDone(c.paper.id, c.unit.id)).length;
  const filtered = papers.filter((p) => (year === 'all' || String(p.year) === year) &&
    (kind === 'all' || (kind === 'common' ? !p.branchId : !!p.branchId)) &&
    `${p.title} ${p.sitting} ${p.subject}`.toLowerCase().includes(query.toLowerCase()));
  const selectedPaper = filtered.find((p) => p.id === openId);
  const written = scheme.status === 'verified' && plans.every((p) => p.marks !== null) ? plans.reduce((n, p) => n + p.marks!, 0) : null;
  function paperCard(p: ArchivedExamPaper) {
    return <article className="overview-paper-card" key={p.id}>
      <span className="eg-year">{p.year} · {p.branchId ? 'Branch paper' : 'Common paper'}</span>
      <h3 className="mt-2 font-display text-md leading-snug">{p.subject}{p.paperNumber ? ` · Paper ${p.paperNumber}` : ''}</h3>
      <p className="overview-paper-exam" title={p.sitting}>{p.sitting}</p>
      <p className="eg-muted">{p.schemeBasis === 'source' ? 'Legacy sitting verified' : 'Scheme inferred from year'}</p>
      <div className="overview-paper-actions">
        {sourcePaperId(p) && <Link className="overview-paper-browse" to={viewUrl('browse', p.id)}>Browse questions →</Link>}
        <button className="eg-button" onClick={() => { setYear('all'); setKind('all'); setQuery(''); setOpenId(p.id); setParams(viewUrl('papers').slice(1)); window.setTimeout(() => document.querySelector('.eg-reader')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 0); }}>Read paper</button>
        <a className="overview-paper-link" href={p.url} target="_blank" rel="noreferrer">PDF ↗</a>
      </div>
    </article>;
  }
  return <div className="eg-page"><ExamOverview title={guide.title} collections={[]} presentationId={guide.id} description={guide.description} headerAction={<Link className="eg-back" to="/exams">← Exams</Link>}>
    <div className="eg-layout">
      <aside className="eg-sidebar">
        <label className="eg-label" htmlFor="exam-scheme">Exam scheme</label>
        <select id="exam-scheme" value={schemeId} onChange={(e) => navigate({ scheme: e.target.value })}>{guide.schemes.map((s) => <option key={s.id} value={s.id}>{s.title}</option>)}</select>
        <div className="eg-kicker eg-branch-label">Choose your branch</div>
        <nav className="eg-branches" aria-label="Engineering branch">{branchesForScheme(guide, schemeId).map((b) => <button key={b.id} aria-pressed={branchId === b.id} className={branchId === b.id ? 'is-active' : ''} onClick={() => navigate({ branch: b.id })}><span>{b.short}</span><span aria-hidden="true">{branchId === b.id ? '●' : '→'}</span></button>)}</nav>
        <div className="eg-side-note">{scheme.status === 'verified' ? 'Syllabus verified against the official regulations.' : 'Legacy archive · full syllabus unverified.'}<br />Progress stays separate for each branch and scheme.</div>
      </aside>
      <main className="eg-main">
        <div className="eg-heading"><div><span className="eg-kicker">{scheme.title}</span><h2>{branch.title}</h2></div><span className="eg-pill">{papers.length} past papers</span></div>
        <nav className="module-view-nav" aria-label={`${guide.title} module views`}>{examGuideViews.map(([key, title]) => <Link key={key} aria-current={view === key ? 'page' : undefined} to={viewUrl(key)}>{title}</Link>)}</nav>
        {storageError && <p role="status" className="eg-notice">{storageError}</p>}
        {view === 'overview' && <>
          <dl className="exam-overview-stats">{[[papers.length, 'source papers'], [papers.filter((p) => p.branchId).length, 'branch papers'], [cards.length, 'syllabus topics'], [completed, 'topics revised']].map(([value, label]) => <div key={label}><dd>{value}</dd><dt>{label}</dt></div>)}</dl>
          <details className="eg-card eg-format"><summary>{scheme.title} · {written === null ? 'Full marking scheme unverified' : `${written} written marks · ${scheme.interviewMarks ?? '—'} interview marks`}</summary><p>{scheme.description}</p><div className="eg-actions">{scheme.sourceIds.map((id) => <SourceLink key={id} guide={guide} id={id} />)}</div><div className="eg-paper-plans">{plans.map((p) => <div key={p.id}><h3>{p.title}</h3><p>{p.marks ?? '—'} marks · {p.durationMinutes ? `${p.durationMinutes / 60} hours` : 'See original'}<br />{p.format}</p></div>)}</div></details>
          <div className="exam-overview-note">Browse a source paper, study its syllabus under Subjects, or practise available MCQs. Syllabus recall is under Practice. Common papers are included for your branch.</div>
          <div className="exam-overview-toolbar"><h2 className="font-display text-lg">Past papers</h2><Link to={viewUrl('papers')}>View all {papers.length} papers →</Link></div>
          <div className="exam-overview-papers" aria-label="Past paper summaries">{papers.slice(0, 6).map(paperCard)}</div>
        </>}
        {view === 'browse' && <GuideQuestionBrowser key={`${schemeId}:${branchId}`} papers={papers} guideId={guide.id} />}
        {view === 'topics' && <>
          <p className="eg-muted">{cards.length ? 'Expand a topic to read its scope. Your checklist is self-assessed and saved on this device.' : 'No full legacy syllabus has been verified. Only the source-checked common-paper formats are shown.'}</p>
          {plans.map((p) => <section className="eg-card" key={p.id}><div className="eg-line"><h3>{p.title}</h3><SourceLink guide={guide} id={p.sourceId} page={p.sourcePage} /></div><p className="eg-muted">{p.marks} marks · {p.durationMinutes! / 60} hours · {p.format}</p>{p.units.map((u) => <div className="eg-unit" key={u.id}><input id={`${p.id}-${u.id}`} type="checkbox" aria-label={`Mark ${u.title} revised`} checked={isDone(p.id, u.id)} onChange={(e) => record(p.id, u.id, e.target.checked)} /><details><summary>{u.title}</summary><p>{u.description}</p></details></div>)}</section>)}
        </>}
        {view === 'papers' && <>
          <p className="eg-muted">Common papers are included for your branch. Scheme grouping for papers from 2014 onward is inferred from the sitting year; confirm the booklet and recruitment notification.</p>
          <div className="eg-filters"><label>Year<select value={year} onChange={(e) => { setYear(e.target.value); setOpenId(null); }}><option value="all">All years</option>{[...new Set(papers.map((p) => p.year))].map((y) => <option key={y} value={y}>{y}</option>)}</select></label><label>Paper type<select value={kind} onChange={(e) => { setKind(e.target.value); setOpenId(null); }}><option value="all">All papers</option><option value="technical">Branch papers</option><option value="common">Common papers</option></select></label><label className="eg-search">Search<input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Department, subject or paper…" /></label></div>
          <p className="eg-muted" role="status">{filtered.length} papers match</p>
          {selectedPaper && <section className="eg-reader"><div className="eg-line"><h3>{selectedPaper.title}</h3><button className="eg-button" onClick={() => setOpenId(null)}>Close reader</button></div><p><a href={selectedPaper.url} target="_blank" rel="noreferrer">Open the official original PDF ↗</a></p>{selectedPaper.readerUrl ? <Suspense fallback={<p role="status">Loading paper reader…</p>}><PaperPdf key={selectedPaper.id} url={selectedPaper.readerUrl} questionPage={null} questionId={selectedPaper.id} /></Suspense> : <p>This original is hosted by MPSC. Open the official PDF above to read it.</p>}</section>}
          <div className="exam-overview-papers" aria-label="Source papers">{filtered.map(paperCard)}</div>
          {!filtered.length && <div className="eg-empty">No papers match. Try another year or clear the search.</div>}
        </>}
        {view === 'practice' && <>
          <div className="eg-practice-modes" aria-label="Practice mode"><Link className="eg-button" aria-current={!recall ? 'page' : undefined} to={viewUrl('practice')}>Past-paper MCQs</Link><Link className="eg-button" aria-current={recall ? 'page' : undefined} to={viewUrl('practice', undefined, 'recall')}>Syllabus recall</Link></div>
          {recall ? <Recall key={`${schemeId}:${branchId}`} cards={cards} isDone={isDone} record={record} /> : <GuideQuestionBrowser key={`${schemeId}:${branchId}`} papers={papers} guideId={guide.id} practice />}
        </>}
        {view === 'progress' && <>
          <h2 className="font-display text-xl">Your revision progress</h2>
          <p className="eg-muted">Self-assessed syllabus revision, saved on this device for this account, branch and scheme.</p>
          <article className="eg-card"><h3>{completed} / {cards.length} topics revised</h3>{cards.length ? <progress max={cards.length} value={completed} aria-label="Revision progress" /> : <p>No verified topic checklist is available for this legacy scheme.</p>}</article>
          {plans.filter((p) => p.units.length).map((p) => { const done = p.units.filter((u) => isDone(p.id, u.id)).length; return <article className="eg-card" key={p.id}><div className="eg-line"><h3>{p.title}</h3><span className="eg-muted">{done} / {p.units.length} revised</span></div><progress max={p.units.length} value={done} aria-label={`${p.title} revision progress`} /></article>; })}
          <div className="eg-actions"><Link className="overview-paper-browse" to={viewUrl('topics')}>Continue in Subjects →</Link><Link to={viewUrl('practice', undefined, 'recall')}>Revise with recall</Link></div>
          <p className="eg-muted">Question practice uses your normal answer history. This checklist measures syllabus revision, rather than an exam score.</p>
        </>}
        <footer className="eg-footer">Source check: {guide.sources.find((s) => s.id === guide.directorySourceId)?.checkedOn} · <SourceLink guide={guide} id={guide.directorySourceId} /><br />Follow the notification for your recruitment. Progress is saved separately for this branch and scheme on this device.</footer>
      </main>
    </div>
  </ExamOverview></div>;
}

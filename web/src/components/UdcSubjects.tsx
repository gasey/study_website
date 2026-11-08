import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getExamStudyTopics, type ExamStudyTopics } from '../lib/api'

const primarySubjects = ['gk-gs', 'english', 'mathematics', 'computer-science', 'reasoning-and-aptitude']

/** Shortcuts are drawn from UDC's approved topic map and always retain its scope. */
export default function UdcSubjects() {
  const [data, setData] = useState<ExamStudyTopics | null>(null)
  const [error, setError] = useState(false)
  useEffect(() => {
    let live = true
    getExamStudyTopics('udc').then(value => { if (live) setData(value) }).catch(() => { if (live) setError(true) })
    return () => { live = false }
  }, [])
  const subjects = data?.subjects.filter(subject => primarySubjects.includes(subject.id)) ?? []
  return <section className="mt-6" aria-labelledby="udc-subjects-heading">
    <div className="flex flex-wrap items-end justify-between gap-2">
      <div><h2 id="udc-subjects-heading" className="font-display text-[26px]">Study a UDC subject</h2><p className="mt-1 text-[13px] text-secondary">Practise one subject at a time using UDC past-paper questions.</p></div>
      <Link to="/exams/udc?view=topics#exam-study-heading" className="inline-flex min-h-11 items-center text-[13px] font-semibold text-link">All subjects &amp; topics →</Link>
    </div>
    {!data && !error && <p role="status" className="mt-3 text-[13px] text-muted">Loading UDC subjects…</p>}
    {error && <p className="mt-3 text-[13px] text-secondary">Open all subjects to load the UDC topic map.</p>}
    <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{subjects.map(subject => <Link key={subject.id} to={`/exams/udc?view=practice&subject_id=${encodeURIComponent(subject.id)}#exam-question-browser`} className="flex min-h-11 items-center justify-between gap-3 rounded-xl border border-hairline bg-card p-4 hover:border-ink">
      <span><strong className="text-[15px]">{subject.title}</strong><span className="mt-1 block text-[12px] text-secondary">{subject.questions.toLocaleString('en-IN')} questions in UDC papers</span></span><span aria-hidden="true">→</span>
    </Link>)}</div>
    <details className="mt-4 rounded-xl border border-hairline bg-card px-4">
      <summary className="min-h-11 cursor-pointer py-3 text-[13px] font-semibold">Syllabus, written practice &amp; coverage</summary>
      <div className="pb-4 text-[13px] leading-relaxed text-secondary">
        <h3 className="font-semibold text-ink">2026 combined Assistant / UDC syllabus</h3>
        <p className="mt-2">Two papers, each 3 hours and 200 marks. Paper I has 50 General Knowledge MCQs (100 marks), 25 General English MCQs (50 marks), and written English: précis (10), essay (20) and comprehension (20).</p>
        <p className="mt-2">Paper II has 35 Basic Computer Knowledge MCQs (70 marks), 30 Simple Arithmetic MCQs (60 marks), and 35 General Intelligence &amp; Reasoning MCQs (70 marks).</p>
        <p className="mt-2">MCQs carry 2 marks each. A wrong answer loses one third of the question’s marks (⅔ mark); a blank answer has no penalty. The official document includes compensatory-time provisions. Checked against the syllabus linked from the 2026 recruitment notice on 2 November 2026.</p>
        <p className="mt-2">These rules describe the 2026 combined examination. Historical papers and the app’s timed practice retain their own stated rules.</p>
        <p className="mt-2">These counts describe indexed past-paper questions, including historical papers and booklet copies. They do not confirm complete syllabus coverage. Other historical subjects remain under All subjects &amp; topics.</p>
        <p className="mt-2">Short sets cover MCQs. Make separate time for written English practice, including précis, essays and comprehension. Timed MCQ practice does not assess written work.</p>
        <div className="mt-2 flex flex-wrap gap-x-5">
          <a href="https://mpsc.mizoram.gov.in/post/advertisement-no13-of-2026-27-assistant-udccombined" target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center font-semibold text-link underline">MPSC 2026 recruitment notice ↗</a>
          <a href="https://mpsc.mizoram.gov.in/uploads/attachments/2026/05/f74b4d6652a90a741cd5907be6fad00d/syllabus-for-assistant-udc-combined.pdf" target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center font-semibold text-link underline">Official syllabus &amp; penalty rules ↗</a>
        </div>
      </div>
    </details>
  </section>
}

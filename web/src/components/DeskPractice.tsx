import { useEffect, useState } from "react";
import {
  getQuestion,
  listQuestions,
  type QuestionPage,
  type QuestionDetail,
} from "../lib/api";
import QuestionCard from "./QuestionCard";
import { AnswerLayoutControl } from "./AnswerLayout";
export function DeskQuestion({
  qid,
  onAnswered,
}: {
  qid: string;
  onAnswered?: () => void;
}) {
  const [q, setQ] = useState<QuestionDetail | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    getQuestion(qid)
      .then((q) => {
        if (active) setQ(q);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [qid]);
  return error ? (
    <p role="alert" className="mt-3 text-[13px] text-mypick">
      {error}
    </p>
  ) : q ? (
    <QuestionCard q={q} onAnswered={onAnswered} />
  ) : (
    <p className="mt-3 text-[13px] text-muted">Loading the bank question…</p>
  );
}
export default function DeskPractice({
  subject,
  questions,
  onAnswered,
}: {
  subject: string;
  questions?: string[];
  onAnswered: () => void;
}) {
  const [page, setPage] = useState<QuestionPage | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const shared = questions !== undefined;
  const questionKey = questions?.join(",") || "";
  useEffect(() => setOffset(0), [subject, questionKey]);
  useEffect(() => {
    let active = true;
    setPage(null);
    setError("");
    (shared
      ? Promise.all(
          (questions || [])
            .slice(offset, offset + 5)
            .map((id) => getQuestion(id)),
        ).then((items) => ({
          items,
          total: questions?.length || 0,
          limit: 5,
          offset,
        }))
      : listQuestions({
          pool: "scorable",
          limit: 5,
          offset,
          ...(subject ? { subject_id: subject } : {}),
        })
    )
      .then((p) => {
        if (active) setPage(p);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [subject, offset, shared, questionKey]);
  return (
    <>
      <div className="rounded-[8px] border border-[#2D5BD0] bg-[#DAE3F1] p-5">
        <div className="desk-v3-label !text-[#2D5BD0]">
          {shared
            ? "Shared desk set · practice"
            : "Your desk set · practice questions"}
        </div>
        <h3 className="mt-2 font-display text-[24px]">
          Five questions, one focused step.
        </h3>
        <p className="mt-2 text-[13px] text-secondary">
          {shared
            ? "Work through the questions your members shared. Your answers and progress stay in your own account."
            : "Questions come from the shared bank engine. Answers are recorded in your account; use the focus subject in your plan to narrow this set."}
        </p>
      </div>
      <AnswerLayoutControl />
      {error && (
        <p role="alert" className="mt-3 text-[13px] text-mypick">
          {error}
        </p>
      )}
      {!page && !error && (
        <p className="desk-v3-empty">Loading your desk set…</p>
      )}
      <div className="mt-4">
        {page?.items.map((q) => (
          <QuestionCard key={q.id} q={q} onAnswered={onAnswered} />
        ))}
        {page && !page.items.length && (
          <p className="desk-v3-empty">
            {shared
              ? "No questions have been shared for this desk set yet. Use Share from the bank."
              : "No questions with usable answers are available for this subject yet. Choose another subject."}
          </p>
        )}
      </div>
      {page && page.total > 5 && (
        <nav
          aria-label="Desk practice pages"
          className="mt-3 flex justify-between"
        >
          <button
            disabled={!offset}
            className="desk-v3-button"
            onClick={() => setOffset(Math.max(0, offset - 5))}
          >
            Previous set
          </button>
          <span className="self-center text-[12px] text-muted">
            {offset + 1}–{Math.min(offset + 5, page.total)} of{" "}
            {page.total.toLocaleString("en-IN")}
          </span>
          <button
            disabled={offset + 5 >= page.total}
            className="desk-v3-button"
            onClick={() => setOffset(offset + 5)}
          >
            Next set
          </button>
        </nav>
      )}
    </>
  );
}

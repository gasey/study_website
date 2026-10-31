import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getAccountSession } from "../lib/api";
import { reviewSession } from "../lib/review";
import { scopeLink } from "../lib/examScope";
import {
  SourceQuestionContext,
  SourceQuestionText,
} from "../components/SourceQuestionText";
import { AnswerOptions, AnswerLayoutControl } from "../components/AnswerLayout";
import {
  vocabularyRequest,
  type VocabularyCard,
  type VocabularyOverview,
  type VocabularyResult,
} from "../lib/vocabulary";
const stageLabel = (n: number) =>
  n >= 5
    ? "Retaining"
    : n >= 3
      ? "Strengthening"
      : n >= 1
        ? "Learning"
        : "Getting started";
const dateLabel = (s: string) =>
  new Date(s).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  }) + " IST";
export default function Vocabulary() {
  const [params, setParams] = useSearchParams();
  const [restored, setRestored] = useState(false);
  const [user, setUser] = useState(""),
    [auth, setAuth] = useState<"loading" | "guest" | "ready">("loading"),
    [card, setCard] = useState<VocabularyCard | null>(null),
    [overview, setOverview] = useState<VocabularyOverview | null>(null);
  const [selected, setSelected] = useState<number | null>(null),
    [result, setResult] = useState<VocabularyResult | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [completed, setCompleted] = useState(0),
    [finished, setFinished] = useState(false);
  const epoch = useRef(0),
    generation = useRef(0),
    answering = useRef(false);
  useEffect(() => {
    let active = true;
    async function sync() {
      const run = ++epoch.current;
      ++generation.current;
      setUser("");
      setAuth("loading");
      setLoading(false);
      setRestored(false);
      setCard(null);
      setResult(null);
      setSelected(null);
      setOverview(null);
      setError("");
      setCompleted(0);
      setFinished(false);
      setBusy(false);
      answering.current = false;
      try {
        const session = await getAccountSession();
        if (!active || run !== epoch.current) return;
        if (!session.authenticated) {
          setAuth("guest");
          return;
        }
        const who = await reviewSession(true);
        if (!active || run !== epoch.current) return;
        setUser(who.user_id);
        setAuth("ready");
      } catch (e) {
        if (active && run === epoch.current) {
          setError((e as Error).message);
          setAuth("guest");
        }
      }
    }
    void sync();
    window.addEventListener("ism-auth-change", sync);
    return () => {
      active = false;
      ++epoch.current;
      ++generation.current;
      window.removeEventListener("ism-auth-change", sync);
    };
  }, []);
  async function load(resume = true) {
    if (!user) return;
    const run = ++generation.current,
      owner = epoch.current;
    setLoading(true);
    setError("");
    setCard(null);
    setResult(null);
    setSelected(null);
    try {
      const next = await vocabularyRequest<{
        card: VocabularyCard | null;
        result?: VocabularyResult;
        restored?: boolean;
      }>("/card", user, { resume_id: resume ? params.get("review") : null, question_id:params.get("question_id") });
      const summary = await vocabularyRequest<VocabularyOverview>(
        "/overview",
        user,
      );
      if (run !== generation.current || owner !== epoch.current) return;
      setOverview(summary);
      setCard(next.card);
      setResult(next.result || null);
      setRestored(!!next.restored);
      setParams(
        (p) => {
          if (next.card) p.set("review", next.card.id);
          else p.delete("review");
          if(!next.card||next.card.question_id===p.get("question_id"))p.delete("question_id");
          return p;
        },
        { replace: true, preventScrollReset: true },
      );
    } catch (e) {
      if (run === generation.current && owner === epoch.current)
        setError((e as Error).message);
    } finally {
      if (run === generation.current && owner === epoch.current)
        setLoading(false);
    }
  }
  useEffect(() => {
    void load();
    return () => {
      ++generation.current;
    };
  }, [user]);
  async function answer(action: "answer" | "reveal" | "defer") {
    if (
      !card ||
      answering.current ||
      (action === "answer" && selected === null)
    )
      return;
    answering.current = true;
    const owner = epoch.current,
      cid = card.id;
    setBusy(true);
    setError("");
    try {
      const saved = await vocabularyRequest<VocabularyResult>(
        "/cards/" + cid + "/answer",
        user,
        { action, chosen_index: action === "answer" ? selected : null },
      );
      if (owner !== epoch.current) return;
      setResult(saved);
      setRestored(false);
      setCompleted((n) => n + 1);
      void vocabularyRequest<VocabularyOverview>("/overview", user)
        .then((x) => {
          if (owner === epoch.current) setOverview(x);
        })
        .catch(() => {});
      window.dispatchEvent(new Event("ism-progress-change"));
    } catch (e) {
      if (owner === epoch.current) setError((e as Error).message);
    } finally {
      if (owner === epoch.current) {
        setBusy(false);
        answering.current = false;
      }
    }
  }
  const revisionReturn=params.get('return_to');
  return (
    <div className="mx-auto max-w-[900px] px-4 pb-24 pt-9 sm:px-6">
      {revisionReturn&&/^rev_[a-f0-9]+$/.test(revisionReturn)&&<Link to={'/revision?session='+revisionReturn} className="mb-3 inline-flex min-h-11 items-center rounded-pill border border-hairline px-4 text-[13px] text-link">← Return to daily revision</Link>}
      <Link to="/english" className="text-[13px] text-link">
        ← English practice
      </Link>
      <div className="mt-5 font-mono text-[11px] uppercase tracking-[.1em] text-[#72509A]">
        Vocabulary · automatic spaced review
      </div>
      <h1 className="mt-2 font-display text-[clamp(34px,5vw,48px)] leading-tight tracking-[-.02em]">
        Answer. We’ll plan the next review.
      </h1>
      <p className="mt-3 max-w-[700px] text-[15px] leading-relaxed text-secondary">
        Practise vocabulary from verified exam questions. Your checked answers
        set the review schedule automatically—no confidence ratings needed.
      </p>
      {auth === "loading" && (
        <p role="status" className="mt-7">
          Loading your account…
        </p>
      )}
      {auth === "guest" && (
        <section className="mt-6 rounded-[14px] border border-hairline bg-card p-6">
          <h2 className="font-display text-[26px]">
            A review plan that follows you
          </h2>
          <p className="mt-2 text-[14px] text-secondary">
            Sign in free to save your answers and review schedule across
            devices.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link
              to="/login"
              className="min-h-[44px] rounded-pill bg-ink px-5 py-3 text-[13px] font-semibold text-paper"
            >
              Log in
            </Link>
            <Link
              to="/join"
              className="rounded-pill border border-hairline px-5 py-3 text-[13px]"
            >
              Create free account
            </Link>
            <Link
              to="/english?view=practice"
              className="px-3 py-3 text-[13px] text-link underline"
            >
              Browse English practice
            </Link>
          </div>
        </section>
      )}
      {overview && (
        <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            [overview.due, "due now"],
            [overview.started, `of ${overview.eligible} started`],
            [
              overview.graded
                ? Math.round((100 * overview.correct) / overview.graded) + "%"
                : "—",
              "checked answer accuracy",
            ],
            [overview.retaining, "in longer review intervals"],
          ].map(([value, label]) => (
            <div key={label} className="rounded-[10px] bg-[#F1EBF7] p-3">
              <div className="font-display text-[25px]">{value}</div>
              <div className="text-[12px] text-secondary">{label}</div>
            </div>
          ))}
        </div>
      )}
      {error && (
        <p
          role="alert"
          className="mt-5 rounded-[10px] bg-mypick-soft p-4 text-[13px] text-mypick"
        >
          {error}
          {user && (
            <button
              onClick={() => void load()}
              disabled={busy}
              className="ml-3 underline"
            >
              Reload review
            </button>
          )}
        </p>
      )}
      {loading && (
        <p
          role="status"
          className="mt-6 rounded-[14px] border border-hairline bg-card p-7"
        >
          Preparing your next review…
        </p>
      )}
      {card && !loading && !finished && (
        <section className="mt-5 rounded-[16px] border border-hairline bg-card p-5 shadow-sm sm:p-8">
          <div className="mb-5 flex flex-wrap justify-between gap-2 font-mono text-[11px] text-muted">
            <span>
              {card.seen ? stageLabel(card.stage) : "New question"} ·{" "}
              {card.question.answer_source === "official"
                ? "Official key"
                : "Transcribed source key"}
            </span>
            <span>
              {restored
                ? "Saved feedback restored"
                : `${completed} completed · 10-card session`}
            </span>
          </div>
          <SourceQuestionContext
            direction={card.question.direction}
            passage={card.question.passage}
          />
          <h2 className="text-[18px] leading-relaxed">
            <SourceQuestionText
              text={card.question.question_markup || card.question.question}
            />
          </h2>
          {card.question.figure_image_url && (
            <img
              src={card.question.figure_image_url}
              alt="Figure from the source question"
              className="my-4 max-h-[360px] max-w-full object-contain"
            />
          )}
          <AnswerLayoutControl />
          <AnswerOptions>
            {card.question.options.map((option, i) => (
              <button
                key={i}
                aria-pressed={selected === i}
                disabled={busy || !!result}
                onClick={() => setSelected(i)}
                className={
                  "flex min-h-[48px] items-start gap-3 rounded-[9px] border p-4 text-left text-[14px] " +
                  (result?.answer_text === option
                    ? "border-correct bg-correct-soft"
                    : selected === i
                      ? "border-[#7653A0] bg-[#F1EBF7]"
                      : "border-hairline bg-paper")
                }
              >
                <span className="font-mono text-[12px] text-muted">
                  {String.fromCharCode(65 + i)}
                </span>
                <SourceQuestionText
                  text={card.question.options_markup?.[i] || option}
                />
              </button>
            ))}
          </AnswerOptions>
          {!result ? (
            <div className="mt-5 flex flex-wrap gap-2">
              <button
                disabled={busy || selected === null}
                onClick={() => void answer("answer")}
                className="min-h-[44px] rounded-pill bg-ink px-5 text-[14px] font-semibold text-paper disabled:opacity-40"
              >
                {busy ? "Saving…" : "Check answer"}
              </button>
              <button
                disabled={busy}
                onClick={() => void answer("reveal")}
                className="min-h-[44px] rounded-pill border border-hairline px-4 text-[13px]"
              >
                I don’t know · show answer
              </button>
              <button
                disabled={busy}
                onClick={() => void answer("defer")}
                className="min-h-[44px] px-3 text-[13px] text-muted underline"
              >
                Skip for now
              </button>
            </div>
          ) : (
            <div className="mt-5">
              <div
                role="status"
                className={
                  "rounded-[10px] p-4 text-[14px] " +
                  (result.correct ? "bg-correct-soft" : "bg-[#F7EAD0]")
                }
              >
                <strong>
                  {result.correct
                    ? "Correct."
                    : result.outcome === "defer"
                      ? "Deferred, without a wrong answer."
                      : result.outcome === "reveal"
                        ? "A chance to learn this one."
                        : "Not quite."}
                </strong>
                {result.answer_text && (
                  <p className="mt-1">
                    Answer: <SourceQuestionText text={result.answer_text} />
                  </p>
                )}
                {result.explanation && (
                  <p className="mt-2">
                    <SourceQuestionText text={result.explanation} />
                  </p>
                )}
                <p className="mt-3 text-[13px]">
                  Next review:{" "}
                  <time dateTime={result.next_due}>
                    {dateLabel(result.next_due)}
                  </time>{" "}
                  · saved to your account.
                </p>
              </div>
              <button
                onClick={() => {
                  if (completed >= 10) setFinished(true);
                  else void load(false);
                }}
                className="mt-4 min-h-[44px] rounded-pill bg-ink px-5 text-[14px] font-semibold text-paper"
              >
                {completed >= 10 ? "Finish session" : "Next review →"}
              </button>
            </div>
          )}
          <div className="mt-6 flex flex-wrap gap-4 border-t border-hairline pt-4 text-[12px]">
            <Link
              to={scopeLink("/bank/" + card.question_id)}
              className="text-link underline"
            >
              Question, source & discussion
            </Link>
            {card.question.source_pdf_url && (
              <a
                href={
                  card.question.source_pdf_url +
                  (card.question.page ? "#page=" + card.question.page : "")
                }
                target="_blank"
                rel="noreferrer"
                className="text-link underline"
              >
                Original source PDF ↗
              </a>
            )}
            <Link
              to={
                "/contribute/new?question=" +
                encodeURIComponent(card.question_id)
              }
              className="text-link underline"
            >
              Flag a source or answer issue
            </Link>
          </div>
          <p className="mt-3 text-[11px] text-muted">
            Original option order is preserved, including letter references.
          </p>
        </section>
      )}
      {auth === "ready" && !loading && !error && (!card || finished) && (
        <section className="mt-6 rounded-[14px] border border-hairline bg-card p-7">
          <h2 className="font-display text-[27px]">
            {finished ? "Session complete" : "You’re clear for now"}
          </h2>
          <p className="mt-2 text-[14px] text-secondary">
            {finished
              ? `${completed} reviews saved. Your next dates are already planned.`
              : overview?.eligible
                ? "No more reviews are due in this focus, or your daily target of 10 new cards is complete."
                : "No verified vocabulary questions are currently eligible in this focus."}
          </p>
          {overview?.next_due && (
            <p className="mt-3 text-[13px]">
              Next scheduled review: {dateLabel(overview.next_due)}
            </p>
          )}
          <button
            onClick={() => {
              setCompleted(0);
              setFinished(false);
              void load(false);
            }}
            className="mt-4 min-h-[44px] rounded-pill border border-hairline px-4 text-[13px]"
          >
            {finished ? "Continue due reviews" : "Refresh review plan"}
          </button>
        </section>
      )}
      <p className="mt-6 text-[12px] leading-relaxed text-muted">
        This tracks recognition of exam questions, not proof that a word is
        mastered. Correct answers extend intervals when they are spaced apart;
        misses get a short review. Skipping is not marked wrong, and speed does
        not affect your schedule. Earlier browser-only confidence ratings are
        not imported as checked answers.
      </p>
    </div>
  );
}

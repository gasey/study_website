import {scopeLink} from '../lib/examScope'
import AnswerComparison from './AnswerComparison'
import {UserAvatar} from './AvatarArt'
import type {AvatarLook} from '../lib/avatar'
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { deviceId } from "../lib/device";
import { reviewRequest } from "../lib/review";

export interface DiscussionContext {
  paper_id?: string | null;
  collection_id?: string | null;
}
interface Source {
  url: string;
  note: string;
}
export interface DiscussionPost {
  id: number;
  canonical_id: string;
  parent_id: number | null;
  kind: "doubt" | "explanation" | "reply";
  body: string;
  avatar?:AvatarLook|null;
  author: string;
  author_id: string;
  is_author: boolean;
  needs_approval: boolean;
  pinned: boolean;
  accepted: boolean;
  voted: boolean;
  helpful: number;
  created_at: string;
  source_links: Source[];
  source_context: {
    paper_id?: string;
    appearance_id?: string;
    collection_id?: string;
    exam_name?: string;
    year?: number;
    qnum?: string;
  };
}
interface Page {
  items: DiscussionPost[];
  has_more: boolean;
  focused?: DiscussionPost | null;
}
interface Thread extends Page {
  allowed: boolean;
  can_disclose: boolean;
  registered: boolean;
  locked: boolean;
  lock_reason: string | null;
}
const BTN =
  "inline-flex min-h-11 items-center rounded-pill border border-hairline px-3 py-2 text-[12px] font-semibold disabled:opacity-50";
const INPUT =
  "w-full rounded-[6px] border border-[#DCD3C2] bg-[#FFFDF8] p-3 text-[14px]";
async function read<T>(path: string): Promise<T> {
  const r = await fetch("/api/community" + path, {
    credentials: "include",
    headers: { "x-device-id": deviceId() },
  });
  if (!r.ok) {
    const e = await r.json();
    throw new Error(e.detail || "Discussion could not load");
  }
  return r.json();
}
export function questionLink(
  qid: string,
  context: DiscussionContext = {},
  post?: number,
) {
  const p = new URLSearchParams();
  if (context.paper_id) p.set("paper", context.paper_id);
  if (context.collection_id && context.paper_id)
    p.set("exam", context.collection_id);
  if (post) p.set("post", String(post));
  return (
    "/bank/" + encodeURIComponent(qid) + (p.size ? "?" + p : "") + "#discussion"
  );
}

export function QuestionActions({
  qid,
  context = {},
  answeredSignal,
  initialOpen = false,
  questionType = "mcq",
}: {
  qid: string;
  context?: DiscussionContext;
  answeredSignal?: unknown;
  initialOpen?: boolean;
  questionType?: "mcq" | "descriptive";
}) {
  const [open, setOpen] = useState(initialOpen);
  const [copied, setCopied] = useState(false);
  const [manual, setManual] = useState(false);
  const url = window.location.origin + scopeLink(questionLink(qid, context));
  async function share() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setManual(false);
    } catch {
      setManual(true);
    }
  }
  return (
    <div className="mt-4">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          className={BTN}
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? "Hide discussion" : "Discuss / Ask a doubt"}
        </button>
        <button type="button" className={BTN} onClick={() => void share()}>
          {copied ? "Link copied" : "Share question"}
        </button>
        <Link
          className={BTN + " text-link"}
          to={"/contribute/new?" + new URLSearchParams({ question: qid })}
        >
          Suggest correction
        </Link>
      </div>
      {questionType==='mcq'&&<AnswerComparison key={qid+':'+(context.paper_id||'')} qid={qid} paperId={context.paper_id}/>}
      {open && <p className="mt-2 text-[12px] text-secondary">This conversation stays with the question across papers and practice. <Link to="/feed?tab=questions" className="font-semibold text-link underline">Explore Questions & Doubts →</Link></p>}
      {manual && (
        <label className="mt-2 block text-[12px]">
          Copy this question link
          <input
            readOnly
            value={url}
            onFocus={(e) => e.target.select()}
            className={INPUT}
          />
        </label>
      )}
      {open && (
        <QuestionDiscussion
          key={qid}
          qid={qid}
          context={context}
          answeredSignal={answeredSignal}
        />
      )}
    </div>
  );
}

function Composer({
  qid,
  context,
  parent,
  onSaved,
}: {
  qid: string;
  context: DiscussionContext;
  parent?: number;
  onSaved: () => void;
}) {
  const [kind, setKind] = useState<"doubt" | "explanation">("doubt");
  const [body, setBody] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const retry = useRef({ payload: "", key: crypto.randomUUID() });
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const payload = {
        kind: parent ? "reply" : kind,
        parent_id: parent || null,
        body,
        context,
        sources,
      };
      const serialized = JSON.stringify(payload);
      if (retry.current.payload !== serialized)
        retry.current = { payload: serialized, key: crypto.randomUUID() };
      const saved = await reviewRequest<{ needs_approval: boolean }>(
        "/community/questions/" + qid + "/discussion",
        payload,
        retry.current.key,
      );
      setBody("");
      setSources([]);
      setNotice(
        saved.needs_approval
          ? "Saved. Your post is awaiting moderation and is visible only to you."
          : "Posted to this question discussion and the community feed.",
      );
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      onSubmit={(e) => void submit(e)}
      className="mt-4 rounded-[8px] border border-hairline bg-paper p-4"
    >
      {!parent && (
        <label className="block text-[13px] font-semibold">
          Join the discussion
          <select
            value={kind}
            onChange={(e) => setKind(e.target.value as typeof kind)}
            className={INPUT + " mt-2"}
          >
            <option value="doubt">Ask a doubt</option>
            <option value="explanation">Write an explanation</option>
          </select>
        </label>
      )}
      <label className="mt-3 block text-[13px] font-semibold">
        {parent
          ? "Your reply"
          : kind === "doubt"
            ? "What is confusing you?"
            : "Explain your reasoning"}
        <textarea
          required
          minLength={10}
          maxLength={5000}
          rows={3}
          value={body}
          onChange={(e) => setBody(e.target.value)}
          className={INPUT + " mt-2"}
          placeholder="Mention the relevant wording or option. Include a source when you can."
        />
      </label>
      <p className="mt-1 text-[11px] text-muted">
        {body.length}/5000 · Plain text · Your first three approved posts
        require moderation.
      </p>
      {sources.map((s, i) => (
        <div key={i} className="mt-3 grid gap-2">
          <label className="text-[12px]">
            Source {i + 1} URL
            <input
              required
              type="url"
              pattern="https://.*"
              maxLength={2000}
              value={s.url}
              onChange={(e) =>
                setSources((xs) =>
                  xs.map((x, j) =>
                    i === j ? { ...x, url: e.target.value } : x,
                  ),
                )
              }
              className={INPUT}
            />
          </label>
          <label className="text-[12px]">
            What does this source support?
            <input
              required
              minLength={3}
              maxLength={1000}
              value={s.note}
              onChange={(e) =>
                setSources((xs) =>
                  xs.map((x, j) =>
                    i === j ? { ...x, note: e.target.value } : x,
                  ),
                )
              }
              className={INPUT}
            />
          </label>
          <button
            type="button"
            onClick={() => setSources((xs) => xs.filter((_, j) => j !== i))}
            className="min-h-11 text-left text-[12px] text-link"
          >
            Remove source
          </button>
        </div>
      ))}
      <div className="mt-3 flex flex-wrap gap-2">
        {sources.length < 5 && (
          <button
            type="button"
            onClick={() => setSources((xs) => [...xs, { url: "", note: "" }])}
            className={BTN}
          >
            Add source
          </button>
        )}
        <button disabled={busy} className={BTN + " bg-ink text-paper"}>
          {busy ? "Saving…" : parent ? "Post reply" : "Post to discussion"}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-[13px] text-mypick">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="mt-2 text-[13px] text-correct-dark">
          {notice}
        </p>
      )}
    </form>
  );
}

function Topic({
  post,
  qid,
  context,
  registered,
  locked,
  onChange,
  parentAuthor = false,
  focusPost,
}: {
  post: DiscussionPost;
  qid: string;
  context: DiscussionContext;
  registered: boolean;
  locked: boolean;
  onChange: () => void;
  parentAuthor?: boolean;
  focusPost?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [page, setPage] = useState<Page | null>(null);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState(false);
  const [reason, setReason] = useState("spam");
  const [note, setNote] = useState("");
  const [withdraw, setWithdraw] = useState(false);
  const pid = post.id;
  useEffect(() => {
    if (!post.parent_id && focusPost && focusPost !== pid) void load();
  }, [focusPost, pid]);
  async function load(next = 0) {
    try {
      const r = await read<Page>(
        "/posts/" +
          pid +
          "/replies?offset=" +
          next +
          (focusPost && focusPost !== pid ? "&focus=" + focusPost : ""),
      );
      setPage((old) => {
        const items =
          r.focused && !r.items.some((p) => p.id === r.focused?.id)
            ? [r.focused, ...r.items]
            : r.items;
        return next && old
          ? {
              ...r,
              items: [
                ...old.items,
                ...items.filter((x) => !old.items.some((p) => p.id === x.id)),
              ],
            }
          : { ...r, items };
      });
      setOffset(next);
      setExpanded(true);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function act(path: string, body: unknown) {
    setBusy(true);
    setError("");
    try {
      await reviewRequest("/community/posts/" + pid + "/" + path, body);
      onChange();
      return true;
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      setBusy(false);
    }
  }
  return (
    <article
      id={"discussion-post-" + pid}
      className={
        "min-w-0 rounded-[8px] border border-hairline p-4 " +
        (post.accepted ? "bg-[#E3EEE0]" : "bg-card")
      }
    >
      <div className="flex flex-wrap items-center gap-2 text-[12px]">
        <UserAvatar look={post.avatar} initials={post.author} size={30}/><b>{post.author}</b>
        <span className="rounded-pill bg-community-soft px-2 py-1 text-community-dark">
          {post.kind === "reply"
            ? "Reply"
            : post.kind === "doubt"
              ? "Doubt"
              : "Explanation"}
        </span>
        {post.accepted && (
          <span className="font-semibold text-correct-dark">
            ✓ Accepted by asker
          </span>
        )}
        {post.pinned && <span>Pinned explanation</span>}
        {post.needs_approval && (
          <span className="text-attention-dark">
            Awaiting moderation · only you can see this
          </span>
        )}
        <span className="text-muted">
          {new Date(post.created_at).toLocaleDateString("en-IN")}
        </span>
      </div>
      {post.source_context.exam_name && (
        <p className="mt-2 text-[12px] text-muted">
          {post.source_context.exam_name} · {post.source_context.year} · Q
          {post.source_context.qnum || "—"}
        </p>
      )}
      <p className="mt-3 whitespace-pre-wrap break-words text-[14.5px] leading-[1.6]">
        {post.body}
      </p>
      {post.source_links.map((s, i) => (
        <p key={i} className="mt-2 break-words text-[12px]">
          <a
            href={s.url}
            target="_blank"
            rel="noreferrer nofollow ugc"
            className="text-link underline"
          >
            {s.note} ↗
          </a>
        </p>
      ))}
      <div className="mt-3 flex flex-wrap gap-2">
        {registered && !post.is_author && !post.needs_approval && !locked && (
          <button
            disabled={busy}
            className={BTN}
            aria-pressed={post.voted}
            onClick={() => void act("helpful", { enabled: !post.voted })}
          >
            ▲ Helpful · {post.helpful}
          </button>
        )}
        {(!registered || post.is_author || locked) && (
          <span className="self-center text-[12px] text-muted">
            {post.helpful} helpful
          </span>
        )}
        {!post.parent_id && !post.needs_approval && (
          <button
            className={BTN}
            onClick={() => (expanded ? setExpanded(false) : void load())}
          >
            {expanded ? "Hide replies" : "Replies / Reply"}
          </button>
        )}
        {registered && parentAuthor && !post.is_author && !locked && (
          <button
            disabled={busy}
            className={BTN}
            onClick={() => void act("accept", { enabled: !post.accepted })}
          >
            {post.accepted ? "Unmark accepted" : "Accept reply"}
          </button>
        )}
        {registered && !post.needs_approval && (
          <Link
            className={BTN + " text-link"}
            to={
              "/contribute/new?" +
              new URLSearchParams({
                question: qid,
                discussion_post: String(pid),
                ...(post.source_context.appearance_id
                  ? { appearance: post.source_context.appearance_id }
                  : {}),
              })
            }
          >
            Use in correction draft
          </Link>
        )}
        {registered && !post.is_author && (
          <button className={BTN} onClick={() => setReport(!report)}>
            Report / block
          </button>
        )}
        {post.is_author && (
          <button className={BTN} onClick={() => setWithdraw(!withdraw)}>
            Withdraw
          </button>
        )}
      </div>
      {withdraw && (
        <div className="mt-3 text-[13px]">
          <p>Withdraw this post? It will leave the public discussion.</p>
          <button
            disabled={busy}
            className={BTN + " mt-2"}
            onClick={() => void act("withdraw", {})}
          >
            Confirm withdrawal
          </button>
        </div>
      )}
      {report && (
        <form
          className="mt-3 space-y-2"
          onSubmit={(e) => {
            e.preventDefault();
            void act("report", { reason, note }).then((ok) => {
              if (ok) setReport(false);
            });
          }}
        >
          <label className="block text-[12px]">
            Conduct issue
            <select
              className={INPUT}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            >
              {["spam", "harassment", "answer_leak", "copyright", "other"].map(
                (x) => (
                  <option key={x} value={x}>
                    {x.replace("_", " ")}
                  </option>
                ),
              )}
            </select>
          </label>
          <label className="block text-[12px]">
            Details
            <textarea
              required
              minLength={10}
              maxLength={2000}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className={INPUT}
            />
          </label>
          <p className="text-[12px] text-secondary">
            For an incorrect answer or typo, use Suggest correction.
          </p>
          <button disabled={busy} className={BTN}>
            Send conduct report
          </button>
          <button
            type="button"
            disabled={busy}
            className={BTN + " ml-2"}
            onClick={async () => {
              try {
                await reviewRequest("/creators/" + post.author_id + "/block", {
                  enabled: true,
                });
                onChange();
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            Block this author
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="mt-2 text-[13px] text-mypick">
          {error}
        </p>
      )}
      {expanded && (
        <div className="mt-4 space-y-3 border-t border-hairline pt-4">
          {page?.items.map((reply) => (
            <Topic
              key={reply.id}
              post={reply}
              qid={qid}
              context={context}
              registered={registered}
              locked={locked}
              parentAuthor={post.is_author && post.kind === "doubt"}
              onChange={() => {
                void load();
                onChange();
              }}
            />
          ))}
          {!page?.items.length && (
            <p className="text-[13px] text-muted">No published replies yet.</p>
          )}
          {page?.has_more && (
            <button className={BTN} onClick={() => void load(offset + 20)}>
              More replies
            </button>
          )}
          {registered && !locked && (
            <Composer
              qid={qid}
              context={context}
              parent={pid}
              onSaved={() => void load()}
            />
          )}
        </div>
      )}
    </article>
  );
}

export default function QuestionDiscussion({
  qid,
  context,
  answeredSignal,
}: {
  qid: string;
  context: DiscussionContext;
  answeredSignal?: unknown;
}) {
  const [data, setData] = useState<Thread | null>(null);
  const [error, setError] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const generation = useRef(0);
  const focus = new URLSearchParams(window.location.search).get("post");
  async function load(next = offset) {
    const run = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const r = await read<Thread>(
        "/questions/" +
          qid +
          "/discussion?offset=" +
          next +
          (focus && /^\d+$/.test(focus) ? "&focus=" + focus : ""),
      );
      if (run !== generation.current) return;
      setData(r);
      setOffset(next);
    } catch (e) {
      if (run === generation.current) setError((e as Error).message);
    } finally {
      if (run === generation.current) setLoading(false);
    }
  }
  useEffect(() => {
    let active = true;
    const run = ++generation.current;
    setData(null);
    setError("");
    read<Thread>(
      "/questions/" +
        qid +
        "/discussion" +
        (focus && /^\d+$/.test(focus) ? "?focus=" + focus : ""),
    )
      .then((r) => {
        if (active && run === generation.current) setData(r);
      })
      .catch((e) => {
        if (active && run === generation.current) setError(e.message);
      });
    const update = () => {
      setData(null);
      void load(0);
    };
    window.addEventListener("ism-auth-change", update);
    return () => {
      active = false;
      ++generation.current;
      window.removeEventListener("ism-auth-change", update);
    };
  }, [qid, answeredSignal, focus]);
  const posts =
    data?.focused && !data.items.some((p) => p.id === data.focused?.id)
      ? [data.focused, ...data.items]
      : data?.items || [];
  return (
    <section
      id={"discussion-" + qid}
      aria-label="Question discussion"
      className="mt-4 border-t border-ink pt-4"
    >
      <h2 className="font-display text-[25px]">Question discussion</h2>
      <p className="mt-1 text-[13px] leading-relaxed text-secondary">
        Ask doubts, explain a method and compare sources. Accepted replies and
        helpful votes reflect community feedback. Bank corrections require
        separate review.
      </p>
      {error && (
        <div role="alert" className="mt-3 text-[13px] text-mypick">
          {error}
          <button className={BTN + " ml-2"} onClick={() => void load()}>
            Retry
          </button>
        </div>
      )}
      {!data && !error && (
        <p className="mt-3 text-[13px] text-muted">Loading discussion…</p>
      )}
      {data && !data.allowed && (
        <div className="mt-4 rounded-[8px] border border-hairline bg-paper p-4">
          <p className="text-[14px]">
            {data.can_disclose
              ? "This question is unscored or has no checkable MCQ answer. Discussion may contain suggested answers."
              : "Answer this question to unlock its discussion."}
          </p>
          {data.can_disclose &&
            (data.registered ? (
              <button
                className={BTN + " mt-3"}
                onClick={async () => {
                  try {
                    await reviewRequest(
                      "/community/questions/" + qid + "/discussion/open",
                      {},
                    );
                    void load();
                  } catch (e) {
                    setError((e as Error).message);
                  }
                }}
              >
                Open discussion · may contain answers
              </button>
            ) : (
              <Link to="/login" className={BTN + " mt-3"}>
                Sign in to open discussion
              </Link>
            ))}
        </div>
      )}
      {data?.allowed && (
        <>
          <p className="mt-2 text-[12px] text-muted">
            First three approved posts are moderated. Community feedback earns
            no points.
          </p>
          {data.locked && (
            <p className="mt-3 text-[13px] text-attention-dark">
              Discussion locked · {data.lock_reason}
            </p>
          )}
          <div className="mt-4 space-y-3">
            {posts.map((p) => (
              <Topic
                key={p.id}
                post={p}
                qid={qid}
                context={context}
                registered={data.registered}
                locked={data.locked}
                focusPost={
                  focus && p.id === data.focused?.id ? Number(focus) : undefined
                }
                onChange={() => void load()}
              />
            ))}
            {!posts.length && (
              <p className="rounded-[8px] bg-paper p-4 text-[14px] text-secondary">
                No discussions yet. Ask the first doubt or share a worked
                explanation.
              </p>
            )}
          </div>
          {(offset > 0 || data.has_more) && (
            <nav
              aria-label="Discussion pages"
              className="mt-3 flex justify-between"
            >
              <button
                disabled={!offset || loading}
                className={BTN}
                onClick={() => void load(offset - 20)}
              >
                Previous
              </button>
              <button
                disabled={!data.has_more || loading}
                className={BTN}
                onClick={() => void load(offset + 20)}
              >
                Next
              </button>
            </nav>
          )}
          {data.registered && !data.locked ? (
            <Composer
              qid={qid}
              context={context}
              onSaved={() => void load(0)}
            />
          ) : (
            !data.registered && (
              <Link to="/login" className={BTN + " mt-4"}>
                Sign in to post, reply or vote
              </Link>
            )
          )}
        </>
      )}
    </section>
  );
}

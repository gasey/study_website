import {ContributorName,type ContributorTier} from './ContributorStanding'
import PostEditing,{EditMarker,type EditablePost} from './PostEditing'
import AcceptanceNudge from './AcceptanceNudge'
import BlockAuthor,{CommunityFeedback} from './BlockAuthor'
import CommunityText, {ComposerFormatting} from './CommunityText'
import DraftNotice from './DraftNotice'
import {useComposerDraft} from '../lib/useComposerDraft'
import {hasComposerDraft} from '../lib/communityDrafts'
import QuestionReport from './QuestionReport'
import {useQuestionStaff} from '../lib/useQuestionStaff'
import {scopeLink} from '../lib/examScope'
import {UserAvatar} from './AvatarArt'
import type {AvatarLook} from '../lib/avatar'
import { useEffect, useRef, useState, type ReactNode } from "react";
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
export interface DiscussionPost extends EditablePost {
  author_tier?:ContributorTier|null; author_profile_id?:string|null;
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
  "inline-flex min-h-11 items-center rounded-pill border border-hairline px-3 py-2 text-xs font-semibold disabled:opacity-50";
const INPUT =
  "w-full rounded-[6px] border border-hairline bg-card p-3 text-sm text-ink";
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
  sourceDetails,
}: {
  qid: string;
  context?: DiscussionContext;
  answeredSignal?: unknown;
  initialOpen?: boolean;
  questionType?: "mcq" | "descriptive";
  sourceDetails?: ReactNode;
}) {
  const staff = useQuestionStaff();
  const [open, setOpen] = useState(initialOpen);
  const [copied, setCopied] = useState(false);
  const [manual, setManual] = useState(false);
  const params = new URLSearchParams();
  if (context.paper_id) params.set('paper', context.paper_id);
  const url = window.location.origin + scopeLink('/api/questions/' + encodeURIComponent(qid) + '/share' + (params.size ? '?' + params : ''));
  const shareBinding = useRef(url);
  shareBinding.current = url;
  useEffect(() => { setCopied(false); setManual(false); }, [url]);
  async function share() {
    try {
      await navigator.clipboard.writeText(url);
      if (shareBinding.current === url) { setCopied(true); setManual(false); }
    } catch {
      if (shareBinding.current === url) setManual(true);
    }
  }
  return (
    <details key={qid+String(context.paper_id)} open={initialOpen||undefined} className="mt-0 text-xs text-secondary open:basis-full">
      <summary className="min-h-11 cursor-pointer py-3 font-semibold">More</summary>
      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {sourceDetails&&<details className="text-xs text-secondary open:basis-full"><summary className="min-h-11 cursor-pointer py-3">Source</summary>{sourceDetails}</details>}
        <button
          type="button"
          className="min-h-11 py-2 text-xs text-secondary"
          aria-expanded={open}
          onClick={() => setOpen(!open)}
        >
          {open ? "Hide discussion" : "Discussion"}
        </button>
        <button type="button" className="min-h-11 py-2 text-xs text-secondary" onClick={() => void share()}>
          {copied ? "Link copied" : "Share"}
        </button>
        <a className="inline-flex min-h-11 items-center py-2 text-xs text-link" href={'https://wa.me/?text='+encodeURIComponent('Practice this question on Finna:\n'+url)} target="_blank" rel="noreferrer">Share on WhatsApp ↗</a>
      <QuestionReport key={qid+String(context.paper_id)} qid={qid} paperId={context.paper_id}/>
        {staff && <Link className="inline-flex min-h-11 items-center text-xs text-link underline" to={'/admin/bank?'+new URLSearchParams({tab:'questions',question:qid,issue:'all'})}>Review / edit</Link>}
      </div>
      {open && <p className="mt-2 text-xs text-secondary">This conversation stays with the question across papers and practice. <Link to="/community/questions" className="font-semibold text-link underline">Explore Questions & Doubts →</Link></p>}
      {manual && (
        <label className="mt-2 block text-xs">
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
    </details>
  );
}

function Composer({
  qid,
  context,
  parent,
  onSaved,
  onJoin,
  threadVersion = 0,
}: {
  qid: string;
  context: DiscussionContext;
  parent?: number;
  onSaved: () => void;
  onJoin?: (post: DiscussionPost) => void;
  threadVersion?: number;
}) {
  const scope = 'question:' + JSON.stringify([qid, parent || null, context.paper_id || null, context.collection_id || null]);
  const draft = useComposerDraft(scope, true); // Mounted only after registered/unlocked access.
  const {body} = draft.fields;
  const {kind, sources} = draft.fields.discussion || {kind: 'doubt' as const, sources: []};
  const setBody = (value: string) => draft.update({body: value});
  const setKind = (value: 'doubt' | 'explanation') => draft.update({discussion: {kind: value, sources}});
  const setSources = (update: (xs: Source[]) => Source[]) => draft.update({discussion: {kind, sources: update(sources)}});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [suggestions, setSuggestions] = useState<Page | null>(null);
  const form = useRef<HTMLFormElement>(null);
  const generation = useRef(0);
  useEffect(() => () => { ++generation.current; }, []);
  useEffect(() => {
    ++generation.current;
    setSuggestions(null);
    setBusy(false);
  }, [threadVersion]);
  async function submit(e?: React.FormEvent, reviewed = false) {
    e?.preventDefault();
    if (reviewed && !form.current?.reportValidity()) return;
    const run = ++generation.current;
    setBusy(true);
    setError("");
    try {
      if (!parent && kind === "doubt" && !reviewed) {
        const existing = await read<Thread>("/questions/" + encodeURIComponent(qid) + "/discussion");
        if (run !== generation.current) return;
        if (!existing.allowed || !existing.registered || existing.locked)
          throw new Error("Reload this discussion before posting. Its access or moderation state changed.");
        const items = existing.items.filter((post) => !post.needs_approval);
        setSuggestions({items, has_more: existing.has_more});
        if (items.length) return;
      }
      const payload = {
        kind: parent ? "reply" : kind,
        parent_id: parent || null,
        body,
        context,
        sources,
      };
      const serialized = JSON.stringify(payload);
      const saved = await reviewRequest<{ needs_approval: boolean }>(
        "/community/questions/" + qid + "/discussion",
        payload,
        draft.requestKey(serialized),
      );
      if (run !== generation.current) return;
      draft.clear();
      setSuggestions(null);
      setNotice(
        saved.needs_approval
          ? "Saved. Your post is awaiting moderation and is visible only to you."
          : "Posted to this question discussion and the community feed.",
      );
      onSaved();
    } catch (e) {
      if (run === generation.current) setError((e as Error).message);
    } finally {
      if (run === generation.current) setBusy(false);
    }
  }
  return (
    <form
      ref={form}
      aria-busy={busy}
      onSubmit={(e) => void submit(e)}
      className="mt-4 rounded-[8px] border border-hairline bg-paper p-4"
    >
      {!parent && (
        <label className="block text-sm font-semibold">
          Join the discussion
          <select
            value={kind}
            onChange={(e) => {setKind(e.target.value as typeof kind);setSuggestions(null)}}
            disabled={busy}
            className={INPUT + " mt-2"}
          >
            <option value="doubt">Ask a doubt</option>
            <option value="explanation">Write an explanation</option>
          </select>
        </label>
      )}
      <label className="mt-3 block text-sm font-semibold">
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
          disabled={busy}
          onChange={(e) => setBody(e.target.value)}
          className={INPUT + " mt-2"}
          placeholder="Mention the relevant wording or option. Include a source when you can."
        />
      </label>
      <p className="mt-1 text-xs text-muted">
        {body.length}/5000 · Bold, lists and inline code · Your first three approved posts
        require moderation.
      </p>
      <ComposerFormatting body={body} sourceLinks />
      <DraftNotice status={draft.status} hasDraft={hasComposerDraft(draft.fields)} onDiscard={() => {draft.clear();setSuggestions(null);setError('');setNotice('');}} />
      {!parent && kind === "doubt" && !!suggestions?.items.length && (
        <aside aria-label="Existing discussions" className="mt-3 rounded-[8px] border border-hairline bg-community-soft p-3">
          <p role="status" className="text-sm font-semibold">Discussions already exist — does one cover your doubt?</p>
          <p className="mt-1 text-xs text-secondary">Join a conversation to keep its answers together. Your draft stays here.{suggestions.has_more ? " Showing the most recent discussions; more are available above." : ""}</p>
          <ul className="mt-2 space-y-2">
            {suggestions.items.map(post => <li key={post.id} className="min-w-0 border-t border-hairline pt-2">
              <p className="break-words text-sm">{post.body.length > 240 ? post.body.slice(0, 240) + "…" : post.body}</p>
              <button type="button" disabled={busy} className={BTN + " mt-1 text-link"} onClick={() => onJoin?.(post)}>Join discussion by {post.author}</button>
            </li>)}
          </ul>
          <button type="button" disabled={busy || body.trim().length < 10} className={BTN + " mt-3 bg-ink text-paper"} onClick={() => void submit(undefined, true)}>My doubt is different · post it</button>
        </aside>
      )}
      {sources.map((s, i) => (
        <div key={i} className="mt-3 grid gap-2">
          <label className="text-xs">
            Source {i + 1} URL
            <input
              required
              type="url"
              pattern="https://.*"
              maxLength={2000}
              disabled={busy}
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
          <label className="text-xs">
            What does this source support?
            <input
              required
              minLength={3}
              maxLength={1000}
              disabled={busy}
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
            disabled={busy}
            onClick={() => setSources((xs) => xs.filter((_, j) => j !== i))}
            className="min-h-11 text-left text-xs text-link"
          >
            Remove source
          </button>
        </div>
      ))}
      <div className="mt-3 flex flex-wrap gap-2">
        {sources.length < 5 && (
          <button
            type="button"
            disabled={busy}
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
        <p role="alert" className="mt-2 text-sm text-mypick">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="mt-2 text-sm text-correct-dark">
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
  joinRequested,
}: {
  post: DiscussionPost;
  qid: string;
  context: DiscussionContext;
  registered: boolean;
  locked: boolean;
  onChange: () => void;
  parentAuthor?: boolean;
  focusPost?: number;
  joinRequested?: number;
}) {
  const staff = useQuestionStaff();
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
  const article = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!post.parent_id && joinRequested) void load();
  }, [joinRequested, pid]);
  useEffect(() => {
    if (joinRequested && expanded && page) article.current?.querySelector<HTMLTextAreaElement>("textarea")?.focus();
  }, [joinRequested, expanded, page]);
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
      if(path==='helpful')window.dispatchEvent(new Event('ism-community-standing-change'));
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
      ref={article}
      id={"discussion-post-" + pid}
      className={
        "min-w-0 rounded-[8px] border border-hairline p-4 " +
        (post.accepted ? "bg-correct-soft" : "bg-card")
      }
    >
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <UserAvatar look={post.avatar} initials={post.author} size={30}/><ContributorName {...post}/>
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
        <p className="mt-2 text-xs text-muted">
          {post.source_context.exam_name} · {post.source_context.year} · Q
          {post.source_context.qnum || "—"}
        </p>
      )}
      <EditMarker post={post}/><CommunityText body={post.body} className="mt-3 text-sm leading-[1.6]" />
      {post.is_author&&registered&&!locked&&<PostEditing key={'edit:'+post.id+':'+(post.content_version||0)} post={post} canonical onSaved={onChange}/>}
      {post.source_links.map((s, i) => (
        <p key={i} className="mt-2 break-words text-xs">
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
          <span className="self-center text-xs text-muted">
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
        {staff && registered && !post.needs_approval && (
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
            Report post
          </button>
        )}
        {registered && !post.is_author && <BlockAuthor authorId={post.author_id} disabled={busy}/>}
        {post.is_author && (
          <button className={BTN} onClick={() => setWithdraw(!withdraw)}>
            Withdraw
          </button>
        )}
      </div>
      {withdraw && (
        <div className="mt-3 text-sm">
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
          <label className="block text-xs">
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
          <label className="block text-xs">
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
          <p className="text-xs text-secondary">
            For an incorrect answer or typo, use Report an issue.
          </p>
          <button disabled={busy} className={BTN}>
            Send conduct report
          </button>

        </form>
      )}
      {error && (
        <p role="alert" className="mt-2 text-sm text-mypick">
          {error}
        </p>
      )}
      {expanded && (
        <div className="mt-4 space-y-3 border-t border-hairline pt-4">
          {registered && !locked && post.is_author && post.kind === 'doubt' && !post.needs_approval &&
            page?.items.some(reply => !reply.is_author && !reply.needs_approval) && !page.items.some(reply => reply.accepted) &&
            <AcceptanceNudge key={pid} postId={pid}/>}
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
            <p className="text-sm text-muted">No published replies yet.</p>
          )}
          {page?.has_more && (
            <button className={BTN} onClick={() => void load(offset + 20)}>
              More replies
            </button>
          )}
          {registered && !locked && (
            <Composer
              key={JSON.stringify([qid, context.paper_id, context.collection_id])}
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
  const [joined, setJoined] = useState<{post: DiscussionPost; request: number} | null>(null);
  const generation = useRef(0);
  const focus = new URLSearchParams(window.location.search).get("post");
  async function load(next = offset) {
    const run = ++generation.current;
    setJoined(null);
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
    setJoined(null);
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
      setJoined(null);
      void load(0);
    };
    window.addEventListener("ism-auth-change", update);
    window.addEventListener("ism-auth-expired", update);
    window.addEventListener("ism-community-change", update);
    window.addEventListener("ism-answer-viewed", update);
    return () => {
      active = false;
      ++generation.current;
      window.removeEventListener("ism-auth-change", update);
      window.removeEventListener("ism-auth-expired", update);
      window.removeEventListener("ism-community-change", update);
      window.removeEventListener("ism-answer-viewed", update);
    };
  }, [qid, answeredSignal, focus]);
  const listed =
    data?.focused && !data.items.some((p) => p.id === data.focused?.id)
      ? [data.focused, ...data.items]
      : data?.items || [];
  const posts = joined && !listed.some(post => post.id === joined.post.id) ? [joined.post, ...listed] : listed;
  return (
    <section
      id={"discussion-" + qid}
      aria-label="Question discussion"
      className="mt-4 border-t border-ink pt-4"
    >
      <CommunityFeedback/>
      <h2 className="font-display text-xl">Question discussion</h2>
      <p className="mt-1 text-sm leading-relaxed text-secondary">
        Ask doubts, explain a method and compare sources. Accepted replies and
        helpful votes reflect community feedback. Bank corrections require
        separate review.
      </p>
      {error && (
        <div role="alert" className="mt-3 text-sm text-mypick">
          {error}
          <button className={BTN + " ml-2"} onClick={() => void load()}>
            Retry
          </button>
        </div>
      )}
      {!data && !error && (
        <p className="mt-3 text-sm text-muted">Loading discussion…</p>
      )}
      {data && !data.allowed && (
        <div className="mt-4 rounded-[8px] border border-hairline bg-paper p-4">
          <p className="text-sm">
            {data.can_disclose
              ? "This question is unscored or has no checkable MCQ answer. Discussion may contain suggested answers."
              : "Check or show the answer to unlock its discussion."}
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
          <p className="mt-2 text-xs text-muted">
            First three approved posts are moderated. Community feedback earns
            no points.
          </p>
          {data.locked && (
            <p className="mt-3 text-sm text-attention-dark">
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
                joinRequested={joined?.post.id === p.id ? joined.request : undefined}
                focusPost={
                  focus && p.id === data.focused?.id ? Number(focus) : undefined
                }
                onChange={() => void load()}
              />
            ))}
            {!posts.length && (
              <p className="rounded-[8px] bg-paper p-4 text-sm text-secondary">
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
              key={JSON.stringify([qid, context.paper_id, context.collection_id])}
              qid={qid}
              context={context}
              onSaved={() => void load(0)}
              onJoin={post => setJoined(previous => ({post, request: (previous?.request || 0) + 1}))}
              threadVersion={generation.current}
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

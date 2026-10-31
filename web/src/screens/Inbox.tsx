import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getAccountSession } from "../lib/api";
import { reviewSession } from "../lib/review";
import { hydrateDesk, getDeskSync } from "../lib/desk";
import { deskWrite, type ChatMessage } from "../lib/studyDesks";
import {
  categories,
  categoryLabels,
  inboxRequest,
  noticeLink,
  type Category,
  type Notice,
  type NoticePage,
  type InboxThread,
} from "../lib/inbox";
const signal = () =>
  window.dispatchEvent(new Event("ism-notifications-change"));
const initialPrefs = Object.fromEntries(
  categories.map((c) => [c, true]),
) as Record<Category, boolean>;
const stamp = (date: string) =>
  new Date(date).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  }) + " IST";
export default function Inbox() {
  const [params, setParams] = useSearchParams(),
    category = (
      categories.includes(params.get("category") as Category)
        ? params.get("category")
        : "all"
    ) as Category | "all",
    unread = params.get("unread") === "1",
    did = params.get("desk") || "";
  const [user, setUser] = useState(""),
    [auth, setAuth] = useState<"loading" | "guest" | "ready">("loading"),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [page, setPage] = useState<NoticePage | null>(null),
    [items, setItems] = useState<Notice[]>([]),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false);
  const [prefs, setPrefs] = useState(initialPrefs),
    [prefsBusy, setPrefsBusy] = useState(false);
  const [threads, setThreads] = useState<InboxThread[]>([]),
    [threadError, setThreadError] = useState(""),
    [messages, setMessages] = useState<ChatMessage[]>([]),
    [chatCursor, setChatCursor] = useState<number | null>(null),
    [chatLoading, setChatLoading] = useState(false),
    [draft, setDraft] = useState(""),
    [sending, setSending] = useState(false);
  const seenMessages = useRef<Record<string, number>>({});
  const threadRun = useRef(0);
  const [threadOffset, setThreadOffset] = useState<number | null>(null);
  const activeDesk = useRef(did);
  activeDesk.current = did;
  const epoch = useRef(0),
    listRun = useRef(0),
    chatRun = useRef(0),
    sendKey = useRef({ payload: "", key: crypto.randomUUID() }),
    mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    async function start() {
      const run = ++epoch.current;
      ++listRun.current;
      ++chatRun.current;
      setUser("");
      setAuth("loading");
      setItems([]);
      setPage(null);
      setThreads([]);
      seenMessages.current = {};
      setThreadOffset(null);
      setMessages([]);
      setDraft("");
      setError("");
      setThreadError("");
      setNotice("");
      setPrefs(initialPrefs);
      setBusy(false);
      setSending(false);
      try {
        const session = await getAccountSession();
        if (!mounted.current || run !== epoch.current) return;
        if (!session.authenticated) {
          setAuth("guest");
          return;
        }
        const actor = await reviewSession(true);
        await hydrateDesk();
        if (!mounted.current || run !== epoch.current) return;
        setUser(actor.user_id);
        setAuth("ready");
      } catch (e) {
        if (mounted.current && run === epoch.current) {
          setAuth("guest");
          setError((e as Error).message);
        }
      }
    }
    void start();
    window.addEventListener("ism-auth-change", start);
    return () => {
      mounted.current = false;
      ++epoch.current;
      ++listRun.current;
      ++chatRun.current;
      window.removeEventListener("ism-auth-change", start);
    };
  }, []);
  function filters(key: string, value: string) {
    setParams((p) => {
      if (value) p.set(key, value);
      else p.delete(key);
      return p;
    });
  }
  async function loadNotices(older = false) {
    if (!user) return;
    const run = ++listRun.current,
      owner = epoch.current;
    setLoading(true);
    setError("");
    const query = new URLSearchParams({ category, unread: String(unread) });
    if (older && page?.next_cursor)
      query.set("before", String(page.next_cursor));
    try {
      const data = await inboxRequest<NoticePage>(
        "/notifications?" + query,
        user,
      );
      if (run !== listRun.current || owner !== epoch.current) return;
      setPage((old) => ({
        ...data,
        snapshot_id: older && old ? old.snapshot_id : data.snapshot_id,
      }));
      setItems((old) =>
        older
          ? [
              ...old,
              ...data.items.filter((n) => !old.some((x) => x.id === n.id)),
            ]
          : data.items,
      );
    } catch (e) {
      if (run === listRun.current && owner === epoch.current)
        setError((e as Error).message);
    } finally {
      if (run === listRun.current && owner === epoch.current) setLoading(false);
    }
  }
  async function loadThreads(older = false) {
    if (!user || !getDeskSync().privateEnabled) return;
    const owner = epoch.current,
      run = ++threadRun.current;
    try {
      const data = await inboxRequest<{
        items: InboxThread[];
        next_offset: number | null;
      }>(
        "/threads" +
          (older && threadOffset !== null ? "?offset=" + threadOffset : ""),
        user,
      );
      const selected = activeDesk.current;
      if (selected && !data.items.some((t) => t.id === selected) && !older) {
        const pinned = await inboxRequest<{ items: InboxThread[] }>(
          "/threads?selected=" + encodeURIComponent(selected),
          user,
        );
        data.items.push(...pinned.items);
      }
      if (owner === epoch.current && run === threadRun.current) {
        setThreads((old) =>
          older
            ? [
                ...old,
                ...data.items.filter((t) => !old.some((x) => x.id === t.id)),
              ]
            : data.items,
        );
        setThreadOffset(data.next_offset);
        setThreadError("");
      }
    } catch (e) {
      if (owner === epoch.current) {
        setThreads([]);
        setMessages([]);
        setThreadError((e as Error).message);
      }
    }
  }
  useEffect(() => {
    void loadNotices();
    return () => {
      ++listRun.current;
    };
  }, [user, category, unread]);
  useEffect(() => {
    if (!user) return;
    const owner = epoch.current;
    void inboxRequest<{ in_app: Record<Category, boolean> }>(
      "/preferences",
      user,
    )
      .then((x) => {
        if (owner === epoch.current) setPrefs(x.in_app);
      })
      .catch((e) => {
        if (owner === epoch.current) setError(e.message);
      });
    void loadThreads();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void loadThreads();
    }, 30000);
    return () => clearInterval(timer);
  }, [user]);
  async function read(n: Notice, value: boolean) {
    if (busy) return;
    const owner = epoch.current;
    setBusy(true);
    setError("");
    try {
      await inboxRequest("/notifications/" + n.id + "/read", user, {
        read: value,
      });
      if (owner !== epoch.current) return;
      setItems((old) =>
        old
          .map((x) =>
            x.id === n.id
              ? {
                  ...x,
                  read_at: value ? new Date().toISOString() : null,
                  silent: value ? x.silent : false,
                }
              : x,
          )
          .filter((x) => !unread || !x.read_at),
      );
      signal();
      void loadNotices();
    } catch (e) {
      if (owner === epoch.current) setError((e as Error).message);
    } finally {
      if (owner === epoch.current) setBusy(false);
    }
  }
  async function readAll() {
    if (!page || busy) return;
    const owner = epoch.current;
    setBusy(true);
    try {
      await inboxRequest("/notifications/read-all", user, {
        through_id: page.snapshot_id,
        category,
      });
      if (owner === epoch.current) {
        signal();
        setNotice("Notifications marked read.");
        void loadNotices();
      }
    } catch (e) {
      if (owner === epoch.current) setError((e as Error).message);
    } finally {
      if (owner === epoch.current) setBusy(false);
    }
  }
  async function savePrefs() {
    const owner = epoch.current;
    setPrefsBusy(true);
    setError("");
    try {
      await inboxRequest("/preferences", user, prefs);
      if (owner === epoch.current)
        setNotice("Preferences saved. Changes apply to new notifications.");
    } catch (e) {
      if (owner === epoch.current) setError((e as Error).message);
    } finally {
      if (owner === epoch.current) setPrefsBusy(false);
    }
  }
  async function loadChat(older = false) {
    if (!did || !user) return;
    const run = ++chatRun.current,
      owner = epoch.current;
    setChatLoading(true);
    setThreadError("");
    try {
      const data = await inboxRequest<{
        items: ChatMessage[];
        next_cursor: number | null;
      }>(
        "/threads/" +
          encodeURIComponent(did) +
          "/messages" +
          (older && chatCursor ? "?before=" + chatCursor : ""),
        user,
      );
      if (
        owner !== epoch.current ||
        run !== chatRun.current ||
        did !== activeDesk.current
      )
        return;
      setMessages((old) => {
        const merged = older
          ? [
              ...old,
              ...data.items.filter((n) => !old.some((x) => x.id === n.id)),
            ]
          : data.items;
        return merged.sort((a, b) => a.id - b.id);
      });
      setChatCursor(data.next_cursor);
      const through = Math.max(0, ...data.items.map((x) => x.id));
      if (!older && through > (seenMessages.current[did] || 0)) {
        await inboxRequest(
          "/threads/" + encodeURIComponent(did) + "/read",
          user,
          { through_id: through },
        );
        if (owner === epoch.current && did === activeDesk.current) {
          seenMessages.current[did] = through;
          signal();
          void loadThreads();
        }
      }
    } catch (e) {
      if (
        owner === epoch.current &&
        run === chatRun.current &&
        did === activeDesk.current
      ) {
        setThreadError((e as Error).message);
        setMessages([]);
      }
    } finally {
      if (
        owner === epoch.current &&
        run === chatRun.current &&
        did === activeDesk.current
      )
        setChatLoading(false);
    }
  }
  useEffect(() => {
    setMessages([]);
    setChatCursor(null);
    setDraft("");
    sendKey.current = { payload: "", key: crypto.randomUUID() };
    void loadChat();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible" && !draft.trim())
        void loadChat();
    }, 15000);
    return () => {
      clearInterval(timer);
      ++chatRun.current;
    };
  }, [user, did]);
  async function send() {
    if (!draft.trim() || sending || !did) return;
    const owner = epoch.current,
      room = did,
      body = draft.trim();
    setSending(true);
    setThreadError("");
    if (sendKey.current.payload !== room + "\n" + body)
      sendKey.current = {
        payload: room + "\n" + body,
        key: crypto.randomUUID(),
      };
    try {
      await deskWrite(
        "/rooms/" + encodeURIComponent(room) + "/messages",
        { body },
        sendKey.current.key,
      );
      if (owner !== epoch.current || room !== activeDesk.current) return;
      setDraft("");
      setNotice("Message sent.");
      void loadChat();
      void loadThreads();
    } catch (e) {
      if (owner === epoch.current && room === activeDesk.current)
        setThreadError((e as Error).message);
    } finally {
      if (owner === epoch.current) setSending(false);
    }
  }
  const active = threads.find((t) => t.id === did);
  if (auth === "loading")
    return (
      <main className="mx-auto max-w-[1240px] px-6 py-10" aria-busy="true">
        Loading your Inbox…
      </main>
    );
  if (auth === "guest")
    return (
      <main className="mx-auto max-w-[1240px] px-6 py-10">
        <h1 className="font-display text-[44px]">Inbox</h1>
        <p className="mt-3 text-secondary">
          Sign in to see your private notifications and study desk messages.
        </p>
        {error && <p role="alert">{error}</p>}
        <Link
          to="/login"
          className="mt-5 inline-block rounded-pill bg-ink px-6 py-3 text-paper"
        >
          Log in
        </Link>
      </main>
    );
  return (
    <main className="mx-auto max-w-[1240px] px-4 pb-24 pt-9 sm:px-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-[clamp(36px,5vw,52px)] leading-tight tracking-[-.02em]">
            Inbox
          </h1>
          <p className="mt-2 text-[14px] text-secondary">
            Your study updates and private desk conversations.
          </p>
        </div>
        <button
          onClick={() => {
            void loadNotices();
            void loadThreads();
            void loadChat();
          }}
          className="min-h-[44px] rounded-pill border border-hairline px-4 text-[13px]"
        >
          Refresh Inbox
        </button>
      </div>
      {notice && (
        <p role="status" className="mb-4 text-[13px] text-link">
          {notice}
        </p>
      )}
      <div className="flex flex-wrap items-start gap-6 lg:gap-10">
        <section
          aria-label="Notifications"
          className="min-w-0 flex-[1_1_340px] rounded-[14px] border border-hairline bg-white px-[18px] pb-[18px] pt-2 shadow-sm"
        >
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-hairline py-3">
            <h2 className="text-[14px] font-semibold">
              Notifications{" "}
              {page && (
                <span className="ml-1 rounded-pill bg-mypick px-2 py-1 font-mono text-[11px] text-white">
                  {page.unread} unread
                </span>
              )}
            </h2>
            <button
              onClick={readAll}
              disabled={
                busy ||
                !(category === "all"
                  ? page?.unread
                  : page?.unread_by_category[category])
              }
              className="min-h-[44px] text-[12px] underline disabled:opacity-40"
            >
              {category === "all" ? "Mark all read" : "Mark category read"}
            </button>
          </div>
          <div className="flex flex-wrap gap-2 py-3">
            <select
              aria-label="Notification category"
              value={category}
              onChange={(e) =>
                filters(
                  "category",
                  e.target.value === "all" ? "" : e.target.value,
                )
              }
              className="min-h-[44px] min-w-0 rounded-md border border-hairline bg-paper px-2 text-[13px]"
            >
              <option value="all">All notifications</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {categoryLabels[c]}
                  {page?.unread_by_category[c]
                    ? " · " + page.unread_by_category[c]
                    : ""}
                </option>
              ))}
            </select>
            <label className="flex min-h-[44px] items-center gap-2 text-[13px]">
              <input
                type="checkbox"
                checked={unread}
                onChange={(e) => filters("unread", e.target.checked ? "1" : "")}
              />
              Unread only
            </label>
          </div>
          {error && (
            <p role="alert" className="my-3 text-[13px] text-mypick">
              {error}{" "}
              <button onClick={() => void loadNotices()} className="underline">
                Retry
              </button>
            </p>
          )}
          <div aria-busy={loading} className="max-h-[560px] overflow-y-auto">
            {items.map((n) => {
              const action = noticeLink(n);
              return (
                <article
                  key={n.id}
                  className="flex gap-3 border-b border-[#F1EBDF] py-[14px]"
                >
                  <span
                    aria-label={
                      n.read_at
                        ? "Read"
                        : n.silent
                          ? "Quiet notification"
                          : "Unread"
                    }
                    className={
                      "mt-[7px] h-2 w-2 shrink-0 rounded-full " +
                      (!n.read_at && !n.silent ? "bg-mypick" : "bg-hairline")
                    }
                  />
                  <div className="min-w-0 flex-1">
                    <p className="break-words text-[14px] leading-[1.5]">
                      {n.message}
                    </p>
                    <p className="mt-1 font-mono text-[10px] text-muted">
                      {categoryLabels[n.category]} ·{" "}
                      <time dateTime={n.created_at}>{stamp(n.created_at)}</time>
                      {n.silent ? " · Quiet" : ""}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-3">
                      {action && (
                        <Link
                          to={action.url}
                          onClick={() => {
                            if (!n.read_at) void read(n, true);
                          }}
                          className="inline-flex min-h-[36px] items-center rounded-pill border border-ink px-3 text-[12px] font-semibold"
                        >
                          {action.label}
                        </Link>
                      )}
                      <button
                        disabled={busy}
                        onClick={() => void read(n, !n.read_at)}
                        className="min-h-[36px] text-[12px] text-link underline"
                      >
                        {n.read_at ? "Mark unread" : "Mark read"}
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
          {!loading && !error && !items.length && (
            <p className="py-8 text-[14px] text-secondary">
              {unread
                ? "You’re all caught up."
                : "No notifications here yet. Study updates will appear as you use the site."}
            </p>
          )}
          {loading && (
            <p role="status" className="py-3 text-[13px]">
              Loading notifications…
            </p>
          )}
          {page?.next_cursor && (
            <button
              disabled={loading}
              onClick={() => void loadNotices(true)}
              className="mt-3 min-h-[44px] rounded-pill border border-hairline px-4 text-[13px]"
            >
              Load older notifications
            </button>
          )}
          <h2 className="mt-5 border-b border-hairline py-3 text-[14px] font-semibold">
            Notification settings
          </h2>
          <p className="py-3 text-[12px] leading-relaxed text-secondary">
            Choose which new updates count as unread. Quiet updates remain in
            All notifications. Existing updates keep their state.
          </p>
          <div className="grid grid-cols-[minmax(0,1fr)_64px] border-b border-hairline py-2 font-mono text-[10px] uppercase text-muted">
            <span>Category</span>
            <span className="text-center">In app</span>
          </div>
          {categories.map((c) => (
            <label
              key={c}
              className="grid min-h-[44px] grid-cols-[minmax(0,1fr)_64px] items-center border-b border-[#F1EBDF] text-[13px]"
            >
              <span>{categoryLabels[c]}</span>
              <input
                type="checkbox"
                aria-label={categoryLabels[c] + " in-app notifications"}
                checked={prefs[c]}
                disabled={prefsBusy}
                onChange={(e) =>
                  setPrefs((old) => ({ ...old, [c]: e.target.checked }))
                }
                className="justify-self-center accent-[#B23A9A]"
              />
            </label>
          ))}
          <button
            disabled={prefsBusy}
            onClick={() => void savePrefs()}
            className="mt-4 min-h-[44px] rounded-pill border border-ink px-4 text-[13px] font-semibold"
          >
            {prefsBusy ? "Saving…" : "Save preferences"}
          </button>
          <p className="mt-3 text-[12px] text-muted">
            Email and push delivery are not configured. No external
            notifications are sent.
          </p>
        </section>
        <section
          aria-label="Private desk messages"
          className="min-w-0 flex-[1.6_1_480px] overflow-hidden rounded-[14px] border border-hairline bg-white shadow-sm"
        >
          <div className="border-b border-hairline px-4 py-3">
            <h2 className="text-[14px] font-semibold">Messages</h2>
            <p className="mt-1 text-[12px] text-secondary">
              Only people in your accepted private study desks.{" "}
              <Link to="/desk" className="text-link underline">
                Manage desks & invitations
              </Link>
            </p>
          </div>
          <div className="flex min-h-[480px] flex-wrap">
            <nav
              aria-label="Desk conversations"
              className="min-w-0 flex-[1_1_180px] border-r border-hairline bg-paper"
            >
              {threads.map((t) => (
                <button
                  key={t.id}
                  aria-current={did === t.id ? "page" : undefined}
                  onClick={() => filters("desk", t.id)}
                  className={
                    "block w-full border-b border-[#F1EBDF] px-4 py-3 text-left " +
                    (did === t.id ? "bg-[#EFE5D4]" : "hover:bg-[#F3EDE0]")
                  }
                >
                  <span className="flex justify-between gap-2 text-[14px] font-semibold">
                    <span className="break-words">{t.name}</span>
                    {t.unread > 0 && (
                      <span
                        aria-label={t.unread + " unread messages"}
                        className="rounded-pill bg-mypick px-2 text-[11px] text-white"
                      >
                        {t.unread}
                      </span>
                    )}
                  </span>
                  <span className="mt-1 block truncate text-[13px] text-secondary">
                    {t.last_message
                      ? (t.author || "Learner") + ": " + t.last_message
                      : "No messages yet"}
                  </span>
                </button>
              ))}
              {threadOffset !== null && (
                <button
                  onClick={() => void loadThreads(true)}
                  className="min-h-[44px] w-full p-3 text-[12px] text-link underline"
                >
                  Load more conversations
                </button>
              )}
              {!threads.length && (
                <p className="p-4 text-[13px] text-secondary">
                  {getDeskSync().privateEnabled
                    ? "Your joined desk conversations will appear here."
                    : "Private study desks are currently unavailable."}
                </p>
              )}
            </nav>
            <div className="flex min-w-0 flex-[2_1_280px] flex-col">
              <div className="border-b border-[#F1EBDF] px-[18px] py-[14px] font-display text-[19px]">
                {active?.name || "Choose a conversation"}
                {active && (
                  <Link
                    to={"/desk/" + active.id}
                    className="ml-3 font-sans text-[12px] text-link underline"
                  >
                    Open desk
                  </Link>
                )}
              </div>
              {threadError && (
                <p role="alert" className="p-4 text-[13px] text-mypick">
                  {threadError}{" "}
                  <button
                    onClick={() => {
                      void loadThreads();
                      void loadChat();
                    }}
                    className="underline"
                  >
                    Retry
                  </button>
                </p>
              )}
              <div
                role="log"
                aria-label="Desk messages"
                aria-live="polite"
                className="flex max-h-[560px] min-h-[260px] flex-1 flex-col gap-[10px] overflow-y-auto p-[18px]"
              >
                {chatCursor && (
                  <button
                    disabled={chatLoading}
                    onClick={() => void loadChat(true)}
                    className="min-h-[44px] text-[12px] text-link underline"
                  >
                    Load older messages
                  </button>
                )}
                {messages.map((m) => (
                  <article
                    key={m.id}
                    className={
                      "max-w-[88%] rounded-[10px] px-[14px] py-[10px] text-[14px] leading-[1.5] " +
                      (m.author_id === user
                        ? "self-end bg-[#86226F] text-white"
                        : "self-start bg-[#F3EDE0] text-ink")
                    }
                  >
                    <div className="mb-1 text-[11px] opacity-75">
                      {m.author_id === user ? "You" : m.author || "Learner"} ·{" "}
                      <time dateTime={m.created_at}>{stamp(m.created_at)}</time>
                    </div>
                    <p className="whitespace-pre-wrap break-words">{m.body}</p>
                  </article>
                ))}
                {!messages.length && !chatLoading && (
                  <p className="text-[13px] text-secondary">
                    {active
                      ? "Start a conversation with your desk."
                      : "Choose a desk to read its private conversation."}
                  </p>
                )}
                {chatLoading && (
                  <p role="status" className="text-[13px] text-muted">
                    Loading messages…
                  </p>
                )}
              </div>
              {did && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void send();
                  }}
                  className="flex items-end gap-2 border-t border-hairline p-3"
                >
                  <label className="min-w-0 flex-1">
                    <span className="sr-only">Write a message</span>
                    <textarea
                      aria-label="Write a message"
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      maxLength={2000}
                      rows={2}
                      disabled={sending || !active || !!threadError}
                      placeholder="Write a message"
                      className="min-h-[44px] w-full resize-y rounded-[16px] border border-hairline bg-[#F7F3EA] px-3 py-2 text-[14px]"
                    />
                    <span className="text-[10px] text-muted">
                      {draft.length}/2000 · Visible to this desk’s members
                    </span>
                  </label>
                  <button
                    disabled={
                      sending || !draft.trim() || !active || !!threadError
                    }
                    className="mb-5 min-h-[44px] rounded-pill bg-[#B23A9A] px-4 text-[14px] font-semibold text-white disabled:opacity-40"
                  >
                    {sending ? "Sending…" : "Send"}
                  </button>
                </form>
              )}
              <p className="border-t border-[#F1EBDF] px-4 py-3 text-[11px] text-muted">
                Manage blocking, reports and your membership in the desk. No
                public messaging directory.
              </p>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

import DeskCalendar from '../components/DeskCalendar'
import DeskWeeklyGoal from '../components/DeskWeeklyGoal'
import DeskDiscussionButton from '../components/DeskDiscussionButton'
import {UserAvatar} from '../components/AvatarArt'
import {AVATAR_COLORS} from '../lib/avatar'
import { lazy, Suspense, useEffect, useRef, useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import DeskScene, { type SceneMember } from "../components/DeskScene";
import DeskFocus from "../components/DeskFocus";
import { DeskBrassClock } from "../components/DeskCampfireClock";
import FlashBanner from "../components/FlashBanner";
import { DeskEmpty as Empty, DeskModal as Modal } from "../components/DeskParts";
import { DeskQuestion } from "../components/DeskPractice";
import {
  getQuestion,
  listQuestions,
  type Question,
} from "../lib/api";
import {
  deskRead,
  flushDesk,
  getDesk,
  getDeskSync,
  importGuestDesk,
  reloadAccountDesk,
  saveDesk,
  subscribeDesk,
  type DeskData,
  type DeskNote,
} from "../lib/desk";
import {
  deskWrite,
  getOverview,
  getRoom,
  getRooms,
  type ChatMessage,
  type DeskOverview,
  type RoomDetail,
  type RoomList,
  type SharedItem,
} from "../lib/studyDesks";
import { reviewRequest } from "../lib/review";
const DeskLinkedNote = lazy(() => import("../components/DeskLinkedNote"));
const DeskPracticeSessions = lazy(() => import("../components/DeskPracticeSessions"));
const DeskPractice = lazy(() => import("../components/DeskPractice"));
const TABS = [
  ["shared", "Shared Qs", "#C0462C", "#F6DDD3"],
  ["practice", "Desk set", "#2D5BD0", "#DAE3F1"],
  ["notes", "Shared notes", "#B7791A", "#F6E7C6"],
  ["bookmarks", "Bookmarks", "#1F7F86", "#D8E9E5"],
  ["progress", "Progress", "#3F8350", "#E3EEE0"],
  ["mistakes", "Mistakes wall", "#9A5B34", "#F6DDD3"],
  ["session", "Focus session", "#8A4A86", "#EEDDEC"],
];
const emptyOverview: DeskOverview = {
  stats: { answered: 0, correct: 0, unique_questions: 0, week_answers: 0 },
  questions: [],
  subjects: [],
  mistakes: [],
  sessions: [],
  server_time: new Date().toISOString(),
};
const COLORS = [
  "#C0462C",
  "#1F7F86",
  "#33609E",
  "#8A4A86",
  "#3F8350",
  "#B7791A",
];
const B = "desk-v3-button";
const I = "desk-v3-input";
const uid = () => crypto.randomUUID();
type Panel =
  | "create"
  | "invite"
  | "share"
  | "note"
  | "settings"
  | "report"
  | "message"
  | null;

export default function StudyDesk() {
  const nav = useNavigate();
  const { deskId } = useParams();
  const roomId = deskId?.startsWith("desk_") ? deskId : undefined;
  const [params, setParams] = useSearchParams();
  const requested = params.get("tab") || "shared";
  const raw = requested === "focus" ? "session" : !roomId && requested === "bookmarks" ? "shared" : requested;
  const tabs = roomId ? TABS : TABS.filter(t => !["progress", "mistakes", "practice", "bookmarks"].includes(t[0])).map(t => [t[0], t[0] === "shared" ? "Saved questions" : t[0] === "notes" ? "Notes" : t[0] === "session" ? "Focus timer" : t[1], t[2], t[3]]);
  const tab = tabs.some((t) => t[0] === raw) ? raw : "shared";
  useEffect(() => {if (!roomId && ["progress", "mistakes", "practice"].includes(raw)) nav(raw === "progress" ? "/profile#mastery" : raw === "practice" ? "/practice" : "/revise?tab=queue", {replace: true})}, [roomId, raw, nav]);
  const [desk, setDesk] = useState(getDesk);
  const [sync, setSync] = useState(getDeskSync);
  const [overview, setOverview] = useState<DeskOverview>(emptyOverview);
  const [list, setList] = useState<RoomList | null>(null);
  const [room, setRoom] = useState<RoomDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [items, setItems] = useState<SharedItem[]>([]);
  const [discussionFilter, setDiscussionFilter] = useState<"all" | "needed" | "resolved">("all");
  useEffect(() => { if (!sync.privateEnabled) setDiscussionFilter("all"); }, [sync.privateEnabled]);
  const itemSequence = useRef(0);
  const itemKind = tab === "shared" && discussionFilter !== "all" ? "all" :
    tab === "shared" || tab === "practice" ? "question" :
    tab === "notes" ? "note" : tab === "bookmarks" ? "bookmark" :
    tab === "mistakes" ? "mistake" : "update";
  const itemQuery = "/items?kind=" + itemKind + "&discussion=" +
    (tab === "shared" ? discussionFilter : "all") + "&limit=" + (["shared", "practice"].includes(tab) ? 5 : 20);
  const [cursor, setCursor] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatCursor, setChatCursor] = useState<number | null>(null);
  const [chat, setChat] = useState("");
  const [chatNote, setChatNote] = useState<{id:string;title:string} | null>(null);
  useEffect(() => setChatNote(null), [roomId, sync.userId]);
  const [messageEdit, setMessageEdit] = useState<ChatMessage | null>(null);
  const [messageBody, setMessageBody] = useState("");
  const [activeMember, setActiveMember] = useState("");
  const [expanded, setExpanded] = useState("");
  const [savedPage, setSavedPage] = useState(0);
  const [previews, setPreviews] = useState<DeskOverview["questions"]>([]);
  const [panel, setPanel] = useState<Panel>(null);
  const [name, setName] = useState("");
  const [goal, setGoal] = useState("");
  const [handle, setHandle] = useState("");
  const [note, setNote] = useState<DeskNote>({
    id: "",
    title: "",
    body: "",
    subject: "",
  });
  const [editItem, setEditItem] = useState<SharedItem | null>(null);
  const [shareKind, setShareKind] = useState<
    "question" | "bookmark" | "mistake" | "update"
  >("question");
  const [search, setSearch] = useState("");
  const [found, setFound] = useState<Question[]>([]);
  const [selected, setSelected] = useState<Question | null>(null);
  const [shareNote, setShareNote] = useState("");
  const [reportTarget, setReportTarget] = useState({ kind: "desk", id: "" });
  const [reportReason, setReportReason] = useState("");
  const [confirmation, setConfirmation] = useState<{
    title: string;
    text: string;
    run: () => Promise<void>;
  } | null>(null);
  const [notice, setNotice] = useState("");
  const [showDiagram, setShowDiagram] = useState(() => {
    try {
      return typeof localStorage !== "undefined" && localStorage.getItem("finna:desk-diagram:v1") === "1";
    } catch {
      return false;
    }
  });
  function toggleDiagram() {
    setShowDiagram((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("finna:desk-diagram:v1", next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  }
  const createKey = useRef(uid());
  const shareKey = useRef({ payload: "", key: uid() });
  const chatKey = useRef({ payload: "", key: uid() });
  useEffect(
    () =>
      subscribeDesk(() => {
        setDesk(getDesk());
        setSync(getDeskSync());
      }),
    [],
  );
  async function refresh() {
    try {
      const result = await getOverview();
      setOverview(result);
      if (sync.registered) {
        setList(await getRooms());
        if (roomId) setRoom(await getRoom(roomId));
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    let active = true;
    setRoom(null);
    setList(null);
    setItems([]);
    setMessages([]);
    setPanel(null);
    setError("");
    setOverview(emptyOverview);
    if (sync.loading) return;
    setLoading(true);
    Promise.all([
      getOverview(),
      sync.registered ? getRooms() : Promise.resolve(null),
      sync.registered && roomId ? getRoom(roomId) : Promise.resolve(null),
    ])
      .then(([o, l, r]) => {
        if (!active) return;
        setOverview(o);
        setList(l);
        setRoom(r);
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [sync.userId, sync.registered, sync.loading, roomId]);
  useEffect(() => {
    if (!roomId || !room?.id) return;
    let alive = true;
    const timer = window.setInterval(async () => {
      if (document.visibilityState !== "visible") return;
      try {
        const nextRoom = await getRoom(roomId);
        const chat = await deskRead<{
          items: ChatMessage[];
          next_cursor: number | null;
        }>("/rooms/" + roomId + "/messages");
        if (!alive) return;
        const itemRun = ++itemSequence.current;
        const shared = await deskRead<{ items: SharedItem[]; next_cursor: string | null }>("/rooms/" + roomId + itemQuery);
        if (alive) {
          setRoom(nextRoom);
          setMessages(chat.items);
          setChatCursor(chat.next_cursor);
          if (itemRun === itemSequence.current) {
            setItems(shared.items); setCursor(shared.next_cursor);
          }
        }
      } catch (e) {
        if (alive) {
          setRoom(null);
          setMessages([]);
          setItems([]);
          setError((e as Error).message);
        }
      }
    }, 30000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [roomId, room?.id, sync.userId, itemQuery]);
  async function loadItems(next?: string) {
    if (!roomId) return;
    const run = ++itemSequence.current;
    const result = await deskRead<{
      items: SharedItem[];
      next_cursor: string | null;
    }>(
      "/rooms/" + roomId + itemQuery + (next ? "&before=" + next : ""),
    );
    if (run !== itemSequence.current) return;
    setItems((old) => (next ? [...old, ...result.items] : result.items));
    setCursor(result.next_cursor);
  }
  async function loadChat(next?: number) {
    if (!roomId) return;
    const result = await deskRead<{
      items: ChatMessage[];
      next_cursor: number | null;
    }>("/rooms/" + roomId + "/messages" + (next ? "?before=" + next : ""));
    setMessages((old) => (next ? [...old, ...result.items] : result.items));
    setChatCursor(result.next_cursor);
  }
  useEffect(() => {
    let active = true;
    const run = ++itemSequence.current;
    setItems([]);
    setMessages([]);
    setCursor(null);
    setChatCursor(null);
    if (!room || !roomId) return;
    deskRead<{ items: SharedItem[]; next_cursor: string | null }>(
      "/rooms/" + roomId + itemQuery,
    )
      .then((r) => {
        if (active && run === itemSequence.current) {
          setItems(r.items);
          setCursor(r.next_cursor);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    deskRead<{ items: ChatMessage[]; next_cursor: number | null }>(
      "/rooms/" + roomId + "/messages",
    )
      .then((r) => {
        if (active) {
          setMessages(r.items);
          setChatCursor(r.next_cursor);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [roomId, room?.id, itemQuery, sync.userId]);
  useEffect(() => {
    let active = true;
    const ids = desk.saved.slice(savedPage * 20, savedPage * 20 + 20);
    if (!ids.length) {
      setPreviews([]);
      return;
    }
    deskRead<{ items: DeskOverview["questions"] }>(
      "/questions?" + new URLSearchParams(ids.map((x) => ["ids", x])),
    )
      .then((r) => {
        if (active) setPreviews(r.items);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [desk.saved.join(","), savedPage]);
  useEffect(() => {
    if (panel !== "share") return;
    let active = true;
    const timer = window.setTimeout(() => {
      listQuestions({ q: search, pool: "all", limit: 5, offset: 0 })
        .then((r) => {
          if (active) setFound(r.items);
        })
        .catch((e) => {
          if (active) setError(e.message);
        });
    }, 300);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [panel, search]);
  const myId = sync.userId;
  const owner = !!room && room.owner_id === myId;
  const registered = sync.registered;
  const members = room?.members || [
    {
      avatar:sync.avatar,
      user_id: myId,
      handle: sync.handle || "You",
      is_you: true,
      blocked: false,
      focusing: false,
      progress: overview.stats,
    },
  ];
  const focused =
    members.find((m) => m.user_id === activeMember) ||
    members.find((m) => m.is_you) ||
    members[0];
  const acc = (answered: number, correct: number) =>
    answered ? Math.round((correct / answered) * 100) + "%" : "—";
  const sceneMembers: (SceneMember | null)[] = Array.from(
    { length: 6 },
    (_, i) => {
      const m = members[i];
      return m
        ? {
            ini: m.user_id,
            name: (m.is_you ? "You" : m.handle).slice(0, 14),
            here: !m.blocked,
            avatar:m.avatar,
            body: m.avatar?AVATAR_COLORS[m.avatar.top]||COLORS[i % COLORS.length]:COLORS[i % COLORS.length],
            skin: m.avatar?.skin||"#E6C4A5",
            hair: m.avatar?.hairC||"#453329",
            arm: m.avatar?.skin||"#D7B08A",
          }
        : null;
    },
  );
  function setTab(value: string) {
    if (!roomId && ["progress", "mistakes", "practice"].includes(value)) { nav(value === "progress" ? "/profile#mastery" : value === "practice" ? "/practice" : "/revise?tab=queue"); return; }
    setParams((previous) => {
      const p = new URLSearchParams(previous);
      p.set("tab", value);
      return p;
    });
  }
  function open(value: Panel) {
    setError("");
    setNotice("");
    setEditItem(null);
    createKey.current = uid();
    if (value === "create") {
      setName("");
      setGoal("");
    }
    if (value === "settings") {
      setName(room?.name || "");
      setGoal(room?.goal || "");
    }
    if (value === "note")
      setNote({ id: uid(), title: "", body: "", subject: desk.goalSubject });
    if (value === "share") {
      setSelected(null);
      setSearch("");
      setShareNote("");
      setShareKind(
        tab === "mistakes"
          ? "mistake"
          : tab === "bookmarks"
            ? "bookmark"
            : "question",
      );
    }
    setPanel(value);
  }
  async function execute(fn: () => Promise<void>) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function confirm(title: string, text: string, fn: () => Promise<void>) {
    setPanel(null);
    setConfirmation({ title, text, run: fn });
  }
  function update(next: DeskData) {
    saveDesk(next);
  }
  async function savePanel(e: React.FormEvent) {
    e.preventDefault();
    await execute(async () => {
      if (panel === "create") {
        const result = await deskWrite<{ id: string }>(
          "/rooms",
          { name, goal },
          createKey.current,
        );
        setPanel(null);
        nav("/desk/" + result.id);
        return;
      }
      if (panel === "settings" && roomId && room) {
        await deskWrite("/rooms/" + roomId + "/settings", {
          name,
          goal,
          expected_version: room.version,
        });
        await refresh();
      }
      if (panel === "invite" && roomId) {
        await deskWrite("/rooms/" + roomId + "/invite", { handle });
        setHandle("");
        await refresh();
        setNotice("Invitation sent. The recipient must accept before joining.");
        return;
      }
      if (panel === "note") {
        if (roomId) {
          if (editItem)
            await deskWrite("/rooms/" + roomId + "/items/" + editItem.id, {
              title: note.title,
              body: note.body,
              question_id: note.question_id || null,
              expected_version: editItem.version,
              delete: false,
            });
          else
            await deskWrite(
              "/rooms/" + roomId + "/items",
              { kind: "note", title: note.title, body: note.body, question_id: note.question_id || null },
              createKey.current,
            );
          await loadItems();
        } else
          update({
            ...desk,
            notes: [note, ...desk.notes.filter((n) => n.id !== note.id)],
          });
      }
      if (panel === "share") {
        if (roomId) {
          const payload = {
            kind: shareKind,
            question_id: selected?.id || null,
            title: shareKind === "update" ? "Study update" : "",
            body: shareNote,
          };
          const serialized = JSON.stringify(payload);
          if (shareKey.current.payload !== serialized)
            shareKey.current = { payload: serialized, key: uid() };
          await deskWrite(
            "/rooms/" + roomId + "/items",
            payload,
            shareKey.current.key,
          );
          await loadItems();
        } else if (selected) {
          update({
            ...desk,
            saved: [...new Set([selected.id, ...desk.saved])].slice(0, 500),
          });
          setTab("bookmarks");
        }
      }
      if (panel === "message" && messageEdit && roomId) {
        await deskWrite("/rooms/" + roomId + "/messages/" + messageEdit.id, {
          body: messageBody,
          expected_version: messageEdit.version,
          delete: false,
        });
        await loadChat();
      }
      if (panel === "report") {
        if (reportTarget.kind === "invite")
          await deskWrite("/invites/" + reportTarget.id + "/report", {
            reason: reportReason,
          });
        else if (roomId)
          await deskWrite("/rooms/" + roomId + "/report", {
            target_kind: reportTarget.kind,
            target_id: reportTarget.id || roomId,
            reason: reportReason,
          });
        setNotice(
          "Report saved for the site owner. Only the reported content is included.",
        );
      }
      setPanel(null);
    });
  }
  async function send(e: React.FormEvent) {
    e.preventDefault();
    if (!roomId || !chat.trim()) return;
    await execute(async () => {
      const serialized = JSON.stringify([chat,chatNote?.id || null]);
      if (chatKey.current.payload !== serialized)
        chatKey.current = { payload: serialized, key: uid() };
      await deskWrite(
        "/rooms/" + roomId + "/messages",
        { body: chat, ...(chatNote ? {note_id:chatNote.id} : {}) },
        chatKey.current.key,
      );
      setChat(""); setChatNote(null);
      await loadChat();
    });
  }
  function shareMistake(qid: string) {
    if (!roomId) {
      setExpanded(qid);
      return;
    }
    void execute(async () => {
      const q = await getQuestion(qid);
      setSelected(q);
      setShareKind("mistake");
      setShareNote("");
      setPanel("share");
    });
  }
  function exportPersonal() {
    window.open('/api/me/data-export?'+new URLSearchParams({user_id:sync.userId}), '_blank', 'noopener,noreferrer');
  }
  if (sync.loading)
    return (
      <div role="status" className="desk-v3">
        <p className="desk-v3-label">Study desk</p>
        <h1 className="desk-v3-heading mt-2">Opening your desk…</h1>
      </div>
    );
  if (roomId && !room && !loading && error)
    return (
      <main className="desk-v3" data-desk-room={!!room}>
        <h1 className="desk-v3-heading">This desk is unavailable</h1>
        <p role="alert" className="mt-3 text-sm text-secondary">
          {error}
        </p>
        <Link to="/desk" className={B + " mt-4"}>
          Return to my private study
        </Link>
      </main>
    );
  return (
    <main className="desk-v3" data-desk-room={!!room}>
      <section className="desk-hero">
        <div className="desk-hero-top">
          <div className="desk-hero-id">
            <DeskBrassClock size={60} />
            <div className="desk-hero-copy">
              <div className="desk-hero-kicker-row">
                <span className="desk-hero-eyebrow">
                  {room ? "Shared desk · Partners only · up to 6" : "Study desk · Private"}
                </span>
                <span
                  role="status"
                  className={
                    "desk-sync-pill" +
                    (sync.status === "saved" ? " is-saved" : "")
                  }
                >
                  {sync.status === "saved"
                    ? "✓ Saved"
                    : sync.status === "saving"
                      ? "Saving…"
                      : registered
                        ? "Account desk"
                        : sync.userId
                          ? "Browser only"
                          : "Offline"}
                </span>
              </div>
              <h1 className="desk-hero-title">
                {room?.name || "Your study desk"}
              </h1>
              <p className="desk-hero-sub">
                {room
                  ? `You and ${Math.max(0, room.members.length - 1)} ${room.members.length === 2 ? "partner" : "partners"} · invite-only circle`
                  : "Private notes, saved questions, interactive desk & focus timer"}
              </p>
            </div>
          </div>

          <div className="desk-hero-actions">
            <select
              aria-label="Choose your study workspace"
              value={roomId || ""}
              onChange={(e) =>
                nav(e.target.value ? "/desk/" + e.target.value : "/desk")
              }
              className="desk-workspace-select"
            >
              <option value="">My private study</option>
              {list?.items.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => open("share")}
              className="cr-primary-btn"
            >
              {room ? "Share from bank" : "+ Save question"}
            </button>
            <button
              type="button"
              onClick={() => setTab("session")}
              className="cr-glass-btn"
            >
              Focus timer
            </button>
            <details className="desk-tools-drop">
              <summary className="cr-glass-btn">Tools ⌄</summary>
              <div className="desk-tools-menu">
                <button type="button" onClick={() => void refresh()}>
                  Refresh desk
                </button>
                {registered && (
                  <button type="button" onClick={() => open("create")}>
                    + New shared desk
                  </button>
                )}
                {room && (
                  <button type="button" onClick={() => open("settings")}>
                    Desk settings &amp; members
                  </button>
                )}
                {registered ? (
                  <>
                    <button
                      type="button"
                      onClick={() =>
                        confirm(
                          "Import this browser’s plan?",
                          "This copies browser goals, checklist, saved questions and notes into your signed-in account. Check that they belong to you.",
                          async () => {
                            importGuestDesk();
                            await flushDesk();
                          },
                        )
                      }
                    >
                      Import browser desk
                    </button>
                    <button type="button" onClick={exportPersonal}>
                      Export data (JSON)
                    </button>
                    <a
                      target="_blank"
                      rel="noreferrer"
                      href={
                        "/api/me/desk-notes-print?" +
                        new URLSearchParams({
                          user_id: sync.userId,
                          ...(roomId ? { desk_id: roomId } : {}),
                        })
                      }
                    >
                      {roomId ? "Print room notes (PDF)" : "Print notes (PDF)"}
                    </a>
                  </>
                ) : (
                  <Link to="/login">Sign in to sync &amp; share →</Link>
                )}
                {!room && (
                  <>
                    <Link to="/home">Today’s plan on Home →</Link>
                    <Link to="/practice">Practice &amp; timed runs →</Link>
                    <Link to="/profile#mastery">Mastery map →</Link>
                  </>
                )}
              </div>
            </details>
          </div>
        </div>

        <div className="desk-hero-bar">
          <div className="desk-members-strip">
            {members.map((m, i) => (
              <button
                key={m.user_id}
                type="button"
                onClick={() => setActiveMember(m.user_id)}
                className={
                  "desk-member-chip" +
                  (focused?.user_id === m.user_id ? " is-active" : "")
                }
              >
                <UserAvatar
                  look={m.avatar}
                  initials={m.is_you ? "You" : m.handle}
                  size={24}
                />
                <span>
                  {m.is_you ? "You" : m.handle}
                  {m.blocked ? " · blocked" : ""}
                </span>
                <i
                  aria-hidden="true"
                  style={{ background: COLORS[i % COLORS.length] }}
                />
              </button>
            ))}
            <button
              type="button"
              onClick={() => open(room ? "invite" : "create")}
              className="desk-member-chip is-invite"
            >
              <span>+</span>
              <span>
                {room
                  ? `Invite · ${Math.max(0, 6 - members.length)} open`
                  : "Start shared desk"}
              </span>
            </button>
          </div>

          <div className="desk-hero-right-stats">
            <div className="desk-kpi-strip" aria-label="Desk quick summary">
              <span><b>{desk.saved.length}</b> saved</span>
              <span><b>{desk.notes.length}</b> notes</span>
              <span><b>{overview.stats.week_answers}</b> this week</span>
            </div>
            <button
              type="button"
              aria-pressed={showDiagram}
              onClick={toggleDiagram}
              className="desk-diagram-toggle"
            >
              {showDiagram ? "Hide room view" : "Show room view"}
            </button>
          </div>
        </div>
      </section>

      {sync.error && (
        <FlashBanner
          kind="error"
          title="Sync conflict"
          message={`${sync.error} Your local edits are retained in this browser.`}
          actionLabel="Retry save"
          onAction={() => void flushDesk()}
          extra={
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                className="finna-flash-subbtn"
                onClick={() => void execute(() => reloadAccountDesk(false))}
              >
                Load account version
              </button>
              <button
                type="button"
                className="finna-flash-subbtn"
                onClick={() =>
                  confirm(
                    "Keep this browser’s version?",
                    "This replaces the latest account desk with the local edits shown here. Your notes and saved questions on another device may differ.",
                    () => reloadAccountDesk(true),
                  )
                }
              >
                Keep local edits
              </button>
            </div>
          }
        />
      )}
      {error && (
        <FlashBanner
          kind="error"
          title="Desk error"
          message={error}
          actionLabel="Refresh"
          onAction={() => void refresh()}
          onDismiss={() => setError("")}
        />
      )}
      {notice && (
        <FlashBanner
          kind="success"
          title="Saved"
          message={notice}
          onDismiss={() => setNotice("")}
        />
      )}

      {list?.invitations.length ? (
        <section className="desk-invite-banner">
          <h2 className="font-display text-lg">Your desk invitations</h2>
          {list.invitations.map((i) => (
            <div key={i.id} className="mt-3 border-t border-hairline pt-3">
              <p className="text-sm">
                <b>@{i.sender}</b> invited you to <b>{i.name}</b>
              </p>
              <p className="mt-1 text-xs text-secondary">
                Current shared resources become visible on joining. Personal
                scores and mistakes stay private until you choose otherwise.
                Expires {new Date(i.expires_at).toLocaleDateString("en-IN")}.
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  disabled={busy}
                  className="cr-primary-btn"
                  onClick={() =>
                    void execute(async () => {
                      await deskWrite("/invites/" + i.id, {
                        decision: "accept",
                      });
                      nav("/desk/" + i.desk_id);
                      await refresh();
                    })
                  }
                >
                  Accept invitation
                </button>
                <button
                  disabled={busy}
                  className="finna-st-btn"
                  onClick={() =>
                    void execute(async () => {
                      await deskWrite("/invites/" + i.id, {
                        decision: "decline",
                      });
                      setList(await getRooms());
                    })
                  }
                >
                  Decline
                </button>
                <button
                  className="finna-st-btn"
                  onClick={() => {
                    setReportTarget({ kind: "invite", id: i.id });
                    setReportReason("");
                    setPanel("report");
                  }}
                >
                  Report
                </button>
                {i.sender_id && (
                  <button
                    className="finna-st-btn"
                    onClick={() =>
                      confirm(
                        "Block this inviter?",
                        "The invitation will be cancelled and further invitations will be prevented.",
                        async () => {
                          await reviewRequest(
                            "/creators/" + i.sender_id + "/block",
                            { enabled: true },
                          );
                          setList(await getRooms());
                        },
                      )
                    }
                  >
                    Block inviter
                  </button>
                )}
              </div>
            </div>
          ))}
        </section>
      ) : null}

      {showDiagram && (
        <div className="desk-v3-scene">
          <div className="desk-v3-scene-canvas">
            <DeskScene
              active={tab}
              personal={!room}
              pick={(key) => {
                if (!room && key === "practice") nav("/practice");
                else if (!room && key === "mistakes") nav("/revise?tab=queue");
                else if (!room && key === "progress") nav("/profile#mastery");
                else if (!room && key === "bookmarks") setTab("shared");
                else setTab(key);
              }}
              members={sceneMembers}
              focus={focused?.user_id || ""}
              pickMember={setActiveMember}
              invite={() => open(room ? "invite" : "create")}
            />
          </div>
          <div className="desk-scene-foot">
            <div className="desk-scene-legend">
              {members.map((m, i) => (
                <span key={m.user_id} className="desk-scene-person">
                  <i
                    aria-hidden="true"
                    style={{ background: COLORS[i % COLORS.length] }}
                  />
                  <b>{m.is_you ? "You" : m.handle}</b>
                  <small>
                    {m.blocked
                      ? "blocked"
                      : m.focusing
                        ? "focus active"
                        : room
                          ? "member"
                          : "solo mode"}
                  </small>
                </span>
              ))}
            </div>
            <span className="desk-scene-tip">
              Click any item on the desk to jump straight to that tool
            </span>
          </div>
        </div>
      )}

      {loading && (
        <p role="status" className="mt-4 text-sm text-muted">
          Loading your study activity…
        </p>
      )}
      <div className="desk-v3-columns">
        <section className="desk-v3-main">
          <div
            className="desk-v3-tabs desk-tabs-v4"
            role="group"
            aria-label="Desk content sections"
          >
            {tabs.map(([id, label, color]) => (
              <button
                key={id}
                type="button"
                aria-pressed={tab === id}
                onClick={() => setTab(id)}
                className={"desk-tab-pill" + (tab === id ? " is-active" : "")}
              >
                <span
                  className="desk-tab-dot"
                  style={{ background: tab === id ? "#FFFFFF" : color }}
                />
                {label}
              </button>
            ))}
          </div>
          <div className="desk-main-surface">
          {roomId && params.get('note') && <Suspense fallback={<Empty>Opening shared note…</Empty>}>
            <DeskLinkedNote key={sync.userId+":"+roomId+":"+params.get('note')} deskId={roomId} noteId={params.get('note')!} />
          </Suspense>}
          {tab === "practice" && (
            <Suspense fallback={<Empty>Loading room practice…</Empty>}>
              {room ? (
                <>
                  {sync.privateEnabled && <DeskPracticeSessions key={sync.userId + ":" + room.id} deskId={room.id} />}
                  <DeskPractice
                    questions={items.filter((i) => i.question_id).map((i) => i.question_id!)}
                    subject={desk.goalSubject}
                    onAnswered={() => void refresh()}
                  />
                </>
              ) : (
                <section className="rounded-xl border border-hairline bg-card p-5">
                  <h2 className="text-lg font-bold text-ink">Solo practice lives in Practice</h2>
                  <p className="mt-2 text-sm text-secondary">
                    Use your personal Desk for notes, bookmarks and Pomodoro focus sessions. Open Practice for untimed runs or timed mocks.
                  </p>
                  <Link to="/practice" className={B + " mt-4 bg-ink text-paper"}>
                    Open Practice →
                  </Link>
                </section>
              )}
            </Suspense>
          )}
          {tab === "session" && (
            <>
            <DeskFocus
              sessions={overview.sessions}
              serverTime={overview.server_time}
              registered={registered}
              deskId={roomId}
              onChange={() => void refresh()}
            />
            {room && sync.privateEnabled && <section aria-label="Room focus board" className="my-4 rounded-panel border border-hairline bg-card p-4 sm:p-5">
              <h2 className="text-base font-bold">Focusing together</h2>
              <p className="mt-2 text-sm text-secondary">Members who choose to share their current server-timed focus session. This board earns no XP or points.</p>
              {members.some(m => m.focusing && !m.blocked) ? <ul className="mt-3 flex flex-wrap gap-3">
                {members.filter(m => m.focusing && !m.blocked).map(m => <li key={m.user_id} className="flex min-h-11 min-w-0 max-w-full items-center gap-2 text-sm">
                  <UserAvatar look={m.avatar} initials={m.is_you ? "You" : m.handle} size={28} />
                  <span className="min-w-0 break-words"><b>{m.is_you ? "You" : m.handle}</b> · focusing now</span>
                </li>)}
              </ul> : <p className="mt-3 text-sm">No current focus sessions are shared with you.</p>}
              {!room.sharing.times && <p className="mt-2 text-sm text-secondary">Your focus session stays private. Use “My desk focus session” in What you share to opt in.</p>}
            </section>}
            </>
          )}
          {tab === "progress" && (
            <>
              {room && sync.privateEnabled && <DeskWeeklyGoal key={sync.userId + ":" + room.id} deskId={room.id} />}
              <div className="desk-v3-subhead">
                <h2>{room ? "Desk progress" : "Your progress"}</h2>
                <span className="text-sm text-secondary">
                  {room
                    ? "Only members who choose to share"
                    : "Private to your account"}
                </span>
              </div>
              {room && (
                <div className="mt-5 grid gap-2">
                  {members.map((m) => (
                    <div
                      key={m.user_id}
                      className="flex justify-between gap-3 border-b border-hairline py-3 text-sm"
                    >
                      <span>{m.is_you ? "You" : m.handle}</span>
                      <span>
                        {m.progress
                          ? `${m.progress.answered} answers · ${acc(m.progress.answered, m.progress.correct)} accuracy`
                          : "Progress private"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              <h3 className="mt-6 border-b border-hairline pb-2 font-display text-lg">
                Your subjects
              </h3>
              {overview.subjects.map((s) => (
                <div key={s.subject} className="border-b border-hairline2 py-3">
                  <div className="flex justify-between text-sm">
                    <span>{s.subject}</span>
                    <span className="font-mono text-xs">
                      {acc(s.answered, s.correct)}
                    </span>
                  </div>
                  <div className="mt-2 h-[5px] rounded-full bg-[#E8DFCC]">
                    <div
                      className="h-full rounded-full bg-[#3F8350]"
                      style={{
                        width:
                          (s.answered ? (s.correct / s.answered) * 100 : 0) +
                          "%",
                      }}
                    />
                  </div>
                </div>
              ))}
              {!overview.subjects.length && (
                <Empty>
                  Subject progress appears as you practise classified questions.
                </Empty>
              )}

            </>
          )}
          {(tab === "shared" ||
            tab === "notes" ||
            tab === "bookmarks" ||
            tab === "mistakes") && (
            <>
              <div className="desk-v3-subhead">
                <h2>
                  {tab === "shared"
                    ? room
                      ? "Shared from the bank"
                      : "Saved questions"
                    : tab === "notes"
                      ? room
                        ? "Shared notes"
                        : "Your notes"
                      : tab === "bookmarks"
                        ? "Bookmarks"
                        : "Mistakes wall"}
                </h2>
                <button
                  type="button"
                  className="desk-sub-cta"
                  onClick={() =>
                    tab === "notes" ? open("note") : open("share")
                  }
                >
                  {tab === "notes"
                    ? "+ Add a note"
                    : room
                      ? "+ Share a question"
                      : "+ Save a question"}
                </button>
              </div>
              {roomId ? (
                <>
                  {tab === "shared" && sync.privateEnabled && <label className="mt-3 block text-sm font-semibold">Review circle
                    <select className="desk-v3-input mt-2" value={discussionFilter}
                      onChange={e => setDiscussionFilter(e.target.value as typeof discussionFilter)}>
                      <option value="all">All shared questions</option>
                      <option value="needed">Needs discussion</option>
                      <option value="resolved">Resolved discussions</option>
                    </select>
                  </label>}
                  <div className="mt-3">
                    {items.map((item) => (
                      <article
                        key={item.id}
                        className={
                          "border-b border-hairline2 py-[18px] " +
                          (tab === "mistakes" ? "desk-v3-mistake mt-4" : "")
                        }
                      >
                        <div className="flex flex-wrap items-center gap-2 text-xs text-secondary">
                          <span className="rounded-pill bg-community-soft px-2 py-1 text-xs uppercase text-community-dark">
                            {item.kind}
                          </span>
                          {sync.privateEnabled && item.discussion_state && item.discussion_state !== "none" && <span className="font-semibold">{item.discussion_state === "needed" ? "Needs discussion" : "Discussion resolved"}</span>}
                          <span>
                            Shared by{" "}
                            <b>
                              {item.author_id === myId ? "You" : item.author}
                            </b>{" "}
                            ·{" "}
                            {new Date(item.created_at).toLocaleDateString(
                              "en-IN",
                            )}
                          </span>
                        </div>
                        {item.body && (
                          <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-relaxed text-secondary">
                            {item.body}
                          </p>
                        )}
                        {(!item.question_id || tab !== "shared") && (
                          <h3 className="mt-3 font-display text-lg leading-snug">
                            {item.kind === 'note' ? item.title || 'Shared note' : item.question || item.title}
                          </h3>
                        )}
                        <div className="mt-3 flex flex-wrap gap-2">
                          {sync.privateEnabled && item.question_id && ["question", "mistake"].includes(item.kind) &&
                            <DeskDiscussionButton key={myId + ":" + roomId + ":" + item.id + ":" + tab + ":" + discussionFilter}
                              deskId={roomId} item={item} onChange={() => loadItems()} />}
                          {item.question_id && tab !== "shared" && (
                            <button
                              className={B}
                              onClick={() =>
                                setExpanded(expanded === item.id ? "" : item.id)
                              }
                            >
                              {expanded === item.id
                                ? "Close practice"
                                : "Practise this question"}
                            </button>
                          )}
                          {item.kind === "note" && <button className={B} onClick={() => {
                            setChatNote({id:item.id,title:item.title || 'Shared note'});
                            setNotice('Shared note attached to your next chat message.');
                          }}>Link in chat</button>}
                          {item.author_id === myId && item.kind === "note" && (
                            <button
                              className={B}
                              onClick={() => {
                                setEditItem(item);
                                setNote({
                                  id: item.id,
                                  title: item.title,
                                  body: item.body,
                                  subject: "",
                                  question_id: item.question_id,
                                });
                                setPanel("note");
                              }}
                            >
                              Edit note
                            </button>
                          )}
                          {(item.author_id === myId || owner) && (
                            <button
                              className={B}
                              onClick={() =>
                                confirm(
                                  "Remove this shared item?",
                                  "It will leave the desk. A reported version may be retained for moderation.",
                                  async () => {
                                    await deskWrite(
                                      "/rooms/" + roomId + "/items/" + item.id,
                                      {
                                        expected_version: item.version,
                                        title: item.title,
                                        body: item.body,
                                        delete: true,
                                      },
                                    );
                                    await loadItems();
                                  },
                                )
                              }
                            >
                              Remove
                            </button>
                          )}
                          <button
                            className={B}
                            onClick={() => {
                              setReportTarget({ kind: "item", id: item.id });
                              setReportReason("");
                              setPanel("report");
                            }}
                          >
                            Report
                          </button>
                        </div>
                        {item.question_id &&
                          (tab === "shared" || expanded === item.id) && (
                            <div className="desk-shared-question mt-3">
                              <DeskQuestion
                                qid={item.question_id}
                                onAnswered={() => void refresh()}
                              />
                            </div>
                          )}
                      </article>
                    ))}
                  </div>
                  {!items.length && (
                    <Empty>
                      {tab === "shared" && discussionFilter !== "all"
                        ? "No visible questions match this discussion filter."
                        : tab === "shared"
                        ? "Questions shared with a note about why they matter will appear here."
                        : tab === "notes"
                          ? "Add a note for the people on this desk."
                          : tab === "mistakes"
                            ? "Members can deliberately share a mistake after turning on mistake sharing."
                            : "No bank bookmarks have been shared yet."}
                    </Empty>
                  )}
                  {cursor && (
                    <button
                      className={B + " mt-3"}
                      onClick={() => void execute(() => loadItems(cursor))}
                    >
                      More shared items
                    </button>
                  )}
                </>
              ) : tab === "notes" ? (
                <div className="mt-3">
                  {desk.notes.map((n) => (
                    <article
                      key={n.id}
                      className="flex flex-wrap justify-between gap-3 border-b border-hairline2 py-4"
                    >
                      <div className="min-w-0 flex-1">
                        <h3 className="font-display text-lg">{n.title}</h3>
                        <p className="mt-1 whitespace-pre-wrap break-words text-sm leading-relaxed text-secondary">
                          {n.body}
                        </p>
                        {n.question_id && <Link className="mt-2 block min-h-11 break-all text-sm text-link underline" to={'/bank/'+encodeURIComponent(n.question_id)}>Question: {n.question_id}</Link>}
                        <span className="mt-2 inline-block font-mono text-xs uppercase text-muted">
                          {n.subject || "Private note"}
                        </span>
                      </div>
                      <div className="flex items-start gap-2">
                        <button
                          className={B}
                          onClick={() => {
                            setNote(n);
                            setPanel("note");
                          }}
                        >
                          Edit
                        </button>
                        <button
                          className={B}
                          onClick={() =>
                            confirm(
                              "Delete this private note?",
                              "Export your desk first if you need a copy.",
                              async () =>
                                update({
                                  ...desk,
                                  notes: desk.notes.filter(
                                    (x) => x.id !== n.id,
                                  ),
                                }),
                            )
                          }
                        >
                          Delete
                        </button>
                      </div>
                    </article>
                  ))}
                  {!desk.notes.length && (
                    <Empty>
                      Your notes stay private. Add your first revision note.
                    </Empty>
                  )}
                </div>
              ) : tab === "mistakes" ? (
                <>
                  <div className="mt-5 grid gap-[18px] sm:grid-cols-2">
                    {overview.mistakes.map((m, i) => (
                      <article
                        key={m.id}
                        className="desk-v3-mistake"
                        style={{ transform: `rotate(${i % 2 ? 1 : -1}deg)` }}
                      >
                        <div className="desk-v3-label !text-[#9E2A1F]">
                          Your revision · missed {m.times_wrong} times
                        </div>
                        <h3 className="mt-2 font-display text-md leading-snug">
                          {m.question}
                        </h3>
                        <button
                          className={B + " mt-3 bg-card"}
                          onClick={() =>
                            setExpanded(expanded === m.id ? "" : m.id)
                          }
                        >
                          Review this question
                        </button>
                        {room && (
                          <button
                            className={B}
                            onClick={() => shareMistake(m.id)}
                          >
                            Share deliberately
                          </button>
                        )}
                      </article>
                    ))}
                  </div>
                  {expanded &&
                    overview.mistakes.some((m) => m.id === expanded) && (
                      <div className="mt-5">
                        <DeskQuestion
                          qid={expanded}
                          onAnswered={() => void refresh()}
                        />
                      </div>
                    )}
                  {!overview.mistakes.length && (
                    <Empty>
                      No missed questions are waiting here. Your next practice
                      answers will build this revision list.
                    </Empty>
                  )}
                </>
              ) : (
                <>
                  <div className="mt-4">
                    {previews.map((q) => (
                      <div
                        key={q.id}
                        className="border-b border-hairline2 py-4"
                      >
                        <div className="flex flex-wrap gap-2 font-mono text-xs uppercase text-muted">
                          <span>{q.subject || "Question bank"}</span>
                          <span>
                            {q.type === "descriptive"
                              ? "Descriptive"
                              : q.answer_source === "none"
                                ? "No key yet"
                                : q.answer_source + " answer"}
                          </span>
                        </div>
                        <h3 className="mt-2 font-display text-lg leading-snug">
                          {q.question}
                        </h3>
                        <div className="mt-3 flex flex-wrap gap-2">
                          <button
                            className={B}
                            onClick={() =>
                              setExpanded(expanded === q.id ? "" : q.id)
                            }
                          >
                            {expanded === q.id
                              ? "Close question"
                              : "Open on this desk"}
                          </button>
                          <button
                            className={B}
                            onClick={() =>
                              update({
                                ...desk,
                                saved: desk.saved.filter((id) => id !== q.id),
                              })
                            }
                          >
                            Remove bookmark
                          </button>
                        </div>
                        {expanded === q.id && (
                          <DeskQuestion
                            qid={q.id}
                            onAnswered={() => void refresh()}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                  {!desk.saved.length && (
                    <Empty>
                      Save questions from the bank or use Save a question above.
                      You can answer and discuss them here.
                    </Empty>
                  )}
                  {desk.saved.length > 20 && (
                    <nav
                      className="mt-4 flex justify-between"
                      aria-label="Saved question pages"
                    >
                      <button
                        disabled={!savedPage}
                        className={B}
                        onClick={() => setSavedPage(savedPage - 1)}
                      >
                        Previous
                      </button>
                      <span className="self-center text-xs text-muted">
                        {savedPage + 1} / {Math.ceil(desk.saved.length / 20)}
                      </span>
                      <button
                        disabled={(savedPage + 1) * 20 >= desk.saved.length}
                        className={B}
                        onClick={() => setSavedPage(savedPage + 1)}
                      >
                        Next
                      </button>
                    </nav>
                  )}
                </>
              )}
            </>
          )}
          </div>
        </section>
        <aside className="desk-v3-rail">
          <DeskCalendar key={sync.userId+':'+(roomId||'personal')} deskId={roomId || undefined}/>
          {room && <>
          <article className="desk-rail-card desk-rail-profile">
            <div className="flex items-center gap-3">
              <UserAvatar look={focused?.avatar} initials={focused?.is_you?'You':focused?.handle||'S'} size={52}/>
              <div className="min-w-0">
                <h2 className="break-words font-display text-lg">
                  {focused?.is_you ? "Your desk profile" : focused?.handle}
                </h2>
                <p className="text-xs text-secondary">
                  {focused?.is_you
                    ? "Personal study stays private"
                    : focused?.blocked
                      ? "You have blocked this member"
                      : "Shared desk member"}
                </p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 border-t border-hairline2 pt-3">
              {[
                [
                  focused?.progress
                    ? acc(focused.progress.answered, focused.progress.correct)
                    : "Private",
                  "Accuracy",
                ],
                [
                  focused?.is_you ? overview.stats.week_answers : "—",
                  "This week",
                ],
                [focused?.is_you ? desk.saved.length : "—", "Saved"],
              ].map(([value, label]) => (
                <div key={String(label)}>
                  <p className="font-display text-lg">{value}</p>
                  <p className="text-xs text-secondary">{label}</p>
                </div>
              ))}
            </div>
            {focused?.is_you ? (
              <Link to="/profile" className={B + " mt-3"}>
                View your profile →
              </Link>
            ) : (
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  className={B}
                  onClick={() =>
                    confirm(
                      focused?.blocked
                        ? "Unblock this member?"
                        : "Block this member?",
                      "Their messages and shared items will be hidden from you. Both of you may remain members; you can also leave the desk.",
                      async () => {
                        await reviewRequest(
                          "/creators/" + focused?.user_id + "/block",
                          { enabled: !focused?.blocked },
                        );
                        await refresh();
                        await loadItems();
                        await loadChat();
                      },
                    )
                  }
                >
                  {focused?.blocked ? "Unblock" : "Block member"}
                </button>
              </div>
            )}
          </article>
          </>}
          <section className="desk-rail-card desk-rail-toolbox">
            <div className="desk-rail-eyebrow">
              {room ? "Private desk" : "Your toolbox"}
            </div>
            <h3 className="mt-1.5 font-display text-lg">
              {room
                ? "Study together, keep your own history"
                : "Keep your study things together"}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-secondary">
              {room
                ? "Questions and notes shared here are visible to members. Individual attempts, points and private notes stay in their own accounts."
                : "Save a question, write a private note or use the focus timer. Your daily plan stays on Home."}
            </p>
            <Link to="/home" className={B + " mt-3"}>Open Today on Home →</Link>
            {!room && (
              <p className="mt-3 text-xs text-secondary">
                Shared desks are created with Pro. Invited members join free.
              </p>
            )}
          </section>
          {room && (
            <section className="desk-rail-card">
              <h3 className="desk-rail-eyebrow border-b border-hairline pb-2">
                What you share
              </h3>
              {(
                [
                  ["progress", "Progress and accuracy"],
                  ["mistakes", "Mistakes I deliberately post"],
                  ["times", "My desk focus session"],
                ] as const
              ).map(([field, label]) => (
                <button
                  key={field}
                  role="switch"
                  aria-checked={room.sharing[field]}
                  disabled={busy}
                  onClick={() =>
                    void execute(async () => {
                      await deskWrite("/rooms/" + roomId + "/sharing", {
                        ...room.sharing,
                        [field]: !room.sharing[field],
                      });
                      await refresh();
                      await loadItems();
                    })
                  }
                  className="flex min-h-11 w-full items-center justify-between gap-3 border-b border-hairline2 py-2.5 text-left text-sm"
                >
                  <span>{label}</span>
                  <span
                    className={
                      "relative h-5 w-[34px] shrink-0 rounded-full transition-colors " +
                      (room.sharing[field] ? "bg-[#0A7D8C]" : "bg-[#CBD5E1]")
                    }
                  >
                    <span
                      className={
                        "absolute top-0.5 h-4 w-4 rounded-full bg-card transition-all " +
                        (room.sharing[field] ? "left-4" : "left-0.5")
                      }
                    />
                  </span>
                </button>
              ))}
              <p className="mt-2 text-xs leading-relaxed text-muted">
                Sharing starts off. Turning it off hides earlier shared mistakes
                or updates. It never posts an answer automatically.
              </p>
            </section>
          )}
          <section className="desk-rail-card">
            <div className="desk-rail-eyebrow border-b border-hairline pb-2">
              Desk chat
            </div>
            {room ? (
              <>
                <div className="desk-v3-chat mt-3">
                  {[...messages].reverse().map((m) => (
                    <div
                      key={m.id}
                      className={
                        "max-w-[92%] " +
                        (m.author_id === myId ? "self-end" : "self-start")
                      }
                    >
                      <div className="mb-1 text-xs font-semibold text-secondary">
                        {m.author_id === myId ? "You" : m.author}
                      </div>
                      <p
                        className={
                          "desk-chat-bubble " +
                          (m.author_id === myId ? "is-me" : "is-them")
                        }
                      >
                        {m.body}
                        {m.note_id && <Link className="mt-2 block min-h-11 break-words underline" to={'/desk/'+roomId+'?'+new URLSearchParams({tab:'notes',note:m.note_id})}>Open note: {m.note_title || 'Shared note'}</Link>}
                      </p>
                      <div className="mt-1 flex gap-3 text-xs text-muted">
                        {m.author_id === myId && (
                          <button
                            className="min-h-9"
                            onClick={() => {
                              setMessageEdit(m);
                              setMessageBody(m.body);
                              setPanel("message");
                            }}
                          >
                            Edit
                          </button>
                        )}
                        {m.author_id === myId && (
                          <button
                            className="min-h-9"
                            onClick={() =>
                              confirm(
                                "Delete this message?",
                                "A reported version may be retained for moderation.",
                                async () => {
                                  await deskWrite(
                                    "/rooms/" + roomId + "/messages/" + m.id,
                                    {
                                      expected_version: m.version,
                                      body: m.body,
                                      delete: true,
                                    },
                                  );
                                  await loadChat();
                                },
                              )
                            }
                          >
                            Delete
                          </button>
                        )}
                        <button
                          className="min-h-9"
                          onClick={() => {
                            setReportTarget({
                              kind: "message",
                              id: String(m.id),
                            });
                            setReportReason("");
                            setPanel("report");
                          }}
                        >
                          Report
                        </button>
                      </div>
                    </div>
                  ))}
                  {!messages.length && (
                    <p className="py-4 text-sm text-muted">
                      No messages since you joined this desk.
                    </p>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button
                    className="min-h-9 text-xs text-link underline"
                    aria-pressed={room.sharing.muted}
                    onClick={() =>
                      void execute(async () => {
                        await deskWrite("/rooms/" + roomId + "/sharing", {
                          ...room.sharing,
                          muted: !room.sharing.muted,
                        });
                        await refresh();
                      })
                    }
                  >
                    {room.sharing.muted
                      ? "Unmute desk notifications"
                      : "Mute desk notifications"}
                  </button>
                  <button
                    className="min-h-9 text-xs text-link underline"
                    onClick={() => void execute(() => loadChat())}
                  >
                    Refresh chat
                  </button>
                  {chatCursor && (
                    <button
                      className="min-h-9 text-xs text-link underline"
                      onClick={() => void execute(() => loadChat(chatCursor))}
                    >
                      Earlier messages
                    </button>
                  )}
                </div>
                {chatNote && <div className="mt-3 rounded-panel border border-hairline bg-card p-3 text-sm break-words">
                  Shared note: {chatNote.title}<button className={B+' mt-2'} onClick={() => setChatNote(null)}>Remove note link</button>
                </div>}
                <form onSubmit={send} className="mt-3 flex gap-1.5">
                  <input
                    required
                    maxLength={2000}
                    value={chat}
                    onChange={(e) => setChat(e.target.value)}
                    placeholder="Message the desk"
                    aria-label="Message the desk"
                    className={I + " !min-h-11"}
                  />
                  <button
                    disabled={busy || !chat.trim()}
                    className="rounded-[6px] bg-[#B23A9A] px-[14px] text-sm font-semibold text-white disabled:opacity-50"
                  >
                    Send
                  </button>
                </form>
              </>
            ) : (
              <div className="py-4 text-sm leading-relaxed text-secondary">
                A shared desk opens chat for its accepted members. Your private
                study notes are yours alone.
                <button onClick={() => open("create")} className={B + " mt-3"}>
                  Create a private shared desk
                </button>
              </div>
            )}
          </section>
          {overview.questions.filter((q) => desk.recent.includes(q.id)).length >
            0 && (
            <section>
              <h3 className="desk-v3-label border-b border-hairline pb-2">
                Pick up where you left off
              </h3>
              {overview.questions
                .filter((q) => desk.recent.includes(q.id))
                .slice(0, 4)
                .map((q) => (
                  <Link
                    key={q.id}
                    to={"/bank/" + q.id}
                    className="block border-b border-hairline2 py-3 font-display text-md leading-snug"
                  >
                    {q.question}
                  </Link>
                ))}
            </section>
          )}
        </aside>
      </div>
      <section className="mt-12 border-t border-hairline pt-6">
        <div className="desk-v3-subhead">
          <h2>Your private desks</h2>
          <span className="text-sm text-secondary">
            Invitations only · no public listing
          </span>
        </div>
        <div className="mt-[18px] grid gap-[18px] md:grid-cols-2 lg:grid-cols-3">
          {list?.items.map((r, i) => (
            <Link
              key={r.id}
              to={"/desk/" + r.id}
              className="rounded-[8px] bg-[#EEDDEC] p-[18px] shadow-[inset_0_4px_0_#B23A9A]"
            >
              <span className="desk-v3-label !text-[#86226F]">
                {r.members} of 6 seats
              </span>
              <h3 className="mt-2 font-display text-lg">{r.name}</h3>
              <p className="mt-2 text-sm text-secondary">
                {r.goal || "A small private study space."}
              </p>
              <span
                className="mt-3 inline-block text-xs font-semibold"
                style={{ color: COLORS[i % 6] }}
              >
                Open desk →
              </span>
            </Link>
          ))}
          {!list?.items.length && (
            <div className="desk-v3-card">
              <h3 className="font-display text-lg">
                A seat for someone you know
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-secondary">
                Create a private desk or accept an invitation. No one can
                discover or join your desk automatically.
              </p>
              <button className={B + " mt-3"} onClick={() => open("create")}>
                Create a shared desk
              </button>
            </div>
          )}
        </div>
      </section>
      {panel && (
        <Modal
          title={
            panel === "create"
              ? "Create a private desk"
              : panel === "invite"
                ? "Invite someone you know"
                : panel === "share"
                  ? room
                    ? "Share from the bank"
                    : "Save a bank question"
                  : panel === "note"
                    ? room
                      ? "Shared desk note"
                      : "Your private note"
                    : panel === "settings"
                      ? "Desk settings & members"
                      : panel === "message"
                          ? "Edit your desk message"
                          : "Report desk content"
          }
          onClose={() => setPanel(null)}
        >
          {!registered && panel !== "note" && panel !== "share" ? (
            <p className="text-sm leading-relaxed">
              Sign in to create or join a shared desk and save your progress
              across devices.
              <Link to="/login" className={B + " mt-4 bg-ink text-paper"}>
                Sign in
              </Link>
            </p>
          ) : (
            <form onSubmit={savePanel} className="space-y-4">
              {(panel === "create" || panel === "settings") && (
                <>
                  <label className="block text-sm font-semibold">
                    Desk name
                    <input
                      required
                      minLength={3}
                      maxLength={100}
                      value={name}
                      disabled={panel === "settings" && !owner}
                      onChange={(e) => setName(e.target.value)}
                      className={I + " mt-2"}
                    />
                  </label>
                  <label className="block text-sm font-semibold">
                    Shared goal
                    <textarea
                      rows={3}
                      maxLength={500}
                      value={goal}
                      disabled={panel === "settings" && !owner}
                      onChange={(e) => setGoal(e.target.value)}
                      className={I + " mt-2"}
                    />
                  </label>
                  {panel === "create" && (
                    <p className="text-sm leading-relaxed text-secondary">
                      Up to six members. Pro creates the desk; invitations are
                      free to accept. Current shared resources become visible on
                      joining; chat begins at the joining time. Public discovery
                      and class desks are off.
                    </p>
                  )}
                  {panel === "create" && !list?.can_create && registered && (
                    <Link to="/plans" className={B}>
                      View Pro plans
                    </Link>
                  )}
                  {panel === "settings" && room && (
                    <>
                      <h3 className="font-display text-lg">Members</h3>
                      {room.members.map((m) => (
                        <div
                          key={m.user_id}
                          className="border-b border-hairline py-3"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                            <span>
                              @{m.handle}
                              {m.user_id === room.owner_id ? " · owner" : ""}
                              {m.is_you ? " · you" : ""}
                            </span>
                            {owner && !m.is_you && (
                              <div className="flex gap-2">
                                <button
                                  type="button"
                                  className={B}
                                  onClick={() =>
                                    confirm(
                                      "Remove this desk member?",
                                      "Their access ends immediately. They can only rejoin with a new accepted invitation.",
                                      async () => {
                                        await deskWrite(
                                          "/rooms/" + roomId + "/remove",
                                          { user_id: m.user_id },
                                        );
                                        await refresh();
                                      },
                                    )
                                  }
                                >
                                  Remove
                                </button>
                                <button
                                  type="button"
                                  className={B}
                                  onClick={() =>
                                    confirm(
                                      "Transfer desk ownership?",
                                      "The new owner needs Pro. You remain a member and can leave afterwards.",
                                      async () => {
                                        await deskWrite(
                                          "/rooms/" + roomId + "/transfer",
                                          { user_id: m.user_id },
                                        );
                                        await refresh();
                                      },
                                    )
                                  }
                                >
                                  Transfer
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {room.invitations.map((i) => (
                        <div
                          key={i.id}
                          className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm"
                        >
                          <span>Pending: @{i.handle}</span>
                          <button
                            type="button"
                            className={B}
                            onClick={() =>
                              void execute(async () => {
                                await deskWrite("/invites/" + i.id, {
                                  decision: "cancel",
                                });
                                await refresh();
                              })
                            }
                          >
                            Cancel invitation
                          </button>
                        </div>
                      ))}
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          className={B}
                          onClick={() => {
                            setReportTarget({ kind: "desk", id: roomId! });
                            setReportReason("");
                            setPanel("report");
                          }}
                        >
                          Report this desk
                        </button>
                        {owner ? (
                          <button
                            type="button"
                            className={B + " text-mypick"}
                            onClick={() =>
                              confirm(
                                "Close this private desk?",
                                "Every member loses access and pending invitations are cancelled. Shared content is retained for existing operational/report requirements.",
                                async () => {
                                  await deskWrite(
                                    "/rooms/" + roomId + "/close",
                                  );
                                  nav("/desk");
                                  setList(await getRooms());
                                },
                              )
                            }
                          >
                            Close desk
                          </button>
                        ) : (
                          <button
                            type="button"
                            className={B + " text-mypick"}
                            onClick={() =>
                              confirm(
                                "Leave this desk?",
                                "Access ends immediately. Shared resources you posted may remain for members; delete them first if you want to withdraw them.",
                                async () => {
                                  await deskWrite(
                                    "/rooms/" + roomId + "/leave",
                                  );
                                  nav("/desk");
                                  setList(await getRooms());
                                },
                              )
                            }
                          >
                            Leave desk
                          </button>
                        )}
                      </div>
                    </>
                  )}
                </>
              )}
              {panel === "invite" &&
                (room && !owner ? (
                  <p>Only the desk owner can invite another member.</p>
                ) : (
                  <>
                    <p className="text-sm leading-relaxed text-secondary">
                      Use the exact registered handle your friend gives you. The
                      invitation expires in seven days and must be accepted.
                      Email addresses are never searched or displayed.
                    </p>
                    <label className="block text-sm font-semibold">
                      Exact account handle
                      <input
                        required
                        minLength={2}
                        maxLength={100}
                        value={handle}
                        onChange={(e) =>
                          setHandle(e.target.value.replace(/^@/, ""))
                        }
                        className={I + " mt-2"}
                        placeholder="their-handle"
                        autoComplete="off"
                      />
                    </label>
                  </>
                ))}
              {panel === "note" && (
                <>
                  <label className="block text-sm font-semibold">
                    Note title
                    <input
                      required
                      maxLength={140}
                      value={note.title}
                      onChange={(e) =>
                        setNote({ ...note, title: e.target.value })
                      }
                      className={I + " mt-2"}
                    />
                  </label>
                  <label className="block text-sm font-semibold">
                    Your note
                    <textarea
                      required
                      rows={7}
                      maxLength={4000}
                      value={note.body}
                      onChange={(e) =>
                        setNote({ ...note, body: e.target.value })
                      }
                      className={I + " mt-2"}
                    />
                  </label>
                  <label className="block text-sm font-semibold">Canonical question ID (optional)
                    <input className={I+' mt-2'} maxLength={100} value={note.question_id || ''}
                      onChange={e => setNote({...note,question_id:e.target.value.trim() || null})}
                      placeholder="Copy the question ID from its bank link" />
                  </label>
                  {!room && (
                    <label className="block text-sm">
                      Subject (optional)
                      <input
                        maxLength={100}
                        value={note.subject}
                        onChange={(e) =>
                          setNote({ ...note, subject: e.target.value })
                        }
                        className={I + " mt-2"}
                      />
                    </label>
                  )}
                  <p className="text-xs text-muted">
                    {room
                      ? "Visible to accepted members of this desk. A reported version may be retained for moderation."
                      : "Private to your account. It is never shared automatically."}
                  </p>
                </>
              )}
              {panel === "share" && (
                <>
                  {room && (
                    <label className="block text-sm">
                      Share as
                      <select
                        value={shareKind}
                        onChange={(e) =>
                          setShareKind(e.target.value as typeof shareKind)
                        }
                        className={I + " mt-2"}
                      >
                        <option value="question">Question with context</option>
                        <option value="bookmark">Desk bookmark</option>
                        <option value="mistake">
                          A mistake I want help with
                        </option>
                        <option value="update">Study update</option>
                      </select>
                    </label>
                  )}
                  {shareKind !== "update" && (
                    <>
                      <label className="block text-sm font-semibold">
                        Find a question
                        <input
                          type="search"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                          className={I + " mt-2"}
                          placeholder="Search the question bank"
                          maxLength={160}
                        />
                      </label>
                      <div className="max-h-[270px] overflow-auto space-y-2">
                        {found.map((q) => (
                          <button
                            key={q.id}
                            type="button"
                            aria-pressed={selected?.id === q.id}
                            onClick={() => setSelected(q)}
                            className={
                              "w-full rounded-[8px] border p-3 text-left text-sm " +
                              (selected?.id === q.id
                                ? "border-community bg-community-soft"
                                : "border-hairline bg-card")
                            }
                          >
                            {q.question}
                            <small className="mt-1 block text-muted">
                              {q.taxonomy_subject || "Bank question"} ·{" "}
                              {q.first_year || q.last_year || "year unknown"}
                            </small>
                          </button>
                        ))}
                      </div>
                      {selected && (
                        <p className="rounded-[8px] bg-community-soft p-3 text-sm">
                          Selected: {selected.question}
                        </p>
                      )}
                    </>
                  )}
                  {room && (
                    <>
                      <label className="block text-sm font-semibold">
                        {shareKind === "update"
                          ? "The update you choose to share"
                          : "Why are you sharing this?"}
                        <textarea
                          required
                          minLength={5}
                          maxLength={4000}
                          rows={3}
                          value={shareNote}
                          onChange={(e) => setShareNote(e.target.value)}
                          className={I + " mt-2"}
                        />
                      </label>
                      <p className="text-xs text-secondary">
                        Audience: members of {room.name}. Your actual answer,
                        score and private notes are not copied.{" "}
                        {shareKind === "mistake"
                          ? "Enable mistake sharing in What you share first."
                          : shareKind === "update"
                            ? "Enable progress sharing first."
                            : ""}
                      </p>
                    </>
                  )}
                </>
              )}
              {panel === "message" && (
                <label className="block text-sm font-semibold">
                  Your message
                  <textarea
                    required
                    minLength={1}
                    maxLength={2000}
                    rows={5}
                    value={messageBody}
                    onChange={(e) => setMessageBody(e.target.value)}
                    className={I + " mt-2"}
                  />
                </label>
              )}
              {panel === "report" && (
                <>
                  <p className="text-sm leading-relaxed text-secondary">
                    The site owner receives the selected content and your
                    explanation. They do not receive access to browse your
                    private desk.
                  </p>
                  <label className="block text-sm font-semibold">
                    What happened?
                    <textarea
                      required
                      minLength={10}
                      maxLength={2000}
                      rows={4}
                      value={reportReason}
                      onChange={(e) => setReportReason(e.target.value)}
                      className={I + " mt-2"}
                    />
                  </label>
                </>
              )}
              {(panel === "settings" && !owner) ||
              (panel === "invite" && !owner) ? null : (
                <button
                  disabled={
                    busy ||
                    (panel === "create" &&
                      (!list?.can_create || !list.enabled)) ||
                    (panel === "share" && shareKind !== "update" && !selected)
                  }
                  className={B + " bg-ink text-paper"}
                >
                  {busy
                    ? "Saving…"
                    : panel === "invite"
                      ? "Send invitation"
                      : panel === "create"
                        ? "Create desk"
                        : panel === "share"
                          ? room
                            ? "Share with this desk"
                            : "Save question"
                          : panel === "report"
                            ? "Send report"
                            : "Save"}
                </button>
              )}
              {error && (
                <p role="alert" className="text-sm text-mypick">
                  {error}
                </p>
              )}
              {notice && (
                <p role="status" className="text-sm text-correct-dark">
                  {notice}
                </p>
              )}
            </form>
          )}
        </Modal>
      )}
      {confirmation && (
        <Modal title={confirmation.title} onClose={() => setConfirmation(null)}>
          <p className="text-sm leading-relaxed text-secondary">
            {confirmation.text}
          </p>
          <div className="mt-5 flex gap-2">
            <button
              className={B + " bg-ink text-paper"}
              disabled={busy}
              onClick={() =>
                void execute(async () => {
                  await confirmation.run();
                  setConfirmation(null);
                })
              }
            >
              {busy ? "Saving…" : "Confirm"}
            </button>
            <button className={B} onClick={() => setConfirmation(null)}>
              Cancel
            </button>
          </div>
          {error && (
            <p role="alert" className="mt-3 text-sm text-mypick">
              {error}
            </p>
          )}
        </Modal>
      )}
    </main>
  );
}

import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { accountGeneration } from "../lib/accountContext";
import { deskRead } from "../lib/desk";
import { deskWrite } from "../lib/studyDesks";
import type { GameRoom } from "../lib/games";

type Preview = { context_hash: string; available: number; required: number; can_start: boolean; capacity: number; round_seconds: number; message: string };
type Session = { id: string; state: string; players: number; capacity: number; context_hash: string; joined: boolean; can_join: boolean; questions: number; round_seconds: number };
type Data = { preview: Preview; sessions: Session[]; active_game: { id: string; state: string } | null };

export default function DeskPracticeSessions({ deskId }: { deskId: string }) {
  const navigate = useNavigate();
  const [data, setData] = useState<Data | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lifetime = useRef(0), active = useRef(false), generation = useRef(accountGeneration());
  const refreshRef = useRef<() => Promise<void>>(async () => {});
  const startKey = useRef<{ hash: string; key: string } | null>(null);
  const valid = () => active.current && generation.current === accountGeneration();
  useEffect(() => {
    active.current = true; ++lifetime.current; generation.current = accountGeneration();
    setData(null); setError(""); setBusy(false); startKey.current = null;
    let sequence = 0;
    async function refresh() {
      const run = ++sequence;
      try {
        const next = await deskRead<Data>(`/rooms/${deskId}/practice`);
        if (valid() && run === sequence) { setData(next); setError(""); }
      } catch (e) {
        if (valid() && run === sequence) { setData(null); setError((e as Error).message); }
      }
    }
    refreshRef.current = refresh; void refresh();
    const visible = () => { if (document.visibilityState === "visible") void refresh(); };
    const reset = () => { active.current = false; ++lifetime.current; ++sequence; setData(null); setError(""); setBusy(false); startKey.current = null; };
    const timer = window.setInterval(visible, 5000);
    window.addEventListener("focus", visible);
    window.addEventListener("ism-auth-change", reset);
    window.addEventListener("ism-auth-expired", reset);
    return () => {
      active.current = false; ++lifetime.current; ++sequence;
      window.clearInterval(timer); window.removeEventListener("focus", visible);
      window.removeEventListener("ism-auth-change", reset); window.removeEventListener("ism-auth-expired", reset);
    };
  }, [deskId]);

  async function enter(session?: Session) {
    if (!valid() || busy || !data) return;
    const run = lifetime.current, current = () => valid() && run === lifetime.current;
    setBusy(true); setError("");
    try {
      let room: GameRoom;
      if (session) {
        room = await deskWrite<GameRoom>(`/rooms/${deskId}/practice/${session.id}/join`, { context_hash: session.context_hash });
      } else {
        const hash = data.preview.context_hash;
        if (startKey.current?.hash !== hash) startKey.current = { hash, key: crypto.randomUUID() };
        room = await deskWrite<GameRoom>(`/rooms/${deskId}/practice`, { preview_hash: hash, request_key: startKey.current.key });
      }
      if (current()) navigate(`/games/${room.id}`);
    } catch (e) {
      if (current()) { setError((e as Error).message); setData(null); }
    } finally { if (current()) setBusy(false); }
  }

  return <section aria-label="Synchronized Desk practice" className="mb-5 min-w-0 rounded-panel border border-hairline bg-card p-4 sm:p-5">
    <div className="flex flex-wrap items-center justify-between gap-2">
      <h2 className="text-lg font-bold">Practice together</h2>
      <button className="desk-v3-button" disabled={busy} onClick={() => { if (valid()) void refreshRef.current(); }}>Refresh sessions</button>
    </div>
    <p className="mt-2 text-sm text-secondary">The same 10 questions, 25 seconds each, for 2–4 members of this private Desk. Everyone marks Ready before the host starts.</p>
    <p className="mt-2 text-sm text-secondary">Uses questions and bookmarks deliberately shared here. Private saves, notes and shared mistakes stay out of the set. Normal game discovery and Play limits apply; there is no extra Desk reward.</p>
    {error && <p role="alert" className="mt-3 break-words text-sm text-secondary">{error} Refresh sessions to check whether your session was created before trying again.</p>}
    {!data && !error && <p role="status" className="mt-3 text-sm text-secondary">Loading shared set and sessions…</p>}
    {data && <>
      {data.active_game && <p className="mt-3 text-sm">You have an active game. <Link className="text-link underline" to={`/games/${data.active_game.id}`}>Resume or leave it</Link> before joining another.</p>}
      <p className="mt-3 text-sm">{data.preview.message}</p>
      <button className="desk-v3-button mt-3" disabled={busy || !data.preview.can_start || !!data.active_game} onClick={() => void enter()}>Confirm shared set · Create session</button>
      {!data.preview.can_start && !data.active_game && <p className="mt-2 text-sm text-secondary">Share at least {data.preview.required} eligible questions or bookmarks from the bank. Ineligible or assessment-locked questions are excluded.</p>}
      <ul className="mt-4 space-y-3">
        {data.sessions.map(session => <li key={session.id} className="flex min-w-0 flex-wrap items-center justify-between gap-3 rounded-panel border border-hairline p-3">
          <p className="text-sm">{session.state === "waiting" ? "Waiting for members" : "In progress"} · {session.players}/{session.capacity} players<br /><span className="text-secondary">{session.questions} shared questions · {session.round_seconds}s each</span></p>
          {session.joined ? <Link className="desk-v3-button" to={`/games/${session.id}`}>Open session</Link> : <button className="desk-v3-button" disabled={busy || !session.can_join || !!data.active_game} onClick={() => void enter(session)}>{session.can_join ? "Confirm set · Join" : session.state === "waiting" ? "Session full" : "Already started"}</button>}
        </li>)}
      </ul>
      {!data.sessions.length && <p className="mt-3 text-sm text-secondary">No active room sessions yet.</p>}
      <p className="mt-3 text-xs text-secondary">Lobby expires after 10 minutes. Leaving this Desk or withdrawing a shared source ends access to its session. You can release a seat from Games.</p>
    </>}
  </section>;
}

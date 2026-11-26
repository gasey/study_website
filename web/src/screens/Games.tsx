import WeeklyStandings from '../components/WeeklyStandings'
import {learnerExplanation} from '../lib/answerStatus'
import GameSetup from "../components/GameSetup";
import {useEffect,useRef,useState} from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  gameRead,
  gameWrite,
  MODE_NAMES,
  type GamesData,
  type GameMode,
  type GameRoom,
  type GameSelection,
  type GamePreview,
  type JoinPreview,
} from "../lib/games";
import {
  SourceQuestionContext,
  SourceQuestionText,
} from "../components/SourceQuestionText";
import { AnswerOptions } from "../components/AnswerLayout";
import { UserAvatar } from "../components/AvatarArt";
import type { AvatarLook } from "../lib/avatar";
const BTN =
  "ism-tactile-btn inline-flex min-h-11 items-center justify-center rounded-pill border border-hairline bg-card px-4 py-2 text-sm font-semibold disabled:opacity-40 hover:border-hairline2";
const MODES: {
  id: GameMode;
  body: string;
  meta: string;
  hue: string;
  tint: string;
  icon: string;
}[] = [
  {
    id: "gauntlet",
    body: "Pass MCQ gates, build a multiplier and protect three lives. Correct gates add distance; a wrong answer or timeout costs a life.",
    meta: "Solo · 20 gates · 3 lives",
    hue: "#9A6410",
    tint: "#F6E7C6",
    icon: "↟",
  },
  {
    id: "speed",
    body: "Race through ten official-key questions before the 60-second clock expires.",
    meta: "Solo · 10 questions · 60 seconds",
    hue: "#C0462C",
    tint: "#F6DDD3",
    icon: "⏱",
  },
  {
    id: "duel",
    body: "Play the same ten questions against a friend, or join the random queue on your topic.",
    meta: "2 players · 20 seconds per round",
    hue: "#33609E",
    tint: "#DAE3F1",
    icon: "⚔",
  },
  {
    id: "party",
    body: "Share a private room code and play together. The host starts when everyone is ready.",
    meta: "2–4 players · 10 questions",
    hue: "#1F7F86",
    tint: "#D3EAEA",
    icon: "◎",
  },
  {
    id: "cup",
    body: "One weekly attempt on a shared official-key set. Opens Sunday at 7 pm India time.",
    meta: "25 questions · 30 seconds per round",
    hue: "#8A4A86",
    tint: "#EEDDEC",
    icon: "♜",
  },
];
function readableTime(s: string) {
  return (
    new Date(s).toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      dateStyle: "medium",
      timeStyle: "short",
    }) + " IST"
  );
}
function useClock() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}
export default function Games() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [data, setData] = useState<GamesData | null>(null);
  const [selection,setSelection]=useState<GameSelection|null>(null);
  const [chosenMode,setChosenMode]=useState<GameMode|null>((["gauntlet","speed","duel","party","cup","daily"].includes(params.get("mode")||"")?params.get("mode") as GameMode:null));
  useEffect(() => {
    const mode = params.get("mode");
    setChosenMode(
      ["gauntlet", "speed", "duel", "party", "cup", "daily"].includes(mode || "")
        ? (mode as GameMode)
        : null,
    );
  }, [params]);
  const [matchmaking,setMatchmaking]=useState(false);
  const [joinPreview,setJoinPreview]=useState<JoinPreview|null>(null);
  const joinEpoch=useRef(0);
  const restored=useRef(false);
  const [code, setCode] = useState(params.get("join") || "");
  const [publicCup, setPublicCup] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const epoch = useRef(0);
  const retry = useRef({ body: "", key: crypto.randomUUID() });
  const now = useClock();
  useEffect(() => {
    const gen = ++epoch.current;
    let timer: number | undefined;
    const load = () => {
      if (document.hidden) return;
      gameRead<GamesData>("")
        .then((r) => {
          if (gen === epoch.current) {
            setData(r);
            if(!restored.current){restored.current=true;setSelection(r.setup?.saved_selection||null)}
            setError("");
          }
        })
        .catch((e) => {
          if (gen === epoch.current) setError(e.message);
        });
    };
    void load();
    timer = window.setInterval(load, 30000);
    const auth = () => {
      epoch.current++;
      setData(null);setSelection(null);setChosenMode(null);setJoinPreview(null);setBusy(false);setError("");joinEpoch.current++;restored.current=false;
      setReload((n) => n + 1);
    };
    window.addEventListener("ism-auth-change", auth);
    window.addEventListener("visibilitychange", load);
    return () => {
      epoch.current++;
      clearInterval(timer);
      window.removeEventListener("ism-auth-change", auth);
      window.removeEventListener("visibilitychange", load);
    };
  }, [reload]);
  function requestStart(mode:GameMode,random=false){setChosenMode(mode);setMatchmaking(random);document.getElementById('game-setup')?.scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'})}
  async function start(mode: GameMode, preview:GamePreview, matchmaking = false) {
    if (!data?.registered) {
      navigate("/login");
      return;
    }
    const startEpoch=epoch.current;
    setBusy(true);
    setError("");
    try {
      const body = {
        mode,
        selection:preview.public.selector,
        preview_hash:preview.context_hash,
        matchmaking,
        public_result: mode === "cup" && publicCup,
      };
      const serialized = JSON.stringify(body);
      if (retry.current.body !== serialized)
        retry.current = { body: serialized, key: crypto.randomUUID() };
      const r = await gameWrite<GameRoom>("/rooms", {
        ...body,
        request_key: retry.current.key,
      });
      if(startEpoch===epoch.current)navigate("/games/" + r.id);
    } catch (e) {
      if(startEpoch!==epoch.current)return;
      setError((e as Error).message);
      if (/active mock/i.test((e as Error).message)) {
        const gen=epoch.current;
        gameRead<GamesData>("").then(r=>{if(gen===epoch.current)setData(r)}).catch(()=>{});
      }
    } finally {
      if(startEpoch===epoch.current)setBusy(false);
    }
  }
  async function join(e:React.FormEvent){
    e.preventDefault();if(!data?.registered){navigate('/login');return}
    const gen=++joinEpoch.current;setBusy(true);setError('');setJoinPreview(null);
    try{const r=await gameRead<JoinPreview>('/join-preview?code='+encodeURIComponent(code.trim().toUpperCase()));if(gen===joinEpoch.current)setJoinPreview(r)}catch(e){if(gen===joinEpoch.current)setError((e as Error).message)}finally{if(gen===joinEpoch.current)setBusy(false)}
  }
  async function acceptJoin(){if(!joinPreview)return;const gen=joinEpoch.current;setBusy(true);setError('');try{const r=await gameWrite<GameRoom>('/join',{code:code.trim().toUpperCase(),context_hash:joinPreview.context_hash});if(gen===joinEpoch.current)navigate('/games/'+r.id)}catch(e){if(gen===joinEpoch.current)setError((e as Error).message)}finally{if(gen===joinEpoch.current)setBusy(false)}}
  const cup = data?.cup;
  const cupOpen =
    !!cup &&
    now >= Date.parse(cup.opens_at) &&
    now <= Date.parse(cup.closes_at) - 750000;
  return (
    <main className="mx-auto max-w-[1240px] px-4 pb-24 pt-8 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-xs uppercase tracking-[.1em] text-practice-dark">
            Game time
          </div>
          <h1 className="mt-2 font-display text-[clamp(36px,5vw,52px)] leading-tight">
            Play
          </h1>
          <p className="mt-3 max-w-[640px] text-md leading-relaxed text-secondary">
            Every game runs on official-key questions from the bank. Play solo,
            challenge a friend or meet in a private multiplayer room.
          </p>
        </div>
        <div className="ism-card-surface rounded-[12px] border border-exams bg-exams-soft px-4 py-3 text-sm">
          Games XP today{" "}
          <b className="ml-2 font-mono text-exams-dark">{data?.game_xp_today ?? "—"}</b>
          <div className="mt-1 text-xs text-secondary">
            Shares the 300 XP daily study/game budget
          </div>
        </div>
      </div>
      {error && (
        <div
          role="alert"
          className="mt-4 rounded-[8px] border border-mypick bg-mypick-soft p-3 text-sm text-mypick"
        >
          {error}
          <button
            className="ml-3 min-h-11 underline"
            onClick={() => setReload((n) => n + 1)}
          >
            Refresh games
          </button>
        </div>
      )}
      {data?.active_mock && <section aria-label="Unfinished mock" className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-exams bg-exams-soft p-4"><div><h2 className="font-display text-lg">You have an unfinished mock</h2><p className="mt-1 text-sm text-secondary">{data.active_mock.collection_title || 'Timed mock'} · {data.active_mock.seconds_remaining>0?'Continue or submit this mock to unlock games.':'Time has ended. Open the mock to complete submission and unlock games.'}</p></div><Link className={BTN+' !bg-ink !text-paper'} to={data.active_mock.resume_url}>Resume unfinished mock →</Link></section>}
      {data?.active && (
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-[12px] border border-practice bg-practice-soft p-4">
          <p className="text-sm">
            You have an unfinished {MODE_NAMES[data.active.mode]}.
          </p>
          <Link
            to={'/games/'+data.active.id+(data.active.mode==='trail'?'?mode=trail':'')}
            className={BTN + " !bg-ink !text-paper"}
          >
            Resume / leave →
          </Link>
        </div>
      )}
      <section
        aria-label="Finna Quest RPG"
        className="mt-5 overflow-hidden rounded-[22px] p-5 text-white shadow-lg sm:p-6"
        style={{
          background:
            "linear-gradient(135deg, #121d2f 0%, #1b324b 55%, #0f4c5c 100%)",
        }}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="min-w-0 flex-1">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 font-mono text-[11px] font-bold uppercase tracking-[0.08em] text-amber-200">
              ⚔️ New Flagship RPG · Curated General Realms
            </span>
            <h2 className="mt-2.5 font-display text-2xl font-bold text-white sm:text-3xl">
              Finna Quest — Ascend the Blue Mountain
            </h2>
            <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-slate-200">
              Battle Realm Guardians across <strong>English, Geography, Computer, History, Polity, Science, Economy &amp; Maths</strong> (plus optional Mizo) — zero radiology or specialist technical leaks. 12-Floor Expedition, 3 Bosses, Campfire Power-up Shop, Endless Tower &amp; Daily 10-Q Gauntlet!
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/games/quest"
              className="inline-flex min-h-11 items-center rounded-pill bg-amber-400 px-5 text-sm font-extrabold text-slate-950 shadow hover:bg-amber-300"
            >
              ⚔️ Play Finna Quest →
            </Link>
            <Link
              to="/games/quest?mode=daily"
              className="inline-flex min-h-11 items-center rounded-pill border border-white/30 bg-white/10 px-4 text-sm font-bold text-white hover:bg-white/20"
            >
              📅 Daily Gauntlet
            </Link>
            <Link
              to="/games/quest?mode=endless"
              className="inline-flex min-h-11 items-center rounded-pill border border-white/30 bg-white/10 px-4 text-sm font-bold text-white hover:bg-white/20"
            >
              🏔️ Endless Tower
            </Link>
          </div>
        </div>
      </section>

      <div className="mt-5 flex flex-wrap items-start gap-8">
        <section aria-label="Play modes" className="grid min-w-0 flex-[999_1_620px] gap-3 sm:grid-cols-2">
          <section aria-label="Daily Five" className="ism-card-surface flex flex-col items-start justify-between gap-4 rounded-[16px] border border-practice bg-practice-soft p-5">
        <div><h2 className="font-display text-xl">Daily Five</h2><p className="mt-2 text-sm text-secondary">Five shared questions · GK/GS, English and everyday maths · 20 seconds each. One attempt per India calendar day.</p></div>
        {data?.daily?.entry_room?<Link className={BTN} to={'/games/'+data.daily.entry_room}>Open my Daily Five →</Link>:<button className={BTN} disabled={busy||!data||!!data.active||!!data.active_mock||now>Date.parse(data.daily.closes_at)-100000} onClick={()=>requestStart('daily')}>Review Daily Five setup →</button>}
      </section>
          <Link to="/games?mode=trail" className="ism-card-surface group block rounded-[16px] border border-correct bg-correct-soft/75 p-5 hover:border-correct"><h2 className="font-display text-xl text-correct-dark group-hover:underline">Topic Trail ↗</h2><p className="mt-2 text-sm text-secondary">Ten stepping stones, one topic, a little hill to climb. Pause between questions and choose one Double next.</p></Link>

          {MODES.map((m) => (
            <article
              key={m.id}
              className="ism-card-surface flex flex-col rounded-[14px] border border-hairline bg-card p-5"
              style={{ boxShadow: `inset 0 4px 0 ${m.hue}` }}
            >
              <span
                className="mb-3 grid h-12 w-12 place-items-center rounded-[10px] text-xl"
                style={{ background: m.tint, color: m.hue }}
              >
                {m.icon}
              </span>
              <h2 className="font-display text-xl">{MODE_NAMES[m.id]}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-secondary">
                {m.body}
              </p>
              <p className="mt-3 font-mono text-xs text-muted">{m.meta}</p>
              {m.id === "cup" && cup && (
                <>
                  <p className="mt-2 text-xs">
                    {readableTime(cup.opens_at)} · {cup.entries} entries
                  </p>
                  <label className="mt-3 flex items-start gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={publicCup}
                      onChange={(e) => setPublicCup(e.target.checked)}
                    />
                    Publish my handle and result on this cup’s standings
                  </label>
                </>
              )}
              {m.id === "cup" && cup?.entry_room ? (
                <Link className={BTN + " mt-4"} to={"/games/" + cup.entry_room}>
                  Open my cup entry →
                </Link>
              ) : (
                <button
                  disabled={
                    busy ||
                    !data ||
                    !!data.active ||
                    !!data.active_mock ||
                    (m.id === "cup" && !cupOpen)
                  }
                  className={BTN + " mt-4"}
                  onClick={() => requestStart(m.id)}
                >
                  {m.id === "cup"
                    ? cupOpen
                      ? "Enter weekly cup"
                      : "Opens Sunday · 7 pm IST"
                    : m.id === "duel"
                      ? "Create private duel"
                      : m.id === "party"
                        ? "Create multiplayer room"
                        : m.id === "gauntlet" ? "Play Gauntlet Run" : "Play speed round"}
                </button>
              )}
              {m.id === "duel" && (
                <button
                  disabled={busy || !data || !!data.active || !!data.active_mock}
                  className={BTN + " mt-2"}
                  onClick={() => requestStart("duel", true)}
                >
                  Find a random opponent
                </button>
              )}
            </article>
          ))}
        </section>
        <aside className="grid min-w-0 flex-[1_1_280px] gap-6 lg:max-w-[330px]">
          <section className="rounded-[10px] border border-hairline bg-card p-4">
            <h2 className="font-display text-lg">Join friends</h2>
            <p className="mt-2 text-sm leading-relaxed text-secondary">
              The room’s players can see your handle and avatar. Share codes
              only with people you want to play with. No chat or public room
              directory.
            </p>
            <form className="mt-3 grid gap-2" onSubmit={(e) => void join(e)}>
              <input
                aria-label="Room code"
                required
                minLength={12}
                maxLength={12}
                value={code}
                onChange={(e) => {setCode(e.target.value);setJoinPreview(null);joinEpoch.current++}}
                placeholder="12-character room code"
                className="min-h-11 min-w-0 rounded-[6px] border border-hairline bg-paper px-3 font-mono text-sm"
              />
              <button disabled={busy || !!data?.active_mock} className={BTN}>
                Preview room
              </button>
            </form>
            {joinPreview&&<section aria-label="Accept room rules"className="mt-3 rounded-[8px] bg-[#F6F2E9] p-3 text-sm"><h3 className="font-semibold">{joinPreview.label}</h3><p className="mt-1">{joinPreview.source_label}</p><p className="mt-1">{joinPreview.questions} questions · {joinPreview.round_seconds} seconds each · same questions for every player</p>{joinPreview.excluded_labels.length>0&&<p>Left out: {joinPreview.excluded_labels.join(', ')}</p>}<p className="mt-2">{joinPreview.players}/{joinPreview.capacity} players. You will confirm Ready in the lobby.</p><button className={BTN+' mt-3 bg-ink text-paper'}disabled={busy}onClick={()=>void acceptJoin()}>Accept area & join</button></section>}
          </section>
          <section>
            <h2 className="border-b border-ink pb-2 font-mono text-xs uppercase tracking-wider">
              Recent games
            </h2>
            {data?.history.map((h) => (
              <Link
                key={h.id}
                to={'/games/'+h.id+(h.mode==='trail'?'?mode=trail':'')}
                className="flex items-center justify-between gap-3 border-b border-hairline py-3"
              >
                <span className="text-sm">
                  {MODE_NAMES[h.mode]}
                  <span className="mt-1 block text-xs text-muted">
                    {h.state} ·{" "}
                    {new Date(h.finished_at).toLocaleDateString("en-IN")}
                  </span>
                  {!!(h.pace_bonus || h.streak_bonus || h.courage_bonus || h.best_streak) && (
                    <span className="mt-0.5 block font-mono text-xs text-[#9A6410]">
                      Pace +{h.pace_bonus || 0} · Streak +{h.streak_bonus || 0} (🔥{h.best_streak || 0})
                      {h.courage_bonus ? ` · ⚡+${h.courage_bonus}` : ""}
                    </span>
                  )}
                </span>
                <b className="font-display text-lg">{h.score}</b>
              </Link>
            ))}
            {!data?.history.length && (
              <p className="mt-3 text-sm text-muted">
                Your completed games will appear here.
              </p>
            )}
          </section>
          {cup && <CupBoard cupId={cup.id} />}
          <p className="text-xs leading-relaxed text-secondary">
            New correct official-key answers can earn 10 XP and 1 reward point
            under the shared daily limits. Repeating a question earns no extra
            credit. Run scores are separate from your wallet. Cup results carry
            no cash or coin prizes.
          </p>
          <Link
            className="text-xs font-semibold text-link underline"
            to={data?.registered ? "/profile" : "/login"}
          >
            {data?.registered ? "Your profile →" : "Sign in to play →"}
          </Link>
        </aside>
      </div>
      {data?.setup&&<GameSetup data={data.setup}registered={data.registered}selection={selection}onChange={setSelection}mode={chosenMode}matchmaking={matchmaking}onMode={setChosenMode}onConfirm={p=>{if(chosenMode)void start(chosenMode,p,matchmaking)}}busy={busy}disabled={!!data.active||!!data.active_mock||(chosenMode==='daily'&&(!!data.daily?.entry_room||now>Date.parse(data.daily.closes_at)-100000))}/>}

      <CompetitiveLeaderboardSection />
    </main>
  );
}
function CompetitiveLeaderboardSection() {
 const [track,setTrack]=useState<'gauntlet'|'speed'|'duel'|'daily'>('gauntlet')
 const modes=[['gauntlet','Gauntlet best score','score'],['speed','Speed best score','score'],['duel','Duel wins','wins'],['daily','Daily Five streak','days']] as const
 return <section aria-label="Weekly game boards" className="mt-8 rounded-[18px] border border-hairline bg-card p-5 sm:p-6">
  <h2 className="font-display text-xl">Weekly game boards</h2>
  <p className="mt-2 text-sm text-secondary">Finished games, one shared visibility choice. Daily Five ranks your longest run of completed days within this India week. Duel ties don’t count as wins.</p>
  <div role="group" aria-label="Game board mode" className="mt-4 flex flex-wrap gap-2">{modes.map(([id,label])=><button key={id} type="button" aria-pressed={track===id} onClick={()=>setTrack(id)} className={BTN+(track===id?' !bg-ink !text-paper':'')}>{label}</button>)}</div>
  <WeeklyStandings key={track} endpoint={'/games/leaderboard?contract=2&track='+track} unit={modes.find(m=>m[0]===track)![2]} empty="No public results for this mode this week yet."/>
  <Link to="/profile/rewards" className={BTN+' mt-5'}>Weekly XP league →</Link><Link to="/profile/rewards" className={BTN+' ml-2 mt-5'}>My visibility →</Link>
 </section>
}
function CupBoard({ cupId }: { cupId: string }) {
  const [items, setItems] = useState<
    {
      handle: string;
      avatar: AvatarLook | null;
      score: number;
      correct: number;
      rank: number;
      is_you: boolean;
      public_result: boolean;
    }[]
  >([]);
  const [error, setError] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [busy, setBusy] = useState(false);
  async function visibility(enabled: boolean) {
    setBusy(true);
    try {
      await gameWrite("/cup/visibility", { cup_id: cupId, enabled });
      setReload((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const [more, setMore] = useState(false);
  useEffect(() => {
    let live = true;
    gameRead<{ items: typeof items; has_more: boolean }>(
      "/cup/board?cup_id=" + cupId + "&offset=" + offset,
    )
      .then((r) => {
        if (live) {
          setItems(r.items);
          setMore(r.has_more);
        }
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, [cupId, offset, reload]);
  return (
    <section>
      <h2 className="border-b border-ink pb-2 font-mono text-xs uppercase tracking-wider">
        Weekly cup standings
      </h2>
      {error ? (
        <p className="mt-3 text-xs text-mypick">{error}</p>
      ) : items.length ? (
        items.map((p) => (
          <div
            key={p.handle}
            className="flex items-center gap-2 border-b border-hairline py-3"
          >
            <span className="font-mono text-xs">{p.rank}</span>
            <UserAvatar look={p.avatar} initials={p.handle} />
            <span className="flex-1 text-sm">
              {p.handle}
              {p.is_you ? " · you" : ""}
            </span>
            <b>{p.score}</b>
            {p.is_you && (
              <button
                className="min-h-11 text-xs text-link underline"
                disabled={busy}
                onClick={() => void visibility(!p.public_result)}
              >
                {p.public_result ? "Hide my result" : "Publish my result"}
              </button>
            )}
          </div>
        ))
      ) : (
        <p className="mt-3 text-sm text-muted">
          No published results yet. Your own result appears here even if you
          keep it private.
        </p>
      )}
      {(offset > 0 || more) && (
        <nav aria-label="Cup standings pages" className="mt-3 flex gap-2">
          <button
            className={BTN}
            disabled={!offset}
            onClick={() => setOffset((n) => Math.max(0, n - 20))}
          >
            Previous
          </button>
          <button
            className={BTN}
            disabled={!more}
            onClick={() => setOffset((n) => n + 20)}
          >
            Next
          </button>
        </nav>
      )}
    </section>
  );
}
export function GamePlayer() {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const [room, setRoom] = useState<GameRoom | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const lastVersion = useRef(-1);
  const progressReported = useRef<string | null>(null);
  const alive = useRef(true);
  const actionEpoch = useRef(0);
  const now = useClock();
  const [serverOffset, setServerOffset] = useState(0);
  const [scratchOpen, setScratchOpen] = useState(false);
  const [scratchText, setScratchText] = useState("");
  const apply = (r: GameRoom) => {
    if (alive.current && r.id === id && r.version >= lastVersion.current) {
      if(r.state === "finished" && progressReported.current !== r.id){
        progressReported.current = r.id;
        window.dispatchEvent(new Event("ism-progress-change"));
      }
      lastVersion.current = r.version;
      if(r.mode==='trail'){navigate('/games/'+r.id+'?mode=trail',{replace:true});return}
      setRoom(r);
      setServerOffset(Date.parse(r.server_now) - Date.now());
      setError("");
    }
  };
  useEffect(() => {
    alive.current = true;
    actionEpoch.current++;
    lastVersion.current = -1;
    setRoom(null);
    let live = true;
    let timer: number;
    let failures = 0;
    const epoch = actionEpoch.current;
    const load = async () => {
      if (!live) return;
      if (!document.hidden) {
        try {
          const r = await gameRead<GameRoom>(
            "/rooms/" + encodeURIComponent(id),
          );
          if (live && epoch === actionEpoch.current) {
            apply(r);
            failures = 0;
            if (r.state === "finished" || r.state === "cancelled") {
              const unlock = r.review_available_at
                ? Date.parse(r.review_available_at) - Date.now()
                : 0;
              if (r.state === "finished" && unlock > 0)
                timer = window.setTimeout(load, Math.min(30000, unlock + 1000));
              return;
            }
          }
        } catch (e) {
          if (live) setError((e as Error).message);
          failures++;
          if (
            [401, 403, 404].includes((e as Error & { status: number }).status)
          )
            return;
        }
      }
      if (live)
        timer = window.setTimeout(load, Math.min(30000, 2000 * 2 ** failures));
    };
    void load();
    const visible = () => {
      if (!document.hidden) {
        clearTimeout(timer);
        void load();
      }
    };
    const auth = () => {
      actionEpoch.current++;
      setRoom(null);
      setRetry((n) => n + 1);
    };
    window.addEventListener("ism-auth-change", auth);
    window.addEventListener("visibilitychange", visible);
    return () => {
      actionEpoch.current++;
      window.removeEventListener("ism-auth-change", auth);
      live = false;
      alive.current = false;
      clearTimeout(timer);
      window.removeEventListener("visibilitychange", visible);
    };
  }, [id, retry]);
  async function action(path: string, body: unknown = {}) {
    const epoch = actionEpoch.current;
    setBusy(true);
    setError("");
    try {
      const r = await gameWrite<GameRoom>("/rooms/" + id + "/" + path, body);
      if (epoch !== actionEpoch.current) return;
      if (path === "leave") {
        navigate("/games");
        return;
      }
      apply(r);
    } catch (e) {
      if (alive.current && epoch === actionEpoch.current) setError((e as Error).message);
    } finally {
      if (alive.current && epoch === actionEpoch.current) setBusy(false);
    }
  }
  const remaining = room?.round_ends_at
    ? Math.max(
        0,
        Math.ceil((Date.parse(room.round_ends_at) - now - serverOffset) / 1000),
      )
    : 0;
  const mine = room?.players.find((p) => p.user_id === room.viewer_id);
  return (
    <main className="mx-auto max-w-[1240px] px-4 pb-24 pt-9 sm:px-6">
      <Link to="/games" className="min-h-11 py-3 text-sm text-link">
        ← Games
      </Link>
      <div className="mt-4 font-mono text-xs uppercase tracking-wider text-link">
        Game time
      </div>
      <h1 className="mt-2 font-display text-[clamp(36px,5vw,52px)]">
        {room ? MODE_NAMES[room.mode] : "Your game"}
      </h1>
      {error && (
        <div
          role="alert"
          className="mt-4 rounded-[8px] border border-mypick p-3 text-sm text-mypick"
        >
          {error}
          <button
            className="ml-3 min-h-11 underline"
            onClick={() => setRetry((n) => n + 1)}
          >
            Reconnect
          </button>
          <button
            className="ml-3 min-h-11 underline"
            disabled={busy}
            onClick={() => void action("leave")}
          >
            Leave this game
          </button>
          <Link className="ml-3 underline" to="/login">
            Sign in
          </Link>
        </div>
      )}
      {!room ? (
        <p role="status" className="mt-6 text-muted">
          {error ? "Game unavailable." : "Connecting to your game…"}
        </p>
      ) : (
        <>
          {room.desk_id && <p className="mt-3 text-sm"><Link className="text-link underline" to={`/desk/${room.desk_id}`}>Back to private Desk</Link> · Members join from the Desk’s Practice tab.</p>}
          <p className="mt-4 rounded-[8px] border border-hairline bg-card p-3 text-sm">{room.selection?`${room.selection.label} · ${room.selection.source_label}`:`Legacy game · ${room.subject_id||'Mixed subjects'} · MPSC & Mizoram recruitment`}</p>
          <div className="mt-5 flex flex-wrap items-start gap-7">
            <section className="min-w-0 flex-[999_1_560px] overflow-hidden border border-ink bg-card">
              <header className="flex flex-wrap items-center gap-4 border-b border-ink px-5 py-[18px]">
                {room.players.map((p) => (
                  <div
                    key={p.user_id}
                    className="flex min-w-0 flex-[1_1_160px] items-center gap-2"
                  >
                    <UserAvatar look={p.avatar} initials={p.handle} />
                    <div className="min-w-0">
                      <b className="block truncate text-sm">
                        {p.user_id === room.viewer_id ? "You" : p.handle}
                      </b>
                      <span className="block text-xs text-muted">
                        {p.left_at
                          ? "Left / forfeited"
                          : room.state === "finished"
                            ? `${p.correct} correct · ${p.excluded} excluded`
                            : room.state === "waiting"
                              ? p.ready?"Ready":"Not ready"
                              : "Playing"}
                      </span>
                    </div>
                    {room.state === "finished" && (
                      <b className="ml-auto font-display text-xl">
                        {p.left_at ? "—" : p.score}
                      </b>
                    )}
                  </div>
                ))}
              </header>
              {room.state === "waiting" && (
                <div className="p-6">
                  <h2 className="font-display text-xl">
                    Waiting for players
                  </h2>
                  <p className="mt-3 text-sm text-secondary">
                    {room.mode === "duel"
                      ? room.selection?"Both players must accept this area and press Ready. Random queues match the exact confirmed choices.":"This legacy duel starts when a second player joins."
                      : room.desk_id ? "Desk members join from its Practice tab and confirm Ready. The host starts with two to four ready players. Players cannot join after the start." : "Share the code, confirm Ready, then the host starts with two to four ready players. Players cannot join after the start."}{" "}
                    Empty lobbies expire after ten minutes.
                  </p>
                  {!room.desk_id && <p
                    className="mt-5 font-mono text-xl tracking-widest"
                    aria-label="Private room code"
                  >
                    {room.join_code}
                  </p>}
                  <p className="mt-2 text-xs text-muted">
                    {room.players.filter((p) => !p.left_at).length} /{" "}
                    {room.capacity} players
                  </p>
                  {room.selection&&<div className="mt-4 rounded-[8px] border border-hairline bg-card p-4"><h3 className="font-semibold">{room.selection.label}</h3><p className="mt-1 text-sm">{room.selection.source_label}</p><p className="mt-1 text-sm">{room.total} identical questions · {room.round_seconds} seconds each · official-key scoring</p>{room.selection.excluded_labels.length>0&&<p className="mt-1 text-xs">Left out: {room.selection.excluded_labels.join(', ')}</p>}<button className={BTN+' mt-3 bg-ink text-paper'}disabled={busy}onClick={()=>void action('ready',{ready:!room.players.find(p=>p.user_id===room.viewer_id)?.ready})}>{room.players.find(p=>p.user_id===room.viewer_id)?.ready?'Not ready / change my mind':'I accept this area · Ready'}</button></div>}
                  {room.owner_id === room.viewer_id && (
                    <button
                      className={BTN + " mt-5 bg-ink text-paper"}
                      disabled={
                        busy ||
                        room.players.filter((p) => !p.left_at).length < 2 || (!!room.selection&&room.players.some(p=>!p.left_at&&!p.ready))
                      }
                      onClick={() => void action("start")}
                    >
                      Start game
                    </button>
                  )}
                </div>
              )}
              {room.state === "running" && room.question && (
                <div className="p-5 sm:p-[22px]">
                  <div className="flex flex-wrap items-center justify-between gap-2 font-mono text-xs text-muted">
                    <div className="flex flex-wrap items-center gap-2">
                      <span>
                        Question {room.position + 1} of {room.total}
                      </span>
                      {room.question.pillar_label && (
                        <span className="rounded-pill bg-ink/10 px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-ink">
                          {room.question.pillar_label}
                        </span>
                      )}
                      {room.question.pillar === "everyday_math" && (
                        <span className="rounded-pill bg-[#F6DDD3] px-2.5 py-0.5 text-xs font-semibold text-[#C0462C]">
                          ⏱ {room.question.round_seconds || 40}s Extended Math Clock
                        </span>
                      )}
                      {room.question.courage_eligible && (
                        <span className="rounded-pill bg-[#F6E7C6] px-2.5 py-0.5 text-xs font-semibold text-[#9A6410]">
                          ⚡ +25 Cross-Stream Courage
                        </span>
                      )}
                    </div>
                    <span role="timer">{remaining}s</span>
                  </div>
                  {room.question.pillar === "everyday_math" && (
                    <div className="mt-3 rounded-[10px] border border-[#D8A33A]/50 bg-[#FBF4E6] p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-mono text-xs font-semibold text-[#9A6410]">
                          Everyday Class-10 Math Tools · Pace bonus normalized to {room.question.round_seconds || 40}s
                        </span>
                        <button
                          type="button"
                          onClick={() => setScratchOpen((v) => !v)}
                          className="min-h-8 rounded-pill border border-ink/20 bg-paper px-3 py-1 font-mono text-xs font-semibold text-ink"
                        >
                          {scratchOpen ? "Hide Scratchpad" : "✎ Open Quick Math Scratchpad"}
                        </button>
                      </div>
                      {scratchOpen && (
                        <div className="mt-2.5 space-y-2">
                          <div className="flex flex-wrap gap-1.5 font-mono text-xs text-secondary">
                            <span className="rounded bg-paper px-2 py-0.5">HCF × LCM = A × B</span>
                            <span className="rounded bg-paper px-2 py-0.5">SI = (P × R × T) / 100</span>
                            <span className="rounded bg-paper px-2 py-0.5">Speed = Distance / Time</span>
                            <span className="rounded bg-paper px-2 py-0.5">Net % = a + b + (ab/100)</span>
                          </div>
                          <textarea
                            rows={2}
                            value={scratchText}
                            onChange={(e) => setScratchText(e.target.value)}
                            placeholder="Jot down quick ratios, percentages or steps here…"
                            className="w-full rounded-[6px] border border-hairline bg-paper p-2 font-mono text-xs"
                          />
                        </div>
                      )}
                    </div>
                  )}
                  {room.mode === "speed" && room.deadline && (
                    <p className="mt-2 text-xs text-muted">
                      {Math.max(
                        0,
                        Math.ceil(
                          (Date.parse(room.deadline) - now - serverOffset) /
                            1000,
                        ),
                      )}
                      s left in your speed round
                    </p>
                  )}
                  {room.mode === "gauntlet" && (
                    <div className="mt-4 rounded-[10px] bg-ink p-4 text-paper">
                      <div className="flex justify-between gap-3 text-sm">
                        <span>
                          {mine?.lives ?? 3} lives ·{" "}
                          {"♥".repeat(mine?.lives ?? 3)}
                        </span>
                        <span>{mine?.distance ?? 0} m</span>
                      </div>
                      <div className="relative mt-5 h-14 border-b-4 border-dashed border-[#D8A33A]">
                        <div
                          className="absolute bottom-0 transition-[left] duration-300 motion-reduce:transition-none"
                          style={{
                            left: `${Math.min(88, (room.position / room.total) * 88)}%`,
                          }}
                        >
                          <UserAvatar
                            look={mine?.avatar}
                            initials={mine?.handle || "You"}
                          />
                        </div>
                        <span className="absolute bottom-1 right-0 font-mono text-xs">
                          GATE {room.position + 1}
                        </span>
                      </div>
                    </div>
                  )}
                  <div aria-live="polite" className="mt-4">
                    <SourceQuestionContext
                      direction={room.question.direction}
                      passage={room.question.passage}
                    />
                    <h2 className="font-display text-xl leading-[1.35]">
                      <SourceQuestionText
                        text={
                          room.question.question_markup ||
                          room.question.question
                        }
                      />
                    </h2>
                  </div>
                  {room.question.figure_image_url && (
                    <img
                      className="my-4 max-h-[320px] w-full object-contain"
                      src={room.question.figure_image_url}
                      alt="Source question figure"
                    />
                  )}
                  <AnswerOptions className="mt-5">
                    {room.question.options.map((text, i) => (
                      <button
                        key={i}
                        className={
                          "answer-option flex min-h-12 items-center gap-3 rounded-[6px] border p-3 text-left text-base " +
                          (room.answered && room.chosen_index === i
                            ? "border-link bg-[#E3E9F8]"
                            : "border-hairline bg-card")
                        }
                        disabled={
                          busy ||
                          room.answered ||
                          remaining === 0 ||
                          !!mine?.left_at
                        }
                        aria-pressed={room.answered && room.chosen_index === i}
                        onClick={() =>
                          void action("answer", {
                            position: room.position,
                            chosen_index: i,
                          })
                        }
                      >
                        <span className="font-mono text-xs">
                          {String.fromCharCode(65 + i)}
                        </span>
                        <SourceQuestionText
                          text={room.question?.options_markup?.[i] || text}
                        />
                      </button>
                    ))}
                  </AnswerOptions>
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-secondary">
                      {room.answered
                        ? "Answer saved · waiting for the next round"
                        : remaining === 0
                          ? "Time is up · synchronizing the next round…"
                          : "Tap one option to submit your answer."}
                    </p>
                    <button
                      className={BTN}
                      disabled={busy || room.answered || remaining === 0}
                      onClick={() =>
                        void action("answer", {
                          position: room.position,
                          chosen_index: null,
                        })
                      }
                    >
                      Skip
                    </button>
                  </div>
                  <p className="mt-4 border-t border-hairline pt-3 text-xs text-muted">
                    {room.question.exam_name || "MPSC paper"}
                    {room.question.year ? " · " + room.question.year : ""}
                    {room.question.qnum
                      ? " · Q" + room.question.qnum
                      : ""} ·{" "}
                    {room.question.answer_source === "official"
                      ? "Official key"
                      : "Transcribed key"}
                    {room.question.source_pdf_url && (
                      <a
                        className="ml-3 text-link underline"
                        target="_blank"
                        rel="noreferrer"
                        href={
                          room.question.source_pdf_url +
                          (room.question.page
                            ? "#page=" + room.question.page
                            : "")
                        }
                      >
                        Source PDF ↗
                      </a>
                    )}
                  </p>
                </div>
              )}
              {room.state === "finished" && (
                <div className="p-6">
                  <h2 className="font-display text-2xl">
                    {mine?.left_at ? "Game forfeited" : "Game complete"}
                  </h2>
                  <div className="mt-4 flex flex-wrap gap-5 text-sm">
                    <span>
                      <b>{mine?.correct ?? 0}</b> correct
                    </span>
                    <span>
                      <b>{mine?.wrong ?? 0}</b> wrong
                    </span>
                    <span>
                      <b>{mine?.skipped ?? 0}</b> skipped
                    </span>
                    <span>
                      <b>{mine?.excluded ?? 0}</b> excluded
                    </span>
                  </div>
                  {!mine?.left_at && (
                    <div className="mt-4 grid gap-2.5 rounded-[12px] border border-[#D8A33A] bg-[#FBF4E6] p-4 sm:grid-cols-4">
                      <div>
                        <div className="font-mono text-xs uppercase text-muted">
                          Base Accuracy
                        </div>
                        <div className="mt-1 font-display text-lg">
                          {Math.max(
                            0,
                            (mine?.score ?? 0) -
                              (mine?.pace_bonus ?? 0) -
                              (mine?.streak_bonus ?? 0) -
                              (mine?.courage_bonus ?? 0),
                          )}{" "}
                          pts
                        </div>
                      </div>
                      <div>
                        <div className="font-mono text-xs uppercase text-muted">
                          {room.mode==='daily'?'Seconds left bonus':'Normalized Pace'}
                        </div>
                        <div className="mt-1 font-display text-lg text-[#1F44A6]">
                          +{mine?.pace_bonus ?? 0} pts
                        </div>
                      </div>
                      <div>
                        <div className="font-mono text-xs uppercase text-muted">
                          Streak Combo (🔥{mine?.best_streak ?? 0})
                        </div>
                        <div className="mt-1 font-display text-lg text-[#C0462C]">
                          +{mine?.streak_bonus ?? 0} pts
                        </div>
                      </div>
                      <div>
                        <div className="font-mono text-xs uppercase text-muted">
                          Cross-Stream ⚡
                        </div>
                        <div className="mt-1 font-display text-lg text-[#9A6410]">
                          +{mine?.courage_bonus ?? 0} pts
                        </div>
                      </div>
                    </div>
                  )}
                  <p className="mt-3 text-sm text-secondary">
                    {room.mode==='daily'?'Daily Five scores 100 per correct answer plus 5 for each whole second left.':'Game points use correct answers, task-normalized server timing, streak combos and cross-stream courage bonuses.'} Bank
                    changes before finalization are excluded. Learning XP
                    follows the shared daily budget and first-question reward
                    rules.
                  </p>
                  {room.review_available_at &&
                    Date.parse(room.review_available_at) >
                      now + serverOffset && (
                      <p className="mt-4 rounded-[8px] bg-[#F6E7C6] p-3 text-sm">
                        {room.mode==='daily'?'Daily Five':'Cup'} answer review unlocks after{" "}
                        {readableTime(room.review_available_at)}.
                      </p>
                    )}
                  <div className="mt-5 flex flex-wrap gap-3">
                    <Link className={BTN + " bg-ink text-paper"} to="/games">
                      Choose another game →
                    </Link>
                    <Link className={BTN} to="/profile/rewards">
                      Daily quests & streak chests →
                    </Link>
                  </div>
                </div>
              )}
              {room.state === "cancelled" && (
                <div className="p-6">
                  <h2 className="font-display text-xl">Lobby closed</h2>
                  <p className="mt-3 text-sm text-secondary">
                    The host left or the lobby expired. No game rewards were
                    awarded.
                  </p>
                  <Link className={BTN + " mt-4"} to="/games">
                    Back to Games
                  </Link>
                </div>
              )}
            </section>
            <aside className="min-w-0 flex-[1_1_260px] lg:max-w-[330px]">
              <h2 className="border-b border-ink pb-3 font-display text-xl">
                How this works
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-secondary">
                Your game is saved on the server. Refresh or reconnect to
                continue; the clock keeps running while you are away. Every
                player sees the same question order in shared rooms.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-secondary">
                Correct answers and scores are revealed when the shared game
                ends. Weekly cup and Daily Five answers stay hidden until their event closes.
                External sources and previously known questions can’t be
                prevented; these games are practice competitions.
              </p>
              {["running", "waiting"].includes(room.state) && (
                <>
                  <p className="mt-4 text-xs text-muted">
                    Leaving an active game forfeits its rewards. You can start
                    another game immediately.
                  </p>
                  <button
                    className={BTN + " mt-3 text-mypick"}
                    disabled={busy}
                    onClick={() => void action("leave")}
                  >
                    Leave / forfeit game
                  </button>
                </>
              )}
              <Link
                className="mt-5 block min-h-11 py-3 text-sm text-link underline"
                to="/profile/rewards"
              >
                XP & reward points →
              </Link>
            </aside>
          </div>
          {!!room.review.length && (
            <section className="mt-8">
              <h2 className="font-display text-2xl">
                Review your played questions
              </h2>
              {room.review.map((q) => (
                <details
                  key={q.position}
                  className="mt-3 rounded-[10px] border border-hairline bg-card p-4"
                >
                  <summary className="min-h-11 cursor-pointer text-sm font-semibold">
                    Question {q.position + 1} ·{" "}
                    {q.excluded
                      ? "Excluded · source changed"
                      : q.chosen_index === null
                        ? "Skipped"
                        : q.correct
                          ? "Correct"
                          : "Incorrect"}
                  </summary>
                  <SourceQuestionContext
                    direction={q.direction}
                    passage={q.passage}
                  />
                  <div className="mt-3 font-display text-lg">
                    <SourceQuestionText
                      text={q.question_markup || q.question}
                    />
                  </div>
                  <p className="mt-3 text-sm">
                    Original game key:{" "}
                    {String.fromCharCode(65 + q.answer_index)}.{" "}
                    {q.options[q.answer_index]}
                  </p>
                  {q.chosen_index !== null && (
                    <p className="mt-2 text-sm text-secondary">
                      Your choice: {String.fromCharCode(65 + q.chosen_index)}.{" "}
                      {q.options[q.chosen_index]}
                    </p>
                  )}
                  {q.excluded ? (
                    <p className="mt-2 text-sm text-mypick">
                      This source changed before finalization; the original game
                      key is not a current answer verification.
                    </p>
                  ) : (
                    q.explanation && (
                      <p className="mt-2 text-sm text-secondary">
                        {learnerExplanation(q.explanation)}
                      </p>
                    )
                  )}
                  <Link
                    className="mt-3 inline-flex min-h-11 items-center text-sm text-link underline"
                    to={"/bank/" + q.id}
                  >
                    Open question & discussion →
                  </Link>
                </details>
              ))}
            </section>
          )}
        </>
      )}
    </main>
  );
}

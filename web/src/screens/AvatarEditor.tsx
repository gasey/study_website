import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import AvatarArt, { UserAvatar } from "../components/AvatarArt";
import {
  AVATAR_COLORS,
  loadAvatar,
  saveAvatar,
  type AvatarAccount,
  type AvatarLook,
  type AvatarItem,
} from "../lib/avatar";
const CATEGORIES: [keyof AvatarLook, string][] = [
  ["skin", "Skin"],
  ["hair", "Hair"],
  ["hairC", "Hair colour"],
  ["top", "Top"],
  ["acc", "Accessory"],
  ["bg", "Background"],
  ["frame", "Frame"],
];
const B =
  "inline-flex min-h-11 items-center justify-center rounded-pill border border-ink px-4 py-2 text-[13px] font-semibold disabled:opacity-50";
export default function AvatarEditor() {
  const [account, setAccount] = useState<AvatarAccount | null>(null),
    [look, setLook] = useState<AvatarLook | null>(null),
    [tab, setTab] = useState("Customize"),
    [category, setCategory] = useState<keyof AvatarLook>("hair"),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(true);
  const generation = useRef(0);
  const [initialsPreview, setInitialsPreview] = useState(false);
  async function load() {
    const run = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const a = await loadAvatar();
      if (run !== generation.current) return;
      setAccount(a);
      setLook(a.avatar || a.default);
      setInitialsPreview(false);
    } catch (e) {
      if (run === generation.current) setError((e as Error).message);
    } finally {
      if (run === generation.current) setLoading(false);
    }
  }
  useEffect(() => {
    void load();
    const auth = () => {
      setAccount(null);
      setLook(null);
      setNotice("");
      setBusy(false);
      void load();
    };
    window.addEventListener("ism-auth-change", auth);
    return () => {
      generation.current++;
      window.removeEventListener("ism-auth-change", auth);
    };
  }, []);
  const dirty =
    !!account &&
    !!look &&
    (initialsPreview
      ? account.avatar !== null
      : JSON.stringify(account.avatar) !== JSON.stringify(look));
  function equip(item: AvatarItem) {
    if (!item.available || !look) return;
    setInitialsPreview(false);
    setLook({ ...look, [item.category]: item.value });
    setNotice("");
  }
  function shuffle() {
    if (!account || !look) return;
    const next = { ...look };
    for (const [cat] of CATEGORIES) {
      if (cat === "skin") continue;
      const options = account.catalog.filter(
        (i) => i.category === cat && i.available,
      );
      next[cat] = options[Math.floor(Math.random() * options.length)].value;
    }
    setInitialsPreview(false);
    setLook(next);
    setNotice("");
  }
  async function save(reset = false) {
    if (!account || !account.registered) return;
    const owner = account.user_id;
    const run = generation.current;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const r = await saveAvatar(
        owner,
        account.avatar_version,
        reset || initialsPreview ? null : look,
      );
      if (run !== generation.current) return;
      const a = await loadAvatar();
      if (run !== generation.current) return;
      if (a.user_id !== owner)
        throw new Error("Account changed. Reload your saved look.");
      setAccount(a);
      setLook(a.avatar || a.default);
      setInitialsPreview(a.avatar === null);
      setNotice(
        reset
          ? "Initials restored. Your earned items are kept."
          : "Look saved to your account.",
      );
      window.dispatchEvent(new Event("ism-avatar-change"));
      void r;
    } catch (e) {
      if (run === generation.current) setError((e as Error).message);
    } finally {
      if (run === generation.current) setBusy(false);
    }
  }
  return (
    <main className="mx-auto max-w-[1240px] px-6 pb-24 pt-8">
      <Link
        to="/profile"
        className="inline-flex min-h-11 items-center text-[13px] text-link"
      >
        ← Your profile
      </Link>
      <div className="font-mono text-[11px] uppercase tracking-[.1em] text-[#9A6410]">
        Profile
      </div>
      <h1 className="mt-2 font-display text-[clamp(34px,5vw,50px)] font-medium -tracking-[.02em]">
        Avatar & inventory
      </h1>
      {loading && (
        <p role="status" className="mt-6">
          Loading your saved look…
        </p>
      )}
      {error && (
        <div
          role="alert"
          className="mt-5 rounded-[10px] border border-wrong bg-wrong-soft p-4 text-[14px]"
        >
          {error}{" "}
          <button
            className="min-h-11 px-3 underline"
            onClick={() => void load()}
          >
            Reload saved look
          </button>
        </div>
      )}
      {account && look && !loading && (
        <div className="mt-[22px] flex flex-wrap items-start gap-7">
          <aside
            className="flex min-w-0 flex-[1_1_280px] flex-col gap-3.5 sm:sticky sm:top-20"
            style={{ maxWidth: 360 }}
          >
            <div className="overflow-hidden rounded-[14px] border border-ink bg-[#FBF8F1]">
              <div className="h-[70px] bg-[linear-gradient(90deg,#C0462C,#D8A33A,#1F7F86,#33609E)]" />
              <div className="-mt-14 flex flex-col items-center px-5 pb-5">
                {initialsPreview ? (
                  <UserAvatar initials={account.handle} size={168} />
                ) : (
                  <AvatarArt
                    look={look}
                    size={168}
                    label="Your avatar preview"
                  />
                )}
                <div className="mt-2 max-w-full break-words text-center font-display text-[24px]">
                  {account.name || account.handle}
                </div>
                <p className="text-[13px] text-secondary">
                  Level {account.level} · @{account.handle}
                </p>
                <span className="mt-3 rounded-pill bg-rewards-soft px-3 py-1 text-[11px]">
                  {dirty ? "Preview · save your look" : "Your saved look"}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                className={B + " flex-1"}
                disabled={busy}
                onClick={shuffle}
              >
                Shuffle
              </button>
              {account.registered ? (
                <button
                  className={B + " flex-1 bg-ink text-paper"}
                  disabled={busy || !dirty}
                  onClick={() => void save()}
                >
                  {busy ? "Saving…" : "Save look"}
                </button>
              ) : (
                <Link className={B + " flex-1 bg-ink text-paper"} to="/login">
                  Sign in to save
                </Link>
              )}
            </div>
            <p className="text-[12px] leading-normal text-secondary">
              Your saved avatar appears beside your profile, posts, leaderboard
              entry and study desk membership. Your existing visibility settings
              still apply.
            </p>
            {notice && (
              <p role="status" className="text-[13px] text-correct-dark">
                {notice}
              </p>
            )}
            <button
              className={B}
              disabled={busy}
              onClick={() => {
                setLook(account.avatar || account.default);
                setInitialsPreview(!account.avatar);
                setNotice("Preview changes discarded.");
              }}
            >
              Revert preview
            </button>
            {account.avatar && account.registered && (
              <button
                className={B}
                disabled={busy}
                onClick={() => void save(true)}
              >
                Use initials instead
              </button>
            )}
          </aside>
          <section className="min-w-0 flex-[999_1_560px]">
            <div
              role="group"
              aria-label="Avatar workspace"
              className="flex gap-[22px] border-b border-ink"
            >
              {["Customize", "Inventory"].map((t) => (
                <button
                  key={t}
                  aria-pressed={tab === t}
                  onClick={() => setTab(t)}
                  className={
                    "min-h-11 border-b-2 py-[11px] text-[14px] font-semibold " +
                    (tab === t ? "border-ink" : "border-transparent text-muted")
                  }
                >
                  {t}
                </button>
              ))}
            </div>
            {tab === "Customize" ? (
              <>
                <div
                  role="group"
                  aria-label="Avatar category"
                  className="mt-4 flex flex-wrap gap-1.5"
                >
                  {CATEGORIES.map(([cat, label]) => (
                    <button
                      key={cat}
                      aria-pressed={category === cat}
                      onClick={() => setCategory(cat)}
                      className={
                        B +
                        " !min-h-11 !px-[13px] !py-1.5 " +
                        (category === cat ? "bg-ink text-paper" : "")
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>
                <div className="mt-4 grid grid-cols-[repeat(auto-fill,minmax(132px,1fr))] gap-3">
                  {account.catalog
                    .filter((i) => i.category === category)
                    .map((item) => (
                      <button
                        key={item.id}
                        disabled={!item.available || busy}
                        aria-pressed={look[item.category] === item.value}
                        onClick={() => equip(item)}
                        className={
                          "flex min-h-[132px] min-w-0 flex-col gap-1.5 rounded-[10px] border-2 bg-[#FBF8F1] p-3 text-left disabled:opacity-55 " +
                          (look[item.category] === item.value
                            ? "border-ink"
                            : "border-[#E4DBC9]")
                        }
                      >
                        <span
                          className="flex h-16 w-full items-center justify-center overflow-hidden rounded-lg"
                          style={{
                            background: ["skin", "hairC", "bg"].includes(
                              item.category,
                            )
                              ? item.value
                              : AVATAR_COLORS[item.value] || "#EFE6D3",
                          }}
                        >
                          {["hair", "acc", "frame"].includes(item.category) && (
                            <AvatarArt
                              look={{ ...look, [item.category]: item.value }}
                              size={64}
                              label={item.label + " preview"}
                            />
                          )}
                        </span>
                        <span className="text-[13px] font-semibold">
                          {item.label}
                        </span>
                        <span className="font-mono text-[10.5px] text-secondary">
                          {!item.available
                            ? "Unlocks at level " + item.level
                            : look[item.category] === item.value
                              ? "Selected"
                              : item.level === 1
                                ? "Starter · tap to wear"
                                : item.claimed
                                  ? "Earned · tap to wear"
                                  : "Level reward · save to claim"}
                        </span>
                      </button>
                    ))}
                </div>
              </>
            ) : (
              <>
                <p className="mt-4 text-[13.5px] text-secondary">
                  Starter items are free. Saving a look claims your eligible
                  level rewards permanently. Cosmetics do not change XP, points
                  or ranks.
                </p>
                {CATEGORIES.map(([cat, label]) => {
                  const items = account.catalog.filter(
                    (i) => i.category === cat && i.available,
                  );
                  return (
                    <section key={cat} className="mt-[18px]">
                      <h2 className="border-b border-ink pb-2 font-mono text-[11px] uppercase tracking-[.1em] text-muted">
                        {label} · {items.length}
                      </h2>
                      <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-x-5">
                        {items.map((item) => (
                          <div
                            key={item.id}
                            className="flex items-center gap-2.5 border-b border-hairline py-2.5"
                          >
                            <AvatarArt
                              look={{ ...look, [item.category]: item.value }}
                              size={36}
                              label={item.label + " preview"}
                            />
                            <span className="min-w-0 flex-1">
                              <b className="block text-[13.5px]">
                                {item.label}
                              </b>
                              <span className="text-[11.5px] text-muted">
                                {item.level === 1
                                  ? "Starter"
                                  : "Level " +
                                    item.level +
                                    (item.claimed
                                      ? " · earned"
                                      : " · eligible")}
                              </span>
                            </span>
                            <button
                              disabled={busy}
                              className={B + " !px-3 !text-[12px]"}
                              onClick={() => equip(item)}
                            >
                              {look[item.category] === item.value
                                ? "Selected"
                                : "Wear"}
                            </button>
                          </div>
                        ))}
                      </div>
                    </section>
                  );
                })}
              </>
            )}
            <p className="mt-5 text-[12px] text-secondary">
              Shuffle keeps your chosen skin tone. Save look applies every
              selected category.{" "}
              {account.registered
                ? "Level rewards use your earned account XP."
                : "This is a guest preview; sign in for account saving and earned items."}
            </p>
          </section>
        </div>
      )}
    </main>
  );
}

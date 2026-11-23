import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import CosmeticShop from "../components/CosmeticShop";
import AvatarArt, { UserAvatar } from "../components/AvatarArt";
import FlashBanner from "../components/FlashBanner";
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

export default function AvatarEditor() {
  const [account, setAccount] = useState<AvatarAccount | null>(null),
    [look, setLook] = useState<AvatarLook | null>(null),
    [tab, setTab] = useState<"Customize" | "Inventory" | "Shop">("Customize"),
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
      if (options.length) {
        next[cat] = options[Math.floor(Math.random() * options.length)].value;
      }
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

  const ownedCount = account
    ? account.catalog.filter((i) => i.available).length
    : 0;

  return (
    <main className="finna-page av-page">
      <header className="av-hero">
        <div className="av-hero-copy">
          <span className="cr-eyebrow">Profile · Avatar Studio</span>
          <h1>Avatar &amp; inventory</h1>
          <p>
            Customize your study avatar, browse earned level rewards, or unlock
            cosmetics with reward points.
          </p>
        </div>
        <div className="av-hero-actions">
          <Link to="/profile" className="cr-glass-btn">
            ← Profile
          </Link>
          <Link to="/profile/rewards" className="cr-glass-btn">
            Rewards wallet
          </Link>
        </div>
      </header>

      {loading && (
        <div role="status" className="finna-card text-sm text-secondary">
          Loading your saved look…
        </div>
      )}
      {error && (
        <FlashBanner
          kind="error"
          title="Could not load avatar"
          message={error}
          actionLabel="Reload"
          onAction={() => void load()}
          onDismiss={() => setError("")}
        />
      )}
      {notice && (
        <FlashBanner
          kind="success"
          title="Avatar updated"
          message={notice}
          onDismiss={() => setNotice("")}
        />
      )}

      {account && look && !loading && (
        <div className="av-layout">
          <aside className="av-stage-col">
            <div className="av-stage-card">
              <div className="av-stage-banner" />
              <div className="av-stage-body">
                <div className="av-stage-ring">
                  {initialsPreview ? (
                    <UserAvatar initials={account.handle} size={156} />
                  ) : (
                    <AvatarArt
                      look={look}
                      size={156}
                      label="Your avatar preview"
                    />
                  )}
                </div>
                <h2 className="av-stage-name">
                  {account.name || account.handle}
                </h2>
                <p className="av-stage-meta">
                  Level {account.level} · @{account.handle}
                </p>
                <span
                  className={
                    "av-stage-pill" + (dirty ? " is-dirty" : " is-saved")
                  }
                >
                  {dirty ? "Unsaved preview" : "Saved look ✓"}
                </span>

                <div className="av-stage-btns">
                  <button
                    type="button"
                    className="finna-st-btn"
                    disabled={busy}
                    onClick={shuffle}
                  >
                    Shuffle
                  </button>
                  {account.registered ? (
                    <button
                      type="button"
                      className="cr-primary-btn"
                      disabled={busy || !dirty}
                      onClick={() => void save()}
                    >
                      {busy ? "Saving…" : "Save look"}
                    </button>
                  ) : (
                    <Link className="cr-primary-btn" to="/login">
                      Sign in to save
                    </Link>
                  )}
                </div>

                <div className="av-stage-subactions">
                  <button
                    type="button"
                    className="av-text-btn"
                    disabled={busy || !dirty}
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
                      type="button"
                      className="av-text-btn"
                      disabled={busy}
                      onClick={() => void save(true)}
                    >
                      Use initials instead
                    </button>
                  )}
                </div>
              </div>
            </div>

            <p className="av-stage-note">
              Your saved avatar appears beside your profile, study desk seats,
              and public creator page. Privacy settings still apply.
            </p>
          </aside>

          <section className="av-workspace">
            <div className="av-tabs" role="group" aria-label="Avatar workspace">
              {(
                [
                  ["Customize", "Customize", null],
                  ["Inventory", "Inventory", ownedCount],
                  ["Shop", "Shop", null],
                ] as const
              ).map(([id, label, count]) => (
                <button
                  key={id}
                  type="button"
                  aria-pressed={tab === id}
                  onClick={() => setTab(id)}
                  className={"av-tab" + (tab === id ? " is-active" : "")}
                >
                  <span>{label}</span>
                  {count != null && <em className="av-tab-count">{count}</em>}
                </button>
              ))}
            </div>

            {tab === "Customize" ? (
              <div className="av-panel">
                <div
                  role="group"
                  aria-label="Avatar category"
                  className="av-cat-strip"
                >
                  {CATEGORIES.map(([cat, label]) => (
                    <button
                      key={cat}
                      type="button"
                      aria-pressed={category === cat}
                      onClick={() => setCategory(cat)}
                      className={
                        "av-cat-pill" + (category === cat ? " is-active" : "")
                      }
                    >
                      {label}
                    </button>
                  ))}
                </div>

                <div className="av-tile-grid">
                  {account.catalog
                    .filter((i) => i.category === category)
                    .map((item) => {
                      const selected =
                        !initialsPreview && look[item.category] === item.value;
                      return (
                        <button
                          key={item.id}
                          type="button"
                          disabled={!item.available || busy}
                          aria-pressed={selected}
                          onClick={() => equip(item)}
                          className={
                            "av-tile" +
                            (selected ? " is-selected" : "") +
                            (!item.available ? " is-locked" : "")
                          }
                        >
                          <span
                            className="av-tile-preview"
                            style={{
                              background: ["skin", "hairC", "bg"].includes(
                                item.category,
                              )
                                ? item.value
                                : AVATAR_COLORS[item.value] || "#E2E8F0",
                            }}
                          >
                            {["hair", "acc", "frame"].includes(
                              item.category,
                            ) && (
                              <AvatarArt
                                look={{ ...look, [item.category]: item.value }}
                                size={64}
                                label={item.label + " preview"}
                              />
                            )}
                            {selected && (
                              <span className="av-tile-check" aria-hidden="true">
                                ✓
                              </span>
                            )}
                          </span>
                          <span className="av-tile-title">{item.label}</span>
                          <span className="av-tile-sub">
                            {!item.available
                              ? item.price_points
                                ? `${item.price_points} pts · Shop`
                                : `Unlocks Lv. ${item.level}`
                              : selected
                                ? "Equipped"
                                : item.level === 1
                                  ? "Starter"
                                  : item.claimed
                                    ? item.price_points
                                      ? "Owned"
                                      : "Earned"
                                    : "Level reward"}
                          </span>
                        </button>
                      );
                    })}
                </div>
              </div>
            ) : tab === "Shop" ? (
              <div className="av-panel">
                <CosmeticShop
                  key={account.user_id}
                  account={account}
                  look={look}
                  onPurchased={setAccount}
                />
              </div>
            ) : (
              <div className="av-panel">
                <p className="text-sm text-secondary">
                  Starter items are free. Saving a look claims eligible level
                  rewards permanently. Cosmetics never affect XP or ranks.
                </p>
                {CATEGORIES.map(([cat, label]) => {
                  const items = account.catalog.filter(
                    (i) => i.category === cat && i.available,
                  );
                  return (
                    <section key={cat} className="av-inv-group">
                      <div className="finna-st-grouplabel">
                        {label} · {items.length}
                      </div>
                      <div className="av-inv-grid">
                        {items.map((item) => {
                          const selected =
                            !initialsPreview &&
                            look[item.category] === item.value;
                          return (
                            <div key={item.id} className="av-inv-row">
                              <AvatarArt
                                look={{ ...look, [item.category]: item.value }}
                                size={38}
                                label={item.label + " preview"}
                              />
                              <div className="av-inv-meta">
                                <strong>{item.label}</strong>
                                <small>
                                  {item.price_points
                                    ? "Points purchase · owned"
                                    : item.level === 1
                                      ? "Starter"
                                      : `Level ${item.level}${item.claimed ? " · earned" : " · eligible"}`}
                                </small>
                              </div>
                              <button
                                type="button"
                                disabled={busy}
                                className={
                                  "finna-st-btn" +
                                  (selected ? " finna-st-btn--primary" : "")
                                }
                                onClick={() => equip(item)}
                              >
                                {selected ? "Equipped" : "Wear"}
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    </section>
                  );
                })}
              </div>
            )}

            <p className="av-foot-note">
              Shuffle keeps your chosen skin tone. Save look applies every
              selected category.{" "}
              {account.registered
                ? "Level rewards use your earned account XP."
                : "Guest preview · sign in to save and claim earned items."}
            </p>
          </section>
        </div>
      )}
    </main>
  );
}

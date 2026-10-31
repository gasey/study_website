import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHome, type HomeData } from "../lib/api";
import { reviewRequest } from "../lib/review";
import {
  EVENT_KINDS,
  indiaToday,
  type CalendarEvent,
  type EventKind,
} from "../lib/calendar";
const INPUT =
  "min-h-11 w-full rounded-[6px] border border-[#CFC5B2] bg-[#FBF8F1] px-3 py-2 text-[13px]";
const BTN =
  "min-h-11 rounded-pill border border-hairline px-4 py-2 text-[13px] font-semibold disabled:opacity-40";
type Draft = Pick<
  CalendarEvent,
  | "title"
  | "kind"
  | "summary"
  | "source_url"
  | "source_reference"
  | "verification_note"
  | "verified_on"
  | "state"
> & { collection_id: string; starts_on: string; ends_on: string };
const blank = (): Draft => ({
  title: "",
  kind: "notification",
  collection_id: "",
  starts_on: "",
  ends_on: "",
  summary: "",
  source_url: "",
  source_reference: "",
  verification_note: "",
  verified_on: indiaToday(),
  state: "draft",
});
export default function CalendarAdmin() {
  const [items, setItems] = useState<CalendarEvent[]>([]);
  const [exams, setExams] = useState<HomeData["collections"]>([]);
  const [draft, setDraft] = useState<Draft>(blank);
  const [id, setId] = useState("");
  const [version, setVersion] = useState(0);
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);
  const [history, setHistory] = useState<
    { version: number; reason: string; created_at: string }[]
  >([]);
  useEffect(() => {
    let live = true;
    setLoading(true);
    setError("");
    reviewRequest<{ items: CalendarEvent[] }>(
      "/admin/calendar?offset=" + offset,
    )
      .then((r) => {
        if (live) setItems(r.items);
      })
      .catch((e) => {
        if (live) setError(e.message);
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [offset, reload]);
  useEffect(() => {
    getHome()
      .then((h) => setExams(h.collections))
      .catch(() => {});
  }, []);
  useEffect(() => {
    let live = true;
    setHistory([]);
    if (id)
      reviewRequest<{ items: typeof history }>(
        "/admin/calendar/" + id + "/history",
      )
        .then((r) => {
          if (live) setHistory(r.items);
        })
        .catch((e) => {
          if (live) setError(e.message);
        });
    return () => {
      live = false;
    };
  }, [id, version]);
  function edit(e: CalendarEvent) {
    setId(e.id);
    setVersion(e.version);
    setReason("");
    setNotice("");
    setError("");
    setDraft({
      title: e.title,
      kind: e.kind,
      summary: e.summary,
      collection_id: e.collection_id || "",
      starts_on: e.starts_on || "",
      ends_on: e.ends_on || "",
      source_url: e.source_url,
      source_reference: e.source_reference,
      verification_note: e.verification_note,
      verified_on: e.verified_on,
      state: e.state,
    });
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const key = id || "cal_" + crypto.randomUUID();
      const r = await reviewRequest<CalendarEvent>("/admin/calendar/" + key, {
        expected_version: version,
        reason,
        event: {
          ...draft,
          collection_id: draft.collection_id || null,
          starts_on: draft.starts_on || null,
          ends_on: draft.ends_on || null,
        },
      });
      edit(r);
      setNotice("Saved version " + r.version + " · " + r.state);
      setReload((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  function field<K extends keyof Draft>(k: K, v: Draft[K]) {
    setDraft((d) => ({ ...d, [k]: v }));
  }
  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-[30px]">
          Calendar & official notices
        </h2>
        <Link to="/calendar" className="text-[13px] text-link underline">
          Public calendar →
        </Link>
      </div>
      <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-secondary">
        Check the exact official source before publishing. Record revisions and
        withdrawals here; inbox subscribers receive updates. Calendar dates are
        all-day, so include exact closing/reporting times in the summary when
        confirmed.
      </p>
      {error && (
        <p role="alert" className="mt-3 text-mypick">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="mt-3 text-keyed">
          {notice}
        </p>
      )}
      <div className="mt-5 grid items-start gap-5 xl:grid-cols-[minmax(230px,1fr)_minmax(0,2fr)]">
        <aside className="grid gap-2">
          <button
            disabled={busy}
            className={BTN}
            onClick={() => {
              setId("");
              setVersion(0);
              setDraft(blank());
              setReason("");
              setNotice("");
            }}
          >
            New notice / event
          </button>
          {loading ? (
            <p>Loading notices…</p>
          ) : (
            items.map((e) => (
              <button
                key={e.id}
                disabled={busy}
                className={
                  "rounded-[8px] border p-3 text-left " +
                  (id === e.id
                    ? "border-ink bg-[#E3E9F8]"
                    : "border-hairline bg-card")
                }
                onClick={() => edit(e)}
              >
                <span className="block text-[11px] uppercase text-muted">
                  {e.state} · v{e.version} · {e.starts_on || "No date"}
                </span>
                <span className="mt-1 block text-[14px] font-semibold">
                  {e.title}
                </span>
              </button>
            ))
          )}
          {!loading && !items.length && (
            <p className="text-[13px] text-muted">No entries yet.</p>
          )}
          <div className="flex justify-between gap-2">
            <button
              className={BTN}
              disabled={!offset || busy}
              onClick={() => setOffset((n) => Math.max(0, n - 50))}
            >
              Previous
            </button>
            <button
              className={BTN}
              disabled={items.length < 50 || busy}
              onClick={() => setOffset((n) => n + 50)}
            >
              Next
            </button>
          </div>
        </aside>
        <form
          onSubmit={(e) => void save(e)}
          className="rounded-[10px] border border-hairline bg-card p-5"
        >
          <fieldset disabled={busy} className="grid gap-4">
            <legend className="mb-4 font-display text-[24px]">
              {id ? "Edit notice · v" + version : "New draft"}
            </legend>
            <label className="text-[13px]">
              Title
              <input
                required
                minLength={3}
                maxLength={180}
                className={INPUT}
                value={draft.title}
                onChange={(e) => field("title", e.target.value)}
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-[13px]">
                Type
                <select
                  className={INPUT}
                  value={draft.kind}
                  onChange={(e) => field("kind", e.target.value as EventKind)}
                >
                  {Object.entries(EVENT_KINDS).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-[13px]">
                Related exam
                <select
                  className={INPUT}
                  value={draft.collection_id}
                  onChange={(e) => field("collection_id", e.target.value)}
                >
                  <option value="">No matching exam collection</option>
                  {exams.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.title}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-[13px]">
                Start / event date
                <input
                  type="date"
                  required={draft.kind !== "notification"}
                  className={INPUT}
                  value={draft.starts_on}
                  onChange={(e) => field("starts_on", e.target.value)}
                />
              </label>
              <label className="text-[13px]">
                End date (optional, inclusive)
                <input
                  type="date"
                  className={INPUT}
                  min={draft.starts_on}
                  value={draft.ends_on}
                  onChange={(e) => field("ends_on", e.target.value)}
                />
              </label>
            </div>
            <label className="text-[13px]">
              Summary & instructions
              <textarea
                maxLength={3000}
                rows={4}
                className={INPUT}
                value={draft.summary}
                onChange={(e) => field("summary", e.target.value)}
              />
            </label>
            <label className="text-[13px]">
              Official source URL
              <input
                type="url"
                required
                maxLength={2000}
                placeholder="https://mpsc.mizoram.gov.in/…"
                className={INPUT}
                value={draft.source_url}
                onChange={(e) => field("source_url", e.target.value)}
              />
            </label>
            <label className="text-[13px]">
              Notice / advertisement reference
              <input
                required
                minLength={3}
                maxLength={300}
                className={INPUT}
                value={draft.source_reference}
                onChange={(e) => field("source_reference", e.target.value)}
              />
            </label>
            <label className="text-[13px]">
              What was verified?
              <textarea
                required
                minLength={10}
                maxLength={1000}
                rows={2}
                className={INPUT}
                value={draft.verification_note}
                onChange={(e) => field("verification_note", e.target.value)}
              />
            </label>
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-[13px]">
                Verified on
                <input
                  type="date"
                  required
                  max={indiaToday()}
                  className={INPUT}
                  value={draft.verified_on}
                  onChange={(e) => field("verified_on", e.target.value)}
                />
              </label>
              <label className="text-[13px]">
                Publication state
                <select
                  className={INPUT}
                  value={draft.state}
                  onChange={(e) =>
                    field("state", e.target.value as Draft["state"])
                  }
                >
                  <option value="draft">Draft · private</option>
                  <option value="published">Published · public</option>
                  <option value="archived">
                    Withdrawn · remove from dates
                  </option>
                </select>
              </label>
            </div>
            <label className="text-[13px]">
              Reason for this revision
              <textarea
                required
                minLength={10}
                maxLength={1000}
                rows={2}
                className={INPUT}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            <button className={BTN + " bg-ink text-paper"}>
              {busy ? "Saving…" : "Save " + draft.state + " revision"}
            </button>
          </fieldset>
          {history.length > 0 && (
            <section className="mt-6 border-t border-hairline pt-4">
              <h3 className="font-semibold">Revision history</h3>
              {history.map((h) => (
                <p
                  key={h.version}
                  className="mt-2 text-[12px] leading-relaxed text-secondary"
                >
                  v{h.version} ·{" "}
                  {new Date(h.created_at).toLocaleString("en-IN")} · {h.reason}
                </p>
              ))}
            </section>
          )}
        </form>
      </div>
    </section>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { reviewRequest, reviewSession } from "../lib/review";
interface Item {
  source_links?: { url: string; note: string }[];
  id: string;
  post_id: number | null;
  canonical_id: string | null;
  question: string | null;
  body: string;
  author: string;
  note: string | null;
  reasons: string[];
  report_count: number;
  item_type: string;
}
const B =
  "min-h-11 rounded-pill border border-hairline px-4 text-[13px] font-semibold disabled:opacity-50";
export default function DiscussionAdmin() {
  const [tab, setTab] = useState("New users");
  const [items, setItems] = useState<Item[]>([]);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [counts, setCounts] = useState<Record<string, number>>({});
  async function load() {
    setError("");
    try {
      await reviewSession();
      const q = await reviewRequest<{
        items: Item[];
        counts: Record<string, number>;
      }>("/community/admin/queue?tab=" + encodeURIComponent(tab));
      setItems(q.items);
      setCounts(q.counts);
    } catch (e) {
      setItems([]);
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, [tab]);
  async function action(item: Item, action: string) {
    setBusy(true);
    try {
      await reviewRequest(
        "/community/admin/posts/" + item.post_id + "/action",
        { action, note: reason || null },
      );
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function lock(qid: string, enabled: boolean) {
    setBusy(true);
    try {
      await reviewRequest("/community/admin/questions/" + qid + "/lock", {
        enabled,
        reason,
      });
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="mx-auto max-w-[1000px] px-6 pb-24 pt-9">
      <Link to="/admin/bank?tab=workflow" className="text-[13px] text-link">
        ← Publishing dashboard
      </Link>
      <h1 className="mt-3 font-display text-[36px]">
        Question discussion moderation
      </h1>
      <p className="mt-2 text-[14px] text-secondary">
        Review conduct and first posts. Answer correctness follows the
        correction-review workflow. Owner permission and staff authenticator
        verification are required for changes.
      </p>
      <div className="mt-3 flex flex-wrap gap-4 text-[13px]">
        <span>{counts.pending_posts || 0} awaiting moderation</span>
        <span>{counts.open_reports || 0} reported posts</span>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {["New users", "Reported", "My actions"].map((t) => (
          <button
            key={t}
            aria-pressed={tab === t}
            className={B + (tab === t ? " bg-ink text-paper" : "")}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      <label className="mt-4 block text-[13px] font-semibold">
        Moderation reason (required for rejection, hiding and thread locks)
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          maxLength={1000}
          className="mt-2 w-full rounded-[6px] border border-hairline bg-card p-3"
        />
      </label>
      {error && (
        <p role="alert" className="mt-4 text-mypick">
          {error}
        </p>
      )}
      <div className="mt-5 space-y-4">
        {items.map((item) => (
          <article
            key={item.id}
            className="rounded-[8px] border border-hairline bg-card p-5"
          >
            <p className="text-[12px] text-muted">
              {item.author} · {item.reasons.join(", ")} · {item.report_count}{" "}
              reports
            </p>
            <h2 className="mt-2 font-display text-[23px]">{item.question}</h2>
            <p className="mt-3 whitespace-pre-wrap break-words text-[14px]">
              {item.body}
            </p>
            {item.source_links?.map((s, i) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noreferrer nofollow ugc"
                className="mt-2 block break-words text-[13px] text-link underline"
              >
                {s.note} ↗
              </a>
            ))}
            {item.note && (
              <p className="mt-2 text-[13px] text-secondary">{item.note}</p>
            )}
            <div className="mt-4 flex flex-wrap gap-2">
              {tab === "New users" && (
                <>
                  <button
                    disabled={busy}
                    className={B}
                    onClick={() => void action(item, "approve")}
                  >
                    Approve
                  </button>
                  <button
                    disabled={busy || reason.trim().length < 10}
                    className={B}
                    onClick={() => void action(item, "reject")}
                  >
                    Reject
                  </button>
                </>
              )}
              {tab === "Reported" && (
                <>
                  <button
                    disabled={busy || reason.trim().length < 10}
                    className={B}
                    onClick={() => void action(item, "hide")}
                  >
                    Hide post
                  </button>
                  <button
                    disabled={busy}
                    className={B}
                    onClick={() => void action(item, "dismiss")}
                  >
                    Dismiss reports
                  </button>
                </>
              )}
              {item.canonical_id && (
                <>
                  <Link
                    className={B + " inline-flex items-center text-link"}
                    to={
                      "/bank/" +
                      item.canonical_id +
                      "?post=" +
                      item.post_id +
                      "#discussion"
                    }
                  >
                    Open question
                  </Link>
                  <button
                    disabled={busy || reason.trim().length < 10}
                    className={B}
                    onClick={() => void lock(item.canonical_id!, true)}
                  >
                    Lock discussion
                  </button>
                  <button
                    disabled={busy || reason.trim().length < 10}
                    className={B}
                    onClick={() => void lock(item.canonical_id!, false)}
                  >
                    Unlock
                  </button>
                </>
              )}
            </div>
          </article>
        ))}
      </div>
      {!items.length && !error && (
        <p className="mt-5 text-secondary">No items in this queue.</p>
      )}
      <button className={B + " mt-5"} onClick={() => void load()}>
        Refresh queue
      </button>
    </main>
  );
}

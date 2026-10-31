import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { reviewRequest } from "../lib/review";
interface Report {
  id: number;
  desk_id: string;
  target_kind: string;
  target_id: string;
  reason: string;
  snapshot: Record<string, unknown>;
  created_at: string;
}
export default function DeskAdmin() {
  const [reports, setReports] = useState<Report[]>([]);
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() {
    try {
      const r = await reviewRequest<{ items: Report[] }>("/desk/admin/reports");
      setReports(r.items);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  async function resolve(r: Report, action: "dismiss" | "remove") {
    setBusy(true);
    setError("");
    try {
      await reviewRequest("/desk/admin/reports/" + r.id + "/resolve", {
        reason,
        action,
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
      <h1 className="mt-3 font-display text-[36px]">Private desk reports</h1>
      <p className="mt-2 text-[14px] leading-relaxed text-secondary">
        Access is limited to reported snapshots, and viewing this queue is
        audited. Private desks cannot be browsed through this console. Resolve
        with a reason; removal applies only to the exact reported item/message
        version.
      </p>
      <label className="mt-5 block text-[13px] font-semibold">
        Review reason
        <textarea
          minLength={10}
          maxLength={2000}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className="desk-v3-input mt-2"
        />
      </label>
      {error && (
        <p role="alert" className="mt-3 text-mypick">
          {error}
        </p>
      )}
      <div className="mt-5 space-y-4">
        {reports.map((r) => (
          <article key={r.id} className="desk-v3-card">
            <p className="desk-v3-label">
              {r.target_kind} · {new Date(r.created_at).toLocaleString("en-IN")}
            </p>
            <p className="mt-3 text-[14px]">Report: {r.reason}</p>
            <pre className="mt-3 whitespace-pre-wrap break-words rounded-[6px] bg-paper p-3 text-[12px]">
              {JSON.stringify(r.snapshot, null, 2)}
            </pre>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="desk-v3-button"
                disabled={busy || reason.trim().length < 10}
                onClick={() => void resolve(r, "dismiss")}
              >
                Resolve without removal
              </button>
              {["item", "message"].includes(r.target_kind) && (
                <button
                  className="desk-v3-button text-mypick"
                  disabled={busy || reason.trim().length < 10}
                  onClick={() => void resolve(r, "remove")}
                >
                  Remove reported content
                </button>
              )}
            </div>
          </article>
        ))}
      </div>
      {!reports.length && !error && (
        <p className="mt-5 text-secondary">
          No private desk reports are waiting.
        </p>
      )}
      <button className="desk-v3-button mt-5" onClick={() => void load()}>
        Refresh reports
      </button>
    </main>
  );
}

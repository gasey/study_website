import { useEffect, useRef, useState } from "react";
import { accountGeneration } from "../lib/accountContext";
import { deskWrite, type SharedItem } from "../lib/studyDesks";

export default function DeskDiscussionButton({ deskId, item, onChange }: {
  deskId: string; item: SharedItem; onChange: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  const generation = useRef(accountGeneration()), lifetime = useRef(0), active = useRef(false);
  useEffect(() => {
    active.current = true; ++lifetime.current; generation.current = accountGeneration();
    setBusy(false); setError("");
    const reset = () => { active.current = false; ++lifetime.current; setBusy(false); setError(""); };
    window.addEventListener("ism-auth-change", reset); window.addEventListener("ism-auth-expired", reset);
    return () => { reset(); window.removeEventListener("ism-auth-change", reset); window.removeEventListener("ism-auth-expired", reset); };
  }, [deskId, item.id]);
  async function update() {
    const run = lifetime.current;
    const valid = () => active.current && run === lifetime.current && generation.current === accountGeneration();
    if (busy || !valid()) return;
    setBusy(true); setError("");
    try {
      await deskWrite("/rooms/" + deskId + "/items/" + item.id + "/discussion", {
        expected_version: item.version, state: item.discussion_state === "needed" ? "resolved" : "needed",
      });
      if (valid()) await onChange();
    } catch (e) { if (valid()) setError((e as Error).message); }
    finally { if (valid()) setBusy(false); }
  }
  return <span className="min-w-0">
    <button className="desk-v3-button" disabled={busy} onClick={() => void update()}>
      {busy ? "Saving discussion…" : item.discussion_state === "needed" ? "Mark discussion resolved" : item.discussion_state === "resolved" ? "Reopen discussion" : "Discuss this"}
    </button>
    {error && <span role="alert" className="mt-2 block break-words text-sm text-secondary">{error} Refresh desk before trying again.</span>}
  </span>;
}

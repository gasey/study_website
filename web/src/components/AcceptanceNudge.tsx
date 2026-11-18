import { useEffect, useRef, useState } from 'react';
import { reviewRequest } from '../lib/review';

/** Mounted only inside an author's open doubt with published, unaccepted replies. */
export default function AcceptanceNudge({ postId }: { postId: number }) {
  const [shown, setShown] = useState(false);
  const claim = useRef<{ id: number; promise: Promise<{ prompt: boolean }> }>();
  useEffect(() => {
    let active = true;
    setShown(false);
    // Reuse the in-flight claim during React's effect replay. The server owns
    // the durable once-only decision; no reminder state goes in local storage.
    if (claim.current?.id !== postId) {
      claim.current = { id: postId, promise: reviewRequest<{ prompt: boolean }>('/community/posts/' + postId + '/acceptance-nudge', {}) };
    }
    claim.current.promise.then(result => {
      if (active) setShown(result.prompt);
    }).catch(() => { /* Optional prompt: an uncertain response never nags again. */ });
    return () => { active = false; };
  }, [postId]);
  if (!shown) return null;
  return <aside aria-label="Acceptance reminder" className="rounded-[8px] border border-hairline bg-community-soft p-3 text-[13px] text-primary">
    <p className="font-semibold">Did one of these solve it?</p>
    <p className="mt-1">You can mark a reply with “Accept reply” to help others find the answer.</p>
    <button type="button" onClick={() => setShown(false)} className="mt-2 min-h-[44px] rounded-button border border-hairline bg-card px-3 font-semibold">Not now</button>
  </aside>;
}

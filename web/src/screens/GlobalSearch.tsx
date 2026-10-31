import {scopedApiPath} from '../lib/examScope'
import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";
import { deviceId } from "../lib/device";
const TABS = {
  all: "All",
  questions: "Questions",
  people: "People",
  notes: "Notes & materials",
  desks: "Your desks",
  listings: "Listings",
  exams: "Exams",
} as const;
type Category = keyof typeof TABS;
interface Group {
  category: Exclude<Category, "all">;
  total: number;
  items: {
    id: string;
    title: string;
    meta: string;
    snippet: string;
    url: string;
  }[];
}
export default function GlobalSearch() {
  const [params, setParams] = useSearchParams();
  const location=useLocation();
  function resultTarget(item:Group['items'][number]) {
    if(!item.url.startsWith('/materials/'))return item.url
    const next=new URLSearchParams(params);next.set('read_material',item.id)
    if(item.id==='cms-paid-demo')next.set('material_preview','true');else next.delete('material_preview')
    return location.pathname+'?'+next.toString()+location.hash
  }
  const q = params.get("q") || "";
  const raw = params.get("category") || "all";
  const category: Category = raw in TABS ? (raw as Category) : "all";
  const rawOffset = Number(params.get("offset") || 0);
  const offset =
    Number.isInteger(rawOffset) && rawOffset >= 0 && rawOffset <= 10000
      ? rawOffset
      : 0;
  const [input, setInput] = useState(q);
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const generation = useRef(0);
  useEffect(() => setInput(q), [q]);
  useEffect(() => {
    const changed = () => {
      generation.current++;
      setGroups([]);
      setReload((n) => n + 1);
    };
    window.addEventListener("ism-auth-change", changed);
    return () => window.removeEventListener("ism-auth-change", changed);
  }, []);
  useEffect(() => {
    const current = ++generation.current;
    const abort = new AbortController();
    setGroups([]);
    setError("");
    if (q.trim().length < 2) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetch(
      "/api" + scopedApiPath("/search?" + new URLSearchParams({ q, category, offset: String(offset) })),
      {
        credentials: "include",
        cache: "no-store",
        headers: { "x-device-id": deviceId() },
        signal: abort.signal,
      },
    )
      .then(async (r) => {
        if (!r.ok) throw new Error("Search could not load. Please retry.");
        return r.json();
      })
      .then((r) => {
        if (current === generation.current) setGroups(r.groups);
      })
      .catch((e) => {
        if (!abort.signal.aborted && current === generation.current)
          setError(e.message);
      })
      .finally(() => {
        if (current === generation.current) setLoading(false);
      });
    return () => abort.abort();
  }, [q, category, offset, reload]);
  const change = (c: Category, position = 0) =>
    setParams({
      q,
      category: c,
      ...(position ? { offset: String(position) } : {}),
    });
  return (
    <main className="mx-auto max-w-shell px-4 pb-24 pt-8 sm:px-6">
      <h1 className="font-display text-[36px]">Search India Study Map</h1>
      <form
        className="mt-5 flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (input.trim().length >= 2)
            setParams({ q: input.trim(), category });
        }}
      >
        <input
          type="search"
          aria-label="Search questions, people, notes, desks and listings"
          maxLength={120}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Search questions, people, notes, desks, listings"
          className="h-14 min-w-0 flex-1 rounded-[8px] border border-ink bg-[#FBF8F1] px-4 font-display text-[20px]"
        />
        <button className="min-h-11 rounded-pill bg-ink px-4 font-semibold text-paper">
          Search
        </button>
      </form>
      <div
        className="mt-[18px] flex gap-[22px] overflow-x-auto border-b border-ink"
        role="tablist"
        aria-label="Search categories"
      >
        {Object.entries(TABS).map(([key, label]) => (
          <button
            key={key}
            role="tab"
            type="button"
            aria-selected={category === key}
            onClick={() => change(key as Category)}
            className={
              "min-h-11 shrink-0 border-b-2 py-2 text-[14px] font-semibold " +
              (category === key
                ? "border-ink text-ink"
                : "border-transparent text-secondary")
            }
          >
            {label}
            {key !== "all" && groups.find((g) => g.category === key) && (
              <span className="ml-2 font-mono text-[11px] font-normal">
                {groups.find((g) => g.category === key)!.total}
              </span>
            )}
          </button>
        ))}
      </div>
      <p className="mt-3 text-[12px] text-muted">
        People appear through public creator profiles. Private notes and desks
        are visible only to their account or members. Listings currently contain
        published paid-content previews.
      </p>
      {loading && (
        <p role="status" className="mt-8 text-secondary">
          Searching…
        </p>
      )}
      {error && (
        <div role="alert" className="mt-8 text-mypick">
          {error}
          <button
            className="ml-3 min-h-11 underline"
            onClick={() => setReload((n) => n + 1)}
          >
            Retry
          </button>
        </div>
      )}
      {!loading && !error && q.trim().length < 2 && (
        <p className="mt-8 text-secondary">
          Enter at least two characters to search.
        </p>
      )}
      {!loading &&
        !error &&
        q.trim().length >= 2 &&
        !groups.some((g) => g.total > 0) && (
          <p className="mt-8 text-secondary">
            Nothing matches “{q}” in this category. Try a topic, creator handle
            or exam name.
          </p>
        )}
      {!loading &&
        groups
          .filter((g) => g.total > 0)
          .map((g) => (
            <section key={g.category} className="mt-[26px]">
              <div className="flex items-baseline justify-between gap-3">
                <h2 className="font-mono text-[11px] uppercase tracking-wider text-link">
                  {TABS[g.category]} · {g.total.toLocaleString("en-IN")}
                </h2>
                {category === "all" && g.total > g.items.length && (
                  <button
                    type="button"
                    className="min-h-11 text-[13px] font-semibold text-link"
                    onClick={() => change(g.category)}
                  >
                    See all →
                  </button>
                )}
              </div>
              {g.items.map((item) => (
                <Link
                  key={item.id}
                  to={resultTarget(item)}
                  state={item.url.startsWith('/materials/')?{materialReaderFrom:location.pathname+location.search+location.hash}:undefined}
                  preventScrollReset={item.url.startsWith('/materials/')}
                  className="block border-b border-hairline py-[13px] hover:bg-[#EFE8DA]"
                >
                  <h3 className="font-display text-[20px] leading-snug">
                    {item.title}
                  </h3>
                  <p className="mt-1 text-[12px] text-muted">{item.meta}</p>
                  {item.snippet && (
                    <p className="mt-1 line-clamp-2 text-[13px] leading-relaxed text-secondary">
                      {item.snippet}
                    </p>
                  )}
                </Link>
              ))}
            </section>
          ))}
      {category !== "all" &&
        !!groups[0] &&
        (offset > 0 || groups[0].total > 20) && (
          <nav
            aria-label="Search pages"
            className="mt-5 flex items-center justify-between"
          >
            <button
              className="min-h-11 rounded-pill border border-hairline px-4 disabled:opacity-40"
              disabled={!offset}
              onClick={() => change(category, Math.max(0, offset - 20))}
            >
              Previous
            </button>
            <span className="text-[12px]">
              Page {Math.floor(offset / 20) + 1}
            </span>
            <button
              className="min-h-11 rounded-pill border border-hairline px-4 disabled:opacity-40"
              disabled={offset + 20 >= groups[0].total}
              onClick={() => change(category, offset + 20)}
            >
              Next
            </button>
          </nav>
        )}
    </main>
  );
}

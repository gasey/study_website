import { useEffect, useState } from "react";
import { reviewRequest } from "../lib/review";
type MapData = {
  tables: { id: string; title: string; total: number }[];
  coverage: {
    questions: number;
    without_topic: number;
    without_subtopic: number;
  };
  relationships: [string, string, string][];
};
export default function DatabaseMap() {
  const [data, setData] = useState<MapData | null>(null),
    [selected, setSelected] = useState("canonical_questions"),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    reviewRequest<MapData>("/admin/bank/database-map")
      .then((d) => {
        if (live) setData(d);
      })
      .catch((e) => {
        if (live) setError(e.message);
      });
    return () => {
      live = false;
    };
  }, []);
  return (
    <section className="mt-5 min-w-0">
      <h2 className="font-display text-[30px]">Your database, visually</h2>
      <p className="mt-2 max-w-[760px] text-[14px] leading-relaxed text-secondary">
        One shared question connects source papers, topics, exams, discussions
        and study history. Select a card to see its relationships. These are
        live database counts; printed appearances and shared questions can
        differ.
      </p>
      {error && (
        <p role="alert" className="mt-4 text-mypick">
          {error}
        </p>
      )}
      {!data && !error && <p className="mt-4">Loading database map…</p>}
      {data && (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.tables.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelected(t.id)}
                aria-pressed={selected === t.id}
                className={
                  "min-w-0 rounded-[12px] border p-5 text-left " +
                  (selected === t.id
                    ? "border-link bg-[#E3E9F8]"
                    : "border-hairline bg-card")
                }
              >
                <span className="font-display text-[23px]">{t.title}</span>
                <strong className="mt-2 block font-display text-[30px]">
                  {t.total.toLocaleString("en-IN")}
                </strong>
                <span className="mt-2 block break-all font-mono text-[10px] text-muted">
                  {t.id}
                </span>
              </button>
            ))}
          </div>
          <div className="mt-4 rounded-[12px] border border-hairline bg-card p-5">
            <h3 className="font-display text-[24px]">
              Connected to this table
            </h3>
            {data.relationships
              .filter((r) => r[0] === selected || r[1] === selected)
              .map((r) => (
                <div
                  key={r.join(":")}
                  className="mt-3 flex flex-wrap items-center gap-2 text-[13px]"
                >
                  <button
                    className="min-h-11 break-all font-semibold text-link underline"
                    onClick={() => setSelected(r[0])}
                  >
                    {data.tables.find((t) => t.id === r[0])?.title}
                  </button>
                  <span>→ {r[2]} →</span>
                  <button
                    className="min-h-11 break-all font-semibold text-link underline"
                    onClick={() => setSelected(r[1])}
                  >
                    {data.tables.find((t) => t.id === r[1])?.title}
                  </button>
                </div>
              ))}
            {!data.relationships.some(
              (r) => r[0] === selected || r[1] === selected,
            ) && (
              <p className="mt-3 text-[13px] text-secondary">
                Community materials have their own publication and audience
                controls. Embedded question blocks reference the shared bank.
              </p>
            )}
          </div>
          <div className="mt-5 rounded-[12px] border border-hairline bg-[#F6EACB] p-5">
            <h3 className="font-display text-[23px]">Topic coverage</h3>
            <p className="mt-2 text-[14px]">
              {data.coverage.without_topic.toLocaleString("en-IN")} of{" "}
              {data.coverage.questions.toLocaleString("en-IN")} primary
              classifications have no narrower topic. Related topic links extend
              the primary path; they do not replace its history.
            </p>
            <p className="mt-3 text-[13px]">
              Broad subject approval does not establish answer correctness.
              Further classification goes through evidence, independent review
              and publication.
            </p>
          </div>
        </>
      )}
    </section>
  );
}

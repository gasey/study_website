/** Footer, ported from markup line 162. Near-black #14130F with warm grey
 *  #CFC7B8 text — darker than ink, and the only place that colour is used. */
export default function Footer() {
  return (
    <div className="mt-[72px] bg-[#14130F] text-[#CFC7B8]">
      <div className="mx-auto flex max-w-shell flex-wrap justify-between gap-3 px-6 py-[22px] font-mono text-[12px]">
        <span>India Study Map · Aizawl</span>
        <span>Questions sourced from MPSC papers · Answers labelled by provenance</span>
      </div>
    </div>
  )
}

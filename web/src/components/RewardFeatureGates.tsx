export interface RewardLaunchGates {
 catalog_ready:boolean
 checks:{key:string;label:string;ready:boolean;detail:string}[]
 checkout_managed_by:string
 rule_version:string
}

export default function RewardFeatureGates({gates}:{gates:RewardLaunchGates|null}){
 return <section aria-label="Reward launch checklist" className="ism-card-surface mt-5 rounded-[18px] border border-hairline bg-card p-5">
  <h2 className="font-display text-[26px]">Launch checklist</h2>
  <p className="mt-2 text-[13px] text-secondary">Opening earned Pro requires every check below. The server checks again when saving an offer and redeeming points.</p>
  {!gates?<p role="status" className="mt-3 text-[13px] text-secondary">Launch checks unavailable. Redemption controls stay disabled.</p>:<>
   <ul className="mt-4 space-y-3">{gates.checks.map(c=><li key={c.key} className="rounded-[12px] border border-hairline p-3 text-[13px]">
    <div className="flex flex-wrap items-start justify-between gap-2"><strong>{c.label}</strong><span className={c.ready?'text-correct-dark':'text-secondary'}>{c.ready?'Ready':'Pending'}</span></div>
    <p className="mt-1 text-secondary">{c.detail}</p>
   </li>)}</ul>
   <p className="mt-3 text-[13px] text-secondary">{gates.catalog_ready?'Checklist complete. The owner may enable an offer below.':'Catalog launch is blocked until the checklist is complete.'}</p>
   <button type="button" disabled className="mt-3 min-h-11 rounded-pill border border-hairline px-4 text-[13px] disabled:opacity-50">Checkout is managed through {gates.checkout_managed_by}</button>
  </>}
 </section>
}

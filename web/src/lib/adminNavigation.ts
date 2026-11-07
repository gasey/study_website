/** Stable tab IDs preserve bookmarks while task labels can evolve. */
export type AdminGrant={role:string;subject_id:string|null}
export const ADMIN_SECTIONS=[
 ['overview','Overview','daily','staff','See coverage, recorded work and what to fill or correct next.'],
 ['questions','Questions','daily','staff','Find a question, inspect its source and record a reviewed decision.'],
 ['organization','Modules & schemes','daily','inventory','Reuse sources, manage current and legacy schemes, and check original-paper readiness.'],
 ['current-affairs','Current affairs connections','review','staff','Link historical questions to independently reviewed dated facts and later papers.'],
 ['retag','Learning tags','review','inventory','Find reported or missing tags and apply authorised admin corrections.'],
 ['workflow','Review queue','review','owner','Review submitted corrections, materials and reports in one queue.'],
 ['exams','Papers','daily','inventory','Manage exam coverage, source papers and printed paper identities.'],
 ['pdf-library','PDF Library','sources','inventory','Find source PDFs, continue imports and check what still needs attention.'],
 ['intake','Add papers','sources','inventory','Track a source paper from discovery through review and publication.'],
 ['quality','Bank quality','sources','staff','Find coverage gaps and questions that need source or answer review.'],
 ['papers','Paper archive','sources','inventory','Browse the existing exam and paper inventory.'],
 ['review','Community corrections','review','staff','Review proposed bank changes in your permitted subjects.'],
 ['reports','Question reports','review','staff','Inspect reported questions and record the resolution.'],
 ['publications','Publication history','review','staff','Track your corrections, publication dates and saved before-and-after changes.'],
 ['content','Notes & lessons','community','owner','Review learner materials and manage their published revisions.'],
 ['discussions','Discussion moderation','community','owner','Review reported discussions and moderation decisions.'],
 ['desks','Study desk reports','community','owner','Investigate reports from private study desks.'],
 ['calendar','Calendar & notices','community','owner','Check source notices and publish dated exam updates.'],
 ['rewards','Rewards & accounts','system','owner','Inspect reward receipts, account events and earned-benefit settings.'],
 ['people','People & permissions','system','owner','Manage explicitly granted staff roles and subject access.'],
 ['audit','Audit history','system','owner','Inspect recorded admin actions and their reasons.'],
 ['modules','Module comparisons','reference','owner','Use module comparisons as evidence for bank corrections.'],
 ['taxonomy','Taxonomy reference','reference','staff','Browse the registered subject, topic and subtopic hierarchy.'],
 ['database','Database map','reference','owner','Inspect how bank, review and learning records are connected.'],
] as const
export const ADMIN_GROUPS=[['sources','Papers & coverage'],['review','Review & publication'],['community','Content & community'],['system','Accounts & settings'],['reference','References']] as const
export function canOpenAdminTab(tab:string,grants:readonly AdminGrant[]){
 const entry=ADMIN_SECTIONS.find(s=>s[0]===tab)
 if(!entry||!grants.length)return false
 if(entry[3]==='owner')return grants.some(g=>g.role==='owner')
 if(entry[3]==='inventory')return grants.some(g=>g.subject_id===null&&['owner','publisher','senior','reviewer'].includes(g.role))
 return true
}
export function adminNavigation(grants:readonly AdminGrant[]){
 const owner=grants.some(g=>g.role==='owner')
 const entries=ADMIN_SECTIONS.filter(s=>canOpenAdminTab(s[0],grants))
 const primary=entries.filter(s=>['overview','questions','exams','organization','publications'].includes(s[0])||(!owner&&s[0]==='review'))
 return {primary,more:entries.filter(s=>!primary.includes(s))}
}
export function adminTabHref(tab:string){return '/admin/bank?'+new URLSearchParams({tab,...tab==='questions'?{answer_status:'needs-review'}:{}})}

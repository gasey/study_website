/** The admin console's single navigation manifest.
 *
 *  Stable tab IDs preserve bookmarks while task labels and grouping can evolve.
 *
 *  Phase V.22 (§VIII.6) organises these by the **operator's job, not by database table**
 *  (§VII.19.6), and makes this file the only place that decides what the console contains.
 *  Before V.22 `AdminNavigation.tsx` carried its own hardcoded 26-key group list against
 *  these 37 sections, so eleven were unreachable from the sidebar — including `edit`, the
 *  keyboard authoring console, which is the most valuable screen here for bulk correction.
 *
 *  Tuple shape: [id, label, group, minRole, description].
 */
export type AdminGrant={role:string;subject_id:string|null}

/** Job groups, in sidebar order. `start` is rendered above them as a single link. */
export const ADMIN_GROUPS=[
 ['inbox','Inbox & conflicts'],
 ['bank','Bank & workbench'],
 ['authored','Guides, content & calendar'],
 ['system','History & system'],
] as const

export const ADMIN_SECTIONS=[
 ['overview','Overview','start','staff','See coverage, recorded work and what to fill or correct next.'],

 // 1. Waiting for a decision. Exposure ranking orders these queues (§VII.18.9).
 ['workflow','Review queue','inbox','owner','Review submitted corrections, materials and reports in one queue.'],
 ['conflicts','Answer conflicts','inbox','staff','Triage key-versus-solution disagreements ranked by paper clusters and learner exposure.'],
 ['reports','Question reports','inbox','staff','Inspect reported questions and record the resolution.'],
 ['review','Community corrections','inbox','staff','Review proposed bank changes in your permitted subjects.'],
 ['editorial','Editorial review','inbox','staff','Work through assigned editorial review queues and tag cleanup.'],
 ['mcq-solver','MCQ solver drafts','inbox','owner','Inspect staged AI solver drafts before human review.'],
 ['discussions','Discussion moderation','inbox','owner','Review reported discussions and moderation decisions.'],
 ['moderation','Community moderation','inbox','owner','Inspect reported posts, profiles and community flags.'],
 ['desks','Study desk reports','inbox','owner','Investigate reports from private study desks.'],
 ['privacy','Privacy requests','inbox','owner','Review and resolve owned account privacy and correction requests.'],

 // 2. Making and correcting bank content.
 ['edit','Authoring console','bank','staff','Keyboard-first queue for fast text, tag, context and explanation edits.'],
 ['questions','Questions','bank','staff','Find a question, inspect its source and record a reviewed decision.'],
 ['retag','Learning tags','bank','inventory','Find reported or missing tags and apply authorised admin corrections.'],
 ['quality','Bank quality','bank','staff','Find coverage gaps and questions that need source or answer review.'],
 ['organization','Modules & schemes','bank','inventory','Reuse sources, manage current and legacy schemes, and check original-paper readiness.'],
 ['exams','Papers & exams','bank','inventory','Manage exam coverage, source papers and printed paper identities.'],
 ['pdf-library','PDF Library','bank','inventory','Find source PDFs, continue imports and check what still needs attention.'],
 ['intake','Paper pipeline','bank','inventory','Track a source paper from discovery through review and publication.'],
 ['workbench','Paper workbench','bank','owner','Inspect parsed papers and publish guarded paper packages.'],
 ['taxonomy','Taxonomy reference','bank','staff','Browse the registered subject, topic and subtopic hierarchy.'],
 ['modules','Module comparisons','bank','owner','Use module comparisons as evidence for bank corrections.'],

 // 3. Learner-facing content that is authored rather than corrected.
 ['guides-studio','Concept guides studio','authored','owner','Create, edit, preview and publish first-party concept guides linked to subjects and topics.'],
 ['content','Notes & lessons','authored','owner','Review learner materials and manage their published revisions.'],
 ['current-affairs','Current affairs connections','authored','staff','Link historical questions to independently reviewed dated facts and later papers.'],
 ['ca-automation','Current affairs automation','authored','owner','Review staged YouTube and news current-affairs candidates.'],
 ['calendar','Calendar & notices','authored','owner','Check source notices and publish dated exam updates.'],
 ['atlas','Atlas studio','authored','owner','Edit Atlas geography chapters and drafts.'],
 ['atlas-bindings','Atlas topic bindings','authored','owner','Link published maps to approved taxonomy topics.'],
 ['learning','Learning collections','authored','owner','Manage curated practice sets and learning catalog items.'],
 ['topic-trail','Topic Trail admin','authored','owner','Manage Topic Trail routes and nodes.'],
 ['discovery','Practice discovery','authored','owner','Tune discovery pools and practice visibility.'],

 // 4. What already happened, and the machinery.
 ['publications','Publication history','system','staff','Track your corrections, publication dates and saved before-and-after changes.'],
 ['audit','Audit history','system','owner','Inspect recorded admin actions and their reasons.'],
 ['ops','Operations','system','owner','Check worker receipts, service probes, economy and moderation health.'],
 ['users','Account viewer','system','owner','Find account, access, study, economy and community summaries.'],
 ['rewards','Rewards & accounts','system','owner','Manage monthly prices, extra Pro days, reward receipts and account events.'],
 ['people','People & permissions','system','owner','Manage explicitly granted staff roles and subject access.'],
 ['database','Database map','system','owner','Inspect how bank, review and learning records are connected.'],
] as const

export function canOpenAdminTab(tab:string,grants:readonly AdminGrant[]){
 const entry=ADMIN_SECTIONS.find(s=>s[0]===tab)
 if(!entry||!grants.length)return false
 if(tab==='users')return grants.some(g=>g.role==='owner'&&g.subject_id===null)
 if(entry[3]==='owner')return grants.some(g=>g.role==='owner')
 if(entry[3]==='inventory')return grants.some(g=>g.subject_id===null&&['owner','publisher','senior','reviewer'].includes(g.role))
 return true
}

/** One addressing scheme for the console (§VIII.6). `/admin/ops` and `/admin/users`
 *  remain as routes so existing bookmarks keep working, but they redirect here rather
 *  than being a second way to address a section. */
export function adminTabHref(tab:string){
 return '/admin/bank?'+new URLSearchParams({tab,...tab==='questions'?{answer_status:'needs-review'}:{}})
}

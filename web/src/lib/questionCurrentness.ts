/** Editorial revision notes are separate from bank answers and scoring. Dates
 * describe inspected sources, never automatic verification of a stored key. */
export interface RevisionNote {
  id: string
  checkedOn: string
  effectiveOn: string
  reviewBy: string
  historicalContext?: string
  note: string
  revisionHint: string
  reference: {label: string; url: string}
}
export const revisionNotes: RevisionNote[] = [
  {
    id: 'stand-up-india-2016', checkedOn: '2026-11-01', effectiveOn: '2025-07-22', reviewBy: '2027-02-01',
    historicalContext: 'For this 2016 question, distinguish the Stand-Up India initiative from Start-up India and from later enterprise schemes.',
    note: 'The Ministry of Finance release dated 22 July 2025 records the launch on 5 April 2016 and describes bank loans of Rs 10 lakh to Rs 1 crore for SC/ST and women entrepreneurs setting up greenfield enterprises. Those are the terms described by that dated release.',
    revisionHint: 'Keep announcement date, launch date, eligible borrowers and loan limits in separate notes. A later proposal or loan limit does not rewrite the objective asked in the 2016 paper.',
    reference: {label: 'Ministry of Finance · Stand-Up India · 22 July 2025', url: 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2146820&lang=2&reg=3'},
  },
  {
    id: 'eighth-schedule-initial-count', checkedOn: '2026-11-01', effectiveOn: '2024-12-18', reviewBy: '2027-02-01',
    historicalContext: '“Initially included” asks about the original Constitution, rather than the number in a later edition.',
    note: 'A government release dated 18 December 2024 distinguishes the original 14 Eighth Schedule languages from the later total of 22. It records additions in 1967, 1992 and 2003. Eighth Schedule inclusion and classical-language recognition are separate categories.',
    revisionHint: 'Create two columns: original membership and later additions. Do not answer an “initially” question using the later total, or use the count of classical languages as the scheduled-language count.',
    reference: {label: 'Government of India · linguistic heritage · 18 December 2024', url: 'https://www.coal.nic.in/sites/default/files/2024-12/PIB2085529.pdf#page=2'},
  },
  {
    id: 'biodiversity-hotspots-2017', checkedOn: '2026-11-01', effectiveOn: '2026-11-01', reviewBy: '2027-02-01',
    historicalContext: 'This 2017 question asks for the number of designated biodiversity hotspots; keep the source version attached to the count.',
    note: 'Inspected on 1 November 2026, the European Commission Joint Research Centre catalog describes 36 regions in its Biodiversity Hotspots version 2016.1 dataset. The catalog marks that dataset “Not Updated”; it is an archived reference, not a newly checked global designation list.',
    revisionHint: 'Learn both criteria: at least 1,500 endemic vascular-plant species and loss of at least 70% of original native vegetation. Distinguish the global hotspot count from the number overlapping India.',
    reference: {label: 'European Commission JRC · biodiversity hotspots · dataset version 2016.1', url: 'https://africa-knowledge-platform.ec.europa.eu/dataset/biodiversity-hotspots'},
  },

  {
    id: 'shibu-soren-2025', checkedOn: '2026-11-01', effectiveOn: '2025-08-04', reviewBy: '2027-02-01',
    historicalContext: 'In the 2025 question, “August this year” refers to August 2025. Shibu Soren was a former Chief Minister of Jharkhand.',
    note: 'Akashvani’s report dated 4 August 2025 records his death and identifies the state as Jharkhand. This is historical context, not a claim about who holds office today.',
    revisionHint: 'Separate “had been Chief Minister” from “current Chief Minister”. Record the person, state and event date; check a current official profile separately for a question about today’s officeholder.',
    reference: {label: 'Akashvani · former Jharkhand CM · 4 August 2025', url: 'https://newsonair.gov.in/former-jharkhand-cm-shibu-soren-passes-away/'},
  },
  {
    id: 'finance-commission-2026', checkedOn: '2026-11-01', effectiveOn: '2026-04-01', reviewBy: '2027-02-01',
    note: 'The Sixteenth Finance Commission report covers 2026–2031. That award period is a different fact from the commission’s constitution date or the date its report was submitted.',
    revisionHint: 'Compare the commission number, chairperson, constitution date and award period separately. Use the period asked in the original paper before comparing the 2026–2031 report.',
    reference: {label: 'Ministry of Finance · Sixteenth Finance Commission report', url: 'https://www.indiabudget.gov.in/doc/16fcvol1.pdf'},
  },
  {
    id: 'union-budget-2026', checkedOn: '2026-11-01', effectiveOn: '2026-02-01', reviewBy: '2027-02-01',
    note: 'The Ministry of Finance publishes the Union Budget 2026–2027 documents. A figure from this budget does not replace a figure asked for an earlier financial year.',
    revisionHint: 'Compare the same measure and units. Distinguish Budget Estimates, Revised Estimates and Actuals, and keep each figure attached to its financial year.',
    reference: {label: 'Ministry of Finance · Union Budget 2026–2027 documents', url: 'https://www.indiabudget.gov.in/'},
  },
  {
    id: 'mcs-bairabi-sairang-2025', checkedOn: '2026-11-01', effectiveOn: '2026-09-13', reviewBy: '2027-02-01',
    historicalContext: 'The 2025 paper asked about the new Bairabi–Sairang line and its commissioning status.',
    note: 'A Ministry of Railways anniversary report dated 13 September 2026 records that the 51.38 km line and Sairang station were inaugurated on 13 September 2025. It also records the Sairang–Silchar passenger service beginning in January 2026. These later dated milestones do not verify every construction or safety statement in the original question.',
    revisionHint: 'Separate route, construction length, safety approvals and later passenger services; keep each fact attached to its date.',
    reference: {label: 'Ministry of Railways · Bairabi–Sairang one-year report · 13 September 2026', url: 'https://www.pib.gov.in/PressReleseDetailm.aspx?PRID=2309650&lang=1&reg=3'},
  },
  {
    id: 'mcs-muhcs-policy-2025', checkedOn: '2026-11-01', effectiveOn: '2026-04-01', reviewBy: '2027-02-01',
    historicalContext: 'The 2025 question refers to the scheme terms described for that examination year.',
    note: 'Mizoram State Health Care Society’s 16 February 2026 notice describes policy year 2026–27, effective 1 April 2026. It lists annual contribution options of ₹2,500, ₹5,000 and ₹10,000, with cover up to ₹5 lakh per family. These figures belong to that dated notice; check the Society’s subsequent scheme notices for later changes.',
    revisionHint: 'Keep each MUHCS policy year, enrolment category, contribution and cover amount in a separate row.',
    reference: {label: 'Mizoram State Health Care Society · MUHCS 2.0 policy 2026–27 notice · 16 February 2026', url: 'https://mshcs.mizoram.gov.in/post/muhcs-20-enrolment-16-feb-2026-aangin'},
  },
  {
    id: 'mcs-ner-sdg-index-2025', checkedOn: '2026-11-01', effectiveOn: '2025-07-07', reviewBy: '2027-02-01',
    historicalContext: 'This stem names the 2023–24 edition of NITI Aayog’s North Eastern Region District SDG Index.',
    note: 'NITI Aayog’s report page, published 7 July 2025, provides rankings and scores for the 2023–24 edition. Keep district comparisons attached to that report period and methodology. The SDG division listing checked on 1 November 2026 showed this as the latest North Eastern Region District SDG Index edition; its rank is still edition-specific, not a live 2026 ranking.',
    revisionHint: 'Record the index edition, publication date, district boundary and methodology with every rank.',
    reference: {label: 'NITI Aayog · SDG index and report listings · checked 1 November 2026', url: 'https://www.niti.gov.in/divisions/division/sustainable-development-goal'},
  },
  {
    id: 'mcs-ullas-literacy-2025', checkedOn: '2026-11-01', effectiveOn: '2026-04-01', reviewBy: '2027-02-01',
    historicalContext: 'The 2025 stem is tied to Mizoram’s declaration dated 20 May 2025.',
    note: 'The Ministry of Education’s 2026–27 outcome framework continues to list ULLAS and sets a target for States/UTs achieving full literacy during that year. This programme target is not a revised Mizoram literacy rate. No later Mizoram-specific rate was checked; retain the exam’s declaration date as historical context.',
    revisionHint: 'Distinguish a declaration, a survey rate and a future programme target; do not substitute one for another.',
    reference: {label: 'Ministry of Education · Output and Outcome Monitoring Framework 2026–27 · ULLAS', url: 'https://www.education.gov.in/sites/upload_files/mhrd/files/document-reports/OOMF_2026_27.pdf'},
  },
  {
    id: 'mcs-unfpa-swp-2025', checkedOn: '2026-11-01', effectiveOn: '2025-06-10', reviewBy: '2027-02-01',
    historicalContext: 'This is a report-theme question tied to UNFPA’s 2025 State of World Population edition.',
    note: 'UNFPA’s 10 June 2025 release describes the report’s central finding: many people cannot have the number of children they want because economic and social barriers constrain choice. Keep this summary attached to the 2025 report title; no later report theme or current demographic estimate is implied.',
    revisionHint: 'Keep the report year and title beside its theme; do not replace a report summary with a later population statistic.',
    reference: {label: 'UNFPA · 2025 State of World Population report release · 10 June 2025', url: 'https://www.unfpa.org/press/unfpa-report-links-falling-birth-rates-cost-living-sexist-norms-fear-future'},
  },
  {
    id: 'mcs-hero-trination-imphal-2023', checkedOn: '2026-11-01', effectiveOn: '2023-03-22', reviewBy: '2027-02-01',
    historicalContext: 'The question refers to a completed 2023 international friendly tournament.',
    note: 'The All India Football Federation’s match report dated 22 March 2023 records the opening fixture and venue for the Hero Tri-Nation International Football Tournament. Use it as a historical event record only; it says nothing about the host or schedule of later tournaments.',
    revisionHint: 'Keep the event year, venue and fixture date together; do not turn an old host-city question into a current event claim.',
    reference: {label: 'All India Football Federation · Hero Tri-Nation opening match · 22 March 2023', url: 'https://www.the-aiff.com/article/anirudh-thapa-strikes-as-india-edge-past-myanmar-in-hero-tri-nation-opener-in-imphal'},
  },
]
export function revisionNoteFor(question: string, year?: number | null, today = new Date().toISOString().slice(0,10)) {
  const id = /stand[ -]?up india/i.test(question) && year===2016 ? 'stand-up-india-2016'
    : /languages.*initially.*constitution/i.test(question) && year===2015 ? 'eighth-schedule-initial-count'
    : /number of biodiversity hotspots/i.test(question) && year===2017 ? 'biodiversity-hotspots-2017'
    : /\bshibu soren\b/i.test(question) && /chief minister/i.test(question) && year === 2025
    ? 'shibu-soren-2025'
    : year === 2025 && /new railway line in mizoram/i.test(question) && /bairabi/i.test(question) && /sairang/i.test(question)
      ? 'mcs-bairabi-sairang-2025'
      : year === 2025 && /mizoram universal healthcare scheme|muhcs/i.test(question)
        ? 'mcs-muhcs-policy-2025'
        : year === 2025 && /north eastern region district sdg index/i.test(question) && /mizoram/i.test(question)
          ? 'mcs-ner-sdg-index-2025'
          : year === 2025 && /fully literate state/i.test(question) && /mizoram/i.test(question) && /ullas/i.test(question)
            ? 'mcs-ullas-literacy-2025'
            : year === 2025 && /state of world population report\s*2025/i.test(question) && /united nations population fund|unfpa/i.test(question)
              ? 'mcs-unfpa-swp-2025'
              : year === 2023 && /2023 hero tri-nation international football tournament/i.test(question)
                ? 'mcs-hero-trination-imphal-2023'
                : /\bfinance commission\b/i.test(question)
      ? 'finance-commission-2026' : /\b(?:union|indian) budget\b/i.test(question) ? 'union-budget-2026' : null
  const note = revisionNotes.find(n => n.id === id)
  // Future-dated editorial material must not appear before its source was checked.
  return note && today >= note.checkedOn ? {...note, stale: today >= note.reviewBy} : null
}

/** Presentation hints only: never replace the stored historical answer or key. */
export function questionCurrentness(question: string, topic = '', year?: number | null) {
  const text = question.replace(/<[^>]*>/g, ' ')
  const classified = /current[\s-]*affairs/i.test(topic)
  // A year or ‘this year’ inside a grammar exercise is not a current-affairs claim.
  if (!classified && /\b(?:english|grammar|tenses|voice|prepositions|parts-of-speech)\b/i.test(topic)) return null
  const officeholder = /\bwho\s+(?:is|was|has been)\b[\s\S]{0,100}\b(?:president|prime minister|chief minister|governor|chief justice|chairman|chairperson|secretary general)\b/i.test(text)
  const changingMetric = /\b(?:largest|highest|lowest|leading)\b[\s\S]{0,50}\b(?:producer|gdp|population|literacy|rank|consumption|exporter|importer)\b/i.test(text)
  const referenceTopic = /\b(?:finance commission|union budget|indian budget|unified pension scheme)\b/i.test(text)
  const sensitive = /\b(?:current(?:ly)?|present(?:ly)?|incumbent|latest)\b.{0,65}\b(?:president|minister|governor|chair(?:man|person)?|justice|government|secretary|financial year|fiscal year|gdp|rate|ranking|population|census|status|budget|champion|winner)\b|\b(?:recently|newly)\b.{0,120}\b(?:launched|appointed|elected|won|held|announced|crowned|formed|introduced|detained|arrested|released)\b|\bas of\s+(?:the\s+)?(?:19|20)\d{2}\b|\b(?:this|last) year\b/i.test(text)
  const unrelated = /\b(?:present (?:tense|perfect|participle|continuous|value)|current (?:electricity|assets|liabilities|account|density|sheet|cell|directory|folder|slide|page)|present (?:in|at)|electric current|alternating current|direct current)\b/i.test(text)
  const update = revisionNoteFor(text,year)
  if ((!update && !sensitive && !referenceTopic && !officeholder && !changingMetric && !classified) || (unrelated && !classified)) return null
  let reference: {label: string; url: string} | null = null
  if (update) reference = update.reference
  else if (/\bquad\b.*at.?sea|at.?sea.*\bquad\b/i.test(text)) reference = {label:'PIB · QUAD At Sea Observer Mission · 30 June 2025',url:'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2140932&lang=2&reg=3'}
  else if (/\bpresident of india\b|\bindia.{0,8}president\b/i.test(text)) reference = {label:'President of India · official profile',url:'https://www.presidentofindia.gov.in/'}
  else if (/\brbi\b|reserve bank|repo rate|bank rate|cash reserve/i.test(text)) reference = {label:'Reserve Bank of India · official updates',url:'https://www.rbi.org.in/'}
  else if (/chief justice of india/i.test(text)) reference = {label:'Supreme Court of India · Chief Justice and judges',url:'https://www.sci.gov.in/chief-justice-judges/'}
  else if (/asian development bank|\badb\b/i.test(text)) reference = {label:'Asian Development Bank · India economy updates',url:'https://www.adb.org/where-we-work/india/economy'}
  else if (/shashank manohar|international cricket council/i.test(text)) reference = {label:'International Cricket Council · office-bearer history',url:'https://www.icc-cricket.com/about/the-icc/history-of-icc/icc-office-bearers'}
  else if (/\bmizoram\b|mizo national front/i.test(text)) reference = {label:'Government of Mizoram · official information',url:'https://mizoram.gov.in/'}
  return {reference, update}
}

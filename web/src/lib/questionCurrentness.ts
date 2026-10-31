/** Presentation hints only: never replace the stored historical answer or key. */
export function questionCurrentness(question: string, topic = '') {
  const text = question.replace(/<[^>]*>/g, ' ')
  const classified = /current[\s-]*affairs/i.test(topic)
  // A year or ‘this year’ inside a grammar exercise is not a current-affairs claim.
  if (!classified && /\b(?:english|grammar|tenses|voice|prepositions|parts-of-speech)\b/i.test(topic)) return null
  const officeholder = /\bwho\s+(?:is|was|has been)\b[\s\S]{0,100}\b(?:president|prime minister|chief minister|governor|chief justice|chairman|chairperson|secretary general)\b/i.test(text)
  const changingMetric = /\b(?:largest|highest|lowest|leading)\b[\s\S]{0,50}\b(?:producer|gdp|population|literacy|rank|consumption|exporter|importer)\b/i.test(text)
  const referenceTopic = /\b(?:finance commission|union budget|indian budget|unified pension scheme)\b/i.test(text)
  const sensitive = /\b(?:current(?:ly)?|present(?:ly)?|incumbent|latest)\b.{0,65}\b(?:president|minister|governor|chair(?:man|person)?|justice|government|secretary|financial year|fiscal year|gdp|rate|ranking|population|census|status|budget|champion|winner)\b|\b(?:recently|newly)\b.{0,120}\b(?:launched|appointed|elected|won|held|announced|crowned|formed|introduced|detained|arrested|released)\b|\bas of\s+(?:the\s+)?(?:19|20)\d{2}\b|\b(?:this|last) year\b/i.test(text)
  const unrelated = /\b(?:present (?:tense|perfect|participle|continuous|value)|current (?:electricity|assets|liabilities|account|density|sheet|cell|directory|folder|slide|page)|present (?:in|at)|electric current|alternating current|direct current)\b/i.test(text)
  if ((!sensitive && !referenceTopic && !officeholder && !changingMetric && !classified) || (unrelated && !classified)) return null
  let reference: {label: string; url: string} | null = null
  let update: {checkedOn: string; note: string} | null = null
  if (/\bfinance commission\b/i.test(text)) {
    reference = {label:'Finance Commission of India · official composition and reports',url:'https://fincomindia.nic.in/'}
    update = {checkedOn:'25 October 2026',note:'The official site publishes the Sixteenth Finance Commission’s composition and its report for 2026–2031. Compare the commission number and period with the original question; this revision note does not replace its historical answer.'}
  }
  else if (/\b(?:union|indian) budget\b/i.test(text)) {
    reference = {label:'Ministry of Finance · Union Budget documents',url:'https://www.indiabudget.gov.in/'}
    update = {checkedOn:'25 October 2026',note:'The official budget site now publishes the 2026–2027 documents. For an older question, use the budget year asked in the source paper, then compare the same measure in the newer official document. A different year’s figure is not a correction to the historical answer.'}
  }
  else if (/\bquad\b.*at.?sea|at.?sea.*\bquad\b/i.test(text)) reference = {label:'PIB · QUAD At Sea Observer Mission · 30 June 2025',url:'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2140932&lang=2&reg=3'}
  else if (/\bpresident of india\b|\bindia.{0,8}president\b/i.test(text)) reference = {label:'President of India · official profile',url:'https://www.presidentofindia.gov.in/'}
  else if (/\brbi\b|reserve bank|repo rate|bank rate|cash reserve/i.test(text)) reference = {label:'Reserve Bank of India · official updates',url:'https://www.rbi.org.in/'}
  else if (/chief justice of india/i.test(text)) reference = {label:'Supreme Court of India · Chief Justice and judges',url:'https://www.sci.gov.in/chief-justice-judges/'}
  else if (/asian development bank|\badb\b/i.test(text)) reference = {label:'Asian Development Bank · India economy updates',url:'https://www.adb.org/where-we-work/india/economy'}
  else if (/shashank manohar|international cricket council/i.test(text)) reference = {label:'International Cricket Council · office-bearer history',url:'https://www.icc-cricket.com/about/the-icc/history-of-icc/icc-office-bearers'}
  else if (/\bmizoram\b|mizo national front|\bchief minister\b/i.test(text)) reference = {label:'Government of Mizoram · official information',url:'https://mizoram.gov.in/'}
  return {reference, update}
}

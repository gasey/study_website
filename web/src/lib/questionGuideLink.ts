import type { Question } from './api'

export interface QuestionGuideMatch {
  slug: string
  anchor: string | null
  to: string
  label: string
  tone: 'teal' | 'cobalt' | 'emerald' | 'terracotta' | 'plum' | 'amber'
}

function makeMatch(
  slug: string,
  anchor: string | null,
  label: string,
  tone: QuestionGuideMatch['tone'],
): QuestionGuideMatch {
  return {
    slug,
    anchor,
    to: anchor ? `/guides/${slug}#${anchor}` : `/guides/${slug}`,
    label,
    tone,
  }
}

/** Resolve the closest published Concept Guide & exact chapter anchor for any question. */
export function resolveQuestionGuide(
  q: Pick<
    Question,
    | 'taxonomy_subject_id'
    | 'taxonomy_topic_id'
    | 'taxonomy_subtopic_id'
    | 'subject'
    | 'topic'
    | 'question'
  >,
): QuestionGuideMatch | null {
  const subj = (q.taxonomy_subject_id || q.subject || '').toLowerCase()
  const topic = (q.taxonomy_topic_id || q.topic || '').toLowerCase()
  const sub = (q.taxonomy_subtopic_id || '').toLowerCase()
  const stem = (q.question || '').toLowerCase()

  // 0. High-confidence cross-subject stem matchers (rescue loosely-tagged questions cleanly)
  if (/\b(pslv|gslv|lvm3|isro|chandrayaan|mangalyaan|aditya-l1|gaganyaan|sriharikota|cryogenic)\b/.test(stem)) {
    return makeMatch('general-science', 'space-isro-applied-science', 'Science Guide · ISRO & Space', 'teal')
  }
  if (/\b(sixth schedule|371g|autonomous district council|ladc|madc|cadc)\b/.test(stem)) {
    return makeMatch('polity-codex', 'sixth', 'Polity Codex · Sixth Schedule', 'cobalt')
  }
  if (/\b(mudra|shishu|kishor|tarun|repo rate|reverse repo|cash reserve ratio|\bcrr\b|\bslr\b|open market operation|credit control by the rbi)\b/.test(stem)) {
    return makeMatch('indian-economy', 'rbi-money-banking', 'Economy Guide · RBI & Banking', 'amber')
  }
  if (/\b(water image|mirror image|clock hands|leap year|odd days|syllogism)\b/.test(stem)) {
    return makeMatch('reasoning-aptitude', 'syllogism-clocks-calendars-images', 'Reasoning · Clocks, Calendars & Images', 'plum')
  }
  if (/\b(ms word|ms excel|powerpoint|format painter|mail merge|vlookup|spreadsheet|windows os|alt\s*\+\s*tab|ctrl\s*\+)/.test(stem)) {
    return makeMatch('computer-fundamentals', /windows|alt\s*\+\s*tab|task manager/.test(stem) ? 'os-windows-shortcuts' : 'ms-office-word-excel-ppt', 'Computer Guide · OS & MS Office', 'cobalt')
  }
  if (/\b(paris agreement|kyoto protocol|sustainable development|biosphere reserve|ramsar|national park|wildlife sanctuary)\b/.test(stem)) {
    return makeMatch('geography-essentials', 'forests', 'Geography Guide · Forests & Environment', 'emerald')
  }

  // 1. Mathematics, Arithmetic & Statistics
  if (
    subj.includes('math') ||
    subj.includes('arith') ||
    subj === 'statistics' ||
    topic.startsWith('mathematics/') ||
    topic.startsWith('statistics/')
  ) {
    if (sub.includes('ratio') || /\b(ratio|proportion|partnership|mixture|alligation)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'ratio-proportion-partnership-mixtures', 'Maths Guide · Ratio & Proportion', 'plum')
    }
    if (sub.includes('percentage') || /\b(percent|%|venn diagram)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'percentages-and-sets', 'Maths Guide · Percentages', 'plum')
    }
    if (sub.includes('profit') || /\b(profit|loss|discount|cost price|selling price|marked price)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'profit-loss-discount', 'Maths Guide · Profit & Loss', 'plum')
    }
    if (sub.includes('average') || /\b(average|mean age|present age|arithmetic progression)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'averages-ages-ap', 'Maths Guide · Averages & Ages', 'plum')
    }
    if (/compound interest|simple interest|\bsi\b|\bci\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'simple-and-compound-interest', 'Maths Guide · SI & CI Shortcuts', 'plum')
    }
    if (/\b(hcf|lcm|divisib|greatest number|least number)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'hcf-and-lcm', 'Maths Guide · HCF & LCM', 'plum')
    }
    if (/\b(train|speed|km\/h|km\/hr|upstream|downstream|boat|distance)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'time-speed-distance-trains', 'Maths Guide · Speed & Distance', 'plum')
    }
    if (/\b(cistern|pipe|days to complete|finish a work|men can do|work in)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'time-work-pipes', 'Maths Guide · Time & Work', 'plum')
    }
    if (topic.includes('algebra') || /\b(quadratic|polynomial|equation|probability|permutation|combination)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'algebra-probability-pnc', 'Maths Guide · Algebra & Probability', 'plum')
    }
    if (topic.includes('mensuration') || /\b(area of|volume of|cylinder|cone|sphere|perimeter|cuboid|trapezium)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'mensuration-2d-3d', 'Maths Guide · 2D & 3D Mensuration', 'plum')
    }
    if (subj === 'statistics' || topic.includes('geometry') || /\b(triangle|circle|sin|cos|tan|median|mode|standard deviation)\b/.test(stem)) {
      return makeMatch('maths-and-arithmetic', 'geometry-trig-di-stats', 'Maths Guide · Geometry, Trig & Stats', 'plum')
    }
    return makeMatch('maths-and-arithmetic', 'number-system-simplification', 'Maths Guide · Number System & Formulas', 'plum')
  }

  // 2. Computer Science & IT
  if (subj.includes('computer') || topic.startsWith('computer-science/')) {
    if (topic.includes('office') || /\b(word|excel|powerpoint|spreadsheet|slide|mail merge|pivot|formula)\b/.test(stem)) {
      return makeMatch('computer-fundamentals', 'ms-office-word-excel-ppt', 'Computer Guide · MS Office', 'cobalt')
    }
    if (topic.includes('network') || /\b(osi|tcp|udp|http|https|dns|smtp|ip address|router|switch|hub|firewall|phishing|malware|lan|wan|topology)\b/.test(stem)) {
      return makeMatch('computer-fundamentals', 'networking-internet-cyber', 'Computer Guide · Networks & Cyber', 'cobalt')
    }
    if (topic.includes('database') || /\b(sql|dbms|rdbms|primary key|foreign key|normalization|truncate|acid|table|query)\b/.test(stem)) {
      return makeMatch('computer-fundamentals', 'databases-sql-basics', 'Computer Guide · DBMS & SQL', 'cobalt')
    }
    if (topic.includes('operating-system') || /\b(operating system|windows|linux|boot|deadlock|paging|virtual memory|shortcut|task manager)\b/.test(stem)) {
      return makeMatch('computer-fundamentals', 'os-windows-shortcuts', 'Computer Guide · OS & Shortcuts', 'cobalt')
    }
    return makeMatch('computer-fundamentals', 'hardware-memory-architecture', 'Computer Guide · Hardware & Memory', 'cobalt')
  }

  // 3. General Science (Physics, Chemistry, Biology, Space)
  if (subj === 'science' || topic.startsWith('science/') || topic.includes('science-in-the-news')) {
    if (topic.includes('biology') || /\b(cell|pancreas|insulin|hormone|vitamin|blood|enzyme|liver|dna|rna|bacteria|virus|malaria|photosynthesis|mitochondria|gland)\b/.test(stem)) {
      return makeMatch('general-science', 'biology-human-body-diseases', 'Science Guide · Biology & Human Body', 'teal')
    }
    if (topic.includes('chemistry') || /\b(acid|base|ph\b|periodic|isotope|alloy|brass|bronze|graphite|diamond|baking soda|bleaching|chemical|amino acid|molecule|atom)\b/.test(stem)) {
      return makeMatch('general-science', 'chemistry-periodic-acids-everyday', 'Science Guide · Chemistry Essentials', 'teal')
    }
    if (topic.includes('science-in-the-news') || /\b(satellite|orbit|nuclear|reactor|fusion|fission|rocket|space)\b/.test(stem)) {
      return makeMatch('general-science', 'space-isro-applied-science', 'Science Guide · Space & Applied Tech', 'teal')
    }
    return makeMatch('general-science', 'physics-units-optics-electricity', 'Science Guide · Physics & SI Units', 'teal')
  }

  // 4. Reasoning & Mental Ability
  if (subj.includes('reasoning') || topic.startsWith('reasoning-and-aptitude/')) {
    if (topic.includes('series') || /\b(series|next term|missing number|fill the blank)\b/.test(stem)) {
      return makeMatch('reasoning-aptitude', 'series-ejoty-patterns', 'Reasoning · Series & EJOTY', 'plum')
    }
    if (topic.includes('data-interpretation') || /\b(pie chart|bar graph|line graph|decision-making|conflict resolution)\b/.test(stem)) {
      return makeMatch('reasoning-aptitude', 'data-interpretation-decision', 'Reasoning · DI & Decision-Making', 'plum')
    }
    if (/\b(certain code|coded as|written as|odd one out|analogy)\b/.test(stem)) {
      return makeMatch('reasoning-aptitude', 'coding-analogy-classification', 'Reasoning · Coding & Analogy', 'plum')
    }
    if (/\b(sitting in a circle|two rows|facing each other|from the left|from the right|rank|row of)\b/.test(stem)) {
      return makeMatch('reasoning-aptitude', 'seating-ranking-order', 'Reasoning · Seating & Ranking', 'plum')
    }
    if (/\b(north|south|east|west|shadow|brother|sister|father|mother|uncle|pointing to)\b/.test(stem)) {
      return makeMatch('reasoning-aptitude', 'blood-relations-directions', 'Reasoning · Blood Relations & Directions', 'plum')
    }
    if (/\b(clock|calendar|day of the week|mirror|water image|statement|conclusion|syllogism|rotated)\b/.test(stem)) {
      return makeMatch('reasoning-aptitude', 'syllogism-clocks-calendars-images', 'Reasoning · Clocks, Calendars & Images', 'plum')
    }
    return makeMatch('reasoning-aptitude', 'coding-analogy-classification', 'Reasoning & Mental Ability Guide', 'plum')
  }

  // 5. Indian Economy, Economics & Public Finance
  if (
    topic.includes('indian-economy') ||
    subj === 'economics' ||
    subj === 'commerce' ||
    subj === 'financial-rules-and-accounts'
  ) {
    if (/\b(rbi|reserve bank|repo|crr|slr|monetary|bank rate|credit control|nabard|sebi|jan dhan|mudra)\b/.test(stem)) {
      return makeMatch('indian-economy', 'rbi-money-banking', 'Economy Guide · RBI & Banking', 'amber')
    }
    if (/\b(budget|fiscal|revenue deficit|primary deficit|gst|customs|direct tax|indirect tax|income tax|finance commission|treasury|audit|export and import)\b/.test(stem)) {
      return makeMatch('indian-economy', 'budget-fiscal-taxation', 'Economy Guide · Budget & Taxation', 'amber')
    }
    if (/\b(unemployment|disguised|inflation|cpi|wpi|stagflation|poverty|five-year|five year|niti aayog|lorenz|gini)\b/.test(stem)) {
      return makeMatch('indian-economy', 'inflation-unemployment-planning', 'Economy Guide · Inflation & Planning', 'amber')
    }
    if (/\b(balance of payments|current account|capital account|fdi|fpi|imf|world bank|wto|export destination|devaluation|forex)\b/.test(stem)) {
      return makeMatch('indian-economy', 'bop-trade-global-bodies', 'Economy Guide · BoP & Global Trade', 'amber')
    }
    return makeMatch('indian-economy', 'national-income-gdp', 'Economy Guide · National Income & GDP', 'amber')
  }

  // 6. English
  if (subj === 'english' || topic.startsWith('english/')) {
    if (sub.includes('voice') || /passive voice|active voice/.test(stem)) {
      return makeMatch('tenses-and-voice', 'active-and-passive-voice', 'English Guide · Active & Passive Voice', 'teal')
    }
    if (/past perfect/.test(stem)) {
      return makeMatch('tenses-and-voice', 'past-perfect', 'English Guide · Past Perfect Tense', 'teal')
    }
    if (/present perfect/.test(stem)) {
      return makeMatch('tenses-and-voice', 'present-perfect', 'English Guide · Present Perfect Tense', 'teal')
    }
    if (/future/.test(stem)) {
      return makeMatch('tenses-and-voice', 'future-simple', 'English Guide · Future Tenses', 'teal')
    }
    if (sub.includes('tenses') || topic.includes('grammar')) {
      return makeMatch('tenses-and-voice', 'present-simple', 'English Guide · Tenses & Voice', 'teal')
    }
    return makeMatch('tenses-and-voice', null, 'English Tenses & Voice Guide', 'teal')
  }

  // 7. Indian Polity, Law & Mizoram Administration
  if (
    topic.includes('polity') ||
    subj.includes('polity') ||
    subj === 'law' ||
    subj === 'mizoram-administration-and-law'
  ) {
    if (topic.includes('village-and-district-councils') || subj === 'mizoram-administration-and-law') {
      return makeMatch('polity-codex', 'sixth', 'Polity Codex · Sixth Schedule & ADCs', 'cobalt')
    }
    if (/regulating act|charter act|1909|1919|1935|morley|montagu/.test(stem)) {
      return makeMatch('polity-codex', 'hist', 'Polity Codex · Constitutional History', 'cobalt')
    }
    if (/drafting committee|constituent assembly/.test(stem)) {
      return makeMatch('polity-codex', 'ca', 'Polity Codex · Constituent Assembly', 'cobalt')
    }
    if (/preamble/.test(stem)) {
      return makeMatch('polity-codex', 'preamble', 'Polity Codex · Preamble', 'cobalt')
    }
    if (/citizenship/.test(stem)) {
      return makeMatch('polity-codex', 'citizen', 'Polity Codex · Citizenship', 'cobalt')
    }
    if (/fundamental right|untouchability|article (14|15|16|17|19|21|32)\b/.test(stem)) {
      return makeMatch('polity-codex', 'fr', 'Polity Codex · Fundamental Rights', 'cobalt')
    }
    if (/directive principle|dpsp|uniform civil code/.test(stem)) {
      return makeMatch('polity-codex', 'dpsp', 'Polity Codex · DPSP', 'cobalt')
    }
    if (/fundamental dut|51a/.test(stem)) {
      return makeMatch('polity-codex', 'fd', 'Polity Codex · Fundamental Duties', 'cobalt')
    }
    if (/amendment|basic structure|368/.test(stem)) {
      return makeMatch('polity-codex', 'amend', 'Polity Codex · Amendments', 'cobalt')
    }
    if (/parliament|lok sabha|rajya sabha|money bill|vote on account|speaker/.test(stem)) {
      return makeMatch('polity-codex', 'parl', 'Polity Codex · Parliament', 'cobalt')
    }
    if (/president|governor|prime minister|council of ministers|chief minister/.test(stem)) {
      return makeMatch('polity-codex', 'exec', 'Polity Codex · Union & State Executive', 'cobalt')
    }
    if (subj === 'law' || /supreme court|high court|writ|habeas corpus|mandamus|certiorari|cpc|judiciary/.test(stem)) {
      return makeMatch('polity-codex', 'judi', 'Polity Codex · Judiciary & Writs', 'cobalt')
    }
    if (/emergency|article (352|356|360)/.test(stem)) {
      return makeMatch('polity-codex', 'emerg', 'Polity Codex · Emergency Provisions', 'cobalt')
    }
    if (/anti-defection|tenth schedule/.test(stem)) {
      return makeMatch('polity-codex', 'adl', 'Polity Codex · Anti-Defection Law', 'cobalt')
    }
    if (/panchayat|municipality|73rd|74th/.test(stem)) {
      return makeMatch('polity-codex', 'local', 'Polity Codex · Local Government', 'cobalt')
    }
    if (/election commission|cag|upsc|finance commission|cbi|article 309|article 315|article 324/.test(stem)) {
      return makeMatch('polity-codex', 'cbody', 'Polity Codex · Constitutional Bodies', 'cobalt')
    }
    return makeMatch('polity-codex', null, 'Indian Polity Codex', 'cobalt')
  }

  // 8. Geography, Environment & Mizoram
  if (topic.includes('mizoram')) {
    return makeMatch('geography-essentials', 'mizoram-geography', 'Geography Guide · Mizoram', 'emerald')
  }
  if (topic.includes('environment') || /biosphere|biodiversity|national park|wildlife|forest/.test(stem)) {
    return makeMatch('geography-essentials', 'forests', 'Geography Guide · Forests & Biosphere', 'emerald')
  }
  if (topic.includes('geography') || subj.includes('geography')) {
    if (/river|ganga|indus|brahmaputra|godavari|narmada|tributary|tlungvel|tlawng|chhimtuipui/.test(stem)) {
      return makeMatch('geography-essentials', 'rivers', 'Geography Guide · Rivers of India', 'emerald')
    }
    if (/monsoon|kharif|rabi|zaid|crop|rainfall|climate/.test(stem)) {
      return makeMatch('geography-essentials', 'climate-monsoon', 'Geography Guide · Climate & Crops', 'emerald')
    }
    if (/soil|alluvial|regur|laterite/.test(stem)) {
      return makeMatch('geography-essentials', 'soils', 'Geography Guide · Soils of India', 'emerald')
    }
    if (/himalaya|pass|peak|mountain|ghat|phawngpui/.test(stem)) {
      return makeMatch('geography-essentials', 'mountains', 'Geography Guide · Mountains & Passes', 'emerald')
    }
    if (/tsunami|earthquake|volcano|tectonic/.test(stem)) {
      return makeMatch('geography-essentials', 'world-restless-earth', 'Geography Guide · Restless Earth', 'emerald')
    }
    if (/wind|cyclone|ocean current|el nino|jet stream/.test(stem)) {
      return makeMatch('geography-essentials', 'world-winds-currents', 'Geography Guide · Winds & Currents', 'emerald')
    }
    return makeMatch('geography-essentials', 'physiographic-divisions', 'Geography of India & Mizoram', 'emerald')
  }

  // 9. Indian & World History
  if (topic.includes('world-history')) {
    return makeMatch('history-essentials', 'modern-india-mizoram-world-milestones', 'History Guide · World & Modern Milestones', 'terracotta')
  }
  if (topic.includes('history') || topic.includes('art-and-culture') || subj.includes('history')) {
    if (/harappa|mohenjodaro|indus|lothal/.test(stem)) {
      return makeMatch('history-essentials', 'indus-valley', 'History Guide · Indus Valley', 'terracotta')
    }
    if (/veda|vedanga|vedic|rigveda/.test(stem)) {
      return makeMatch('history-essentials', 'vedic-age', 'History Guide · Vedic Age', 'terracotta')
    }
    if (/buddh|jain|mahavira/.test(stem)) {
      return makeMatch('history-essentials', 'buddhism-jainism', 'History Guide · Buddhism & Jainism', 'terracotta')
    }
    if (/maurya|ashoka|kautilya|chandragupta/.test(stem)) {
      return makeMatch('history-essentials', 'mahajanapadas-mauryas', 'History Guide · Mauryas', 'terracotta')
    }
    if (/sultan|khilji|tughlaq|lodi|slave dynasty|qutb/.test(stem)) {
      return makeMatch('history-essentials', 'delhi-sultanate', 'History Guide · Delhi Sultanate', 'terracotta')
    }
    if (/chola|vijayanagara|talikota|pallava/.test(stem)) {
      return makeMatch('history-essentials', 'medieval-south', 'History Guide · Medieval South', 'terracotta')
    }
    if (/plassey|buxar/.test(stem)) {
      return makeMatch('history-essentials', 'battle-of-plassey', 'History Guide · Battle of Plassey', 'terracotta')
    }
    if (/1857|swadeshi|boycott|gandhi|congress|calcutta|quit india|dandi|kanpur|non-cooperation/.test(stem)) {
      return makeMatch('history-essentials', 'freedom-struggle-map', 'History Guide · Freedom Struggle', 'terracotta')
    }
    return makeMatch('history-essentials', 'modern-india-mizoram-world-milestones', 'Indian & Mizoram History Guide', 'terracotta')
  }

  // 10. General Knowledge / General Studies fallback
  if (subj === 'gk-gs' || subj.includes('general')) {
    return makeMatch('quick-revision', null, 'MPSC Quick Revision Guide', 'amber')
  }

  return null
}

/** Format a compact, honest source string from a question's source_appearance. */
export function formatQuestionSource(q: Pick<Question, 'source_appearance' | 'first_year' | 'last_year'>): {
  label: string
  pdfUrl: string | null
  hasExactSource: boolean
} {
  const src = q.source_appearance
  if (!src) {
    const yr = q.last_year ?? q.first_year
    return {
      label: yr ? `Exam archive · ${yr}` : 'Verified exam bank',
      pdfUrl: null,
      hasExactSource: false,
    }
  }
  const parts: string[] = []
  const examName = src.exam || src.paper_id?.split('/').pop() || 'Source paper'
  parts.push(examName)
  if (src.year && !examName.includes(String(src.year))) parts.push(String(src.year))
  if (src.paper_label) parts.push(src.paper_label)
  else if (src.paper) parts.push(`Paper ${src.paper}`)
  if (src.section_label) parts.push(src.section_label)
  if (src.series) parts.push(`Series ${src.series}`)
  if (src.qnum) parts.push(`Q${src.qnum}`)
  if (src.page) parts.push(`p. ${src.page}`)
  const pdfUrl = src.source_pdf_url
    ? `${src.source_pdf_url}${src.page ? `#page=${src.page}` : ''}`
    : null
  return {
    label: parts.join(' · '),
    pdfUrl,
    hasExactSource: true,
  }
}

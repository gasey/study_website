/** Visual identity & category classification for Exam and Subject modules.
 *  Source membership and answer states stay authoritative on the backend. */

export const FLAGSHIP_EXAM_IDS = [
  'udc',
  'ldc',
  'combined-prelims',
  'group-b-gazetted',
  'group-b-non-gazetted',
  'assistant',
  'iti-instructor-2026',
] as const

export type ExamCategoryId =
  | 'all'
  | 'civil-services'
  | 'clerical'
  | 'group-b'
  | 'engineering-tech'
  | 'medical-health'
  | 'education'
  | 'police-excise'
  | 'finance-law'
  | 'other'

export const EXAM_CATEGORIES: readonly { id: ExamCategoryId; label: string }[] = [
  { id: 'all', label: 'All categories' },
  { id: 'civil-services', label: 'Civil Services & Forest' },
  { id: 'clerical', label: 'Clerical & Office' },
  { id: 'group-b', label: 'Group B' },
  { id: 'engineering-tech', label: 'Engineering & Tech' },
  { id: 'medical-health', label: 'Medical & Health' },
  { id: 'education', label: 'Teaching & Education' },
  { id: 'police-excise', label: 'Police, Excise & Transport' },
  { id: 'finance-law', label: 'Finance, Accounts & Law' },
  { id: 'other', label: 'Other Departments' },
] as const

export function examCategory(id: string, title = ''): Exclude<ExamCategoryId, 'all'> {
  const text = `${id} ${title}`.toLowerCase()
  if (/\b(mcs|combined-prelims|civil service|acf|forest|mfs|cdpo|tourist|administrative)\b/.test(text)) {
    return 'civil-services'
  }
  if (/\b(group[- ]?b|gazetted|non[- ]?gazetted)\b/.test(text)) {
    return 'group-b'
  }
  if (/\b(udc|ldc|clerk|assistant|stenographer|typist|secretariat|desk|office)\b/.test(text) && !/\b(engineer|conservator|surgeon|professor|librarian|jailor|director|controller|divisional|leso)\b/.test(text)) {
    return 'clerical'
  }
  if (/\b(mes|engineer|je\b|junior engineer|iti|instructor|technical|surveyor|mines|mechanic|electric|civil|computer|draftsman|architecture|geology|horticulture|agriculture|veterinary|fisheries|statistics|statistic|meteorology|metrology|planning|leso)\b/.test(text)) {
    return 'engineering-tech'
  }
  if (/\b(nurse|nursing|mcon|medical|doctor|health|pharmacist|dental|x-ray|lab|hospital|obstetric|gynaecolog|clinical|mhs|health & family)\b/.test(text)) {
    return 'medical-health'
  }
  if (/\b(teacher|lecturer|school|education|professor|librarian|headmaster|b\.?ed|diets|college)\b/.test(text)) {
    return 'education'
  }
  if (/\b(police|excise|sub-inspector|inspector|jailor|fire|station officer|transport|enforcement|home department)\b/.test(text)) {
    return 'police-excise'
  }
  if (/\b(account|finance|audit|tax|taxes|legal|law|judicial|court|jag|treasury|cooperative|co-operative)\b/.test(text)) {
    return 'finance-law'
  }
  return 'other'
}

function smartStamp(id: string, title: string): string {
  const lower = `${id} ${title}`.toLowerCase()
  if (lower.includes('mcs')) return 'MCS'
  if (lower.includes('mes') || lower.includes('engineering service')) return 'MES'
  if (lower.includes('acf') || lower.includes('conservator of forest')) return 'ACF'
  if (lower.includes('junior engineer') || /\bje\b/.test(lower)) return 'JE'
  if (lower.includes('group b')) return 'GB'
  if (lower.includes('udc')) return 'UDC'
  if (lower.includes('ldc')) return 'LDC'
  if (lower.includes('sub-inspector')) return 'SI'
  if (lower.includes('inspector')) return 'INS'
  if (lower.includes('lecturer')) return 'LEC'
  if (lower.includes('teacher')) return 'TCH'
  if (lower.includes('nurse') || lower.includes('nursing')) return 'NRS'
  if (lower.includes('stenographer')) return 'STN'
  if (lower.includes('legal') || lower.includes('jag')) return 'LAW'
  if (lower.includes('account') || lower.includes('finance')) return 'FIN'
  if (lower.includes('cdpo')) return 'CDP'
  if (lower.includes('leso')) return 'LSO'
  if (lower.includes('librarian')) return 'LIB'
  if (lower.includes('surveyor')) return 'SRV'
  if (lower.includes('assistant')) return 'AST'
  const words = title
    .replace(/[^A-Za-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 1 && !['of', 'in', 'to', 'the', 'and', 'for', 'under', 'dept', 'deptt', 'department', 'grade', 'post', 'mizoram'].includes(w.toLowerCase()))
  if (words.length >= 2) return (words[0][0] + words[1][0] + (words[2]?.[0] || '')).toUpperCase().slice(0, 3)
  if (words.length === 1) return words[0].slice(0, 3).toUpperCase()
  return 'EX'
}

export function examPresentation(id: string, title = '') {
  const identities: Record<string, { tone: string; short: string; category: string }> = {
    udc: { tone: 'teal', short: 'UDC', category: 'Clerical preparation' },
    ldc: { tone: 'blue', short: 'LDC', category: 'Clerical preparation' },
    assistant: { tone: 'violet', short: 'AST', category: 'Clerical preparation' },
    'combined-prelims': { tone: 'indigo', short: 'MCS', category: 'Civil services' },
    'group-b-gazetted': { tone: 'violet', short: 'GB', category: 'Gazetted preparation' },
    'group-b-non-gazetted': { tone: 'teal', short: 'GB', category: 'Non-Gazetted preparation' },
    'iti-instructor-2026': { tone: 'amber', short: 'ITI', category: 'Technical preparation' },
    mes: { tone: 'amber', short: 'MES', category: 'Engineering Service preparation' },
    'subject-english': { tone: 'teal', short: 'ENG', category: 'Cross-exam subject' },
    'subject-mathematics': { tone: 'blue', short: 'MTH', category: 'Cross-exam subject' },
    'subject-reasoning': { tone: 'violet', short: 'RSN', category: 'Cross-exam subject' },
    'subject-gk-gs': { tone: 'indigo', short: 'GK', category: 'Cross-exam subject' },
    'subject-mizo': { tone: 'amber', short: 'MIZ', category: 'Cross-exam subject' },
  }
  if (identities[id]) return identities[id]

  const cat = examCategory(id, title)
  const toneByCategory: Record<Exclude<ExamCategoryId, 'all'>, { tone: string; label: string }> = {
    'civil-services': { tone: 'indigo', label: 'Civil Services & Forest' },
    clerical: { tone: 'blue', label: 'Clerical & Office' },
    'group-b': { tone: 'violet', label: 'Group B recruitment' },
    'engineering-tech': { tone: 'amber', label: 'Engineering & Tech' },
    'medical-health': { tone: 'teal', label: 'Medical & Health' },
    education: { tone: 'violet', label: 'Teaching & Education' },
    'police-excise': { tone: 'indigo', label: 'Police & Excise' },
    'finance-law': { tone: 'blue', label: 'Finance & Law' },
    other: { tone: 'teal', label: 'Departmental & Direct' },
  }
  const meta = toneByCategory[cat]
  return {
    tone: meta.tone,
    short: smartStamp(id, title || id),
    category: meta.label,
  }
}

export function examCatalogLayout(value: string | null) {
  return value === 'list' ? 'list' : 'cards'
}

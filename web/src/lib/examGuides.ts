/** Platform-neutral, versioned exam-guide contract. Synced to the mobile app. */
export interface ExamSource {
  id: string;
  title: string;
  url: string;
  checkedOn: string;
}
export interface ExamScheme {
  id: string;
  title: string;
  status: 'verified' | 'archive';
  description: string;
  sourceIds: string[];
  branchIds: string[];
  interviewMarks: number | null;
}
export interface SyllabusUnit {
  id: string;
  title: string;
  description: string;
}
export interface SyllabusPaper {
  id: string;
  schemeId: string;
  /** null = shared by every branch supported by this scheme. */
  branchId: string | null;
  title: string;
  marks: number | null;
  durationMinutes: number | null;
  format: string;
  sourceId: string;
  sourcePage: number | null;
  units: SyllabusUnit[];
}
export interface ArchivedExamPaper {
  id: string;
  title: string;
  sitting: string;
  year: number;
  branchId: string | null;
  schemeId: string | null;
  schemeBasis: 'source' | 'inferred' | 'unknown';
  subject: string;
  paperNumber: string | null;
  url: string;
  /** Existing same-origin source archive; null when the original is external only. */
  readerUrl: string | null;
  sourceId: string;
}
export interface ExamGuide {
  schemaVersion: 1;
  id: string;
  title: string;
  description: string;
  eyebrow: string;
  directorySourceId: string;
  defaultSchemeId: string;
  defaultBranchId: string;
  sources: ExamSource[];
  schemes: ExamScheme[];
  branches: { id: string; title: string; short: string }[];
  syllabus: SyllabusPaper[];
  archive: ArchivedExamPaper[];
}
export type StudyProgress = Record<string, boolean>;
export const examGuideViews = [
  ['overview', 'Overview'], ['browse', 'Browse'], ['topics', 'Subjects'],
  ['papers', 'Papers'], ['practice', 'Practice'], ['progress', 'Progress'],
] as const;
export type ExamGuideView = typeof examGuideViews[number][0];
/** Keep bookmarks from the original guide working when moving to the shared exam tabs. */
export function guideView(view?: string | null, legacyTab?: string | null): ExamGuideView {
  if (examGuideViews.some(([key]) => key === view)) return view as ExamGuideView;
  const legacy: Record<string, ExamGuideView> = {
    Overview: 'overview', Browse: 'browse', Syllabus: 'topics', Subjects: 'topics',
    'Past papers': 'papers', Papers: 'papers', Recall: 'practice', Practice: 'practice', Progress: 'progress',
  };
  return Object.prototype.hasOwnProperty.call(legacy, legacyTab || '') ? legacy[legacyTab!] : 'overview';
}
/** Decode only source-bound archive paths; an external PDF never becomes an unscoped bank query. */
export function sourcePaperId(paper: ArchivedExamPaper): string | null {
  const prefix = '/papers/source/';
  if (!paper.readerUrl?.startsWith(prefix)) return null;
  try {
    const id = decodeURIComponent(paper.readerUrl.slice(prefix.length));
    return id && !/[\u0000?#]/.test(id) && id.split('/').every((part) => part && part !== '.' && part !== '..') ? id : null;
  } catch { return null; }
}
export function selectGuidePaper(papers: ArchivedExamPaper[], requested?: string | null) {
  return papers.find((p) => p.id === requested) ||
    papers.find((p) => p.branchId && sourcePaperId(p)) ||
    papers.find((p) => sourcePaperId(p)) || papers[0];
}
export function branchesForScheme(guide: ExamGuide, schemeId: string) {
  const scheme = guide.schemes.find((s) => s.id === schemeId);
  return guide.branches.filter((b) => scheme?.branchIds.includes(b.id));
}
export function resolveSelection(guide: ExamGuide, scheme?: string | null, branch?: string | null) {
  const schemeId = guide.schemes.some((s) => s.id === scheme) ? scheme! : guide.defaultSchemeId;
  const branches = branchesForScheme(guide, schemeId);
  const branchId = branches.some((b) => b.id === branch) ? branch! :
    branches.find((b) => b.id === guide.defaultBranchId)?.id || branches[0].id;
  return { schemeId, branchId };
}
export function syllabusFor(guide: ExamGuide, schemeId: string, branchId: string) {
  return guide.syllabus.filter((p) => p.schemeId === schemeId && (!p.branchId || p.branchId === branchId));
}
export function archiveFor(guide: ExamGuide, schemeId: string, branchId: string) {
  return guide.archive.filter((p) => p.schemeId === schemeId && (!p.branchId || p.branchId === branchId));
}
/** Keep shared topics independent across schemes AND branches; never copy progress silently. */
export function progressKey(guideId: string, schemeId: string, branchId: string, paperId: string, unitId: string) {
  return JSON.stringify([guideId, schemeId, branchId, paperId, unitId]);
}
export function readStudyProgress(value: unknown): StudyProgress {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return Object.fromEntries(Object.entries(value).filter(([, done]) => typeof done === 'boolean'));
}
export function guideProblems(guide: ExamGuide): string[] {
  const errors: string[] = [];
  const unique = (ids: string[], label: string) => { if (new Set(ids).size !== ids.length) errors.push(`Duplicate ${label}`); };
  if (guide.schemaVersion !== 1) errors.push('Unsupported schema version');
  unique(guide.sources.map((s) => s.id), 'source');
  unique(guide.schemes.map((s) => s.id), 'scheme');
  unique(guide.branches.map((b) => b.id), 'branch');
  unique(guide.syllabus.map((p) => p.id), 'syllabus paper');
  unique(guide.archive.map((p) => p.id), 'archive paper');
  const sources = new Set(guide.sources.map((s) => s.id));
  const branches = new Set(guide.branches.map((b) => b.id));
  const schemes = new Map(guide.schemes.map((s) => [s.id, s]));
  if (!schemes.has(guide.defaultSchemeId)) errors.push('Missing default scheme');
  if (!schemes.get(guide.defaultSchemeId)?.branchIds.includes(guide.defaultBranchId)) errors.push('Invalid default branch');
  for (const s of guide.schemes) {
    if (!s.branchIds.length || s.branchIds.some((b) => !branches.has(b))) errors.push(`Invalid branches: ${s.id}`);
    if (!s.sourceIds.length || s.sourceIds.some((id) => !sources.has(id))) errors.push(`Invalid sources: ${s.id}`);
  }
  for (const p of [...guide.syllabus, ...guide.archive]) {
    if (!sources.has(p.sourceId)) errors.push(`Unknown source: ${p.id}`);
    const scheme = p.schemeId ? schemes.get(p.schemeId) : undefined;
    if (p.schemeId && !scheme) errors.push(`Unknown scheme: ${p.id}`);
    if (p.branchId && (!branches.has(p.branchId) || (scheme && !scheme.branchIds.includes(p.branchId)))) errors.push(`Invalid branch: ${p.id}`);
  }
  for (const p of guide.syllabus) {
    unique(p.units.map((u) => u.id), `unit in ${p.id}`);
    if (p.units.some((u) => !u.title.trim() || !u.description.trim())) errors.push(`Empty syllabus unit: ${p.id}`);
  }
  for (const s of guide.sources) if (!/^https:\/\//.test(s.url)) errors.push(`Source must use HTTPS: ${s.id}`);
  for (const p of guide.archive) {
    if (!/^https:\/\//.test(p.url)) errors.push(`Paper must use HTTPS: ${p.id}`);
    if (p.schemeBasis === 'unknown' && p.schemeId) errors.push(`Unknown scheme cannot be assigned: ${p.id}`);
  }
  return errors;
}

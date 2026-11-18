/** Small public launcher metadata; full syllabus catalogs stay lazy-loaded. */
export const MES_GUIDE = {
  id: 'mes',
  title: 'Mizoram Engineering Service (MES)',
  short: 'MES',
  branchCount: 7,
  paperCount: 159,
  search: 'Engineering Service AE SDO Civil Mechanical Electrical Electronics Computer Science Architecture Agricultural',
} as const;
export const EXAM_GUIDES = [MES_GUIDE] as const;

import data from '@/data/exam-guides/mes.json';
import { ExamGuidePage } from '../components/exam-guide/ExamGuidePage';
import type { ExamGuide } from '@/lib/examGuides';

export default function MesPage() {
  return <ExamGuidePage guide={data as ExamGuide} />;
}

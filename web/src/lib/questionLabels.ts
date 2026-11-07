/** Learning labels never claim to be the original examination paper title. */
export function questionTopicLabel(q: {taxonomy_topic?: string | null; taxonomy_subject?: string | null; taxonomy_subject_id?: string | null}, collectionId?: string): string {
  if (q.taxonomy_topic) return q.taxonomy_topic
  if (['general-knowledge', 'general-studies'].includes(q.taxonomy_subject_id || '')) return ['udc','ldc','assistant','group-b-non-gazetted'].includes(collectionId || '') ? 'General Knowledge' : 'GK/GS'
  return q.taxonomy_subject || 'Unclassified'
}

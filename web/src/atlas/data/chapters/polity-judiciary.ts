import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// JUDICIARY — one integrated pyramid (Art 124–147, Art 32)
//
// Authored concept:
//   "India's judiciary is a single pyramid with its apex in
//   Delhi — and its arms reach everywhere: one High Court can
//   serve four states (Gauhati), and one postcard from Bihar's
//   jails became the first great PIL."
//
// Content mined from olol: Lecture 6 (Judiciary).pptx and
// Lecture 6(SC).pptx (MS Academy).
// ============================================

const SC_DELHI: [number, number] = [28.6219, 77.2384];
const PATNA: [number, number] = [25.5941, 85.1376];

const apex: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'sc', name: 'Supreme Court of India, New Delhi — Part V Ch IV, Articles 124–147' },
      geometry: { type: 'Point', coordinates: [SC_DELHI[1], SC_DELHI[0]] },
    },
  ],
};

/** One High Court, four states — the joint-HC provision in action. */
const gauhatiSystem: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'ghc', name: 'Gauhati High Court (Guwahati) — principal seat; jurisdiction over Assam, Nagaland, Mizoram & Arunachal Pradesh' }, geometry: { type: 'Point', coordinates: [91.7362, 26.1445] } },
    { type: 'Feature', properties: { id: 'ghc-kohima', name: 'Kohima Bench (Nagaland)' }, geometry: { type: 'Point', coordinates: [94.1086, 25.6751] } },
    { type: 'Feature', properties: { id: 'ghc-aizawl', name: 'Aizawl Bench (Mizoram)' }, geometry: { type: 'Point', coordinates: [92.7173, 23.7307] } },
    { type: 'Feature', properties: { id: 'ghc-itanagar', name: 'Itanagar Bench (Arunachal Pradesh)' }, geometry: { type: 'Point', coordinates: [93.6053, 27.0844] } },
  ],
};

/** Spokes from principal seat to benches — the joint HC drawn as a system. */
const gauhatiSpokes: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'sp-k', name: 'Guwahati → Kohima' }, geometry: { type: 'LineString', coordinates: [[91.7362, 26.1445], [94.1086, 25.6751]] } },
    { type: 'Feature', properties: { id: 'sp-a', name: 'Guwahati → Aizawl' }, geometry: { type: 'LineString', coordinates: [[91.7362, 26.1445], [92.7173, 23.7307]] } },
    { type: 'Feature', properties: { id: 'sp-i', name: 'Guwahati → Itanagar' }, geometry: { type: 'LineString', coordinates: [[91.7362, 26.1445], [93.6053, 27.0844]] } },
  ],
};

/** Where PIL began. */
const pilOrigin: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'patna', name: 'Bihar — Hussainara Khatoon v. State of Bihar (9 Mar 1979): the first great PIL, ~40,000 undertrials released' },
      geometry: { type: 'Point', coordinates: [PATNA[1], PATNA[0]] },
    },
  ],
};

export const polityJudiciaryChapter: Chapter = {
  id: 'polity-judiciary',
  subject: 'polity',
  unit: 'Institutions',
  tags: ['delhi', 'constitution', 'mizoram', 'nagaland', 'assam', 'northeast', 'bihar'],
  title: 'Judiciary, Writs & PIL',
  summary: 'One integrated pyramid: Supreme Court (Art 124–147), Article 32 and the five writs, PIL from Hussainara Khatoon, and the joint High Court system.',
  focus:
    'Single integrated judiciary: SC → High Courts → subordinate courts. Master the 5 writs (Habeas Corpus, Mandamus, Prohibition, Certiorari, Quo Warranto), Art 32 vs Art 226, and PIL — locus standi does not apply.',
  view: { center: [25.5, 84.5], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#4a5fa5' },
  layers: [
    {
      id: 'apex',
      name: 'The apex',
      description: 'Supreme Court of India — guardian and final interpreter of the Constitution.',
      kind: 'vector',
      data: apex,
      style: { color: '#4a5fa5', markerRadius: 9, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'gauhati',
      name: 'Joint HC: Gauhati system',
      description: 'One High Court for four states — principal seat + Kohima, Aizawl, Itanagar benches.',
      kind: 'vector',
      data: gauhatiSystem,
      style: { color: '#2e7d5b', markerRadius: 7 },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'gauhati-spokes',
      name: 'Bench spokes',
      description: 'Jurisdiction radiating from the principal seat.',
      kind: 'vector',
      data: gauhatiSpokes,
      style: { color: '#2e7d5b', weight: 2, flow: true, dashArray: '4 8' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'pil',
      name: 'Birth of PIL',
      description: 'Hussainara Khatoon (1979) — Bihar\u2019s undertrials and the right to a speedy trial.',
      kind: 'vector',
      data: pilOrigin,
      style: { color: '#a5504a', markerRadius: 8, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
  ],
  facts: [
    { id: 'f1', text: 'India has a single, integrated judicial system: the Supreme Court at the top, High Courts at state level, subordinate courts below — all links of one chain, with the SC running judicial administration.', linkedLayerId: 'apex' },
    { id: 'f2', text: 'The Supreme Court is established by Part V, Chapter IV; Articles 124–147 lay down its composition and jurisdiction. It is the guardian and final interpreter of the Constitution.' },
    { id: 'f3', text: 'Independence is secured by: appointment by the President, high qualifications, removal only by difficult impeachment, protected salaries and pensions, an independent establishment, and functional autonomy.' },
    { id: 'f4', text: 'A High Court exists for each state, but two or more states can by mutual consent have a Joint High Court — the Gauhati High Court serves Assam, Nagaland, Mizoram and Arunachal Pradesh, with benches at Kohima, Aizawl and Itanagar.', linkedLayerId: 'gauhati' },
    { id: 'f5', text: 'The SC is the arbiter of federal disputes: Centre vs state(s); Centre + state(s) vs other state(s); state vs state.' },
    { id: 'f6', text: 'Article 32 (Right to Constitutional Remedies) lets any individual move the SC directly for enforcement of Fundamental Rights; Art 32(2) confers writ jurisdiction. Ambedkar called it "the heart and soul of the Constitution".' },
    { id: 'f7', text: 'Five writs — Habeas Corpus: produce a detained person, valid reasons or release (not against legislative/court contempt proceedings). Mandamus: command a public authority to perform a duty (never against a private individual). Prohibition: stop a lower court acting outside jurisdiction (judicial/quasi-judicial only). Certiorari: transfer/quash a lower court\u2019s decision for excess or lack of jurisdiction. Quo Warranto: "by what authority" — tests a claim to public office.' },
    { id: 'f8', text: 'Writ jurisdiction differs: under Art 32 the SC acts only for Fundamental Rights; High Courts (Art 226) can issue writs for FRs and for other legal rights — wider in scope.' },
    { id: 'f9', text: 'PIL originated in the USA (there "Social Action Litigation"); rests on pro bono publico — for the common good. Only the SC and HCs can entertain it; it is judge-made law, regulated by neither executive nor legislature.' },
    { id: 'f10', text: 'In PIL, locus standi does not apply — any member of the public may petition on behalf of those who cannot; even a postcard to the court can be a petition, fees can be waived, and free legal aid directed.', linkedLayerId: 'pil' },
    { id: 'f11', text: 'Hussainara Khatoon v. State of Bihar (9 March 1979) — widely counted the first PIL: Bihar undertrials jailed beyond their maximum possible sentences; the Court made speedy trial the issue and ordered the release of nearly 40,000 undertrials.', linkedLayerId: 'pil' },
    { id: 'f12', text: 'Judicial activism: PIL and Lok Adalats expanded the reach of Fundamental Rights and forced the executive and legislature to discharge constitutional obligations — justice made accessible to the poor and marginalised.' },
  ],
  events: [
    { id: 'e1', date: '1950-01-28', label: '1950 — SC inaugurated', description: 'The Supreme Court comes into being under the new Constitution (Part V, Ch IV; Arts 124–147), replacing the Federal Court.', showLayers: ['apex'], view: { center: [28.62, 77.24], zoom: 10 } },
    { id: 'e2', date: '1979-03-09', label: '1979 — Hussainara Khatoon', description: 'The first great PIL: right to speedy trial; ~40,000 Bihar undertrials released.', showLayers: ['pil'], view: { center: [25.6, 85.1], zoom: 7 } },
    { id: 'e3', date: '1990', label: 'Joint HC in action', description: 'The Gauhati High Court model: one principal seat, benches at Kohima, Aizawl and Itanagar serving four states.', showLayers: ['gauhati', 'gauhati-spokes'], view: { center: [25.4, 92.9], zoom: 6 } },
  ],
  quiz: [
    {
      id: 'q1', type: 'mcq',
      question: 'Which Article did Dr Ambedkar call "the heart and soul of the Constitution"?',
      options: ['Article 14', 'Article 21', 'Article 32', 'Article 226'],
      answerIndex: 2,
      explanation: 'Art 32 — the Right to Constitutional Remedies; the fundamental of all Fundamental Rights, without which the Constitution would be a nullity.',
    },
    {
      id: 'q2', type: 'mcq',
      question: 'Which writ CANNOT be issued against a private individual?',
      options: ['Habeas Corpus', 'Mandamus', 'Quo Warranto', 'Certiorari'],
      answerIndex: 1,
      explanation: 'Mandamus commands public authorities/officials to perform duties — never a private individual. (Habeas Corpus can run against private detention.)',
    },
    {
      id: 'q3', type: 'mcq',
      question: 'The writ asking "by what authority do you hold this office?" is:',
      options: ['Prohibition', 'Certiorari', 'Quo Warranto', 'Mandamus'],
      answerIndex: 2,
      explanation: 'Quo Warranto tests the legality of a person\u2019s claim to a public office and prevents illegal usurpation.',
    },
    {
      id: 'q4', type: 'mcq',
      question: 'The writ jurisdiction of High Courts compared to the Supreme Court is:',
      options: ['Narrower — FRs only', 'Wider — FRs plus other legal rights', 'Identical', 'Limited to criminal matters'],
      answerIndex: 1,
      explanation: 'Art 226 (HCs) covers Fundamental Rights AND other legal rights; Art 32 (SC) is confined to Fundamental Rights.',
    },
    {
      id: 'q5', type: 'mcq',
      question: 'Hussainara Khatoon v. State of Bihar (1979) is celebrated as:',
      options: ['The basic structure case', 'The first major Public Interest Litigation', 'The case that created Lok Adalats', 'The first habeas corpus case'],
      answerIndex: 1,
      explanation: 'It made the right to speedy trial central and led to the release of ~40,000 undertrials — PIL\u2019s founding moment in India.',
    },
    {
      id: 'q6', type: 'map_click',
      question: 'Click the Mizoram bench of the Gauhati High Court.',
      answer: { lat: 23.7307, lng: 92.7173, toleranceKm: 90 },
      explanation: 'Aizawl — one of the three benches (Kohima, Aizawl, Itanagar) of the joint High Court serving four NE states.',
    },
    {
      id: 'q7', type: 'map_click',
      question: 'Click the state whose undertrial prisoners gave India its first great PIL.',
      answer: { lat: PATNA[0], lng: PATNA[1], toleranceKm: 180 },
      explanation: 'Bihar — Hussainara Khatoon, 9 March 1979.',
    },
  ],
};

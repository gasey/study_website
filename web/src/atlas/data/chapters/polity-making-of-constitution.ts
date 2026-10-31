import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// MAKING OF THE CONSTITUTION — 1600 → 1950
//
// Authored concept:
//   "The Constitution wasn't written in 1946–49; it accreted
//   for 175 years along a Calcutta→Delhi axis of colonial
//   statutes — and the map shows where each layer was laid."
//
// Content mined from the Polity Codex study guide
// (Historical Background + Constituent Assembly topics).
// ============================================

const CALCUTTA: [number, number] = [22.5726, 88.3639];
const DELHI: [number, number] = [28.6139, 77.209];
const BUXAR: [number, number] = [25.5647, 83.9787];
const ALLAHABAD: [number, number] = [25.4358, 81.8463];
const MADRAS: [number, number] = [13.0827, 80.2707];
const BOMBAY: [number, number] = [18.9582, 72.8321];

/** Seats of colonial constitutional power. */
const powerSeats: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'calcutta-sc', name: 'Calcutta — capital of British India till 1911; Supreme Court set up 1774 (Regulating Act 1773)' },
      geometry: { type: 'Point', coordinates: [CALCUTTA[1], CALCUTTA[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'delhi-ca', name: 'Delhi — capital from 1911; Constituent Assembly met here (9 Dec 1946), Federal Court 1937' },
      geometry: { type: 'Point', coordinates: [DELHI[1], DELHI[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'madras-presi', name: 'Madras Presidency — made subordinate to Bengal by the Regulating Act 1773' },
      geometry: { type: 'Point', coordinates: [MADRAS[1], MADRAS[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'bombay-presi', name: 'Bombay Presidency — made subordinate to Bengal by the Regulating Act 1773' },
      geometry: { type: 'Point', coordinates: [BOMBAY[1], BOMBAY[0]] },
    },
  ],
};

/** Where Company rule became territorial rule. */
const dawnOfCompanyRule: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'buxar', name: 'Buxar (1764) — Company defeats Mir Qasim, Shuja-ud-Daula & Shah Alam II' },
      geometry: { type: 'Point', coordinates: [BUXAR[1], BUXAR[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'allahabad', name: 'Allahabad (1765) — Treaty: Shah Alam II grants Diwani of Bengal, Bihar & Orissa to Clive' },
      geometry: { type: 'Point', coordinates: [ALLAHABAD[1], ALLAHABAD[0]] },
    },
  ],
};

/** The Diwani grant — the revenue territory that started it all. */
const diwaniTerritory: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'diwani-1765', name: 'Diwani of Bengal, Bihar & Orissa (1765)' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [83.3, 25.6], [86.0, 27.2], [88.6, 27.1], [92.3, 26.1],
          [92.6, 24.1], [91.0, 22.0], [88.4, 21.4], [86.8, 19.9],
          [84.6, 19.2], [83.6, 21.6], [84.0, 23.8], [83.3, 25.6],
        ]],
      },
    },
  ],
};

/** Capital shift — the constitutional centre of gravity moves. */
const capitalShift: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'shift-1911', name: 'Capital shift: Calcutta → Delhi (announced 1911)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [88.3639, 22.5726], [86.4, 23.9], [83.9, 25.1], [81.8, 25.6], [79.5, 27.2], [77.209, 28.6139],
        ],
      },
    },
  ],
};

export const polityConstitutionChapter: Chapter = {
  id: 'polity-making-of-constitution',
  subject: 'polity',
  unit: 'Constitution',
  tags: ['calcutta', 'delhi', 'bengal', 'buxar', 'allahabad', 'constitution', 'british'],
  title: 'Making of the Constitution',
  summary: 'From the Regulating Act 1773 to 26 January 1950 — the statutes, cities and committees that built the Constitution.',
  focus:
    'The Constitution accreted over 175 years along a Calcutta→Delhi axis — Regulating Act 1773 → GoI Act 1935 → Constituent Assembly 1946–49. Know the acts in order, and know what each introduced first.',
  view: { center: [24.5, 83.0], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#4a5fa5' },
  layers: [
    {
      id: 'diwani',
      name: 'Diwani grant 1765',
      description: 'Revenue rights over Bengal, Bihar & Orissa — Company rule begins in substance.',
      kind: 'vector',
      data: diwaniTerritory,
      style: { color: '#4a5fa5', fillColor: '#4a5fa5', fillOpacity: 0.1, weight: 2, pattern: 'hatch' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'dawn',
      name: 'Buxar & Allahabad',
      description: 'The battle and the treaty that made traders into rulers.',
      kind: 'vector',
      data: dawnOfCompanyRule,
      style: { color: '#a5504a', markerRadius: 8, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'seats',
      name: 'Seats of power',
      description: 'Calcutta, Delhi and the subordinated presidencies.',
      kind: 'vector',
      data: powerSeats,
      style: { color: '#2e5d8a', markerRadius: 7 },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'capital-shift',
      name: 'Capital shift 1911',
      description: 'Calcutta → Delhi: the constitutional centre of gravity moves.',
      kind: 'vector',
      data: capitalShift,
      style: { color: '#7a4a2a', weight: 3, flow: true, dashArray: '6 8' },
      defaultOn: false,
      labelKey: 'name',
    },
  ],
  facts: [
    { id: 'f1', text: 'The East India Company arrived in 1600 as traders under a charter of Queen Elizabeth I. Company Rule ran 1773–1858, Crown Rule 1858–1947.' },
    { id: 'f2', text: 'Battle of Buxar (1764) → Treaty of Allahabad (1765, Shah Alam II & Robert Clive): the Company gained Diwani (revenue) rights over Bengal, Bihar and Orissa.', linkedLayerId: 'dawn' },
    { id: 'f3', text: 'Regulating Act 1773: Governor of Bengal became Governor-General of Bengal (first: Warren Hastings); Madras & Bombay made subordinate; Supreme Court at Calcutta (1774).', linkedLayerId: 'seats' },
    { id: 'f4', text: 'GoI Act 1919 (Montagu–Chelmsford): dyarchy in provinces (transferred + reserved subjects), bicameralism and direct elections for the first time; High Commissioner for India in London.' },
    { id: 'f5', text: 'GoI Act 1935 — the longest British act (321 Sections, 10 Schedules): All-India Federation (never realised), Federal/Provincial/Concurrent Lists (59/54/36), residuary powers with the Viceroy, RBI and Federal Court (1937), dyarchy abolished in provinces.' },
    { id: 'f6', text: 'Constituent Assembly: idea first proposed by M.N. Roy (1934); set up under the Cabinet Mission Plan 1946; members indirectly elected by Provincial Legislative Assemblies.' },
    { id: 'f7', text: 'Membership: originally 389 (292 provinces + 93 princely states + 4 chief commissioner\u2019s provinces); 299 after Partition.' },
    { id: 'f8', text: 'First sitting 9 Dec 1946. Sachchidananda Sinha = temporary Chairman; Rajendra Prasad = President; H.C. Mookerjee = Vice-President; B.N. Rau = constitutional advisor.' },
    { id: 'f9', text: 'Drafting Committee (29 Aug 1947, 7 members) chaired by Dr B.R. Ambedkar — it sat only 141 days. Objectives Resolution moved by Nehru on 22 Jan 1947.' },
    { id: 'f10', text: 'Adopted 26 Nov 1949 (Preamble + 395 Articles + 8 Schedules); in force 26 Jan 1950. Constitution Day celebrated on 26 Nov since 2015.' },
  ],
  events: [
    { id: 'e1', date: '1600', label: '1600 — EIC arrives', description: 'East India Company comes to India as traders under a royal charter of Elizabeth I.' },
    { id: 'e2', date: '1765', label: '1765 — Diwani', description: 'After Buxar (1764), the Treaty of Allahabad gives the Company Diwani of Bengal, Bihar & Orissa.', showLayers: ['dawn', 'diwani'], view: { center: [25.2, 84.5], zoom: 6 } },
    { id: 'e3', date: '1773', label: '1773 — Regulating Act', description: 'Governor-General of Bengal created (Warren Hastings); Supreme Court at Calcutta 1774; Madras & Bombay subordinated.', showLayers: ['seats'], view: { center: [22.6, 88.36], zoom: 6 } },
    { id: 'e4', date: '1858', label: '1858 — Crown Rule', description: 'GoI Act 1858 after the Revolt of 1857: Company rule ends, Secretary of State for India + Viceroy (first: Canning).' },
    { id: 'e5', date: '1911', label: '1911 — Capital to Delhi', description: 'The capital shifts from Calcutta to Delhi — the future constitutional centre.', showLayers: ['capital-shift'], view: { center: [25.8, 82.5], zoom: 5 } },
    { id: 'e6', date: '1919', label: '1919 — Montford Reforms', description: 'GoI Act 1919: dyarchy in the provinces, bicameralism, first direct elections.' },
    { id: 'e7', date: '1935', label: '1935 — GoI Act', description: 'The 1935 Act — the single biggest source of the 1950 Constitution: federation scheme, three lists, provincial autonomy, RBI, Federal Court.' },
    { id: 'e8', date: '1946-12-09', label: '1946 — CA first sits', description: 'Constituent Assembly first meets in Delhi under temporary Chairman Sachchidananda Sinha.', view: { center: [28.61, 77.21], zoom: 6 } },
    { id: 'e9', date: '1949-11-26', label: '1949 — Adopted', description: 'Constitution adopted: Preamble + 395 Articles + 8 Schedules.' },
    { id: 'e10', date: '1950-01-26', label: '1950 — In force', description: 'Constitution comes into force on 26 January 1950 — the date chosen to honour Purna Swaraj Day (26 Jan 1930).' },
  ],
  quiz: [
    {
      id: 'q1', type: 'mcq',
      question: 'The Regulating Act of 1773 designated whom as the first Governor-General of Bengal?',
      options: ['Robert Clive', 'Warren Hastings', 'Lord Cornwallis', 'Lord Mountbatten'],
      answerIndex: 1,
      explanation: 'The Act renamed the Governor of Bengal as Governor-General of Bengal — first holder Warren Hastings. It also set up the Supreme Court at Calcutta (1774).',
    },
    {
      id: 'q2', type: 'map_click',
      question: 'Click the city where the Regulating Act 1773 established the Supreme Court (1774).',
      answer: { lat: CALCUTTA[0], lng: CALCUTTA[1], toleranceKm: 150 },
      explanation: 'Calcutta — capital of British India until 1911 and seat of the 1774 Supreme Court.',
    },
    {
      id: 'q3', type: 'mcq',
      question: 'Diwani rights over Bengal, Bihar and Orissa came to the Company after which event?',
      options: ['Battle of Plassey', 'Battle of Buxar / Treaty of Allahabad', 'Revolt of 1857', 'Third Round Table Conference'],
      answerIndex: 1,
      explanation: 'After Buxar (1764), the Treaty of Allahabad (1765) between Shah Alam II and Clive granted the Diwani.',
    },
    {
      id: 'q4', type: 'mcq',
      question: 'The Government of India Act 1935 contained:',
      options: ['145 Sections, 5 Schedules', '321 Sections, 10 Schedules', '395 Articles, 8 Schedules', '250 Sections, 12 Schedules'],
      answerIndex: 1,
      explanation: '321 Sections and 10 Schedules — the longest act passed by the British Parliament for India. (395 Articles + 8 Schedules is the 1949 Constitution.)',
    },
    {
      id: 'q5', type: 'mcq',
      question: 'Who first proposed the idea of a Constituent Assembly for India?',
      options: ['Jawaharlal Nehru', 'M.N. Roy', 'B.R. Ambedkar', 'Mahatma Gandhi'],
      answerIndex: 1,
      explanation: 'M.N. Roy proposed it in 1934; Congress made it an official demand in 1935; the British conceded it in the August Offer 1940; it was constituted under the Cabinet Mission Plan 1946.',
    },
    {
      id: 'q6', type: 'mcq',
      question: 'The Drafting Committee of the Constitution was chaired by:',
      options: ['Rajendra Prasad', 'B.N. Rau', 'Dr B.R. Ambedkar', 'H.C. Mookerjee'],
      answerIndex: 2,
      explanation: 'Formed 29 Aug 1947 with 7 members under Ambedkar. Rajendra Prasad presided over the Assembly; B.N. Rau was the constitutional advisor.',
    },
    {
      id: 'q7', type: 'map_click',
      question: 'Click the site of the 1765 treaty that granted the Company the Diwani of Bengal, Bihar and Orissa.',
      answer: { lat: ALLAHABAD[0], lng: ALLAHABAD[1], toleranceKm: 130 },
      explanation: 'Allahabad (Prayagraj) — Treaty of Allahabad, 1765, between Shah Alam II and Robert Clive.',
    },
  ],
};

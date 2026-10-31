import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// UNION & STATES REORGANISATION — Art 1–4
//
// Authored concept:
//   "Article 3 lets Parliament redraw the political map of
//   India by simple majority — and it has, in waves:
//   1953 → 1956 → 1960s → 1971–72 (NE) → 2000 → 2014."
//
// Content mined from the Polity Codex study guide
// (Union & Territory topic).
// ============================================

const MADRAS: [number, number] = [13.0827, 80.2707];
const KURNOOL: [number, number] = [15.8281, 78.0373]; // first Andhra capital
const HYDERABAD: [number, number] = [17.385, 78.4867];
const BOMBAY: [number, number] = [18.9582, 72.8321];
const CHANDIGARH: [number, number] = [30.7333, 76.7794];

/** The linguistic spark — Andhra out of Madras, 1953. */
const andhraSpark: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'madras-1953', name: 'Madras — Potti Sriramulu\u2019s 56-day fast (1952) for a Telugu state' },
      geometry: { type: 'Point', coordinates: [MADRAS[1], MADRAS[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'kurnool', name: 'Kurnool — first capital of Andhra State (1953)' },
      geometry: { type: 'Point', coordinates: [KURNOOL[1], KURNOOL[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'hyderabad-2014', name: 'Hyderabad — shared capital when Telangana became the 29th state (2 June 2014)' },
      geometry: { type: 'Point', coordinates: [HYDERABAD[1], HYDERABAD[0]] },
    },
  ],
};

/** Waves of bifurcation — where new states were carved. */
const bifurcations: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'bombay-split', name: 'Bombay → Maharashtra + Gujarat (1 May 1960)' }, geometry: { type: 'Point', coordinates: [BOMBAY[1], BOMBAY[0]] } },
    { type: 'Feature', properties: { id: 'punjab-split', name: 'Punjab → Punjab + Haryana (1966); Chandigarh = shared capital (UT)' }, geometry: { type: 'Point', coordinates: [CHANDIGARH[1], CHANDIGARH[0]] } },
    { type: 'Feature', properties: { id: 'uttarakhand', name: 'Uttaranchal/Uttarakhand out of UP (9 Nov 2000)' }, geometry: { type: 'Point', coordinates: [79.0193, 30.0668] } },
    { type: 'Feature', properties: { id: 'jharkhand', name: 'Jharkhand out of Bihar (15 Nov 2000)' }, geometry: { type: 'Point', coordinates: [85.3096, 23.6102] } },
    { type: 'Feature', properties: { id: 'chhattisgarh', name: 'Chhattisgarh out of MP (1 Nov 2000)' }, geometry: { type: 'Point', coordinates: [81.8661, 21.2787] } },
    { type: 'Feature', properties: { id: 'telangana', name: 'Telangana out of Andhra Pradesh (2 June 2014) — 29th state' }, geometry: { type: 'Point', coordinates: [79.0193, 18.1124] } },
  ],
};

/** North-East reorganisation 1971–72 + statehood wave. */
const northeastWave: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'meghalaya', name: 'Meghalaya — state 1972 (carved from Assam)' }, geometry: { type: 'Point', coordinates: [91.3662, 25.467] } },
    { type: 'Feature', properties: { id: 'manipur-st', name: 'Manipur — UT 1956 → state 1972' }, geometry: { type: 'Point', coordinates: [93.9063, 24.6637] } },
    { type: 'Feature', properties: { id: 'tripura-st', name: 'Tripura — UT 1956 → state 1972' }, geometry: { type: 'Point', coordinates: [91.2868, 23.8315] } },
    { type: 'Feature', properties: { id: 'nagaland-st', name: 'Nagaland — 16th state, 1 Dec 1963 (13th Amendment, Art 371A)' }, geometry: { type: 'Point', coordinates: [94.1086, 26.1584] } },
    { type: 'Feature', properties: { id: 'mizoram-st', name: 'Mizoram — UT 1972 → 23rd state 1987 (53rd Amendment, Art 371G)' }, geometry: { type: 'Point', coordinates: [92.7173, 23.7307] } },
    { type: 'Feature', properties: { id: 'arunachal-st', name: 'Arunachal Pradesh (NEFA) — UT 1972 → state 1987' }, geometry: { type: 'Point', coordinates: [93.6053, 27.5539] } },
    { type: 'Feature', properties: { id: 'sikkim-st', name: 'Sikkim — associate state (35th Amdt 1974) → full state 1975 (36th Amdt)' }, geometry: { type: 'Point', coordinates: [88.5122, 27.533] } },
  ],
};

/** Acquired territories — India can acquire foreign territory. */
const acquired: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'goa-acq', name: 'Goa, Daman & Diu — liberated from Portugal 1961; Goa a state 1987' }, geometry: { type: 'Point', coordinates: [73.8278, 15.4989] } },
    { type: 'Feature', properties: { id: 'pondi-acq', name: 'Puducherry — ceded by France (de facto 1954)' }, geometry: { type: 'Point', coordinates: [79.8083, 11.9416] } },
  ],
};

export const polityStatesReorgChapter: Chapter = {
  id: 'polity-states-reorganisation',
  subject: 'polity',
  unit: 'Constitution',
  tags: ['madras', 'hyderabad', 'bombay', 'nagaland', 'mizoram', 'sikkim', 'goa', 'states', 'northeast'],
  title: 'Union & States Reorganisation',
  summary: 'Articles 1–4: how Parliament has redrawn India\u2019s map — Andhra 1953, SRA 1956, NE wave 1963–87, three states in 2000, Telangana 2014.',
  focus:
    'Article 3 lets Parliament create/alter states by SIMPLE majority (with the President\u2019s prior recommendation; the affected state\u2019s opinion is not binding). Track the waves: 1953 → 1956 → 1960/66 → 1963–87 (NE) → 2000 → 2014.',
  view: { center: [21.5, 82.0], zoom: 4.5 },
  basemap: 'natgeo',
  theme: { accent: '#4a5fa5' },
  layers: [
    {
      id: 'andhra-spark',
      name: 'The linguistic spark',
      description: 'Potti Sriramulu, Andhra 1953, and the 2014 Telangana echo.',
      kind: 'vector',
      data: andhraSpark,
      style: { color: '#a5504a', markerRadius: 8, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'bifurcations',
      name: 'Bifurcation waves',
      description: '1960 Bombay, 1966 Punjab, 2000 trio, 2014 Telangana.',
      kind: 'vector',
      data: bifurcations,
      style: { color: '#4a5fa5', markerRadius: 7 },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'ne-wave',
      name: 'North-East statehood wave',
      description: 'Nagaland 1963 → NEAR Act 1971 → Mizoram & Arunachal 1987; Sikkim 1975.',
      kind: 'vector',
      data: northeastWave,
      style: { color: '#2e7d5b', markerRadius: 7 },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'acquired',
      name: 'Acquired territories',
      description: 'Goa (1961) and Puducherry (1954) — cession, conquest, plebiscite.',
      kind: 'vector',
      data: acquired,
      style: { color: '#7a4a2a', markerRadius: 7 },
      defaultOn: false,
      labelKey: 'name',
    },
  ],
  facts: [
    { id: 'f1', text: 'Article 1: "India, that is Bharat, shall be a Union of States" — states have no right to secede. Territory of India = states + UTs + acquired territories (First Schedule lists names & extents).' },
    { id: 'f2', text: 'Article 2: Parliament may admit or establish new states. Article 3: form new states, alter areas, boundaries or names — by SIMPLE majority, with the President\u2019s prior recommendation; the concerned state legislature\u2019s view is NOT binding.' },
    { id: 'f3', text: 'Dhar Commission (1948) and the JVP Committee (Nehru–Patel–Pattabhi Sitaramayya, 1948) both rejected language as the sole basis for states.' },
    { id: 'f4', text: 'Potti Sriramulu\u2019s 56-day fast (died Dec 1952) forced the creation of Andhra State (1953, capital Kurnool) — the first linguistic state, carved out of Madras.', linkedLayerId: 'andhra-spark' },
    { id: 'f5', text: 'Fazl Ali Commission / SRC (1953; members K.M. Panikkar & H.N. Kunzru) rejected "one language, one state" → States Reorganisation Act 1956 + 7th Amendment: 14 states + 6 UTs.' },
    { id: 'f6', text: 'Bombay split into Maharashtra + Gujarat (1960); Punjab split into Punjab + Haryana (1966) with Chandigarh as a shared-capital UT.', linkedLayerId: 'bifurcations' },
    { id: 'f7', text: 'North-East: Nagaland state 1963 (Art 371A); North-Eastern Areas (Reorganisation) Act 1971 → Meghalaya, Manipur, Tripura states (1972), Mizoram & Arunachal UTs (1972) → states in 1987 (Mizoram under Art 371G).', linkedLayerId: 'ne-wave' },
    { id: 'f8', text: 'Sikkim: associate state via the 35th Amendment (1974), full state via the 36th (1975) after a plebiscite — Article 371F.' },
    { id: 'f9', text: 'India can acquire foreign territory by cession, occupation, conquest, purchase, gift, lease or plebiscite — e.g. Goa, Daman & Diu (1961), Puducherry, Sikkim.', linkedLayerId: 'acquired' },
    { id: 'f10', text: 'Year 2000: Chhattisgarh (from MP), Uttarakhand (from UP), Jharkhand (from Bihar). 2014: Telangana, the 29th state. After J&K Reorganisation (2019): 28 states + 8 UTs (as of Jan 2025).' },
  ],
  events: [
    { id: 'e1', date: '1953', label: '1953 — Andhra', description: 'Andhra State created out of Madras after Potti Sriramulu\u2019s death — the linguistic dam breaks.', showLayers: ['andhra-spark'], view: { center: [15.5, 79.5], zoom: 6 } },
    { id: 'e2', date: '1956', label: '1956 — SRA', description: 'Fazl Ali Commission → States Reorganisation Act 1956 (7th Amendment): 14 states + 6 UTs.', view: { center: [21.5, 82.0], zoom: 4.5 } },
    { id: 'e3', date: '1960', label: '1960 — Bombay split', description: 'Maharashtra and Gujarat created from bilingual Bombay State (1 May 1960).', showLayers: ['bifurcations'], view: { center: [20.5, 74.5], zoom: 5.5 } },
    { id: 'e4', date: '1963', label: '1963 — Nagaland', description: 'Nagaland becomes the 16th state (13th Amendment; special provisions under Art 371A).', showLayers: ['ne-wave'], view: { center: [25.8, 93.5], zoom: 6 } },
    { id: 'e5', date: '1972', label: '1971–72 — NE reorganised', description: 'NEAR Act 1971: Meghalaya, Manipur, Tripura become states; Mizoram & Arunachal become UTs.', showLayers: ['ne-wave'], view: { center: [25.0, 92.8], zoom: 6 } },
    { id: 'e6', date: '1975', label: '1975 — Sikkim', description: 'Sikkim becomes a full state (36th Amendment, Art 371F).', view: { center: [27.53, 88.51], zoom: 7 } },
    { id: 'e7', date: '1987', label: '1987 — Mizoram, Arunachal, Goa', description: 'Mizoram (53rd Amdt, Art 371G) and Arunachal become states; Goa separated from Daman & Diu as a state.', view: { center: [23.7, 92.7], zoom: 6 } },
    { id: 'e8', date: '2000', label: '2000 — Three new states', description: 'Chhattisgarh (1 Nov), Uttarakhand (9 Nov), Jharkhand (15 Nov).', showLayers: ['bifurcations'], view: { center: [25.0, 82.0], zoom: 5 } },
    { id: 'e9', date: '2014-06-02', label: '2014 — Telangana', description: 'Telangana becomes the 29th state; Hyderabad shared capital for 10 years.', view: { center: [17.8, 79.0], zoom: 6 } },
  ],
  quiz: [
    {
      id: 'q1', type: 'mcq',
      question: 'Parliament can form a new state or alter the boundary/name of an existing state under Article 3 by:',
      options: ['Two-thirds special majority', 'Simple majority', 'Special majority + state ratification', 'Unanimous resolution of both Houses'],
      answerIndex: 1,
      explanation: 'Article 3 needs only a simple majority (plus the President\u2019s prior recommendation). The affected state\u2019s opinion is sought but not binding — which is why India is called "an indestructible Union of destructible states."',
    },
    {
      id: 'q2', type: 'mcq',
      question: 'The States Reorganisation Commission (1953) was chaired by:',
      options: ['S.K. Dhar', 'K.M. Panikkar', 'Fazl Ali', 'H.N. Kunzru'],
      answerIndex: 2,
      explanation: 'Fazl Ali chaired it; Panikkar and Kunzru were members. It led to the SRA 1956 — 14 states + 6 UTs.',
    },
    {
      id: 'q3', type: 'map_click',
      question: 'Click the city where Potti Sriramulu\u2019s fast (1952) forced the creation of the first linguistic state.',
      answer: { lat: MADRAS[0], lng: MADRAS[1], toleranceKm: 150 },
      explanation: 'Madras — Sriramulu fasted for a Telugu state to be carved out of Madras State; Andhra was created in 1953 with Kurnool as capital.',
    },
    {
      id: 'q4', type: 'mcq',
      question: 'Nagaland became a state in 1963 with special provisions under which Article?',
      options: ['Art 370', 'Art 371A', 'Art 371F', 'Art 371G'],
      answerIndex: 1,
      explanation: '371A = Nagaland (1963), 371F = Sikkim (1975), 371G = Mizoram (1987).',
    },
    {
      id: 'q5', type: 'map_click',
      question: 'Click the state that became the 23rd state of India in 1987 under Article 371G.',
      answer: { lat: 23.7307, lng: 92.7173, toleranceKm: 160 },
      explanation: 'Mizoram — UT in 1972 (NEAR Act), full state on 20 Feb 1987 after the Mizo Accord (1986).',
    },
    {
      id: 'q6', type: 'mcq',
      question: 'As of January 2025, India has:',
      options: ['29 states and 7 UTs', '28 states and 8 UTs', '28 states and 9 UTs', '29 states and 6 UTs'],
      answerIndex: 1,
      explanation: '28 states + 8 UTs after the J&K Reorganisation Act 2019 (J&K and Ladakh as UTs) and the DNH–Daman & Diu merger (2020).',
    },
    {
      id: 'q7', type: 'mcq',
      question: 'The names and territorial extents of the states are listed in which Schedule?',
      options: ['First Schedule', 'Fourth Schedule', 'Seventh Schedule', 'Tenth Schedule'],
      answerIndex: 0,
      explanation: 'First Schedule = states & UTs and their extents. (Fourth = Rajya Sabha seats; Seventh = the three lists; Tenth = anti-defection.)',
    },
  ],
};

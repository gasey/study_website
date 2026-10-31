import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// SIXTH SCHEDULE & LOCAL GOVERNMENT — Art 244(2), 73rd/74th
//
// Authored concept:
//   "Grassroots power in India has two geographies: ADCs
//   under the Sixth Schedule in four NE states, and the
//   73rd/74th-Amendment panchayat/municipal system everywhere
//   else — Nagaland & Mizoram sit outside Part IX entirely."
//
// Content mined from the Polity Codex study guide
// (Sixth Schedule + Local Government topics). High MPSC weight.
// ============================================

const NAGAUR: [number, number] = [27.2, 73.7337]; // first Panchayati Raj launch, 2 Oct 1959

/** Sixth Schedule states + ADC headquarters. */
const adcSeats: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    // Mizoram's three ADCs — MPSC favourites
    { type: 'Feature', properties: { id: 'lai-adc', name: 'Lai ADC — HQ Lawngtlai (Mizoram)' }, geometry: { type: 'Point', coordinates: [92.8977, 22.5286] } },
    { type: 'Feature', properties: { id: 'mara-adc', name: 'Mara ADC — HQ Siaha (Mizoram)' }, geometry: { type: 'Point', coordinates: [92.9793, 22.4918] } },
    { type: 'Feature', properties: { id: 'chakma-adc', name: 'Chakma ADC — HQ Chawngte/Kamalanagar (Mizoram)' }, geometry: { type: 'Point', coordinates: [92.6396, 22.7412] } },
    // Assam
    { type: 'Feature', properties: { id: 'kaziranga-karbi', name: 'Karbi Anglong AC — Diphu (Assam)' }, geometry: { type: 'Point', coordinates: [93.4306, 25.8433] } },
    { type: 'Feature', properties: { id: 'dima-hasao', name: 'Dima Hasao (N.C. Hills) AC — Haflong (Assam)' }, geometry: { type: 'Point', coordinates: [93.0169, 25.1698] } },
    { type: 'Feature', properties: { id: 'btc', name: 'Bodoland Territorial Council — Kokrajhar (Assam)' }, geometry: { type: 'Point', coordinates: [90.2661, 26.4014] } },
    // Meghalaya
    { type: 'Feature', properties: { id: 'khasi-adc', name: 'Khasi Hills ADC — Shillong (Meghalaya)' }, geometry: { type: 'Point', coordinates: [91.8933, 25.5788] } },
    { type: 'Feature', properties: { id: 'garo-adc', name: 'Garo Hills ADC — Tura (Meghalaya)' }, geometry: { type: 'Point', coordinates: [90.2201, 25.5143] } },
    { type: 'Feature', properties: { id: 'jaintia-adc', name: 'Jaintia Hills ADC — Jowai (Meghalaya)' }, geometry: { type: 'Point', coordinates: [92.1931, 25.4504] } },
    // Tripura
    { type: 'Feature', properties: { id: 'ttaadc', name: 'Tripura Tribal Areas ADC — Khumulwng (Tripura)' }, geometry: { type: 'Point', coordinates: [91.4074, 23.9137] } },
  ],
};

/** The four Sixth Schedule states — recognition polygons (simplified). */
const sixthStates: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'assam-6', name: 'Assam (Part I)' }, geometry: { type: 'Polygon', coordinates: [[[89.7, 26.2], [92.0, 27.3], [94.5, 27.6], [96.0, 27.3], [95.2, 26.6], [93.5, 25.5], [92.5, 24.8], [92.2, 25.0], [90.6, 25.4], [89.8, 25.6], [89.7, 26.2]]] } },
    { type: 'Feature', properties: { id: 'meghalaya-6', name: 'Meghalaya (Part II)' }, geometry: { type: 'Polygon', coordinates: [[[89.85, 25.55], [90.6, 25.9], [91.8, 26.0], [92.6, 25.6], [92.3, 25.1], [91.0, 25.1], [89.85, 25.55]]] } },
    { type: 'Feature', properties: { id: 'tripura-6', name: 'Tripura (Part IIA)' }, geometry: { type: 'Polygon', coordinates: [[[91.15, 23.9], [91.7, 24.4], [92.3, 24.2], [92.15, 23.7], [91.6, 22.95], [91.25, 23.15], [91.15, 23.9]]] } },
    { type: 'Feature', properties: { id: 'mizoram-6', name: 'Mizoram (Part III)' }, geometry: { type: 'Polygon', coordinates: [[[92.25, 24.2], [92.7, 24.4], [93.15, 24.05], [93.4, 23.3], [93.1, 22.3], [92.7, 21.95], [92.35, 22.7], [92.25, 24.2]]] } },
  ],
};

/** Where Panchayati Raj was launched — the other grassroots geography. */
const panchayatLaunch: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'nagaur', name: 'Nagaur, Rajasthan — Nehru launches Panchayati Raj, 2 Oct 1959' }, geometry: { type: 'Point', coordinates: [NAGAUR[1], NAGAUR[0]] } },
    { type: 'Feature', properties: { id: 'andhra-pr', name: 'Andhra Pradesh — second state to adopt Panchayati Raj (1959)' }, geometry: { type: 'Point', coordinates: [79.74, 15.91] } },
  ],
};

export const politySixthScheduleChapter: Chapter = {
  id: 'polity-sixth-schedule-local-govt',
  subject: 'polity',
  unit: 'Grassroots',
  tags: ['mizoram', 'assam', 'meghalaya', 'tripura', 'nagaland', 'northeast', 'lawngtlai', 'siaha', 'panchayat'],
  title: 'Sixth Schedule & Local Government',
  summary: 'Art 244(2) ADCs in Assam, Meghalaya, Tripura & Mizoram — plus the 73rd/74th Amendment panchayat and municipal system.',
  focus:
    'Two grassroots geographies: (1) Sixth Schedule ADCs (Parts I, II, IIA, III) in four NE states — max 30 members, 5-year term, Governor as executive head in Mizoram; (2) the 73rd/74th Amendments (1992) everywhere else. Nagaland, Meghalaya & Mizoram are exempt from Part IX.',
  view: { center: [24.6, 92.3], zoom: 6 },
  basemap: 'natgeo',
  theme: { accent: '#4a5fa5' },
  layers: [
    {
      id: 'sixth-states',
      name: 'Sixth Schedule states',
      description: 'Assam (I), Meghalaya (II), Tripura (IIA), Mizoram (III) — parts fixed by the NEAR Act 1971.',
      kind: 'vector',
      data: sixthStates,
      style: { color: '#4a5fa5', fillColor: '#4a5fa5', fillOpacity: 0.1, weight: 2, pattern: 'dots' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'adc-seats',
      name: 'ADC headquarters',
      description: 'Where each Autonomous District Council sits — Lai, Mara, Chakma; Khasi, Garo, Jaintia; Karbi Anglong, Dima Hasao, BTC; TTAADC.',
      kind: 'vector',
      data: adcSeats,
      style: { color: '#a5504a', markerRadius: 7, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'panchayat-launch',
      name: 'Panchayati Raj origins',
      description: 'Nagaur (2 Oct 1959) and Andhra Pradesh — the first adopters.',
      kind: 'vector',
      data: panchayatLaunch,
      style: { color: '#2e7d5b', markerRadius: 7 },
      defaultOn: false,
      labelKey: 'name',
    },
  ],
  facts: [
    { id: 'f1', text: 'The Sixth Schedule (Art 244(2) & 275(1)) governs tribal areas in Assam, Meghalaya, Tripura and Mizoram through Autonomous District Councils. The Fifth Schedule covers scheduled areas in the other states.', linkedLayerId: 'sixth-states' },
    { id: 'f2', text: 'Origin: the Bordoloi Sub-Committee (Gopinath Bordoloi, CM of Assam) of the Constituent Assembly recommended District & Regional Councils; Saprawnga and Khawtinkhuma were co-opted to represent the Mizos.' },
    { id: 'f3', text: 'Each ADC: up to 30 members (up to 4 nominated by the Governor, rest elected by adult suffrage), 5-year term (extendable 1 year); members must be citizens, 25+, registered voters.' },
    { id: 'f4', text: 'Lushai Hills District Council formed 1952 → renamed Mizo Hills District Council 1954. The NEAR Act 1971 split the Schedule into Parts I (Assam), II (Meghalaya), IIA (Tripura), III (Mizoram).' },
    { id: 'f5', text: 'Mizoram\u2019s three ADCs: Lai (Lawngtlai), Mara (Siaha), Chakma (Chawngte) — under the Mizoram ADC Rules 1974. The Governor is the executive head; DC laws need the Governor\u2019s assent.', linkedLayerId: 'adc-seats' },
    { id: 'f6', text: 'Each ADC has an Executive Committee: one elected Chief Executive Member + 2 Executive Members. ADCs hold legislative, executive, judicial (Village Courts) and financial powers.' },
    { id: 'f7', text: '73rd Amendment (1992): Panchayati Raj constitutionalised — Part IX + Eleventh Schedule (29 subjects). 74th Amendment: municipalities — Part IXA + Twelfth Schedule (18 subjects).' },
    { id: 'f8', text: 'Three-tier panchayats (village–intermediate–district); SC/ST reservation in proportion to population; one-third of seats for women; fixed 5-year term; State Election Commission conducts polls; State Finance Commission every 5 years.' },
    { id: 'f9', text: 'Balwant Rai Mehta Committee (1957) recommended democratic decentralisation; Rajasthan (Nagaur, 2 Oct 1959) launched Panchayati Raj first, Andhra Pradesh second.', linkedLayerId: 'panchayat-launch' },
    { id: 'f10', text: 'Part IX does NOT apply to Nagaland, Meghalaya and Mizoram, to Sixth Schedule areas, or (mostly) to J&K — their traditional/ADC institutions continue instead.' },
    { id: 'f11', text: 'Municipal types under the 74th: Nagar Panchayat (transitional), Municipal Council (smaller urban), Municipal Corporation (larger urban).' },
  ],
  events: [
    { id: 'e1', date: '1949', label: '1949 — Sixth Schedule adopted', description: 'Bordoloi Sub-Committee\u2019s scheme enters the Constitution as the Sixth Schedule.' },
    { id: 'e2', date: '1952', label: '1952 — Lushai Hills DC', description: 'The Lushai Hills District Council comes into being (renamed Mizo Hills DC, 1954).', view: { center: [23.4, 92.8], zoom: 7 } },
    { id: 'e3', date: '1959-10-02', label: '1959 — Panchayati Raj', description: 'Nehru inaugurates Panchayati Raj at Nagaur, Rajasthan, on Gandhi Jayanti; Andhra follows.', showLayers: ['panchayat-launch'], view: { center: [25.0, 76.0], zoom: 5 } },
    { id: 'e4', date: '1971', label: '1971 — NEAR Act', description: 'Sixth Schedule reorganised into Parts I, II, IIA and III as the North-East is redrawn.', showLayers: ['sixth-states'], view: { center: [24.6, 92.3], zoom: 6 } },
    { id: 'e5', date: '1972', label: '1972 — Mizo District ADCs', description: 'Pawi–Lakher Regional Council splits into Pawi (Lai), Lakher (Mara) and Chakma Regional Councils → ADCs under the 1974 Rules.', showLayers: ['adc-seats'], view: { center: [22.6, 92.8], zoom: 8 } },
    { id: 'e6', date: '1992', label: '1992 — 73rd & 74th', description: 'Panchayats (Part IX, 11th Schedule) and municipalities (Part IXA, 12th Schedule) get constitutional status.' },
  ],
  quiz: [
    {
      id: 'q1', type: 'mcq',
      question: 'The Sixth Schedule provides for the administration of tribal areas in which states?',
      options: ['All North-Eastern states', 'Assam, Meghalaya, Tripura, Mizoram', 'Assam, Nagaland, Manipur, Mizoram', 'Meghalaya, Nagaland, Sikkim, Tripura'],
      answerIndex: 1,
      explanation: 'A-M-T-M: Assam (Part I), Meghalaya (II), Tripura (IIA), Mizoram (III). Nagaland is protected by Art 371A, not the Sixth Schedule.',
    },
    {
      id: 'q2', type: 'mcq',
      question: 'The sub-committee that recommended District & Regional Councils for NE tribal areas was headed by:',
      options: ['B.N. Rau', 'Gopinath Bordoloi', 'Fazl Ali', 'Balwant Rai Mehta'],
      answerIndex: 1,
      explanation: 'Gopinath Bordoloi, then CM of Assam. Saprawnga and Khawtinkhuma represented the Mizos in its deliberations.',
    },
    {
      id: 'q3', type: 'map_click',
      question: 'Click the headquarters of the Mara Autonomous District Council.',
      answer: { lat: 22.4918, lng: 92.9793, toleranceKm: 60 },
      explanation: 'Siaha — Mara ADC. Lai sits at Lawngtlai and Chakma at Chawngte (Kamalanagar).',
    },
    {
      id: 'q4', type: 'mcq',
      question: 'An Autonomous District Council under the Sixth Schedule has a maximum of:',
      options: ['20 members', '26 members', '30 members', '40 members'],
      answerIndex: 2,
      explanation: 'Up to 30 members — a maximum of 4 nominated by the Governor, the rest directly elected; 5-year term.',
    },
    {
      id: 'q5', type: 'map_click',
      question: 'Click the place where Panchayati Raj was first inaugurated on 2 October 1959.',
      answer: { lat: NAGAUR[0], lng: NAGAUR[1], toleranceKm: 130 },
      explanation: 'Nagaur, Rajasthan — inaugurated by Nehru; Andhra Pradesh adopted it next.',
    },
    {
      id: 'q6', type: 'mcq',
      question: 'The Eleventh Schedule (73rd Amendment) lists how many subjects for panchayats?',
      options: ['18', '22', '29', '52'],
      answerIndex: 2,
      explanation: '29 subjects for panchayats; the Twelfth Schedule lists 18 for municipalities.',
    },
    {
      id: 'q7', type: 'mcq',
      question: 'Part IX (Panchayats) does NOT apply to which of these states?',
      options: ['Assam, Tripura, Manipur', 'Nagaland, Meghalaya, Mizoram', 'Sikkim, Goa, Mizoram', 'Nagaland, Assam, Arunachal'],
      answerIndex: 1,
      explanation: 'Nagaland, Meghalaya and Mizoram are exempt — traditional institutions and ADCs operate there instead.',
    },
  ],
};

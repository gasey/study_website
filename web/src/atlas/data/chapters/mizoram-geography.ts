import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// GEOGRAPHY OF MIZORAM (GS-V, Unit II)
//
// Concept:
//   "Mizoram\u2019s N\u2013S ridges sort every river into three families:
//   north to the Barak, south to the Kaladan, west to the
//   Karnaphuli. Know the ridge grain and the drainage answers
//   write themselves."
//
// Source: Geography.pptm (GS V; Unit II) deck.
// River/range positions are simplified for recognition.
// ============================================

/** Mountain ranges (named peaks/ridges as points for clarity). */
const ranges: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'phawngpui', name: 'Phawngpui Range (Lawngtlai) \u2014 Blue Mountain, 2157 m, highest' }, geometry: { type: 'Point', coordinates: [93.03, 22.63] } },
    { type: 'Feature', properties: { id: 'sialkal', name: 'Sialkal Range \u2014 NE Mizoram, Manipur/Myanmar border' }, geometry: { type: 'Point', coordinates: [93.25, 23.9] } },
    { type: 'Feature', properties: { id: 'chalfilh', name: 'Chalfilh Range (Aizawl District)' }, geometry: { type: 'Point', coordinates: [92.9, 23.85] } },
    { type: 'Feature', properties: { id: 'hmuifang', name: 'Hmuifang Range (Aizawl District)' }, geometry: { type: 'Point', coordinates: [92.75, 23.45] } },
    { type: 'Feature', properties: { id: 'reiek', name: 'Reiek Range (Mamit District)' }, geometry: { type: 'Point', coordinates: [92.6, 23.69] } },
  ],
};

/** Three river families \u2014 the chapter\u2019s core idea. */
const northRivers: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'tlawng', name: 'Tlawng \u2014 longest (185.5 km); Zopui Hill \u2192 north; Dhaleswari in Cachar' },
      geometry: {
        type: 'LineString',
        coordinates: [[92.7, 22.9], [92.65, 23.2], [92.6, 23.5], [92.55, 23.8], [92.53, 24.1], [92.5, 24.35]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tuirial', name: 'Tuirial (~117 km) \u2014 Chawilung Hills \u2192 Barak; partially navigable' },
      geometry: {
        type: 'LineString',
        coordinates: [[92.85, 23.55], [92.83, 23.9], [92.8, 24.2], [92.78, 24.45]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tuivawl', name: 'Tuivawl (~72 km) \u2014 from near Chhawrtui, northward' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.0, 23.6], [92.98, 23.9], [92.95, 24.2]],
      },
    },
  ],
};

const southRivers: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'chhimtuipui', name: 'Chhimtuipui (Kaladan) \u2014 largest by volume; Myanmar boundary' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.05, 23.0], [93.0, 22.7], [92.95, 22.4], [92.9, 22.15], [92.88, 21.95]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tiau', name: 'Tiau (~159 km) \u2014 natural boundary with Myanmar (east)' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.35, 23.9], [93.38, 23.6], [93.4, 23.3], [93.42, 23.0]],
      },
    },
  ],
};

const westRivers: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'khawthlangtuipui', name: 'Khawthlangtuipui (Karnaphuli) \u2014 Saithah, Mamit \u2192 Bangladesh near Tlabung (~128 km)' },
      geometry: {
        type: 'LineString',
        coordinates: [[92.5, 23.5], [92.47, 23.25], [92.44, 23.05], [92.42, 22.87]],
      },
    },
  ],
};

/** Lakes + plains. */
const lakesPlains: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'palak', name: 'Palak Dil \u2014 large lake (south)' }, geometry: { type: 'Point', coordinates: [92.9, 22.2] } },
    { type: 'Feature', properties: { id: 'tamdil', name: 'Tamdil \u2014 large lake (near Saitual)' }, geometry: { type: 'Point', coordinates: [92.95, 23.74] } },
    { type: 'Feature', properties: { id: 'rengdil', name: 'Rengdil \u2014 large lake (north)' }, geometry: { type: 'Point', coordinates: [92.55, 24.02] } },
    { type: 'Feature', properties: { id: 'champhai', name: 'Champhai Plain \u2014 largest; wet-rice cultivation' }, geometry: { type: 'Point', coordinates: [93.33, 23.47] } },
  ],
};

export const mizoramGeographyChapter: Chapter = {
  id: 'mizoram-geography',
  subject: 'geography',
  unit: 'Mizoram',
  tags: ['tlawng', 'kaladan', 'karnaphuli', 'mizo-hills', 'purvanchal', 'tropic-of-cancer'],
  title: 'Geography of Mizoram',
  summary: 'Ridges, three river families, lakes, geology & climate \u2014 GS-V Unit II.',
  focus:
    'Mizoram is 90%+ structural hills aligned north\u2013south. That grain sorts every river into three families \u2014 north to the Barak (Tlawng), south to the Kaladan (Chhimtuipui), west to the Karnaphuli (Khawthlangtuipui).',
  view: { center: [23.3, 92.85], zoom: 8 },
  basemap: 'opentopo',
  theme: { accent: '#1e6e5c', mapBg: '#eaf4f0' },

  layers: [
    {
      id: 'ranges',
      name: 'Mountain ranges',
      kind: 'vector',
      data: ranges,
      style: { color: '#6b4f2a', weight: 2, fillColor: '#8a683a', fillOpacity: 0.9, shadow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'north-rivers',
      name: 'North-flowing (\u2192 Barak)',
      kind: 'vector',
      data: northRivers,
      style: { color: '#1f5fa8', weight: 3 , flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'south-rivers',
      name: 'South-flowing (\u2192 Kaladan/Myanmar)',
      kind: 'vector',
      data: southRivers,
      style: { color: '#7a2ea0', weight: 3 , flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'west-rivers',
      name: 'West-flowing (\u2192 Bangladesh)',
      kind: 'vector',
      data: westRivers,
      style: { color: '#0e8a6a', weight: 3 , flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'lakes-plains',
      name: 'Lakes & plains',
      kind: 'vector',
      data: lakesPlains,
      style: { color: '#0d6efd', weight: 2, fillColor: '#3b8beb', fillOpacity: 0.9, shadow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Vitals: 21\u00b056\u2032\u201324\u00b031\u2032 N, 92\u00b016\u2032\u201393\u00b026\u2032 E; area 21,081 sq km (0.64% of India); the Tropic of Cancer crosses the state. Stretch: 277 km N\u2013S, 121 km E\u2013W. International borders: Myanmar 404 km, Bangladesh 318 km; national borders with Manipur, Assam, Tripura total 146.6 km.',
    },
    {
      id: 'f2',
      text: 'Terrain: 90.5% structural hills, 6.4% linear ridges, only 3.1% floodplains and valley fills. Altitude runs 400\u20132,157 m (average ~1,000 m); ridges are N\u2013S aligned and WESTERN slopes are steeper than eastern. Forest cover: 85.34% (ISFR 2023) \u2014 among India\u2019s highest.',
      linkedLayerId: 'ranges',
    },
    {
      id: 'f3',
      text: 'Ranges to name: Sialkal (NE, on the Manipur\u2013Myanmar border), Chalfilh and Hmuifang (Aizawl district), Reiek (Mamit), and Phawngpui (Lawngtlai) \u2014 the Blue Mountain, 2,157 m, the state\u2019s highest point.',
      linkedLayerId: 'ranges',
      linkedFeatureId: 'phawngpui',
    },
    {
      id: 'f4',
      text: 'North-flowing family (\u2192 Barak system): TLAWNG is the longest at 185.5 km \u2014 rises at Zopui Hill (Lunglei), splits the state into two nearly equal halves, and is called the Dhaleswari in Cachar (Assam). Tributaries include Tut and Teirei. Tuirial (~117 km, partially navigable) and Tuivawl (~72 km) also flow north.',
      linkedLayerId: 'north-rivers',
    },
    {
      id: 'f5',
      text: 'South-flowing family: CHHIMTUIPUI (Kaladan) is the largest river by water volume \u2014 it rises in western Myanmar near Sabawngte, flows ~138 km, and forms the international boundary with Myanmar. Dendritic pattern; tributaries Tuichang, Tuichawng, Mat, Mengpui. TIAU (~159 km) is the natural boundary with Myanmar in the east.',
      linkedLayerId: 'south-rivers',
    },
    {
      id: 'f6',
      text: 'West-flowing family: KHAWTHLANGTUIPUI (Karnaphuli) drains the southwest \u2014 rises at Saithah (Mamit), runs ~128 km, enters Bangladesh near Tlabung, and forms the natural boundary with Bangladesh. Tributaries: Kawrpui, Tuichawng, Phairuang, Kau, De. Strategic trade route to Chittagong.',
      linkedLayerId: 'west-rivers',
    },
    {
      id: 'f7',
      text: 'Lakes formed where hills and ridges act as embankments \u2014 large: Palak, Tamdil, Rengdil; smaller: Rungdil, Vachadil. Plains are only ~3% and inter-montane: Champhai (largest \u2014 wet rice), Serchhip plains, the Northern plains, and Chamdur (western Siaha).',
      linkedLayerId: 'lakes-plains',
    },
    {
      id: 'f8',
      text: 'Geology: longitudinal anticlines and synclines control drainage and slopes; BIS (2016) puts Mizoram in SEISMIC ZONE V; the Indo-Myanmar tectonic arc passes through Siaha district. Tertiary sandstones and shales; marine fossils near Lunglei. Stratigraphy (ascending): Barail \u2192 Surma (Bhuban + Bokabil \u2014 Bokabil holds petroleum) \u2192 Tipam (youngest, coarse sandstone).',
    },
    {
      id: 'f9',
      text: 'Climate & vegetation: tropical to temperate-montane; 10\u201330 \u00b0C (avg 22 \u00b0C); ~2,394 mm rain a year, ~40% of it in July\u2013August; three seasons, the rainy one running nearly six months (mid-May to late Oct). Forests: Tropical Wet-Evergreen (west), Tropical Semi-Evergreen (~50% of area, central belt), Mountain Sub-Tropical on the high eastern fringe. Minerals: sandstone widespread, limestone in patches, coal at Kolasib/Thinglian, petroleum confirmed at Bilkhawthlir, uranium potential in Middle Bhuban sandstones (~4 ppm).',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Which is the LONGEST river of Mizoram, and what is it called in Assam\u2019s Cachar district?',
      options: [
        'Chhimtuipui \u2014 Kaladan',
        'Tlawng \u2014 Dhaleswari',
        'Tiau \u2014 Karnaphuli',
        'Tuirial \u2014 Barak',
      ],
      answerIndex: 1,
      explanation: 'Tlawng (185.5 km) rises at Zopui Hill, Lunglei, flows north dividing the state into two nearly equal parts, and becomes the Dhaleswari in Cachar. Chhimtuipui is the largest by VOLUME \u2014 a different superlative.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click Phawngpui \u2014 the Blue Mountain, Mizoram\u2019s highest point (2,157 m).',
      answer: { lat: 22.63, lng: 93.03, toleranceKm: 60 },
      explanation: 'Phawngpui rises in Lawngtlai district in the southeast, near the Myanmar border \u2014 matching the state\u2019s altitude ceiling of 2,157 m.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Match river \u2192 boundary: which pair is CORRECT?',
      options: [
        'Tiau \u2192 Bangladesh; Khawthlangtuipui \u2192 Myanmar',
        'Tiau & Chhimtuipui \u2192 Myanmar (east/southeast); Khawthlangtuipui \u2192 Bangladesh (west)',
        'Tlawng \u2192 Myanmar; Tuirial \u2192 Bangladesh',
        'Chhimtuipui \u2192 Tripura; Tiau \u2192 Assam',
      ],
      answerIndex: 1,
      explanation: 'Tiau and Chhimtuipui form the natural boundaries with Myanmar in the east and southeast; western rivers, led by the Khawthlangtuipui (Karnaphuli), form parts of the Bangladesh boundary.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Under BIS (2016), Mizoram falls in seismic zone:',
      options: ['Zone II', 'Zone III', 'Zone IV', 'Zone V'],
      answerIndex: 3,
      explanation: 'Zone V \u2014 the highest hazard. The Indo-Myanmar tectonic arc passes through Siaha district, giving frequent tectonic disturbance; the hills are Tertiary sandstone and shale, prone to landslides.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click the Champhai plain \u2014 the largest plain, known for wet-rice cultivation.',
      answer: { lat: 23.47, lng: 93.33, toleranceKm: 60 },
      explanation: 'Champhai sits against the Myanmar border in the east. Plains are just ~3% of Mizoram and inter-montane \u2014 Champhai, Serchhip, the Northern plains, and Chamdur.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Which stratigraphic group of Mizoram is the YOUNGEST, and which formation holds petroleum reserves?',
      options: [
        'Barail youngest; Bhuban has petroleum',
        'Surma youngest; Barail has petroleum',
        'Tipam youngest; Bokabil (Surma group) has petroleum',
        'Bhuban youngest; Tipam has petroleum',
      ],
      answerIndex: 2,
      explanation: 'Ascending order: Barail \u2192 Surma \u2192 Tipam (youngest, coarse sandstone with pebbles). Within the Surma group, the Bokabil formation is known for petroleum/hydrocarbons \u2014 confirmed presence at Bilkhawthlir.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'Mizoram\u2019s three large lakes are:',
      options: [
        'Palak, Tamdil, Rengdil',
        'Rungdil, Vachadil, Tamdil',
        'Palak, Loktak, Umiam',
        'Tamdil, Rihdil, Rungdil',
      ],
      answerIndex: 0,
      explanation: 'Palak, Tamdil and Rengdil are the large lakes; Rungdil and Vachadil are smaller. They formed where hills and ridges served as natural embankments. (Loktak is Manipur; Umiam is Meghalaya.)',
    },
    {
      id: 'q8',
      type: 'map_click',
      question: 'Click roughly where the Khawthlangtuipui (Karnaphuli) leaves Mizoram for Bangladesh \u2014 near Tlabung.',
      answer: { lat: 22.87, lng: 92.42, toleranceKm: 60 },
      explanation: 'The Karnaphuli exits near Tlabung in the southwest after ~128 km from its source at Saithah (Mamit) \u2014 the state\u2019s strategic water route toward Chittagong.',
    },
    {
      id: 'q9',
      type: 'mcq',
      question: 'Which statement about Mizoram\u2019s relief is TRUE?',
      options: [
        'Eastern slopes are steeper than western slopes',
        'Plains cover about 30% of the state',
        'Western slopes are steeper; hills are N\u2013S aligned; plains are only ~3%',
        'The ridges run east\u2013west like the Himalayas',
      ],
      answerIndex: 2,
      explanation: '90.5% structural hills in N\u2013S grain, western slopes steeper than eastern, floodplains/valley fills a mere 3.1%. This ridge grain is exactly why the rivers sort into north/south/west families.',
    },
  ],
};

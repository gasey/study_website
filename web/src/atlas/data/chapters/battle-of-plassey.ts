import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// BATTLE OF PLASSEY — June 23, 1757
//
// Authored concept:
//   "Plassey was a small skirmish that decided two centuries
//   of Indian history — and it was decided by geography,
//   weather, and betrayal, not by numerical strength."
//
// Everything in this file serves that sentence.
// ============================================

const PLASSEY: [number, number] = [23.795, 88.255]; // Palashi village
const MURSHIDABAD: [number, number] = [24.187, 88.272];
const CALCUTTA: [number, number] = [22.5726, 88.3639];
const CHANDERNAGORE: [number, number] = [22.866, 88.355];

/** Bengal under Siraj-ud-Daulah — a *very* simplified extent.
 *  Real boundary is a 25-coordinate polygon; we're after recognition. */
const bengalTerritory: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'bengal-1757', name: 'Bengal Subah (under Siraj-ud-Daulah)' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [85.0, 26.5], [88.5, 27.0], [92.2, 26.0], [92.5, 24.0],
          [91.0, 22.0], [88.5, 21.5], [86.5, 22.0], [85.5, 24.0], [85.0, 26.5],
        ]],
      },
    },
  ],
};

/** European trading posts on the Bhagirathi-Hooghly. */
const tradingPosts: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'calcutta', name: 'Calcutta (British — Fort William)', power: 'british' },
      geometry: { type: 'Point', coordinates: [CALCUTTA[1], CALCUTTA[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'chandernagore', name: 'Chandernagore (French)', power: 'french' },
      geometry: { type: 'Point', coordinates: [CHANDERNAGORE[1], CHANDERNAGORE[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'chinsurah', name: 'Chinsurah (Dutch)', power: 'dutch' },
      geometry: { type: 'Point', coordinates: [88.39, 22.90] },
    },
    {
      type: 'Feature',
      properties: { id: 'serampore', name: 'Serampore (Danish)', power: 'danish' },
      geometry: { type: 'Point', coordinates: [88.35, 22.75] },
    },
  ],
};

/** Capitals & key locations. */
const keyLocations: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'murshidabad', name: 'Murshidabad (Nawab\u2019s capital)' },
      geometry: { type: 'Point', coordinates: [MURSHIDABAD[1], MURSHIDABAD[0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'plassey', name: 'Plassey (Palashi)' },
      geometry: { type: 'Point', coordinates: [PLASSEY[1], PLASSEY[0]] },
    },
  ],
};

/** Clive's march from Calcutta to Plassey. ~150 km along the river. */
const cliveMarch: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'clive-march', name: 'Clive\u2019s march, June 13\u201322, 1757' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [CALCUTTA[1], CALCUTTA[0]],
          [88.36, 22.90],
          [88.35, 23.10],
          [88.30, 23.35],
          [88.27, 23.60],
          [PLASSEY[1], PLASSEY[0]],
        ],
      },
    },
  ],
};

/** Troop positions on the morning of June 23, 1757.
 *  Heavily simplified — the real battlefield was ~1 km wide. */
const battlefield: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'british-position', name: 'British line (Clive, 3,000)', side: 'british' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [88.250, 23.800], [88.258, 23.802], [88.258, 23.798],
          [88.250, 23.796], [88.250, 23.800],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'nawab-position', name: 'Nawab\u2019s army (Siraj-ud-Daulah, 50,000)', side: 'nawab' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [88.255, 23.815], [88.275, 23.815], [88.275, 23.805],
          [88.255, 23.805], [88.255, 23.815],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'mir-jafar', name: 'Mir Jafar\u2019s cavalry (the betrayer — refused to fight)', side: 'mir-jafar' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [88.265, 23.810], [88.280, 23.810], [88.280, 23.802],
          [88.265, 23.802], [88.265, 23.810],
        ]],
      },
    },
  ],
};

/** Aftermath — by 1765 the EIC held the Diwani of Bengal, Bihar, Orissa. */
const aftermath1765: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'eic-1765', name: 'East India Company control by 1765 (Diwani)' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [83.5, 26.0], [88.5, 27.0], [92.5, 26.0], [92.5, 24.0],
          [91.0, 21.5], [86.5, 21.5], [83.0, 22.0], [83.5, 26.0],
        ]],
      },
    },
  ],
};

export const plasseyChapter: Chapter = {
  id: 'battle-of-plassey',
  subject: 'history',
  unit: 'Modern',
  tags: ['bengal', 'calcutta', 'hooghly', 'ganga', 'murshidabad', 'carnatic'],
  title: 'Battle of Plassey, 1757',
  summary: 'How one afternoon on a Bengal riverbank changed who ruled India for two centuries.',
  focus:
    'Plassey was a small skirmish that decided two centuries of Indian history — and it was decided by geography, weather, and betrayal, not by numerical strength.',

  view: { center: [23.5, 88.0], zoom: 7 },
  basemap: 'natgeo',

  theme: {
    accent: '#7a4a2a',
    mapBg: '#f0e6d2',
  },

  layers: [
    {
      id: 'bengal-territory',
      name: 'Bengal Subah, 1757',
      description: 'The Nawab\u2019s domain \u2014 wealthiest province of the dying Mughal Empire.',
      kind: 'vector',
      data: bengalTerritory,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#7a4a2a', fillColor: '#c4a06a', fillOpacity: 0.35, weight: 2, pattern: 'hatch' , flow: true },
    },
    {
      id: 'trading-posts',
      name: 'European Trading Posts',
      description: 'Why Europeans were in Bengal in the first place.',
      kind: 'vector',
      data: tradingPosts,
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'key-locations',
      name: 'Murshidabad & Plassey',
      description: 'The Nawab\u2019s capital and the village where it all ended.',
      kind: 'vector',
      data: keyLocations,
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'clive-march',
      name: 'Clive\u2019s March',
      description: '150 km up the Bhagirathi, June 13\u201322, 1757.',
      kind: 'vector',
      data: cliveMarch,
      defaultOn: true,
      style: { color: '#1d4f7a', weight: 3, dashArray: '6 5' },
    },
    {
      id: 'battlefield',
      name: 'Troop Positions, dawn June 23',
      description: 'British 3,000 vs Nawab 50,000 \u2014 but a third of the Nawab\u2019s force was Mir Jafar\u2019s, secretly bribed.',
      kind: 'vector',
      data: battlefield,
      defaultOn: false,
      labelKey: 'name',
      style: { weight: 2.5, fillOpacity: 0.6, shadow: true },
    },
    {
      id: 'aftermath',
      name: 'EIC Territory by 1765',
      description: 'Eight years later: the Diwani of Bengal, Bihar, and Orissa.',
      kind: 'vector',
      data: aftermath1765,
      defaultOn: false,
      labelKey: 'name',
      style: { color: '#7a3a3a', fillColor: '#a05a3a', fillOpacity: 0.4, weight: 2.5, pattern: 'cross' },
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'By 1757 the Mughal Empire was collapsing. Bengal was its wealthiest province, governed by a semi-independent Nawab.',
      linkedLayerId: 'bengal-territory',
    },
    {
      id: 'f2',
      text: 'The East India Company\u2019s Fort William at Calcutta had become rich on Bengal trade — and had been fortifying without the Nawab\u2019s permission.',
      linkedLayerId: 'trading-posts',
      linkedFeatureId: 'calcutta',
    },
    {
      id: 'f3',
      text: 'In June 1756 the young Nawab Siraj-ud-Daulah seized Calcutta. Surviving prisoners died in a packed cell — the "Black Hole" incident gave the British their pretext.',
    },
    {
      id: 'f4',
      text: 'Robert Clive sailed from Madras, retook Calcutta, captured the French post of Chandernagore, then marched north with about 3,000 men.',
      linkedLayerId: 'clive-march',
    },
    {
      id: 'f5',
      text: 'The Nawab\u2019s army was around 50,000 strong with 50 French-officered cannons. The British were outnumbered roughly 17 to 1.',
      linkedLayerId: 'battlefield',
    },
    {
      id: 'f6',
      text: 'But Clive had bribed Mir Jafar, the Nawab\u2019s commander, with the throne. A third of Bengal\u2019s army would not fight.',
      linkedLayerId: 'battlefield',
      linkedFeatureId: 'mir-jafar',
    },
    {
      id: 'f7',
      text: 'During the battle a sudden monsoon downpour soaked the Nawab\u2019s gunpowder. The British had covered theirs with tarpaulins. The artillery duel was decided by weather.',
    },
    {
      id: 'f8',
      text: 'Within three hours the Nawab\u2019s army broke. Mir Jafar was installed as the puppet Nawab.',
    },
    {
      id: 'f9',
      text: 'By 1765 the Company held the Diwani — the right to collect revenue — of Bengal, Bihar, and Orissa. Merchants had become rulers.',
      linkedLayerId: 'aftermath',
    },
  ],

  events: [
    {
      id: 'e1',
      date: '1756-06-20',
      label: 'Calcutta falls',
      description: 'Siraj-ud-Daulah captures Fort William. The "Black Hole" incident follows.',
      showLayers: ['bengal-territory', 'trading-posts'],
      hideLayers: ['clive-march', 'battlefield', 'aftermath'],
      view: { center: [22.7, 88.4], zoom: 8 },
    },
    {
      id: 'e2',
      date: '1757-01-02',
      label: 'Clive retakes Calcutta',
      description: 'Clive\u2019s expedition from Madras recaptures the city.',
      showLayers: ['bengal-territory', 'trading-posts'],
      hideLayers: ['battlefield', 'aftermath'],
      view: { center: [22.7, 88.4], zoom: 8 },
    },
    {
      id: 'e3',
      date: '1757-03-23',
      label: 'Chandernagore taken',
      description: 'The British seize the French outpost — eliminating European competition in Bengal.',
      showLayers: ['trading-posts'],
      hideLayers: ['battlefield', 'aftermath'],
      view: { center: [22.9, 88.35], zoom: 9 },
    },
    {
      id: 'e4',
      date: '1757-06-13',
      label: 'March begins',
      description: 'Clive sets out from Calcutta with 3,000 men, heading for Murshidabad.',
      showLayers: ['bengal-territory', 'clive-march', 'key-locations'],
      hideLayers: ['battlefield', 'aftermath'],
      view: { center: [23.2, 88.3], zoom: 8 },
    },
    {
      id: 'e5',
      date: '1757-06-23',
      label: 'Battle of Plassey',
      description: 'Three hours of fighting. A monsoon downpour, a soaked enemy artillery, and a commander who would not charge. The Nawab flees and is killed days later.',
      showLayers: ['battlefield', 'clive-march', 'key-locations'],
      hideLayers: ['aftermath'],
      view: { center: PLASSEY, zoom: 11 },
    },
    {
      id: 'e6',
      date: '1765-08-12',
      label: 'Diwani granted',
      description: 'The Mughal emperor formally grants the Company the right to collect revenue in Bengal, Bihar, and Orissa. The transformation is complete.',
      showLayers: ['aftermath'],
      hideLayers: ['battlefield', 'clive-march'],
      view: { center: [24.0, 86.0], zoom: 6 },
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'map_click',
      question: 'Click the river along which the Battle of Plassey was fought.',
      answer: { lat: 23.795, lng: 88.255, toleranceKm: 80 },
      explanation: 'The Bhagirathi-Hooghly — a distributary of the Ganges. The battle was on its east bank near Palashi village. The river was the highway of trade, of armies, and of empires.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Despite being outnumbered roughly 17 to 1, the British won at Plassey primarily because:',
      options: [
        'Their muskets had longer range',
        'Mir Jafar, commanding much of the Nawab\u2019s army, had been bribed and refused to fight, and a sudden downpour soaked the Nawab\u2019s gunpowder',
        'They had more artillery',
        'The Mughal emperor sent reinforcements',
      ],
      answerIndex: 1,
      explanation: 'Plassey was decided by betrayal and weather, not numerical or technical superiority. Mir Jafar held back a third of the Nawab\u2019s force; the monsoon ruined the rest of the artillery. This is the single most important fact about the battle.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click the capital of Bengal in 1757 — the city Clive was marching toward.',
      answer: { lat: 24.187, lng: 88.272, toleranceKm: 60 },
      explanation: 'Murshidabad. Named after Murshid Quli Khan, the first Nawab. After Plassey it remained nominally the capital, but real power moved south to Calcutta.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'What did the British gain from the Mughal emperor in 1765, formalizing Plassey\u2019s real consequence?',
      options: [
        'The right to mint coins',
        'A monopoly on Indian Ocean trade',
        'The Diwani of Bengal, Bihar, and Orissa — the right to collect revenue',
        'Direct sovereignty over India',
      ],
      answerIndex: 2,
      explanation: 'The Diwani grant of 1765 turned the East India Company from a trading enterprise into the de facto government of India\u2019s richest provinces. Sovereignty technically remained Mughal; tax revenue went to the Company. This was Plassey\u2019s true meaning.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click the French trading post Clive captured before marching to Plassey.',
      answer: { lat: 22.866, lng: 88.355, toleranceKm: 30 },
      explanation: 'Chandernagore (Chandannagar). Taken in March 1757, just months before Plassey. Removing the French was essential — Siraj-ud-Daulah had been counting on French support that never came.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Which treaty, signed in February 1757 after Clive arrived from Madras, saw Siraj concede British demands months before Plassey?',
      options: [
        'Treaty of Allahabad',
        'Treaty of Alinagar',
        'Treaty of Salbai',
        'Treaty of Srirangapatna',
      ],
      answerIndex: 1,
      explanation: 'The Treaty of Alinagar (Feb 1757) — signed after Siraj had seized the Kasim Bazar factory and taken Fort William (20 June 1756, followed by the Black Hole incident). It bought time, not peace: Plassey came four months later.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'Who among these did NOT betray Siraj-ud-Daulah at Plassey?',
      options: [
        'Mir Jafar (Mir Bakshi)',
        'Jagat Seth (biggest banker of Bengal)',
        'Manik Chand (officer-in-charge of Calcutta)',
        'Mir Qasim',
      ],
      answerIndex: 3,
      explanation: 'The conspirators were Mir Jafar, Manik Chand, Amichand, Jagat Seth and Khadim Khan. Mir Qasim enters the story LATER — as Mir Jafar\u2019s son-in-law and successor, whose revolt led to Buxar (1764). Siraj was killed by Mir Jafar\u2019s son Miran.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'The Battle of Buxar (22 Oct 1764) was fought by the British against the combined forces of:',
      options: [
        'Mir Jafar, Siraj-ud-Daulah and the French',
        'Mir Qasim, Shuja-ud-Daula (Awadh) and Shah Alam II (Mughal emperor)',
        'The Marathas and the Nizam',
        'Haidar Ali and Tipu Sultan',
      ],
      answerIndex: 1,
      explanation: 'Mir Qasim — deposed for abolishing dastak abuse and duties — allied with Shuja-ud-Daula of Awadh and emperor Shah Alam II. Their defeat at Buxar mattered MORE than Plassey militarily, and produced the Treaty of Allahabad (Aug 1765) granting the Diwani.',
    },
    {
      id: 'q9',
      type: 'mcq',
      question: 'Under Clive\u2019s Dual Government of Bengal (1765\u20131772):',
      options: [
        'The Company held Nizamat, the Nawab held Diwani',
        'The Company collected revenue (Diwani) while the Nawab kept civil administration (Nizamat); Warren Hastings ended it in 1772',
        'The Mughal emperor administered Bengal directly',
        'Bengal was split between Britain and France',
      ],
      answerIndex: 1,
      explanation: 'Diwani (revenue) to the Company, Nizamat (administration) to the Nawab — power without responsibility, responsibility without power. Warren Hastings abolished the system in 1772 and the Company took direct charge.',
    },
  ],
};

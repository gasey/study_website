import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// BUDDHISM & JAINISM \u2014 THE SHRAMANA CIRCUIT
//
// Concept:
//   "Buddha's biography is eight pins on one small map \u2014 born
//   Lumbini, enlightened Bodh Gaya, first sermon Sarnath, died
//   Kushinagar \u2014 and all four Buddhist councils sit on the same
//   Magadha\u2013Vaishali circuit."
//
// Source: ANCIENT INDIAN HISTORY \u2014 Prelims (MS Academy) deck.
// ============================================

const buddhaSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'lumbini', name: 'Lumbini (Nepal) \u2014 BORN 563 BC, Shakya clan of Kapilavastu' }, geometry: { type: 'Point', coordinates: [83.28, 27.47] } },
    { type: 'Feature', properties: { id: 'bodhgaya', name: 'Bodh Gaya \u2014 ENLIGHTENMENT at 35, under a pipal tree on the Phalgu' }, geometry: { type: 'Point', coordinates: [84.99, 24.7] } },
    { type: 'Feature', properties: { id: 'sarnath', name: 'Sarnath (near Varanasi) \u2014 FIRST SERMON: Dharma-chakra-pravartana' }, geometry: { type: 'Point', coordinates: [83.02, 25.38] } },
    { type: 'Feature', properties: { id: 'kushinagar', name: 'Kushinagar (UP) \u2014 DIED 483 BC at 80, under a sal tree (Mahaparinirvana)' }, geometry: { type: 'Point', coordinates: [83.89, 26.74] } },
    { type: 'Feature', properties: { id: 'shravasti-b', name: 'Shravasti \u2014 most rainy-season retreats (Jetavana)' }, geometry: { type: 'Point', coordinates: [82.03, 27.52] } },
    { type: 'Feature', properties: { id: 'rajgir-b', name: 'Rajgir \u2014 Griddhakuta hill sermons; 1st Council 483 BC' }, geometry: { type: 'Point', coordinates: [85.42, 25.03] } },
  ],
};

const councils: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'c1', name: '1st Council, 483 BC \u2014 Rajgir, under Ajatashatru (Haryanka)' }, geometry: { type: 'Point', coordinates: [85.42, 25.03] } },
    { type: 'Feature', properties: { id: 'c2', name: '2nd Council, 383 BC \u2014 Vaishali, under Kalashoka (Shishunaga); president Sabakami' }, geometry: { type: 'Point', coordinates: [85.13, 25.99] } },
    { type: 'Feature', properties: { id: 'c3', name: '3rd Council, 250 BC \u2014 Pataliputra, under Ashoka (Maurya)' }, geometry: { type: 'Point', coordinates: [85.14, 25.61] } },
    { type: 'Feature', properties: { id: 'c4', name: '4th Council, AD 72 \u2014 Kashmir, under Kanishka (Kushan); Mahayana finalized' }, geometry: { type: 'Point', coordinates: [74.8, 34.1] } },
  ],
};

const jainSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'kundagrama', name: 'Kundagrama, near Vaishali \u2014 Mahavira\u2019s birthplace (540 BC)' }, geometry: { type: 'Point', coordinates: [85.13, 26.02] } },
    { type: 'Feature', properties: { id: 'pava', name: 'Pava / Pavapuri \u2014 first sermon; Mahavira died here (468 BC)' }, geometry: { type: 'Point', coordinates: [85.55, 25.09] } },
    { type: 'Feature', properties: { id: 'parasnath', name: 'Parasnath Hill (Sammed Shikhar) \u2014 20 tirthankaras attained moksha' }, geometry: { type: 'Point', coordinates: [86.13, 23.96] } },
    { type: 'Feature', properties: { id: 'shravanabelagola', name: 'Shravanabelagola (Karnataka) \u2014 Chandragupta Maurya\u2019s last days; Bahubali' }, geometry: { type: 'Point', coordinates: [76.49, 12.86] } },
  ],
};

export const buddhismJainismChapter: Chapter = {
  id: 'buddhism-jainism',
  subject: 'history',
  unit: 'Ancient',
  tags: ['magadha', 'rajgir', 'pataliputra', 'vaishali', 'varanasi', 'bihar', 'ganga'],
  title: 'Buddhism & Jainism',
  summary: 'Buddha\u2019s life-map, the four councils, Mahavira and the Jain sites.',
  focus:
    'Buddha\u2019s biography is eight pins on one small map \u2014 and every Buddhist council sits on the Magadha\u2013Vaishali circuit you already know from the Mahajanapadas chapter. Same geography, new religion.',
  view: { center: [25.8, 84.0], zoom: 6 },
  basemap: 'natgeo',
  theme: { accent: '#8f4f9f', mapBg: '#f5eff7' },

  layers: [
    {
      id: 'buddha-sites',
      name: 'Buddha\u2019s life sites',
      description: 'Born \u2192 enlightened \u2192 first sermon \u2192 died.',
      kind: 'vector',
      data: buddhaSites,
      style: { color: '#8f4f9f', weight: 2, fillColor: '#8f4f9f', markerRadius: 7, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'councils',
      name: 'Four Buddhist councils',
      kind: 'vector',
      data: councils,
      style: { color: '#b0632c', weight: 2, fillColor: '#b0632c', markerRadius: 6 },
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'jain-sites',
      name: 'Jain sites',
      kind: 'vector',
      data: jainSites,
      style: { color: '#2e7d5b', weight: 2, fillColor: '#2e7d5b', markerRadius: 6 },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Gautama Buddha \u2014 also Siddhartha, Shakyamuni, Tathagata \u2014 born 563 BC at LUMBINI (Nepal) in the Shakya Kshatriya clan of Kapilavastu. Father Suddhodhana, mother Mahamaya (a Koshalan princess); raised by his aunt Mahaprajapati Gautami; wife Yashodhara, son Rahul; teachers Alara Kalama and Udraka Ramaputra; horse Kanthaka.',
      linkedLayerId: 'buddha-sites',
      linkedFeatureId: 'lumbini',
    },
    {
      id: 'f2',
      text: 'The four sights (old man, sick man, corpse, ascetic) drove him out at 29. Enlightenment at 35 at BODH GAYA, under a pipal tree on the banks of the Phalgu, on the 49th day of meditation. First sermon at SARNATH near Varanasi to five disciples \u2014 the Dharma-chakra-pravartana, \u201cturning the wheel of law\u201d. Died 483 BC at 80 at KUSHINAGAR (UP) under a sal tree.',
      linkedLayerId: 'buddha-sites',
    },
    {
      id: 'f3',
      text: 'Core doctrine: Buddhism recognizes neither God nor soul (atma). FOUR NOBLE TRUTHS: the world is full of sorrow; desire causes it; conquering desire removes it (nirvana); the way is the EIGHTFOLD PATH (Ashtangika Marga: right observation, speech, determination, livelihood, memory, action, exercise, meditation). TRIRATNA: Buddha, Dhamma, Sangha.',
    },
    {
      id: 'f4',
      text: 'Four councils \u2014 memorize ruler + dynasty + place: 483 BC Rajgir (Ajatashatru, Haryanka); 383 BC Vaishali (Kalashoka, Shishunaga; president Sabakami); 250 BC Pataliputra (Ashoka, Maurya); AD 72 Kashmir (Kanishka, Kushan) \u2014 where the MAHAYANA doctrine was finalized. Literature: the Tripitakas, in PALI.',
      linkedLayerId: 'councils',
    },
    {
      id: 'f5',
      text: 'Jainism: founded by Rishabhanath (1st tirthankara); 23rd Parshvanath; 24th VARDHAMANA MAHAVIRA \u2014 \u201cJina\u201d, the conqueror \u2014 born near Vaishali (Kundagrama), father Siddhartha, mother Trishala; attained Kaivalya (supreme knowledge) at 42; first sermon at PAVA, where he also died (468 BC).',
      linkedLayerId: 'jain-sites',
    },
    {
      id: 'f6',
      text: 'Jain doctrine: Triratna = right faith, right knowledge, right conduct. FIVE VOWS: ahimsa, satya (non-lying), asteya (non-stealing), aparigraha (non-possession), brahmacharya \u2014 the fifth added by Mahavira to Parshvanath\u2019s four. Sects after the Magadha famine: SVETAMBARA (white-clad, Sthulabhadra) and DIGAMBARA (sky-clad, Bhadrabahu \u2014 who took Chandragupta Maurya south to Shravanabelagola).',
      linkedLayerId: 'jain-sites',
    },
    {
      id: 'f7',
      text: 'Why here, why now? Both faiths rose in the 6th-century-BC Mahajanapada world \u2014 iron-age surplus, new cities, trade wealth, and Kshatriya resentment of Brahmana ritual cost. Both founders were Kshatriyas from the same Magadha\u2013Vaishali region \u2014 the identical geography of the Rise-of-Magadha chapter.',
    },
  ],

  events: [
    { id: 'e1', date: '-0563', label: 'Buddha born', description: 'Lumbini, in the Shakya clan of Kapilavastu.', showLayers: ['buddha-sites'], view: { center: [27.47, 83.28], zoom: 7 } },
    { id: 'e2', date: '-0540', label: 'Mahavira born', description: 'Kundagrama near Vaishali \u2014 the Jain 24th tirthankara.', showLayers: ['jain-sites'], view: { center: [26.02, 85.13], zoom: 7 } },
    { id: 'e3', date: '-0528', label: 'Enlightenment', description: 'Bodh Gaya, under the pipal tree by the Phalgu; then the first sermon at Sarnath.', showLayers: ['buddha-sites'], view: { center: [25.0, 84.0], zoom: 7 } },
    { id: 'e4', date: '-0483', label: 'Mahaparinirvana', description: 'Buddha dies at Kushinagar; the First Council meets the same year at Rajgir under Ajatashatru.', showLayers: ['buddha-sites', 'councils'], view: { center: [25.8, 84.5], zoom: 6 } },
    { id: 'e5', date: '0072', label: '4th Council', description: 'Kanishka\u2019s council in Kashmir finalizes Mahayana Buddhism \u2014 the faith now travels the Silk Road.', showLayers: ['councils'], view: { center: [34.1, 74.8], zoom: 6 } },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'map_click',
      question: 'Click Sarnath \u2014 where Buddha preached the first sermon (Dharma-chakra-pravartana).',
      answer: { lat: 25.38, lng: 83.02, toleranceKm: 80 },
      explanation: 'Sarnath, just outside Varanasi. Birth Lumbini \u2192 enlightenment Bodh Gaya \u2192 first sermon Sarnath \u2192 death Kushinagar: the four-pin biography.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Match the Buddhist council to its patron \u2014 which pair is WRONG?',
      options: [
        '1st, Rajgir \u2014 Ajatashatru',
        '2nd, Vaishali \u2014 Kalashoka',
        '3rd, Pataliputra \u2014 Kanishka',
        '4th, Kashmir \u2014 Kanishka',
      ],
      answerIndex: 2,
      explanation: 'The 3rd council (250 BC, Pataliputra) was under ASHOKA. Kanishka patronized the 4th (AD 72, Kashmir), where Mahayana doctrine was finalized.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Buddha attained enlightenment on the banks of which river?',
      options: ['Ganga', 'Phalgu', 'Son', 'Gandak'],
      answerIndex: 1,
      explanation: 'The Phalgu at Bodh Gaya, under a pipal tree, on the 49th day of meditation, aged 35.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'The fifth vow (brahmacharya) was added to Jainism\u2019s four by:',
      options: ['Rishabhanath', 'Parshvanath', 'Mahavira', 'Bhadrabahu'],
      answerIndex: 2,
      explanation: 'Parshvanath (23rd tirthankara) taught four vows; Mahavira added celibacy as the fifth. Triratna of Jainism: right faith, knowledge, conduct.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click Pavapuri \u2014 where Mahavira preached his first sermon and died.',
      answer: { lat: 25.09, lng: 85.55, toleranceKm: 90 },
      explanation: 'Pava/Pavapuri in Bihar, close to Rajgir. Mahavira died here in 468 BC \u2014 the Jain and Buddhist geographies almost perfectly overlap.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'The Svetambara and Digambara sects of Jainism are associated respectively with:',
      options: [
        'Bhadrabahu and Sthulabhadra',
        'Sthulabhadra and Bhadrabahu',
        'Mahavira and Parshvanath',
        'Rishabhanath and Mahavira',
      ],
      answerIndex: 1,
      explanation: 'Svetambara (white-clad) \u2014 Sthulabhadra; Digambara (unclad) \u2014 Bhadrabahu, who migrated south with Chandragupta Maurya to Shravanabelagola during the Magadha famine.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'Early Buddhist literature (the Tripitakas) was written mostly in:',
      options: ['Sanskrit', 'Prakrit', 'Pali', 'Magadhi'],
      answerIndex: 2,
      explanation: 'Pali \u2014 the people\u2019s tongue, part of why Buddhism spread fast. Tri-pitaka = three baskets: Vinaya, Sutta, Abhidhamma.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Which is NOT one of the Four Noble Truths?',
      options: [
        'The world is full of sorrows',
        'Desire is the cause of sorrow',
        'Sorrow ends when desire is conquered',
        'God must be worshipped to end sorrow',
      ],
      answerIndex: 3,
      explanation: 'Buddhism does not recognize God (or the soul). The fourth truth is the PATH \u2014 the eightfold Ashtangika Marga \u2014 not worship.',
    },
  ],
};

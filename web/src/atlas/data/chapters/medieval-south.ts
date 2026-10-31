import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// MEDIEVAL SOUTH \u2014 CHOLAS, VIJAYANAGARA, BAHMANI
//
// Concept:
//   "The south runs on rivers: Chola power on the Kaveri delta,
//   Vijayanagara on the Tungabhadra, and the Krishna as the
//   fault line between Vijayanagara and the Bahmani sultans."
//
// Source: Medieval Indian History \u2014 Delhi Sultanate deck
// (Cholas, Vijayanagara, Bahmani sections).
// ============================================

const southSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'thanjavur', name: 'Thanjavur \u2014 Chola capital; Rajaraja I\u2019s Brihadesvara temple (1010)' }, geometry: { type: 'Point', coordinates: [79.13, 10.79] } },
    { type: 'Feature', properties: { id: 'gangaikonda', name: 'Gangaikondacholapuram \u2014 Rajendra I\u2019s victory city after the Ganga campaign' }, geometry: { type: 'Point', coordinates: [79.45, 11.21] } },
    { type: 'Feature', properties: { id: 'hampi', name: 'Hampi (Vijayanagara) \u2014 capital on the Tungabhadra, founded 1336 by Harihara & Bukka' }, geometry: { type: 'Point', coordinates: [76.47, 15.34] } },
    { type: 'Feature', properties: { id: 'gulbarga', name: 'Gulbarga \u2014 first Bahmani capital (1347, Alauddin Hasan Bahman Shah)' }, geometry: { type: 'Point', coordinates: [76.83, 17.33] } },
    { type: 'Feature', properties: { id: 'bidar', name: 'Bidar \u2014 later Bahmani capital; Mahmud Gawan\u2019s madrasa' }, geometry: { type: 'Point', coordinates: [77.52, 17.91] } },
    { type: 'Feature', properties: { id: 'talikota', name: 'Talikota / Rakshasa-Tangadi (1565) \u2014 Deccan sultans crush Vijayanagara' }, geometry: { type: 'Point', coordinates: [76.31, 16.47] } },
  ],
};

/** The Krishna \u2014 the Vijayanagara\u2013Bahmani fault line \u2014 and the Kaveri. */
const southRivers: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'krishna-r', name: 'Krishna \u2014 the contested frontier (Raichur doab between Krishna & Tungabhadra)' },
      geometry: { type: 'LineString', coordinates: [[73.7, 17.5], [75.0, 16.9], [76.5, 16.5], [78.0, 16.4], [79.5, 16.2], [80.9, 15.8]] },
    },
    {
      type: 'Feature',
      properties: { id: 'tungabhadra-r', name: 'Tungabhadra \u2014 Vijayanagara\u2019s river (Hampi on its bank)' },
      geometry: { type: 'LineString', coordinates: [[75.3, 14.2], [75.9, 14.8], [76.47, 15.34], [77.2, 15.7], [78.2, 15.9]] },
    },
    {
      type: 'Feature',
      properties: { id: 'kaveri-r', name: 'Kaveri \u2014 the Chola rice bowl; Thanjavur delta' },
      geometry: { type: 'LineString', coordinates: [[75.5, 12.4], [76.6, 12.2], [77.6, 11.9], [78.6, 11.3], [79.13, 10.9], [79.8, 10.75]] },
    },
  ],
};

/** Rajendra Chola's naval reach \u2014 Ganga + Srivijaya expeditions. */
const cholaNavy: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'ganga-exp', name: 'c. 1022: Rajendra I\u2019s Ganga expedition \u2014 defeats Mahipala I of Bengal' },
      geometry: { type: 'LineString', coordinates: [[79.45, 11.21], [80.3, 13.2], [80.9, 15.8], [83.0, 18.0], [85.8, 20.3], [87.5, 22.5], [88.4, 24.0]] },
    },
    {
      type: 'Feature',
      properties: { id: 'srivijaya-exp', name: 'c. 1025: naval expedition against Srivijaya (Malaya\u2013Sumatra) \u2014 command of the sea lanes' },
      geometry: { type: 'LineString', coordinates: [[79.9, 10.8], [84.0, 9.0], [89.0, 7.5], [94.0, 6.0], [98.5, 4.5], [102.0, 3.0]] },
    },
  ],
};

export const medievalSouthChapter: Chapter = {
  id: 'medieval-south',
  subject: 'history',
  unit: 'Medieval',
  tags: ['kaveri', 'krishna', 'tungabhadra', 'deccan', 'hampi', 'thanjavur', 'peninsular-plateau', 'bengal'],
  title: 'Medieval South: Cholas to Talikota',
  summary: 'Chola navy on the Kaveri, Vijayanagara on the Tungabhadra, Bahmani rivalry.',
  focus:
    'The medieval south runs on rivers: Chola power grew from the Kaveri delta and sailed to the Ganga and Srivijaya; Vijayanagara rose on the Tungabhadra; and the Krishna\u2013Tungabhadra doab was the bleeding frontier with the Bahmani sultans \u2014 until Talikota, 1565.',
  view: { center: [14.5, 78.5], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#0e7a70', mapBg: '#eaf5f2' },

  layers: [
    {
      id: 'south-sites',
      name: 'Capitals & battle sites',
      kind: 'vector',
      data: southSites,
      style: { color: '#0e7a70', weight: 2, fillColor: '#0e7a70', markerRadius: 7, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'south-rivers',
      name: 'The three rivers of power',
      kind: 'vector',
      data: southRivers,
      style: { color: '#1f5fa8', weight: 3, flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'chola-navy',
      name: 'Rajendra\u2019s expeditions',
      kind: 'vector',
      data: cholaNavy,
      style: { color: '#b0632c', weight: 2.5, dashArray: '6 6', flow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'The IMPERIAL CHOLAS (c. 850\u20131200) rebuilt Tamil power from the Kaveri delta. RAJARAJA I (985\u20131014) conquered Kerala, northern Sri Lanka and the Maldives, and raised the Brihadesvara (Rajarajesvaram) temple at Thanjavur \u2014 the grandest Dravidian temple, completed 1010.',
      linkedLayerId: 'south-sites',
      linkedFeatureId: 'thanjavur',
    },
    {
      id: 'f2',
      text: 'RAJENDRA I (1014\u201344) took the empire to its peak: marched north and defeated MAHIPALA I of the Pala empire of Bengal, and to commemorate it founded GANGAIKONDACHOLAPURAM (\u201cthe Chola who took the Ganga\u201d) with its own Rajesvaram temple. Called Pandita Cholan for his patronage of learning.',
      linkedLayerId: 'chola-navy',
    },
    {
      id: 'f3',
      text: 'The Chola NAVY was the age\u2019s wonder: the c. 1025 expedition against SRIVIJAYA (Malaya\u2013Sumatra) secured the eastern sea lanes to China. Chola local government is equally famous \u2014 the Uttaramerur inscriptions describe elected village assemblies (sabha/ur) with committee (variyam) systems.',
      linkedLayerId: 'chola-navy',
    },
    {
      id: 'f4',
      text: 'VIJAYANAGARA (1336\u20131672): founded by HARIHARA and BUKKA of the Sangama dynasty on the Tungabhadra \u2014 capital HAMPI. Four dynasties: Sangama \u2192 Saluva \u2192 Tuluva \u2192 Aravidu. Deva Raya II (1425\u201346) recruited Muslim cavalry and archers to modernize the army.',
      linkedLayerId: 'south-sites',
      linkedFeatureId: 'hampi',
    },
    {
      id: 'f5',
      text: 'The BAHMANI kingdom (1347\u20131527): founded by ALAUDDIN HASAN BAHMAN SHAH in revolt against Muhammad-bin-Tughlaq; capital first at GULBARGA, later BIDAR. Its greatest figure was the minister MAHMUD GAWAN (1461\u201381) \u2014 conquests, administrative reform, and the great madrasa at Bidar \u2014 executed on a forged letter; the kingdom then split into the five Deccan sultanates (Bijapur, Ahmadnagar, Golkonda, Bidar, Berar).',
      linkedLayerId: 'south-sites',
      linkedFeatureId: 'bidar',
    },
    {
      id: 'f6',
      text: 'Vijayanagara vs Bahmani: a 200-year war over the RAICHUR DOAB \u2014 the fertile, fort-studded strip between the Krishna and the Tungabhadra. KRISHNADEVA RAYA (1509\u201329, Tuluva) was the climax: took Raichur (1520), patronized Telugu letters (Amuktamalyada), hosted Portuguese travellers (Domingo Paes) \u2014 the \u201cAndhra Bhoja\u201d.',
      linkedLayerId: 'south-rivers',
    },
    {
      id: 'f7',
      text: 'TALIKOTA (Rakshasa-Tangadi / Bannihatti), 1565: the combined Deccan sultanates \u2014 Bijapur, Ahmadnagar, Golkonda and Bidar (all except Berar) \u2014 crushed Vijayanagara; regent RAMA RAYA was captured and executed, Hampi sacked. The empire lingered under the Aravidus but the south\u2019s balance of power was broken \u2014 setting the stage for the Mughals and then the Europeans.',
      linkedLayerId: 'south-sites',
      linkedFeatureId: 'talikota',
    },
  ],

  events: [
    { id: 'e1', date: '1010', label: 'Brihadesvara', description: 'Rajaraja I completes the great temple at Thanjavur \u2014 the Kaveri delta is the engine of Chola power.', showLayers: ['south-sites', 'south-rivers'], hideLayers: ['chola-navy'], view: { center: [10.79, 79.13], zoom: 7 } },
    { id: 'e2', date: '1022', label: 'Ganga campaign', description: 'Rajendra I defeats Mahipala I of Bengal; Gangaikondacholapuram founded in commemoration.', showLayers: ['chola-navy', 'south-sites'], view: { center: [16.0, 83.0], zoom: 5 } },
    { id: 'e3', date: '1025', label: 'Srivijaya raid', description: 'The Chola navy strikes Srivijaya across the Bay of Bengal \u2014 command of the eastern sea lanes.', showLayers: ['chola-navy'], view: { center: [8.0, 90.0], zoom: 4 } },
    { id: 'e4', date: '1336', label: 'Vijayanagara founded', description: 'Harihara and Bukka found the city on the Tungabhadra; the Bahmani kingdom follows in 1347 \u2014 the Deccan splits in two.', showLayers: ['south-sites', 'south-rivers'], hideLayers: ['chola-navy'], view: { center: [16.3, 76.7], zoom: 6 } },
    { id: 'e5', date: '1520', label: 'Raichur', description: 'Krishnadeva Raya takes the Raichur doab \u2014 the Krishna\u2013Tungabhadra frontier at its high-water mark.', view: { center: [16.2, 77.3], zoom: 7 } },
    { id: 'e6', date: '1565', label: 'Talikota', description: 'Four Deccan sultanates combine and destroy Vijayanagara; Rama Raya executed, Hampi sacked.', view: { center: [16.47, 76.31], zoom: 7 } },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'map_click',
      question: 'Click Hampi \u2014 the Vijayanagara capital on the Tungabhadra.',
      answer: { lat: 15.34, lng: 76.47, toleranceKm: 110 },
      explanation: 'Hampi sits on the south bank of the Tungabhadra \u2014 founded 1336 by Harihara and Bukka of the Sangama dynasty. Today a UNESCO site.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Gangaikondacholapuram was founded by Rajendra I to commemorate:',
      options: [
        'The conquest of Sri Lanka',
        'His victory over Mahipala I of Bengal in the Ganga campaign',
        'The Srivijaya naval expedition',
        'The completion of the Brihadesvara temple',
      ],
      answerIndex: 1,
      explanation: '\u201cThe city of the Chola who took the Ganga\u201d \u2014 after defeating the Pala king Mahipala I. He built the Rajesvaram temple there and earned the title Pandita Cholan.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'The 200-year Vijayanagara\u2013Bahmani wars were fought chiefly over:',
      options: [
        'The Kaveri delta',
        'The Raichur doab, between the Krishna and the Tungabhadra',
        'The Konkan coast',
        'The Palghat gap',
      ],
      answerIndex: 1,
      explanation: 'The fertile, fort-studded Raichur doab between the two rivers \u2014 Krishnadeva Raya\u2019s capture of Raichur in 1520 marked Vijayanagara\u2019s high point.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'At Talikota (1565), Vijayanagara was defeated by the combined Deccan sultanates EXCEPT:',
      options: ['Bijapur', 'Ahmadnagar', 'Berar', 'Golkonda'],
      answerIndex: 2,
      explanation: 'Bijapur, Ahmadnagar, Golkonda and Bidar combined \u2014 Berar stayed out. Rama Raya was executed and Hampi sacked; the battle is also called Rakshasa-Tangadi or Bannihatti.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click Thanjavur \u2014 seat of Rajaraja I and the Brihadesvara temple.',
      answer: { lat: 10.79, lng: 79.13, toleranceKm: 100 },
      explanation: 'Thanjavur commands the Kaveri delta \u2014 the rice bowl that funded the Chola navy and the grandest Dravidian temple (completed 1010).',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Mahmud Gawan is remembered as:',
      options: [
        'Founder of Vijayanagara',
        'The great Bahmani minister \u2014 conquests, reforms, the Bidar madrasa \u2014 executed on a forged letter',
        'The admiral of the Chola navy',
        'The last Sangama king',
      ],
      answerIndex: 1,
      explanation: 'Gawan (1461\u201381) was the Bahmani kingdom\u2019s greatest statesman; his judicial murder triggered the breakup into the five Deccan sultanates.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'The Uttaramerur inscriptions are famous for describing:',
      options: [
        'Chola naval tactics',
        'Elected village assemblies and committee (variyam) administration under the Cholas',
        'Vijayanagara market rules',
        'Bahmani land revenue',
      ],
      answerIndex: 1,
      explanation: 'Chola local self-government: village sabhas with lot-based elections and specialized committees \u2014 a favourite of both prelims and mains answers on ancient local governance.',
    },
  ],
};

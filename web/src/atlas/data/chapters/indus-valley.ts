import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// INDUS VALLEY CIVILIZATION (2600 BC \u2013 1500 BC)
//
// Concept:
//   "The IVC is remembered site by site \u2014 every exam question
//   is really a map question: which site, which river, which
//   excavator, which extreme point."
//
// Source: ANCIENT INDIAN HISTORY \u2014 Prelims (MS Academy) deck.
// ============================================

/** Core + extremity sites. `role` drives styling/filtering. */
const ivcSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'harappa', name: 'Harappa \u2014 R. Ravi \u2014 Dayaram Sahni, 1921 (capital city)' },
      geometry: { type: 'Point', coordinates: [72.87, 30.63] },
    },
    {
      type: 'Feature',
      properties: { id: 'mohenjodaro', name: 'Mohenjodaro \u2014 R. Indus \u2014 R.D. Banerji, 1922 (largest site; Great Bath)' },
      geometry: { type: 'Point', coordinates: [68.14, 27.33] },
    },
    {
      type: 'Feature',
      properties: { id: 'chanhudaro', name: 'Chanhudaro (Sindh) \u2014 only site without a citadel' },
      geometry: { type: 'Point', coordinates: [68.32, 26.17] },
    },
    {
      type: 'Feature',
      properties: { id: 'kalibangan', name: 'Kalibangan (Rajasthan) \u2014 world\u2019s first ploughed field' },
      geometry: { type: 'Point', coordinates: [74.13, 29.47] },
    },
    {
      type: 'Feature',
      properties: { id: 'lothal', name: 'Lothal (Gujarat) \u2014 port city; dockyard; rice husk' },
      geometry: { type: 'Point', coordinates: [72.25, 22.52] },
    },
    {
      type: 'Feature',
      properties: { id: 'dholavira', name: 'Dholavira (Gujarat) \u2014 three-part city; water reservoirs' },
      geometry: { type: 'Point', coordinates: [70.21, 23.89] },
    },
    {
      type: 'Feature',
      properties: { id: 'banawali', name: 'Banawali (Haryana)' },
      geometry: { type: 'Point', coordinates: [75.39, 29.6] },
    },
    {
      type: 'Feature',
      properties: { id: 'rakhigarhi', name: 'Rakhigarhi (Haryana) \u2014 largest site in India' },
      geometry: { type: 'Point', coordinates: [76.11, 29.29] },
    },
  ],
};

/** The four extreme points \u2014 a guaranteed prelims question. */
const extremes: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'manda', name: 'NORTH: Manda (Jammu) \u2014 R. Chenab' },
      geometry: { type: 'Point', coordinates: [74.85, 32.72] },
    },
    {
      type: 'Feature',
      properties: { id: 'daimabad', name: 'SOUTH: Daimabad (Maharashtra) \u2014 R. Pravara' },
      geometry: { type: 'Point', coordinates: [74.71, 19.51] },
    },
    {
      type: 'Feature',
      properties: { id: 'sutkagendor', name: 'WEST: Sutkagendor \u2014 Makran coast (also a port)' },
      geometry: { type: 'Point', coordinates: [62.03, 25.5] },
    },
    {
      type: 'Feature',
      properties: { id: 'alamgirpur', name: 'EAST: Alamgirpur (Western U.P.)' },
      geometry: { type: 'Point', coordinates: [77.48, 29.0] },
    },
    {
      type: 'Feature',
      properties: { id: 'shortugai', name: 'Shortugai (Afghanistan) \u2014 farthest outpost, lapis lazuli trade' },
      geometry: { type: 'Point', coordinates: [69.5, 37.35] },
    },
  ],
};

/** Simplified civilization extent \u2014 recognition, not precision. */
const ivcExtent: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'ivc-extent', name: 'Approximate spread of the Harappan Civilization' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [61.5, 25.0], [66.0, 28.5], [69.0, 34.0], [75.0, 33.5],
          [78.0, 29.5], [76.5, 27.0], [75.5, 22.5], [75.0, 19.2],
          [73.5, 19.0], [71.5, 21.0], [68.5, 22.5], [66.5, 24.5],
          [61.5, 25.0],
        ]],
      },
    },
  ],
};

export const indusValleyChapter: Chapter = {
  id: 'indus-valley',
  subject: 'history',
  unit: 'Ancient',
  tags: ['indus', 'ravi', 'chenab', 'ghaggar-saraswati', 'gujarat', 'punjab'],
  title: 'Indus Valley Civilization',
  summary: 'Bronze Age cities on the Indus \u2014 sites, rivers, excavators, extremes.',
  focus:
    'Every IVC exam question is secretly a map question: pin each site to its river, its excavator, and its direction on the map \u2014 Manda north, Daimabad south, Sutkagendor west, Alamgirpur east.',
  view: { center: [26.5, 71.5], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#a5622d', mapBg: '#f6efe4' },

  layers: [
    {
      id: 'ivc-extent',
      name: 'Civilization extent',
      kind: 'vector',
      data: ivcExtent,
      style: { color: '#a5622d', weight: 1.5, fillColor: '#c98a4b', fillOpacity: 0.25, pattern: 'dots' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'ivc-sites',
      name: 'Major sites',
      kind: 'vector',
      data: ivcSites,
      style: { color: '#7a3b10', weight: 2, fillColor: '#7a3b10', fillOpacity: 0.9, shadow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'ivc-extremes',
      name: 'Extreme points (N/S/E/W)',
      kind: 'vector',
      data: extremes,
      style: { color: '#b3261e', weight: 2, fillColor: '#b3261e', fillOpacity: 0.9, shadow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'The IVC belongs to the Bronze Age and to the Proto-history of India. Its contemporaries were Mesopotamia (Tigris\u2013Euphrates), Egypt (Nile), and China (Hwang Ho). Phases: Early 3500\u20132600 BC, Mature 2600\u20131900 BC, Late 1900\u20131500 BC.',
    },
    {
      id: 'f2',
      text: 'Discovery chain: Charles Masson noticed the ruins in 1826; Alexander Cunningham collected seals five decades later; Dayaram Sahni excavated Harappa in 1921 (banks of the Ravi); R.D. Banerji excavated Mohenjodaro (\u201cmound of the dead\u201d) in 1922 on the Indus; in 1924 John Marshall named it the Indus Valley Civilization.',
      linkedLayerId: 'ivc-sites',
    },
    {
      id: 'f3',
      text: 'Extremes \u2014 memorize as a compass: Manda in Jammu (river Chenab) is the northernmost site, Daimabad in Maharashtra (river Pravara) the southernmost, Sutkagendor on the Makran coast the westernmost, Alamgirpur in western U.P. the easternmost. Shortugai in Afghanistan was a distant trade outpost.',
      linkedLayerId: 'ivc-extremes',
    },
    {
      id: 'f4',
      text: 'Superlatives: Mohenjodaro is the largest site overall; Rakhigarhi (Haryana) is the largest site in India; Harappa and Mohenjodaro were the \u201ccapital cities\u201d; Lothal and Sutkagendor were port cities.',
      linkedLayerId: 'ivc-sites',
    },
    {
      id: 'f5',
      text: 'Town planning: grid system with streets at right angles; the raised Citadel on the western mound housed public buildings and the ruling class, the lower eastern town housed common people; brilliant covered drains of mortar, lime and gypsum. The Great Bath (with bitumen-lined bed) and a granary stand at Mohenjodaro; Harappa also had granaries.',
    },
    {
      id: 'f6',
      text: 'Economy: main crops wheat and barley; rice evidence at Lothal and Rangpur; world\u2019s first ploughed field found at Kalibangan; the Indus people were the first in the world to produce cotton (Greeks called it Sindon). Trade with Mesopotamia was by barter \u2014 no coins; Sumerian texts call the Indus region \u201cMeluha\u201d.',
    },
    {
      id: 'f7',
      text: 'Things the Harappans did NOT know \u2014 a favourite trick question: iron, the horse (debated), the lion, and sugarcane. Weights were made of limestone and steatite, usually cubical.',
    },
  ],

  events: [
    {
      id: 'e1',
      date: '1826',
      label: 'Masson',
      description: 'Charles Masson first records the ruins of Harappa.',
      view: { center: [30.63, 72.87], zoom: 6 },
    },
    {
      id: 'e2',
      date: '1921',
      label: 'Harappa dug',
      description: 'Dayaram Sahni excavates Harappa on the banks of the Ravi (Sahiwal district, Pakistan).',
      showLayers: ['ivc-sites'],
      view: { center: [30.63, 72.87], zoom: 7 },
    },
    {
      id: 'e3',
      date: '1922',
      label: 'Mohenjodaro dug',
      description: 'R.D. Banerji excavates Mohenjodaro \u2014 \u201cmound of the dead\u201d \u2014 on the Indus.',
      showLayers: ['ivc-sites'],
      view: { center: [27.33, 68.14], zoom: 7 },
    },
    {
      id: 'e4',
      date: '1924',
      label: 'Named IVC',
      description: 'John Marshall announces and names the Indus Valley Civilization. Historians prefer \u201cHarappan Civilization\u201d \u2014 named after the first site found.',
      showLayers: ['ivc-extent', 'ivc-sites', 'ivc-extremes'],
      view: { center: [26.5, 71.5], zoom: 5 },
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'map_click',
      question: 'Click Mohenjodaro \u2014 the largest Harappan site, excavated by R.D. Banerji in 1922.',
      answer: { lat: 27.33, lng: 68.14, toleranceKm: 150 },
      explanation: 'Mohenjodaro (\u201cmound of the dead\u201d) sits on the Indus in Sindh. It holds the Great Bath (bitumen-lined, for ritual bathing) and a granary to its west.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Match the excavation: Harappa (1921) and Mohenjodaro (1922) were dug by, respectively:',
      options: [
        'John Marshall and Charles Masson',
        'Dayaram Sahni and R.D. Banerji',
        'R.D. Banerji and Dayaram Sahni',
        'Alexander Cunningham and John Marshall',
      ],
      answerIndex: 1,
      explanation: 'Dayaram Sahni excavated Harappa (1921, river Ravi); R.D. Banerji excavated Mohenjodaro (1922, river Indus). John Marshall only *named* the civilization in 1924; Masson had noticed the ruins back in 1826.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Which pairing of extreme points is CORRECT?',
      options: [
        'North: Alamgirpur \u2014 East: Manda',
        'West: Daimabad \u2014 South: Sutkagendor',
        'North: Manda (Chenab) \u2014 South: Daimabad (Pravara)',
        'East: Shortugai \u2014 West: Rakhigarhi',
      ],
      answerIndex: 2,
      explanation: 'Manda in Jammu on the Chenab is northernmost; Daimabad in Maharashtra on the Pravara is southernmost. Sutkagendor (Makran coast) is westernmost and Alamgirpur (western U.P.) easternmost.',
    },
    {
      id: 'q4',
      type: 'map_click',
      question: 'Click Lothal \u2014 the port city where rice husk was found.',
      answer: { lat: 22.52, lng: 72.25, toleranceKm: 120 },
      explanation: 'Lothal in Gujarat had a dockyard and yielded rice evidence (with Rangpur). The other port was Sutkagendor far west on the Makran coast.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'The world\u2019s first ploughed field was found at:',
      options: ['Lothal', 'Kalibangan', 'Banawali', 'Dholavira'],
      answerIndex: 1,
      explanation: 'Kalibangan in Rajasthan preserves furrow marks of the world\u2019s earliest ploughed field. Harappans used wooden ploughshares and stone sickles.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Which of these was UNKNOWN to the Indus people?',
      options: ['Cotton', 'Iron', 'Barley', 'The bull'],
      answerIndex: 1,
      explanation: 'Iron, the lion, and sugarcane were unknown; there were no coins (barter trade). They were, however, the FIRST in the world to grow cotton \u2014 the Greeks called it Sindon.',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click Rakhigarhi \u2014 the largest Harappan site within India.',
      answer: { lat: 29.29, lng: 76.11, toleranceKm: 120 },
      explanation: 'Rakhigarhi in Haryana is India\u2019s largest Harappan site; Mohenjodaro (in Pakistan) is the largest overall.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'In Harappan town planning, the Citadel stood:',
      options: [
        'On the lower eastern mound, for common people',
        'At the exact centre of the grid',
        'On the higher western mound, housing public buildings and the ruling class',
        'Outside the city walls',
      ],
      answerIndex: 2,
      explanation: 'Citadel = higher mound, WESTERN side, public buildings + rulers. The lower EASTERN town housed commoners. Streets crossed at right angles, with covered drains of mortar, lime and gypsum.',
    },
  ],
};

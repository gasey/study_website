import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// THE VEDIC AGE (1500\u2013500 BC)
//
// Concept:
//   "The Rig Veda is a map of rivers. Sapta Sindhu = the Punjab
//   river system under older names \u2014 then the whole civilization
//   slides east down the Ganga. Learn the river name-pairs and
//   half the Vedic questions solve themselves."
//
// Source: ANCIENT INDIAN HISTORY \u2014 Prelims (MS Academy) deck.
// ============================================

/** Sapta Sindhu: Vedic name \u2194 modern river. Simplified courses. */
const saptaSindhu: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'sindhu', name: 'Sindhu = INDUS \u2014 the axis of the Sapta Sindhu' }, geometry: { type: 'LineString', coordinates: [[74.5, 34.5], [72.5, 33.0], [70.9, 31.0], [69.5, 28.5], [68.3, 26.0], [67.9, 24.3]] } },
    { type: 'Feature', properties: { id: 'vitasta', name: 'Vitasta = JHELUM' }, geometry: { type: 'LineString', coordinates: [[74.8, 34.1], [73.7, 33.0], [72.6, 31.9], [71.7, 31.2]] } },
    { type: 'Feature', properties: { id: 'asikni', name: 'Asikni = CHENAB' }, geometry: { type: 'LineString', coordinates: [[76.6, 33.4], [74.9, 32.5], [73.5, 31.7], [71.9, 30.9]] } },
    { type: 'Feature', properties: { id: 'parushni', name: 'Parushni = RAVI \u2014 river of the Battle of Ten Kings' }, geometry: { type: 'LineString', coordinates: [[76.5, 32.5], [75.2, 31.9], [73.9, 31.2], [72.5, 30.6]] } },
    { type: 'Feature', properties: { id: 'vipasha', name: 'Vipasha = BEAS' }, geometry: { type: 'LineString', coordinates: [[77.1, 32.0], [76.0, 31.6], [75.1, 31.4], [74.8, 31.2]] } },
    { type: 'Feature', properties: { id: 'shutudri', name: 'Shutudri = SUTLEJ' }, geometry: { type: 'LineString', coordinates: [[78.7, 31.8], [76.8, 31.2], [75.3, 30.8], [73.8, 30.2], [72.2, 29.6]] } },
    { type: 'Feature', properties: { id: 'saraswati', name: 'Saraswati \u2014 the lost river (Ghaggar\u2013Hakra bed)' }, geometry: { type: 'LineString', coordinates: [[77.2, 30.5], [76.0, 29.9], [74.8, 29.4], [73.6, 28.9], [72.5, 28.3]] } },
  ],
};

/** The eastward shift: Early Vedic homeland \u2192 Later Vedic heartland. */
const eastwardShift: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'shift', name: 'The great eastward shift, 1000\u2013500 BC: Punjab \u2192 Ganga\u2013Yamuna doab \u2192 eastern UP/Bihar' },
      geometry: { type: 'LineString', coordinates: [[73.5, 31.0], [76.0, 29.8], [78.0, 28.6], [80.5, 27.2], [83.0, 26.0], [85.1, 25.6]] },
    },
    { type: 'Feature', properties: { id: 'early-home', name: 'Early Vedic homeland \u2014 Sapta Sindhu (Punjab)' }, geometry: { type: 'Point', coordinates: [73.5, 31.0] } },
    { type: 'Feature', properties: { id: 'later-home', name: 'Later Vedic heartland \u2014 Ganga\u2013Yamuna doab (Kuru\u2013Panchala)' }, geometry: { type: 'Point', coordinates: [78.5, 28.4] } },
    { type: 'Feature', properties: { id: 'pgw', name: 'Hastinapura \u2014 Painted Grey Ware culture zone' }, geometry: { type: 'Point', coordinates: [78.0, 29.15] } },
  ],
};

export const vedicAgeChapter: Chapter = {
  id: 'vedic-age',
  subject: 'history',
  unit: 'Ancient',
  tags: ['indus', 'jhelum', 'chenab', 'ravi', 'beas', 'sutlej', 'ghaggar-saraswati', 'punjab', 'ganga', 'northern-plains'],
  title: 'The Vedic Age',
  summary: 'Sapta Sindhu river names, Rig Vedic society, and the eastward shift.',
  focus:
    'The Rig Veda is a map: Sapta Sindhu is the Punjab river system under older names (Vitasta=Jhelum, Asikni=Chenab, Parushni=Ravi, Vipasha=Beas, Shutudri=Sutlej). Then, 1000\u2013500 BC, the whole civilization slides east down the Ganga.',
  view: { center: [29.5, 75.5], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#9a6b1f', mapBg: '#f7f0df' },

  layers: [
    {
      id: 'sapta-sindhu',
      name: 'Sapta Sindhu rivers',
      description: 'Vedic names \u2194 modern rivers.',
      kind: 'vector',
      data: saptaSindhu,
      style: { color: '#1f5fa8', weight: 3, flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'eastward-shift',
      name: 'Eastward shift (Later Vedic)',
      description: 'Punjab \u2192 doab \u2192 eastern UP/Bihar, 1000\u2013500 BC.',
      kind: 'vector',
      data: eastwardShift,
      style: { color: '#9a6b1f', weight: 3, dashArray: '2 8', flow: true, markerRadius: 7, glow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'The Vedic people \u2014 Indo-European speakers believed to originate in the Steppes of southern Russia and Central Asia \u2014 appeared in India a little before 1500 BC, migrating in waves. Periods: Early/Rig Vedic 1500\u20131000 BC (Sapta Sindhu, late Bronze\u2013early Iron), Later Vedic 1000\u2013500 BC (Ganga\u2013Yamuna valleys).',
    },
    {
      id: 'f2',
      text: 'The Rig Veda \u2014 the earliest Indo-European text \u2014 mentions about 40 rivers. The exam pairs: Vitasta=Jhelum, Asikni=Chenab, Parushni=Ravi, Vipasha=Beas, Shutudri=Sutlej, plus the Sindhu (Indus) and the Saraswati (the \u201clost\u201d Ghaggar). The Battle of Ten Kings (Dasarajna) was fought on the Parushni \u2014 the Ravi.',
      linkedLayerId: 'sapta-sindhu',
    },
    {
      id: 'f3',
      text: 'Rig Vedic economy: primarily PASTORAL \u2014 the cow was the chief wealth and unit of exchange, most wars were fought over cattle; agriculture was secondary. Horses and spoke-wheeled chariots were their signature technology (both unknown to the Harappans \u2014 a favourite contrast question). No clear evidence of trade or coins.',
    },
    {
      id: 'f4',
      text: 'Polity: the tribe (Jana/Vis) under a hereditary chief, the RAJAN, checked by assemblies \u2014 SABHA (council of elders), SAMITI (national assembly; even elected the Rajan in traces), VIDATHA and GANA. Women attended Sabha and Vidatha in the early period. Bali = voluntary offering, not tax; no standing army. Purohita (Vasishtha the conservative, Vishvamitra the liberal) was the key functionary; Senani led the army; Gramani headed the village.',
    },
    {
      id: 'f5',
      text: 'Society: patriarchal, kinship-based; Kula/Griha = family; Vis divided into gramas \u2014 when gramas clashed it was SAMGRAMA (the literal origin of the word for war). Monogamy prevailed, widow remarriage existed, and there is no evidence of child marriage in the Rig Vedic period.',
    },
    {
      id: 'f6',
      text: 'Later Vedic changes (1000\u2013500 BC): iron (shyama ayas) clears the Ganga forests; agriculture overtakes cattle; territory replaces tribe (Rashtra appears); the varna order hardens; Sabha and Samiti fade before rising kingship. Painted Grey Ware pottery marks the doab settlements like Hastinapura. This eastward world is the stage on which the Mahajanapadas rise.',
      linkedLayerId: 'eastward-shift',
    },
    {
      id: 'f7',
      text: 'Vedic literature ladder: 4 Vedas (Rig \u2014 hymns; Sama \u2014 melodies; Yajur \u2014 rituals; Atharva \u2014 charms) \u2192 Brahmanas (ritual explanation) \u2192 Aranyakas (forest books) \u2192 Upanishads (philosophy; \u201cSatyameva Jayate\u201d comes from the Mundaka Upanishad). The Gayatri mantra is addressed to the solar deity Savitri.',
    },
  ],

  events: [
    {
      id: 'e1',
      date: '-1500',
      label: 'Arrival',
      description: 'Rig Vedic people settle the Sapta Sindhu \u2014 the land of seven rivers (Punjab and fringes).',
      showLayers: ['sapta-sindhu'],
      hideLayers: ['eastward-shift'],
      view: { center: [31.0, 73.5], zoom: 6 },
    },
    {
      id: 'e2',
      date: '-1200',
      label: 'Ten Kings',
      description: 'Battle of Ten Kings (Dasarajna) on the Parushni (Ravi): Sudas of the Bharatas defeats the tribal confederacy.',
      showLayers: ['sapta-sindhu'],
      view: { center: [31.2, 74.5], zoom: 7 },
    },
    {
      id: 'e3',
      date: '-1000',
      label: 'Iron & the move east',
      description: 'Iron technology clears the forests; the centre of gravity shifts into the Ganga\u2013Yamuna doab (Kuru\u2013Panchala country).',
      showLayers: ['sapta-sindhu', 'eastward-shift'],
      view: { center: [28.5, 78.0], zoom: 6 },
    },
    {
      id: 'e4',
      date: '-0600',
      label: 'Threshold',
      description: 'By 600 BC the Later Vedic world dissolves into the sixteen Mahajanapadas \u2014 pick up the story in the next chapter.',
      showLayers: ['eastward-shift'],
      view: { center: [26.5, 81.0], zoom: 5 },
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Match the Vedic river names \u2014 which pairing is WRONG?',
      options: [
        'Vitasta = Jhelum',
        'Asikni = Chenab',
        'Parushni = Sutlej',
        'Vipasha = Beas',
      ],
      answerIndex: 2,
      explanation: 'Parushni = RAVI (the Battle of Ten Kings river). Shutudri = Sutlej. The full set: Vitasta\u2013Jhelum, Asikni\u2013Chenab, Parushni\u2013Ravi, Vipasha\u2013Beas, Shutudri\u2013Sutlej.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click the Ravi (Parushni) \u2014 the river of the Battle of Ten Kings.',
      answer: { lat: 31.2, lng: 74.5, toleranceKm: 130 },
      explanation: 'The Ravi flows past Lahore \u2014 the same river whose banks hold Harappa. One river, two chapters of history: a connection worth remembering.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'In Rig Vedic polity, the SAMITI was:',
      options: [
        'The council of elders',
        'The national assembly of the people, with traces of electing the Rajan',
        'The kings bodyguard',
        'A tax on cattle',
      ],
      answerIndex: 1,
      explanation: 'Samiti = national assembly (even shows traces of electing the chief); Sabha = council of elders. Women attended Sabha and Vidatha. Bali was a voluntary offering \u2014 there was no regular taxation.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'The chief form of wealth and the standard unit of exchange in the Early Vedic period was:',
      options: ['Gold coins', 'Land', 'The cow', 'The horse'],
      answerIndex: 2,
      explanation: 'The cow \u2014 most wars were fought over cattle (the word for war, samgrama, literally comes from clashing gramas). The horse mattered almost as much (chariots), but the cow was the currency.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'Which TWO things, central to Vedic life, were absent at Harappa?',
      options: [
        'Cotton and barley',
        'The horse and the spoked-wheel chariot',
        'Bronze and copper',
        'Cattle and pottery',
      ],
      answerIndex: 1,
      explanation: 'The Harappans did not know the horse (or iron); the Vedic people arrived with horse-drawn, spoke-wheeled chariots and probably introduced the spoked wheel to India. Classic contrast question between the two chapters.',
    },
    {
      id: 'q6',
      type: 'map_click',
      question: 'Click the Later Vedic heartland \u2014 the Ganga\u2013Yamuna doab (Kuru\u2013Panchala country).',
      answer: { lat: 28.4, lng: 78.5, toleranceKm: 160 },
      explanation: 'By 1000 BC iron axes and ploughs pulled the centre of gravity from Punjab into the doab \u2014 Hastinapura and the Painted Grey Ware sites mark it.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: '\u201cSatyameva Jayate\u201d, on India\u2019s national emblem, comes from the:',
      options: ['Rig Veda', 'Mundaka Upanishad', 'Sama Veda', 'Aitareya Brahmana'],
      answerIndex: 1,
      explanation: 'The Mundaka Upanishad. Ladder to remember: Vedas \u2192 Brahmanas \u2192 Aranyakas \u2192 Upanishads (ritual to philosophy).',
    },
  ],
};

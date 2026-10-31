import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// PHYSIOGRAPHIC DIVISIONS OF INDIA
//
// Concept:
//   India's six physiographic divisions are the foundation
//   for every other geography topic. Each division emerged
//   from a different geological process and shapes climate,
//   rivers, soils, and human settlement above it.
//
// Six divisions (NCERT / UPSC standard):
//   1. The Northern & North-Eastern Mountains
//   2. The Northern Plains
//   3. The Peninsular Plateau
//   4. The Indian Desert (Thar)
//   5. The Coastal Plains
//   6. The Islands
//
// Sources cross-checked: NCERT Class 9/11, NextIAS, PMF IAS,
// Britannica. Boundaries are intentionally simplified for
// educational clarity, not surveying.
// ============================================

// ---------- The six divisions as simplified polygons ----------

const northernMountains: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'himalayas',
        name: 'Himalayan Mountains',
        sub: 'Greater + Lesser + Shiwaliks, Indus to Brahmaputra'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [74.0, 32.5], [78.0, 30.5], [81.0, 30.0], [85.0, 28.0],
          [88.5, 27.0], [92.0, 27.5], [95.5, 28.5], [97.0, 29.5],
          [95.0, 30.0], [89.0, 29.5], [82.0, 31.0], [76.0, 33.5],
          [74.0, 32.5],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'purvanchal',
        name: 'Purvanchal (NE Hills)',
        sub: 'Patkai, Naga, Manipur, Mizo & Tripura Hills'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [93.0, 27.0], [97.0, 27.5], [97.5, 24.0], [94.5, 22.0],
          [92.5, 22.0], [91.5, 24.0], [92.0, 26.0], [93.0, 27.0],
        ]],
      },
    },
  ],
};

const northernPlains: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'northern-plains',
        name: 'Northern Plains (Indo-Gangetic-Brahmaputra)',
        sub: 'Formed by alluvium from Indus, Ganga, Brahmaputra. ~2400 km long, 240\u2013320 km wide.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [74.0, 31.0], [78.5, 30.0], [83.0, 28.5], [87.0, 27.0],
          [89.5, 26.5], [92.5, 26.5], [92.5, 24.5], [88.0, 24.0],
          [84.0, 24.5], [78.0, 25.5], [74.5, 27.5], [74.0, 31.0],
        ]],
      },
    },
  ],
};

const peninsularPlateau: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'peninsular-plateau',
        name: 'Peninsular Plateau',
        sub: 'Oldest landmass of India \u2014 part of ancient Gondwana. Triangular, Deccan + Central Highlands.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [72.5, 22.0], [78.0, 24.0], [85.0, 24.0], [87.0, 22.0],
          [86.5, 18.0], [85.0, 14.0], [80.0, 11.0], [77.5, 8.5],
          [75.0, 12.0], [73.0, 16.0], [72.5, 19.0], [72.5, 22.0],
        ]],
      },
    },
  ],
};

const indianDesert: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'thar-desert',
        name: 'Thar Desert',
        sub: 'Arid sandy plain. Mostly in western Rajasthan. <250 mm rainfall.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [69.5, 24.5], [73.5, 24.0], [75.0, 26.5], [74.5, 29.0],
          [72.0, 29.5], [70.0, 28.5], [69.5, 24.5],
        ]],
      },
    },
  ],
};

const coastalPlains: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'western-coastal-plain',
        name: 'Western Coastal Plain',
        sub: 'Narrow (50\u2013100 km). Konkan + Kanara + Malabar. Faces Arabian Sea.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [72.5, 20.5], [73.5, 20.0], [74.5, 16.0], [75.5, 12.0],
          [76.5, 8.5], [75.5, 8.5], [74.0, 11.5], [73.0, 15.5],
          [72.5, 19.5], [72.5, 20.5],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'eastern-coastal-plain',
        name: 'Eastern Coastal Plain',
        sub: 'Wider (100\u2013130 km). Northern Circars + Coromandel. Faces Bay of Bengal. Major deltas.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [85.5, 20.5], [87.5, 21.0], [87.5, 19.5], [85.0, 16.0],
          [82.0, 13.0], [80.5, 10.5], [79.5, 8.5], [78.5, 9.5],
          [80.5, 13.0], [83.0, 16.5], [85.5, 20.5],
        ]],
      },
    },
  ],
};

const islands: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {
        id: 'andaman-nicobar',
        name: 'Andaman & Nicobar Islands',
        sub: 'Volcanic / tectonic origin. Bay of Bengal. Southward extension of the Arakan Yoma.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [92.2, 13.7], [93.2, 13.7], [94.3, 9.0], [93.8, 6.7],
          [92.5, 6.7], [92.2, 9.0], [92.2, 13.7],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: {
        id: 'lakshadweep',
        name: 'Lakshadweep Islands',
        sub: 'Coral atolls. Arabian Sea. Formed over Reunion Hotspot volcanism.'
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [71.5, 12.4], [74.1, 12.4], [74.1, 8.0], [71.5, 8.0],
          [71.5, 12.4],
        ]],
      },
    },
  ],
};

// ---------- Sub-features: Himalayan ranges as parallel arcs ----------

const himalayanRanges: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'shiwaliks', name: 'Shiwaliks (Outer Himalayas)', range: 'shiwalik' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.5, 32.4], [77.5, 30.7], [81.0, 29.8], [85.0, 27.8], [88.5, 26.9], [92.0, 27.3]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'himachal', name: 'Himachal (Lesser Himalayas)', range: 'himachal' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.2, 32.9], [77.5, 31.3], [81.0, 30.4], [85.0, 28.4], [88.5, 27.5], [92.5, 28.0]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'himadri', name: 'Himadri (Greater Himalayas) \u2014 contains Mt. Everest', range: 'himadri' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.0, 33.5], [77.5, 32.0], [81.0, 31.0], [85.0, 29.0], [88.0, 28.0], [92.5, 29.0], [95.5, 29.0]],
      },
    },
  ],
};

// ---------- Northern Plains subdivisions (Bhabar / Tarai / Bhangar / Khadar) ----------

const plainsSubdivisions: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'bhabar', name: 'Bhabar', desc: 'Pebble belt at foot of Shiwaliks. Rivers disappear underground. Not cultivable.' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.5, 31.0], [78.0, 29.7], [81.5, 28.9], [85.0, 27.0], [88.5, 26.4], [92.0, 26.4]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tarai', name: 'Tarai', desc: 'Marshy belt south of Bhabar. Rivers re-emerge. Very fertile. Jim Corbett, Kaziranga lie here.' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.5, 30.5], [78.0, 29.2], [81.5, 28.4], [85.0, 26.5], [88.5, 25.9], [92.0, 25.9]],
      },
    },
  ],
};

// ---------- Key peaks and landmarks ----------

const keyPeaks: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'everest', name: 'Mt. Everest (8848 m) \u2014 Nepal/China, on Himadri' }, geometry: { type: 'Point', coordinates: [86.9250, 27.9881] } },
    { type: 'Feature', properties: { id: 'k2', name: 'K2 (8611 m) \u2014 PoK, Karakoram' }, geometry: { type: 'Point', coordinates: [76.5133, 35.8825] } },
    { type: 'Feature', properties: { id: 'kanchenjunga', name: 'Kanchenjunga (8586 m) \u2014 highest peak in India (Sikkim)' }, geometry: { type: 'Point', coordinates: [88.1475, 27.7025] } },
    { type: 'Feature', properties: { id: 'nanda-devi', name: 'Nanda Devi (7816 m) \u2014 Uttarakhand' }, geometry: { type: 'Point', coordinates: [79.9707, 30.3760] } },
    { type: 'Feature', properties: { id: 'anaimudi', name: 'Anaimudi (2695 m) \u2014 highest peak in Peninsular India (Kerala)' }, geometry: { type: 'Point', coordinates: [77.0600, 10.1700] } },
    { type: 'Feature', properties: { id: 'phawngpui', name: 'Phawngpui / Blue Mountain (2157 m) \u2014 highest peak in Mizoram' }, geometry: { type: 'Point', coordinates: [92.8333, 23.1667] } },
    { type: 'Feature', properties: { id: 'guru-shikhar', name: 'Guru Shikhar (1722 m) \u2014 highest in Aravallis (Rajasthan)' }, geometry: { type: 'Point', coordinates: [72.7100, 24.6600] } },
    { type: 'Feature', properties: { id: 'saddle-peak', name: 'Saddle Peak (737 m) \u2014 highest in Andamans' }, geometry: { type: 'Point', coordinates: [93.0167, 13.1500] } },
    { type: 'Feature', properties: { id: 'barren-island', name: 'Barren Island \u2014 India\u2019s only active volcano' }, geometry: { type: 'Point', coordinates: [93.8597, 12.2778] } },
  ],
};

// ---------- The chapter ----------

export const physiographicDivisionsChapter: Chapter = {
  id: 'physiographic-divisions',
  subject: 'geography',
  unit: 'India Physical',
  tags: ['himalayas', 'northern-plains', 'peninsular-plateau', 'thar', 'coasts', 'islands', 'aravalli', 'western-ghats'],
  title: 'Physiographic Divisions of India',
  summary: 'The six physical regions that make up India — and the geological story behind each.',
  focus:
    'India has six physiographic divisions, each born of a different geological process: collision-built mountains, alluvium-built plains, ancient stable plateau, sand desert, sediment-built coasts, and offshore islands of coral and volcano.',

  view: { center: [22.5, 80.0], zoom: 5 },
  basemap: 'physical',

  layers: [
    {
      id: 'northern-mountains',
      name: '1. Northern & NE Mountains',
      description: 'Himalayas + Purvanchal. Young fold mountains formed by India\u2013Eurasia collision.',
      kind: 'vector',
      data: northernMountains,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#5e4a8a', fillColor: '#9b8ac4', fillOpacity: 0.5, weight: 2, shadow: true },
    },
    {
      id: 'northern-plains',
      name: '2. Northern Plains',
      description: 'Indo-Gangetic-Brahmaputra plains. Alluvium from Indus, Ganga, Brahmaputra.',
      kind: 'vector',
      data: northernPlains,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#7a8a3a', fillColor: '#c5d086', fillOpacity: 0.55, weight: 2 },
    },
    {
      id: 'peninsular-plateau',
      name: '3. Peninsular Plateau',
      description: 'India\u2019s oldest landmass. Part of ancient Gondwana. Triangular.',
      kind: 'vector',
      data: peninsularPlateau,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#8a5a3a', fillColor: '#c9a47a', fillOpacity: 0.45, weight: 2, pattern: 'dots' },
    },
    {
      id: 'indian-desert',
      name: '4. Indian Desert (Thar)',
      description: 'Arid sand plain in western Rajasthan. India\u2019s only true desert.',
      kind: 'vector',
      data: indianDesert,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#c46a3d', fillColor: '#e8c590', fillOpacity: 0.6, weight: 2 },
    },
    {
      id: 'coastal-plains',
      name: '5. Coastal Plains',
      description: 'Eastern and Western coastal plains \u2014 narrow strips along the Peninsula.',
      kind: 'vector',
      data: coastalPlains,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#3a7a8a', fillColor: '#86c1d0', fillOpacity: 0.55, weight: 2 },
    },
    {
      id: 'islands',
      name: '6. Islands',
      description: 'Andaman & Nicobar (volcanic) + Lakshadweep (coral).',
      kind: 'vector',
      data: islands,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#3a8a5a', fillColor: '#86d0a8', fillOpacity: 0.6, weight: 2 },
    },
    {
      id: 'himalayan-ranges',
      name: 'Himalayan Ranges (3 parallel)',
      description: 'Shiwaliks (Outer), Himachal (Lesser), Himadri (Greater) \u2014 three roughly parallel arcs.',
      kind: 'vector',
      data: himalayanRanges,
      defaultOn: false,
      labelKey: 'name',
      style: { color: '#5e4a8a', weight: 2.5 },
    },
    {
      id: 'plains-subdivisions',
      name: 'Plains Subdivisions',
      description: 'Bhabar (pebble), Tarai (marshy), then Bhangar (older alluvium) and Khadar (newer alluvium).',
      kind: 'vector',
      data: plainsSubdivisions,
      defaultOn: false,
      labelKey: 'name',
      style: { color: '#7a8a3a', weight: 2.5, dashArray: '5 4' },
    },
    {
      id: 'key-peaks',
      name: 'Key Peaks & Landmarks',
      description: 'Highest points of each region \u2014 the ones UPSC asks about.',
      kind: 'vector',
      data: keyPeaks,
      defaultOn: true,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'India has six physiographic divisions: Northern & NE Mountains, Northern Plains, Peninsular Plateau, Indian Desert, Coastal Plains, and Islands. The Peninsular Plateau is the oldest; the Himalayas and the Northern Plains are the youngest.',
    },
    {
      id: 'f2',
      text: 'The Himalayas are young fold mountains, formed by the ongoing collision of the Indo-Australian plate with the Eurasian plate (started about 50 million years ago). They stretch ~2,400 km from the Indus in the west to the Brahmaputra in the east.',
      linkedLayerId: 'northern-mountains',
    },
    {
      id: 'f3',
      text: 'The Himalayas have three parallel ranges, from south to north: Shiwaliks (Outer, 900\u20131,100 m), Himachal/Lesser (3,500\u20134,500 m), and Himadri/Greater (>6,000 m, with peaks above 8,000 m). The Trans-Himalayas lie further north and include the Karakoram, Ladakh, and Zaskar ranges.',
      linkedLayerId: 'himalayan-ranges',
    },
    {
      id: 'f4',
      text: 'The Purvanchal (Eastern Hills) are a southward continuation of the Himalayas after the Dihang gorge. They include the Patkai, Naga, Manipur, and Mizo (Lushai) Hills \u2014 the entire chain runs largely north\u2013south.',
      linkedLayerId: 'northern-mountains',
      linkedFeatureId: 'purvanchal',
    },
    {
      id: 'f5',
      text: 'Mizoram lies almost entirely within the Mizo Hills, part of the Patkai\u2013Arakan Yoma system. Phawngpui (Blue Mountain), 2,157 m, is the highest peak in Mizoram. About 90% of the state is hilly terrain.',
      linkedFeatureId: 'phawngpui',
    },
    {
      id: 'f6',
      text: 'The Northern Plains were formed by alluvial deposits from the Indus, Ganga, and Brahmaputra systems filling a depression between the rising Himalayas and the old Peninsular block. The plain is ~2,400 km long and 240\u2013320 km wide.',
      linkedLayerId: 'northern-plains',
    },
    {
      id: 'f7',
      text: 'The Northern Plains are divided into four sub-belts from north to south: Bhabar (8\u201316 km pebble belt at Shiwalik foot \u2014 rivers go underground), Tarai (marshy, very fertile \u2014 Corbett & Kaziranga are here), Bhangar (older alluvium with calcareous "kankar" nodules), and Khadar (newer alluvium, flooded yearly, most fertile).',
      linkedLayerId: 'plains-subdivisions',
    },
    {
      id: 'f8',
      text: 'The Peninsular Plateau is India\u2019s oldest landmass \u2014 part of the ancient Gondwana supercontinent. It is geologically stable, rich in minerals, and triangular in shape, bounded by the Aravallis (NW), Vindhya-Satpura (N), Western Ghats (W), and Eastern Ghats (E).',
      linkedLayerId: 'peninsular-plateau',
    },
    {
      id: 'f9',
      text: 'The Peninsular Plateau has two major sub-regions: the Central Highlands (north of the Narmada \u2014 Malwa, Bundelkhand, Chotanagpur plateaus) and the Deccan Plateau (south of the Narmada, the larger half).',
      linkedLayerId: 'peninsular-plateau',
    },
    {
      id: 'f10',
      text: 'The Thar Desert (Indian Desert) lies west of the Aravallis, mostly in western Rajasthan. It receives less than 250 mm of rain a year, has shifting sand dunes (barchans), and an underground stream system fed by the now-vanished Ghaggar-Hakra (ancient Saraswati) river.',
      linkedLayerId: 'indian-desert',
    },
    {
      id: 'f11',
      text: 'The Western Coastal Plain is narrow (50\u2013100 km), faces the Arabian Sea, and is divided into Konkan (north), Kanara (middle), and Malabar (south). The Western Ghats rise sharply behind it.',
      linkedLayerId: 'coastal-plains',
      linkedFeatureId: 'western-coastal-plain',
    },
    {
      id: 'f12',
      text: 'The Eastern Coastal Plain is wider (100\u2013130 km), faces the Bay of Bengal, and is divided into Northern Circars (north) and Coromandel (south). All major peninsular rivers \u2014 Mahanadi, Godavari, Krishna, Kaveri \u2014 form deltas here.',
      linkedLayerId: 'coastal-plains',
      linkedFeatureId: 'eastern-coastal-plain',
    },
    {
      id: 'f13',
      text: 'The Andaman & Nicobar Islands (Bay of Bengal) are of volcanic/tectonic origin \u2014 a southward continuation of the Arakan Yoma. They are separated from each other by the 10\u00b0 Channel. Saddle Peak (737 m) in North Andaman is their highest point. Barren Island is the only active volcano in India.',
      linkedLayerId: 'islands',
      linkedFeatureId: 'andaman-nicobar',
    },
    {
      id: 'f14',
      text: 'The Lakshadweep Islands (Arabian Sea) are coral atolls formed over volcanic seamounts of the Reunion Hotspot. They include around 36 islands; Kavaratti is the capital. They are flat and low-lying \u2014 highly vulnerable to sea-level rise.',
      linkedLayerId: 'islands',
      linkedFeatureId: 'lakshadweep',
    },
    {
      id: 'f15',
      text: 'Highest peaks to remember: Kanchenjunga (8,586 m) is the highest peak entirely within India (Sikkim). Anaimudi (2,695 m) is the highest in Peninsular India (Kerala). Guru Shikhar (1,722 m) is the highest in the Aravallis. Phawngpui (2,157 m) is the highest in Mizoram. K2 (8,611 m) lies in PoK \u2014 administered by Pakistan, claimed by India.',
      linkedLayerId: 'key-peaks',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Which of the six physiographic divisions of India is the geologically oldest?',
      options: [
        'The Himalayan Mountains',
        'The Northern Plains',
        'The Peninsular Plateau',
        'The Coastal Plains',
      ],
      answerIndex: 2,
      explanation: 'The Peninsular Plateau is part of the ancient Gondwana supercontinent \u2014 it is India\u2019s oldest and most stable landmass. The Himalayas and the Northern Plains are the youngest.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click the location of Phawngpui (Blue Mountain), the highest peak in Mizoram.',
      answer: { lat: 22.6333, lng: 93.0167, toleranceKm: 150 },
      explanation: 'Phawngpui (2,157 m) lies in southeastern Mizoram, near the Myanmar border. It is part of the Mizo Hills, which belong to the Patkai\u2013Arakan Yoma system of the Purvanchal Range.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Which sub-belt of the Northern Plains is characterized by pebble beds where rivers descending from the Himalayas disappear underground?',
      options: ['Bhangar', 'Khadar', 'Tarai', 'Bhabar'],
      answerIndex: 3,
      explanation: 'Bhabar is the 8\u201316 km wide pebble belt at the foot of the Shiwaliks. The pebble beds are so porous that streams sink and flow underground. They re-emerge in the Tarai belt just to the south.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'The Andaman & Nicobar Islands are best described as:',
      options: [
        'Coral atolls formed over volcanic seamounts',
        'A southward extension of the Arakan Yoma mountains, of volcanic/tectonic origin',
        'A continental shelf detached from the Peninsular Plateau',
        'Sediment islands built up by the Brahmaputra delta',
      ],
      answerIndex: 1,
      explanation: 'The Andaman & Nicobar Islands are a southward continuation of the Arakan Yoma (which in turn extends from the Purvanchal). They are of volcanic/tectonic origin. Barren Island is India\u2019s only active volcano. Lakshadweep \u2014 the other island group \u2014 is the coral one.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click anywhere in the Thar Desert.',
      answer: { lat: 27.0, lng: 71.5, toleranceKm: 280 },
      explanation: 'The Thar Desert lies in western Rajasthan, west of the Aravalli range. It receives less than 250 mm of rainfall a year and is the only true desert in India.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Which is the highest peak entirely within Indian territory?',
      options: ['Mt. Everest', 'K2', 'Kanchenjunga', 'Nanda Devi'],
      answerIndex: 2,
      explanation: 'Kanchenjunga (8,586 m) in Sikkim. Everest is in Nepal/China. K2 (8,611 m) is in Pakistan-administered Kashmir \u2014 claimed by India but not under Indian administration. Nanda Devi (7,816 m) is the highest peak entirely within India\u2019s undisputed territory in the mainland but Kanchenjunga is taller.',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click the location of Kanchenjunga, the highest peak entirely in India.',
      answer: { lat: 27.7025, lng: 88.1475, toleranceKm: 150 },
      explanation: 'Kanchenjunga lies on the Sikkim\u2013Nepal border in the Greater Himalayas (Himadri). At 8,586 m it is the third-highest mountain in the world.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'The Western Coastal Plain differs from the Eastern Coastal Plain in that:',
      options: [
        'The Western is wider and has major river deltas',
        'The Eastern is narrower and faces the Arabian Sea',
        'The Western is narrower (50\u2013100 km) and has fewer deltas; the Eastern is wider (100\u2013130 km) with major deltas of the Mahanadi, Godavari, Krishna and Kaveri',
        'They are identical in width and drainage',
      ],
      answerIndex: 2,
      explanation: 'The Western Coastal Plain is narrow and steep (Western Ghats rise sharply behind it); rivers cross it quickly into the Arabian Sea without forming large deltas. The Eastern Coastal Plain is wider and gentler, allowing the Mahanadi, Godavari, Krishna, and Kaveri to all build large deltas before reaching the Bay of Bengal.',
    },
  ],
};

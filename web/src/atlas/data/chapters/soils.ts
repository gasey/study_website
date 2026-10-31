import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// SOILS OF INDIA
//
// Concept:
//   Soil = parent rock + climate + time. India's 8 ICAR
//   soil types map almost perfectly onto geology + rainfall:
//   Deccan basalt + monsoon = black cotton soil. Crystalline
//   Peninsular rock + low rain = red soil. Wet tropical
//   weathering = laterite. River alluvium = the Northern
//   Plains' bread basket.
//
// ICAR (Indian Council of Agricultural Research) classifies
// Indian soils into 8 major groups. Source cross-checked
// across NextIAS, Vajiram, Testbook, AgriDots.
// ============================================

// ---------- Soil region polygons (approximate, educational) ----------

const alluvialSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'alluvial-igp', name: 'Alluvial \u2014 Indo-Gangetic-Brahmaputra Plains' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [74.0, 31.5], [78.0, 30.0], [83.0, 28.5], [87.0, 27.0],
          [89.0, 26.5], [92.0, 26.5], [92.0, 24.5], [88.0, 24.0],
          [84.0, 24.5], [78.0, 25.5], [74.5, 27.5], [74.0, 31.5],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'alluvial-east-delta', name: 'Alluvial \u2014 Eastern Coastal Deltas' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [85.5, 21.0], [87.0, 20.5], [86.5, 18.0], [83.0, 16.5],
          [80.5, 14.0], [79.5, 11.0], [78.5, 9.5], [79.8, 11.0],
          [81.0, 13.0], [83.5, 16.5], [85.5, 21.0],
        ]],
      },
    },
  ],
};

const blackSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'black-deccan', name: 'Black Cotton Soil (Regur) \u2014 Deccan basalt zone' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [72.5, 22.5], [76.0, 22.5], [79.5, 22.0], [82.0, 20.5],
          [80.0, 18.0], [77.0, 16.5], [74.0, 17.0], [73.0, 19.0],
          [72.5, 22.5],
        ]],
      },
    },
  ],
};

const redSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'red-east', name: 'Red & Yellow Soil \u2014 Eastern Peninsula' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [82.0, 22.0], [86.5, 23.0], [87.0, 20.5], [85.5, 17.5],
          [82.5, 16.0], [80.0, 17.0], [81.0, 19.5], [82.0, 22.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'red-south', name: 'Red Soil \u2014 Tamil Nadu, Karnataka, AP interior' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [76.5, 15.5], [80.0, 15.0], [80.5, 12.5], [79.5, 10.0],
          [77.5, 9.0], [76.5, 11.0], [76.5, 15.5],
        ]],
      },
    },
  ],
};

const lateriteSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'laterite-wghats', name: 'Laterite \u2014 Western Ghats summit/slopes' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [74.0, 16.0], [75.0, 15.5], [76.5, 12.0], [77.0, 8.5],
          [76.0, 8.5], [75.0, 11.5], [73.5, 15.5], [74.0, 16.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'laterite-eghats', name: 'Laterite \u2014 Eastern Ghats & Odisha' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [83.5, 20.5], [85.5, 20.5], [85.5, 18.5], [83.5, 18.5], [83.5, 20.5],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'laterite-ne', name: 'Laterite \u2014 NE Hills (incl. Mizoram, Meghalaya)' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [91.0, 26.0], [94.0, 26.0], [94.0, 22.5], [91.5, 22.5], [91.0, 26.0],
        ]],
      },
    },
  ],
};

const aridSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'arid-thar', name: 'Arid / Desert Soil \u2014 Thar' },
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

const mountainSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'mountain-himalaya', name: 'Mountain / Forest Soil \u2014 Himalayas' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [74.0, 33.5], [78.0, 31.5], [82.0, 31.0], [88.0, 28.5],
          [93.0, 28.5], [96.0, 29.0], [95.0, 30.5], [88.0, 29.5],
          [82.0, 31.5], [76.0, 34.0], [74.0, 33.5],
        ]],
      },
    },
  ],
};

const peatySoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'peaty-kuttanad', name: 'Peaty / Marshy \u2014 Kuttanad (Kerala)' },
      geometry: {
        type: 'Point',
        coordinates: [76.4070, 9.4980],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'peaty-sundarbans', name: 'Peaty / Marshy \u2014 Sundarbans' },
      geometry: {
        type: 'Point',
        coordinates: [88.9000, 21.9500],
      },
    },
  ],
};

const salineSoil: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'saline-rann', name: 'Saline / Alkaline \u2014 Rann of Kachchh' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [68.5, 24.5], [71.0, 24.5], [71.5, 23.5], [68.5, 23.0], [68.5, 24.5],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'saline-up', name: 'Saline patches \u2014 Western UP / Punjab (Reh / Kallar)' },
      geometry: {
        type: 'Point',
        coordinates: [77.5, 28.5],
      },
    },
  ],
};

// ---------- Chapter ----------

export const soilsChapter: Chapter = {
  id: 'soils-of-india',
  subject: 'geography',
  unit: 'India Physical',
  tags: ['northern-plains', 'peninsular-plateau', 'deccan', 'thar', 'western-ghats'],
  title: 'Soils of India',
  summary: 'The eight major soil types of India and the geology, climate, and crops they dictate.',
  focus:
    'Soil is parent rock plus climate plus time. India\u2019s 8 ICAR soil types match almost perfectly onto geology and rainfall \u2014 and they decide what grows where.',

  view: { center: [22.5, 80.0], zoom: 5 },
  basemap: 'physical',

  layers: [
    {
      id: 'alluvial',
      name: 'Alluvial Soil (~43% of India)',
      description: 'Largest soil type. River deposits in IGP + deltas. K-rich, N-poor. Rice, wheat, sugarcane.',
      kind: 'vector',
      data: alluvialSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#7a8a3a', fillColor: '#c5d086', fillOpacity: 0.55, weight: 1.5 },
    },
    {
      id: 'black',
      name: 'Black (Regur) Soil',
      description: 'From weathered Deccan basalt. Montmorillonite clay. Self-ploughing. Ideal for cotton.',
      kind: 'vector',
      data: blackSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#222', fillColor: '#3a3a3a', fillOpacity: 0.55, weight: 1.5 },
    },
    {
      id: 'red',
      name: 'Red & Yellow Soil',
      description: 'From crystalline igneous rock. Iron oxide gives the colour. Millets, groundnut, pulses.',
      kind: 'vector',
      data: redSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#8a3a3a', fillColor: '#c47a5a', fillOpacity: 0.5, weight: 1.5 },
    },
    {
      id: 'laterite',
      name: 'Laterite Soil',
      description: 'High temperature + heavy rain + leaching. Tea, coffee, cashew, rubber.',
      kind: 'vector',
      data: lateriteSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#c46a3d', fillColor: '#e8985a', fillOpacity: 0.5, weight: 1.5, pattern: 'dots' },
    },
    {
      id: 'arid',
      name: 'Arid / Desert Soil',
      description: 'Sandy, saline, low organic content. Thar.',
      kind: 'vector',
      data: aridSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#c4a06a', fillColor: '#e8c590', fillOpacity: 0.5, weight: 1.5 },
    },
    {
      id: 'mountain',
      name: 'Mountain / Forest Soil',
      description: 'Shallow, immature. Himalayas + NE hills.',
      kind: 'vector',
      data: mountainSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#5e4a8a', fillColor: '#9b8ac4', fillOpacity: 0.4, weight: 1.5 },
    },
    {
      id: 'peaty',
      name: 'Peaty / Marshy Soil',
      description: 'High organic matter. Kuttanad (Kerala, below sea level), Sundarbans.',
      kind: 'vector',
      data: peatySoil,
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'saline',
      name: 'Saline / Alkaline Soil',
      description: 'Salt accumulation. Reh / Kallar / Usar. Rann of Kachchh + arid irrigated patches.',
      kind: 'vector',
      data: salineSoil,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#7a8a8a', fillColor: '#c5d0d0', fillOpacity: 0.5, weight: 1.5 },
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'The Indian Council of Agricultural Research (ICAR) classifies Indian soils into 8 major groups: Alluvial, Black, Red & Yellow, Laterite, Arid/Desert, Mountain/Forest, Peaty/Marshy, and Saline/Alkaline. Soil formation depends on CLORPT \u2014 Climate, Living organisms, Original parent material, Relief, and Time.',
    },
    {
      id: 'f2',
      text: 'Alluvial soil is India\u2019s largest soil group, covering about 43% of the country. Found in the Indo-Gangetic-Brahmaputra Plains and along the eastern coastal deltas. Rich in potash (K) and lime, deficient in nitrogen (N) and humus.',
      linkedLayerId: 'alluvial',
    },
    {
      id: 'f3',
      text: 'Alluvial soils have two sub-types matching the Northern Plains belts: Khadar (newer alluvium, in flood plains, very fertile, replenished yearly) and Bhangar (older alluvium, terrace tops, contains "kankar" calcareous nodules, less fertile).',
      linkedLayerId: 'alluvial',
    },
    {
      id: 'f4',
      text: 'Black soil (locally Regur) formed from weathering of Deccan basalt lava flows. It contains montmorillonite clay, which makes it "self-ploughing" \u2014 it shrinks and cracks deeply when dry, then swells when wet, mixing itself. Highly water-retentive. Ideal for cotton.',
      linkedLayerId: 'black',
    },
    {
      id: 'f5',
      text: 'Black soil distribution: Maharashtra (the largest spread), Madhya Pradesh, Gujarat, northern Karnataka, parts of Andhra Pradesh and Tamil Nadu. Crops: cotton (its main association), soybean, jowar, oilseeds, pulses. Rich in lime, iron, magnesia; poor in nitrogen and phosphorus.',
      linkedLayerId: 'black',
    },
    {
      id: 'f6',
      text: 'Red & Yellow soils form from weathering of crystalline igneous rocks in low-rainfall regions. The colour comes from iron oxide (red when dehydrated, yellow when hydrated). Found in the eastern and southern Peninsular Plateau: Odisha, Chhattisgarh, Jharkhand, parts of AP, Karnataka, Tamil Nadu. Generally low fertility \u2014 needs fertiliser to be productive. Crops: millets, groundnut, potato, pulses.',
      linkedLayerId: 'red',
    },
    {
      id: 'f7',
      text: 'Laterite soil forms in regions with high temperature AND heavy seasonal rainfall \u2014 the alternation between wet and dry causes severe leaching of silica, leaving behind iron and aluminium oxides (gives the brick-red colour). Found on: Western Ghats summit, parts of Eastern Ghats and Odisha, Northeast hills (including Mizoram and Meghalaya).',
      linkedLayerId: 'laterite',
    },
    {
      id: 'f8',
      text: 'Laterite soils are typically acidic and low in nutrients but are valuable for plantation crops that don\u2019t need fertile soil: tea, coffee, cashew, rubber. Karnataka and Kerala laterite zones are famous for coffee, cashew, and spice plantations.',
      linkedLayerId: 'laterite',
    },
    {
      id: 'f9',
      text: 'Arid (Desert) soils cover western Rajasthan and adjoining Gujarat. Sandy, low in organic matter, often saline. High phosphate content but very low nitrogen. With irrigation (Indira Gandhi Canal) parts have become productive for wheat, barley, and cotton.',
      linkedLayerId: 'arid',
    },
    {
      id: 'f10',
      text: 'Mountain (Forest) soils occupy the Himalayan slopes and the NE hills. They are shallow, immature, and stony \u2014 humus-rich on forest floors, less developed on bare slopes. Mizoram\u2019s steep terrain bears mostly thin mountain/forest soils overlying laterite, supporting bamboo and evergreen forests but limiting settled agriculture.',
      linkedLayerId: 'mountain',
    },
    {
      id: 'f11',
      text: 'Peaty/Marshy soils form in waterlogged areas with high organic accumulation. India\u2019s classic example is Kuttanad in Kerala \u2014 a region farmed mostly *below* sea level, where rice is grown on reclaimed wetland. The Sundarbans delta also has peaty soils mixed with saline mud.',
      linkedLayerId: 'peaty',
    },
    {
      id: 'f12',
      text: 'Saline/Alkaline soils (locally Reh, Kallar, or Usar) develop where salts accumulate at the surface \u2014 typically in arid regions with poor drainage, or in over-irrigated areas where rising groundwater brings salts up by capillary action. Found in the Rann of Kachchh and patches of western UP, Punjab, and Haryana.',
      linkedLayerId: 'saline',
    },
    {
      id: 'f13',
      text: 'Reclamation of saline soils: gypsum application (replaces Na\u207a with Ca\u00b2\u207a), improved drainage, and leaching with fresh water. The Central Soil Salinity Research Institute at Karnal leads this work.',
      linkedLayerId: 'saline',
    },
    {
      id: 'f14',
      text: 'Mizoram-specific: the state\u2019s steep terrain and heavy rainfall produce extensive lateritic and mountain/forest soils. Combined with jhum (shifting cultivation), erosion is a major concern. Terrace farming on contour lines is increasingly used to retain soil and water on the slopes.',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Which soil type is India\u2019s most extensive, covering about 43% of the land area?',
      options: ['Black (Regur)', 'Red & Yellow', 'Alluvial', 'Laterite'],
      answerIndex: 2,
      explanation: 'Alluvial soil covers the entire Indo-Gangetic-Brahmaputra Plains and the eastern coastal deltas \u2014 about 43% of India and the source of over 60% of food production.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Black cotton soil (Regur) gets its self-ploughing property from:',
      options: [
        'A high sand content that prevents compaction',
        'Montmorillonite clay that shrinks deeply on drying and swells on wetting',
        'High organic matter from forest litter',
        'Iron oxide that contracts in sunlight',
      ],
      answerIndex: 1,
      explanation: 'Montmorillonite clay is the key. When dry, the soil cracks 1 m+ deep, and surface material falls in. When wet, the clay swells shut, mixing the soil. The soil tills itself.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click anywhere in the main black cotton soil belt.',
      answer: { lat: 20.0, lng: 76.0, toleranceKm: 350 },
      explanation: 'The black soil belt centres on Maharashtra (the largest spread) and extends into MP, Gujarat, and northern Karnataka \u2014 exactly the Deccan basalt zone. Its weathering produced the soil.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Laterite soil is best suited for which group of crops?',
      options: [
        'Wheat and sugarcane',
        'Cotton and soybean',
        'Tea, coffee, cashew, and rubber',
        'Rice and jute',
      ],
      answerIndex: 2,
      explanation: 'Laterite is acidic, leached of nutrients, and not suited for grains. But it works very well for plantation crops that tolerate poor soil and need warm, wet conditions \u2014 tea, coffee, cashew, rubber.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'Mizoram\u2019s dominant soil types are best described as:',
      options: [
        'Alluvial and saline',
        'Black cotton soil',
        'Lateritic and mountain/forest soils',
        'Arid desert soil',
      ],
      answerIndex: 2,
      explanation: 'Mizoram\u2019s combination of steep hilly terrain and very heavy monsoon rainfall produces lateritic soil on weathered slopes and shallow mountain/forest soil over the hill ranges \u2014 acidic, low in nutrients, but supports rich evergreen forest cover.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'What is the most common technique used to reclaim saline/alkaline soils?',
      options: [
        'Adding urea',
        'Application of gypsum and improved drainage',
        'Burning the topsoil',
        'Heavy ploughing to expose subsoil',
      ],
      answerIndex: 1,
      explanation: 'Gypsum (calcium sulphate) replaces the harmful sodium ions in the soil with calcium ions, which leach away. Combined with better drainage and leaching, it restores fertility. CSSRI Karnal leads this research.',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click the Kuttanad region \u2014 famous for peaty/marshy soil and rice farming below sea level.',
      answer: { lat: 9.50, lng: 76.41, toleranceKm: 100 },
      explanation: 'Kuttanad lies in central Kerala, around the backwaters of Vembanad Lake. Much of it is below sea level. Rice is cultivated on reclaimed wetland \u2014 unique within India.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Which factor is NOT one of the five soil-forming factors (CLORPT)?',
      options: ['Climate', 'Living organisms', 'Latitude', 'Parent material'],
      answerIndex: 2,
      explanation: 'CLORPT = Climate, Living organisms, Original parent material, Relief, and Time. Latitude affects climate, but it isn\u2019t one of the five factors directly. Topography/relief is.',
    },
  ],
};

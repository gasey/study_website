import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// MOUNTAINS & PASSES OF INDIA
//
// Concept:
//   India\u2019s mountains tell two stories. The Himalayas (young
//   fold mountains, still rising) define the north; the
//   Peninsular ranges (ancient, weathered) hem in the Deccan.
//   Mountain passes are where geography meets geopolitics:
//   wars, trade, pilgrimage, and modern strategy converge
//   on a few high notches in the rock.
//
// Sources cross-checked: TestBook, Vajiram, StudyIQ, PMF IAS,
// Wikipedia on individual passes.
// ============================================

const himalayanRanges: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'trans-himalaya', name: 'Trans-Himalayas (Karakoram, Ladakh, Zaskar, Kailash)' },
      geometry: {
        type: 'LineString',
        coordinates: [[76.0, 35.5], [78.0, 35.0], [80.5, 34.5], [82.0, 32.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'himadri', name: 'Himadri / Greater Himalayas (highest, >6000 m)' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.0, 33.5], [77.5, 32.0], [81.0, 31.0], [85.0, 29.0], [88.0, 28.0], [92.5, 29.0], [95.5, 29.0]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'himachal', name: 'Himachal / Lesser Himalayas (3500\u20134500 m)' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.2, 32.9], [77.5, 31.3], [81.0, 30.4], [85.0, 28.4], [88.5, 27.5], [92.5, 28.0]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'shiwaliks', name: 'Shiwaliks / Outer Himalayas (900\u20131100 m)' },
      geometry: {
        type: 'LineString',
        coordinates: [[74.5, 32.4], [77.5, 30.7], [81.0, 29.8], [85.0, 27.8], [88.5, 26.9], [92.0, 27.3]],
      },
    },
  ],
};

const peninsularRanges: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'wghats', name: 'Western Ghats / Sahyadri (UNESCO WHS)' },
      geometry: {
        type: 'LineString',
        coordinates: [[73.0, 21.0], [73.5, 19.0], [74.5, 16.0], [75.5, 12.0], [77.0, 8.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'eghats', name: 'Eastern Ghats (broken hill ranges)' },
      geometry: {
        type: 'LineString',
        coordinates: [[86.0, 21.5], [84.5, 19.5], [83.0, 18.0], [81.5, 15.5], [80.0, 13.5], [78.5, 11.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'aravalli', name: 'Aravalli Range (one of the world\u2019s oldest, ~1.7 bn yrs)' },
      geometry: {
        type: 'LineString',
        coordinates: [[72.7, 24.6], [73.8, 25.5], [75.5, 26.5], [77.0, 28.0], [77.2, 28.7]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'vindhya', name: 'Vindhya Range (divides N and S India)' },
      geometry: {
        type: 'LineString',
        coordinates: [[73.5, 22.5], [76.0, 23.5], [79.0, 24.0], [82.5, 24.5], [85.0, 24.0]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'satpura', name: 'Satpura Range (south of Vindhyas, between Narmada & Tapi)' },
      geometry: {
        type: 'LineString',
        coordinates: [[73.5, 21.5], [76.5, 22.0], [79.0, 22.3], [81.5, 22.5], [83.5, 22.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'purvanchal-r', name: 'Purvanchal (Patkai\u2013Naga\u2013Manipur\u2013Mizo\u2013Tripura Hills)' },
      geometry: {
        type: 'LineString',
        coordinates: [[95.5, 28.0], [95.0, 26.5], [94.5, 25.0], [93.5, 23.5], [92.8, 22.5], [91.5, 23.5]],
      },
    },
  ],
};

const keyPeaks: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'k2', name: 'K2 / Godwin Austen (8611 m) \u2014 PoK, Karakoram' }, geometry: { type: 'Point', coordinates: [76.5133, 35.8825] } },
    { type: 'Feature', properties: { id: 'kanchenjunga', name: 'Kanchenjunga (8586 m) \u2014 highest peak entirely in India, Sikkim' }, geometry: { type: 'Point', coordinates: [88.1475, 27.7025] } },
    { type: 'Feature', properties: { id: 'nanda-devi', name: 'Nanda Devi (7816 m) \u2014 Uttarakhand' }, geometry: { type: 'Point', coordinates: [79.9707, 30.3760] } },
    { type: 'Feature', properties: { id: 'kamet', name: 'Kamet (7756 m) \u2014 Uttarakhand' }, geometry: { type: 'Point', coordinates: [79.5933, 30.9200] } },
    { type: 'Feature', properties: { id: 'anaimudi', name: 'Anaimudi (2695 m) \u2014 highest in Peninsular India, Kerala' }, geometry: { type: 'Point', coordinates: [77.0600, 10.1700] } },
    { type: 'Feature', properties: { id: 'doddabetta', name: 'Doddabetta (2637 m) \u2014 Nilgiris, Tamil Nadu' }, geometry: { type: 'Point', coordinates: [76.7400, 11.4000] } },
    { type: 'Feature', properties: { id: 'mahendragiri', name: 'Mahendragiri (1501 m) \u2014 Eastern Ghats, Odisha' }, geometry: { type: 'Point', coordinates: [84.3833, 18.9667] } },
    { type: 'Feature', properties: { id: 'guru-shikhar', name: 'Guru Shikhar (1722 m) \u2014 highest in Aravallis, Rajasthan' }, geometry: { type: 'Point', coordinates: [72.7100, 24.6600] } },
    { type: 'Feature', properties: { id: 'phawngpui', name: 'Phawngpui / Blue Mountain (2157 m) \u2014 highest in Mizoram' }, geometry: { type: 'Point', coordinates: [92.8333, 23.1667] } },
    { type: 'Feature', properties: { id: 'dhupgarh', name: 'Dhupgarh (1350 m) \u2014 highest in Satpura, MP' }, geometry: { type: 'Point', coordinates: [78.4300, 22.4700] } },
  ],
};

const himalayanPasses: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'karakoram-pass', name: 'Karakoram Pass (5540 m, Ladakh) \u2014 India\u2013China, ancient Silk Route' }, geometry: { type: 'Point', coordinates: [77.8167, 35.5167] } },
    { type: 'Feature', properties: { id: 'khardung-la', name: 'Khardung La (5359 m, Ladakh) \u2014 gateway to Nubra Valley' }, geometry: { type: 'Point', coordinates: [77.6047, 34.2778] } },
    { type: 'Feature', properties: { id: 'zoji-la', name: 'Zoji La (3580 m) \u2014 Srinagar to Leh (NH-1D); closed in winter' }, geometry: { type: 'Point', coordinates: [75.4719, 34.2789] } },
    { type: 'Feature', properties: { id: 'banihal', name: 'Banihal Pass (2832 m) \u2014 Jammu to Kashmir Valley; Jawahar Tunnel' }, geometry: { type: 'Point', coordinates: [75.1953, 33.4928] } },
    { type: 'Feature', properties: { id: 'rohtang', name: 'Rohtang Pass (3978 m, HP) \u2014 Manali to Lahaul-Spiti; Atal Tunnel beneath' }, geometry: { type: 'Point', coordinates: [77.2461, 32.3725] } },
    { type: 'Feature', properties: { id: 'shipki-la', name: 'Shipki La (3930 m, HP) \u2014 India\u2013Tibet, Satluj enters here' }, geometry: { type: 'Point', coordinates: [78.7500, 31.8167] } },
    { type: 'Feature', properties: { id: 'baralacha', name: 'Baralacha La (4890 m) \u2014 junction for Lahaul, Spiti, Zanskar, Ladakh' }, geometry: { type: 'Point', coordinates: [77.4422, 32.7567] } },
    { type: 'Feature', properties: { id: 'lipulekh', name: 'Lipulekh Pass (5334 m, Uttarakhand) \u2014 Kailash Mansarovar route' }, geometry: { type: 'Point', coordinates: [81.0167, 30.2333] } },
    { type: 'Feature', properties: { id: 'mana', name: 'Mana Pass (5610 m, Uttarakhand) \u2014 India\u2013Tibet' }, geometry: { type: 'Point', coordinates: [79.4500, 31.0833] } },
    { type: 'Feature', properties: { id: 'niti', name: 'Niti Pass (5070 m, Uttarakhand) \u2014 ancient Tibet trade route' }, geometry: { type: 'Point', coordinates: [79.8833, 30.7833] } },
    { type: 'Feature', properties: { id: 'nathu-la', name: 'Nathu La (4310 m, Sikkim) \u2014 India\u2013China trade reopened 2006' }, geometry: { type: 'Point', coordinates: [88.8333, 27.3833] } },
    { type: 'Feature', properties: { id: 'jelep-la', name: 'Jelep La (4267 m, Sikkim) \u2014 India\u2013Tibet' }, geometry: { type: 'Point', coordinates: [88.7333, 27.3667] } },
    { type: 'Feature', properties: { id: 'bomdi-la', name: 'Bomdi La (2217 m, Arunachal) \u2014 to Tawang and Lhasa' }, geometry: { type: 'Point', coordinates: [92.4167, 27.2667] } },
    { type: 'Feature', properties: { id: 'bum-la', name: 'Bum La Pass (4633 m, Arunachal) \u2014 Tawang to Tibet' }, geometry: { type: 'Point', coordinates: [91.7333, 27.7500] } },
    { type: 'Feature', properties: { id: 'diphu', name: 'Diphu Pass (4587 m, Arunachal) \u2014 India\u2013China\u2013Myanmar tripoint' }, geometry: { type: 'Point', coordinates: [97.1833, 28.1500] } },
    { type: 'Feature', properties: { id: 'umling-la', name: 'Umling La (5882 m, Ladakh) \u2014 highest motorable pass in the world' }, geometry: { type: 'Point', coordinates: [78.6167, 32.6167] } },
  ],
};

const ghatPasses: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'palghat', name: 'Palakkad Gap (~140 km wide) \u2014 main breach in Western Ghats; Kerala\u2013TN' }, geometry: { type: 'Point', coordinates: [76.6500, 10.7700] } },
    { type: 'Feature', properties: { id: 'thal-ghat', name: 'Thal Ghat \u2014 Mumbai to Nashik (Maharashtra)' }, geometry: { type: 'Point', coordinates: [73.5500, 19.7000] } },
    { type: 'Feature', properties: { id: 'bhor-ghat', name: 'Bhor Ghat \u2014 Mumbai to Pune' }, geometry: { type: 'Point', coordinates: [73.3500, 18.7500] } },
    { type: 'Feature', properties: { id: 'shenkottai', name: 'Shenkottai Pass \u2014 Tamil Nadu to Kerala' }, geometry: { type: 'Point', coordinates: [77.2700, 8.9700] } },
  ],
};

export const mountainsChapter: Chapter = {
  id: 'mountains-and-passes',
  subject: 'geography',
  unit: 'India Physical',
  tags: ['himalayas', 'aravalli', 'western-ghats', 'purvanchal', 'khyber', 'passes', 'mizo-hills', 'peninsular-plateau'],
  title: 'Mountains & Passes of India',
  summary: 'The young Himalayas, the ancient Peninsular ranges, and the strategic passes that connect India to the world.',
  focus:
    'India has two kinds of mountains: the young, still-rising Himalayas (and the Purvanchal\u2019s curve into Mizoram) and the ancient, eroded Peninsular ranges. Where these mountains have notches \u2014 the passes \u2014 trade, pilgrimage, war, and modern strategy converge.',

  view: { center: [25.0, 82.0], zoom: 5 },
  basemap: 'physical',

  layers: [
    {
      id: 'himalayan-ranges',
      name: 'Himalayan Ranges (4 parallel zones)',
      description: 'Trans-Himalayas (north) \u2014 Himadri \u2014 Himachal \u2014 Shiwaliks (south). Young fold mountains, still rising.',
      kind: 'vector',
      data: himalayanRanges,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#5e4a8a', weight: 3 },
    },
    {
      id: 'peninsular-ranges',
      name: 'Peninsular Ranges',
      description: 'Western Ghats, Eastern Ghats, Aravalli, Vindhya, Satpura, Purvanchal. Ancient, weathered, lower.',
      kind: 'vector',
      data: peninsularRanges,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#8a5a3a', weight: 2.5 },
    },
    {
      id: 'key-peaks',
      name: 'Key Peaks (memorize these)',
      description: 'Highest peaks by region \u2014 frequently tested.',
      kind: 'vector',
      data: keyPeaks,
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'himalayan-passes',
      name: 'Himalayan Passes',
      description: 'Strategic crossings: trade routes, pilgrimage, military.',
      kind: 'vector',
      data: himalayanPasses,
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'ghat-passes',
      name: 'Western/Eastern Ghats Passes',
      description: 'Gaps in the Peninsular ranges \u2014 small but economically vital.',
      kind: 'vector',
      data: ghatPasses,
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'India\u2019s mountains divide into two families: the young fold Himalayas in the north (still rising due to ongoing India-Eurasia collision) and the ancient block-mountain ranges of the Peninsula (worn down over hundreds of millions of years).',
    },
    {
      id: 'f2',
      text: 'The Himalayas have four parallel zones north-to-south: (1) Trans-Himalayas \u2014 Karakoram, Ladakh, Zaskar (cold desert, K2 is here); (2) Himadri / Greater Himalayas \u2014 highest range, >6,000 m, contains Everest, Kanchenjunga, Nanda Devi; (3) Himachal / Lesser Himalayas \u2014 3,500\u20134,500 m, hill stations; (4) Shiwaliks / Outer Himalayas \u2014 youngest, 900\u20131,100 m, formed from river sediments.',
      linkedLayerId: 'himalayan-ranges',
    },
    {
      id: 'f3',
      text: 'The Himalayas run ~2,400 km from the Indus gorge in the west to the Brahmaputra gorge in the east. They are wider in the west (~400 km in Kashmir) and narrower in the east (~150 km in Arunachal). Beyond the Dihang/Brahmaputra gorge, they curve south as the Purvanchal Ranges.',
      linkedLayerId: 'himalayan-ranges',
    },
    {
      id: 'f4',
      text: 'The Purvanchal is the southward curve of the Himalayan system after the Dihang gorge \u2014 Patkai, Naga, Manipur, Mizo (Lushai), Tripura Hills. They run north\u2013south (unlike the Himalayas which run east\u2013west). The Mizo Hills, in which all of Mizoram lies, are part of this system.',
      linkedLayerId: 'peninsular-ranges',
      linkedFeatureId: 'purvanchal-r',
    },
    {
      id: 'f5',
      text: 'Peninsular ranges (oldest first): The Aravalli (~1.7 billion years old, one of the oldest mountain ranges on Earth) runs NE-SW through Rajasthan; Guru Shikhar (1722 m) is the highest point. The Vindhya and Satpura ranges divide North from South India and frame the Narmada rift valley between them.',
      linkedLayerId: 'peninsular-ranges',
    },
    {
      id: 'f6',
      text: 'The Western Ghats (Sahyadri) run ~1,600 km along the west coast, with the Arabian Sea on one side and the Deccan Plateau on the other. They are a UNESCO World Heritage Site and one of the world\u2019s eight "hottest" biodiversity hotspots. Highest peak: Anaimudi (2,695 m) in Kerala \u2014 the highest in Peninsular India.',
      linkedLayerId: 'peninsular-ranges',
      linkedFeatureId: 'wghats',
    },
    {
      id: 'f7',
      text: 'The Eastern Ghats are NOT continuous \u2014 they are broken into discontinuous hill groups by the great east-flowing rivers (Mahanadi, Godavari, Krishna, Kaveri). They are lower, older, and more eroded than the Western Ghats. Highest peak: Mahendragiri (1,501 m) in Odisha.',
      linkedLayerId: 'peninsular-ranges',
      linkedFeatureId: 'eghats',
    },
    {
      id: 'f8',
      text: 'Highest peak quick reference: K2 (8,611 m) \u2014 PoK, claimed by India. Kanchenjunga (8,586 m) \u2014 highest peak ENTIRELY within India. Nanda Devi (7,816 m) \u2014 second-highest entirely in India\u2019s undisputed territory. Anaimudi (2,695 m) \u2014 highest in Peninsular India. Phawngpui (2,157 m) \u2014 highest in Mizoram and the entire Purvanchal.',
      linkedLayerId: 'key-peaks',
    },
    {
      id: 'f9',
      text: 'Karakoram Pass (5,540 m, Ladakh) connects India to China\u2019s Xinjiang \u2014 part of the ancient Silk Route. Zoji La (3,580 m) is the strategic pass on the Srinagar\u2013Leh highway, closed by snow in winter \u2014 a Zoji La tunnel is under construction for all-weather access.',
      linkedLayerId: 'himalayan-passes',
    },
    {
      id: 'f10',
      text: 'Rohtang Pass (3,978 m, Himachal Pradesh) connected Manali to Lahaul-Spiti seasonally. Today, the Atal Tunnel (opened 2020, 9.02 km) runs beneath it \u2014 once the world\u2019s longest highway tunnel above 10,000 ft \u2014 giving all-weather access to Leh.',
      linkedLayerId: 'himalayan-passes',
      linkedFeatureId: 'rohtang',
    },
    {
      id: 'f11',
      text: 'Nathu La (4,310 m, Sikkim) was reopened for limited India\u2013China border trade in 2006 after being closed since the 1962 war. Jelep La (next to Nathu La) was the historic route to Lhasa used by the British. Bomdi La and Bum La (Arunachal) lead to Tawang and Tibet.',
      linkedLayerId: 'himalayan-passes',
      linkedFeatureId: 'nathu-la',
    },
    {
      id: 'f12',
      text: 'Lipulekh Pass (5,334 m, Uttarakhand) is the traditional pilgrim route to Kailash-Mansarovar; the recent road extension to the pass triggered a 2020 border dispute with Nepal. Mana and Niti passes (also Uttarakhand) are old Tibet trade routes.',
      linkedLayerId: 'himalayan-passes',
    },
    {
      id: 'f13',
      text: 'Umling La (5,882 m, Ladakh) is the highest motorable pass in the world \u2014 constructed by the Border Roads Organisation. Khardung La (5,359 m) leads from Leh to the Nubra Valley and Siachen.',
      linkedLayerId: 'himalayan-passes',
    },
    {
      id: 'f14',
      text: 'Western Ghats passes: the Palakkad Gap is the largest breach (~140 km wide) and the main route between Kerala and Tamil Nadu \u2014 it shapes monsoon patterns by letting moist air through. Thal Ghat (Mumbai\u2013Nashik) and Bhor Ghat (Mumbai\u2013Pune) carry Maharashtra\u2019s busiest road and rail traffic.',
      linkedLayerId: 'ghat-passes',
    },
    {
      id: 'f15',
      text: 'Mizoram-specific: the Mizo Hills run north\u2013south through the state and continue south into Myanmar\u2019s Chin State as the Arakan Yoma. Phawngpui (Blue Mountain) at 2,157 m is the highest. Several smaller hill ranges \u2014 Tlawng Hill, Lurh Tlang, and others \u2014 give Mizoram its distinctive ridge-and-valley topography.',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Arrange the Himalayan ranges from NORTH to SOUTH:',
      options: [
        'Shiwaliks \u2192 Himachal \u2192 Himadri \u2192 Trans-Himalayas',
        'Trans-Himalayas \u2192 Himadri \u2192 Himachal \u2192 Shiwaliks',
        'Himachal \u2192 Trans-Himalayas \u2192 Himadri \u2192 Shiwaliks',
        'Himadri \u2192 Shiwaliks \u2192 Himachal \u2192 Trans-Himalayas',
      ],
      answerIndex: 1,
      explanation: 'From north to south: Trans-Himalayas (Karakoram, etc.) \u2192 Himadri / Greater Himalayas (highest) \u2192 Himachal / Lesser Himalayas (hill stations) \u2192 Shiwaliks / Outer Himalayas (youngest, lowest). The Shiwaliks are closest to the plains.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Why are the Eastern Ghats NOT continuous, unlike the Western Ghats?',
      options: [
        'They are blocked by deserts',
        'They are broken into segments by the great east-flowing rivers (Mahanadi, Godavari, Krishna, Kaveri)',
        'They were destroyed by ancient volcanoes',
        'They never formed continuously',
      ],
      answerIndex: 1,
      explanation: 'The east-flowing peninsular rivers cut through the Eastern Ghats on their way to the Bay of Bengal, breaking the range into discontinuous hill groups. The Western Ghats remain unbroken because most west-flowing rivers (except Narmada and Tapi) are short coastal streams.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click the location of Phawngpui (Blue Mountain) \u2014 highest peak in Mizoram and the Purvanchal range.',
      answer: { lat: 22.6333, lng: 92.8333, toleranceKm: 150 },
      explanation: 'Phawngpui (2,157 m) is in southeastern Mizoram, near the Myanmar border. It is the highest point in the entire Purvanchal range that stretches from Arunachal Pradesh down through Nagaland, Manipur, Mizoram, and Tripura.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Which pass connects Srinagar to Leh and is closed by snow most of winter?',
      options: ['Rohtang Pass', 'Zoji La', 'Nathu La', 'Karakoram Pass'],
      answerIndex: 1,
      explanation: 'Zoji La (3,580 m) is on the Srinagar\u2013Leh highway. It is among the most strategically important passes for India, and the Zoji La Tunnel (under construction) will make access all-weather.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click the location of the Palakkad Gap \u2014 the main breach in the Western Ghats.',
      answer: { lat: 10.77, lng: 76.65, toleranceKm: 120 },
      explanation: 'The Palakkad Gap (~140 km wide) is the largest break in the Western Ghats. It is the main route between Kerala and Tamil Nadu, and the gap also influences the monsoon \u2014 it lets moist air through to Tamil Nadu\u2019s western interior.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Which Aravalli peak is the highest, located in Rajasthan?',
      options: ['Anaimudi', 'Doddabetta', 'Guru Shikhar', 'Mahendragiri'],
      answerIndex: 2,
      explanation: 'Guru Shikhar (1,722 m) on Mount Abu is the highest peak in the Aravallis. Anaimudi is the highest in Peninsular India (Kerala). Doddabetta is in the Nilgiris. Mahendragiri is the highest in the Eastern Ghats.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'Which pass, reopened in 2006 for limited India\u2013China border trade, was previously closed after the 1962 war?',
      options: ['Nathu La', 'Bomdi La', 'Karakoram Pass', 'Bum La'],
      answerIndex: 0,
      explanation: 'Nathu La (4,310 m) in Sikkim was reopened to limited bilateral trade in July 2006 after a 44-year closure following the 1962 Indo-China war. It remains one of the highest border-trading posts in the world.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'The Atal Tunnel, opened in 2020, runs beneath which pass?',
      options: ['Zoji La', 'Rohtang Pass', 'Banihal Pass', 'Khardung La'],
      answerIndex: 1,
      explanation: 'The Atal Tunnel (9.02 km) runs beneath Rohtang Pass in Himachal Pradesh \u2014 giving Manali and Lahaul-Spiti all-weather connectivity that the snow-prone pass itself never had.',
    },
    {
      id: 'q9',
      type: 'map_click',
      question: 'Click the approximate location of Kanchenjunga \u2014 the highest peak entirely within India.',
      answer: { lat: 27.70, lng: 88.15, toleranceKm: 150 },
      explanation: 'Kanchenjunga (8,586 m) lies on the Sikkim\u2013Nepal border in the Greater Himalayas. It is the third-highest mountain in the world and the highest peak entirely within India\u2019s undisputed territory.',
    },
  ],
};

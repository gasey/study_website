import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// MAHAJANAPADAS \u2192 MAGADHA \u2192 MAURYAS
//
// Concept:
//   "Sixteen states enter, one leaves. Magadha\u2019s rise from
//   Rajgir to the Mauryan empire is the first unification of
//   India \u2014 and Kalinga is where conquest turned into Dhamma."
//
// Source: ANCIENT INDIAN HISTORY \u2014 Prelims (MS Academy) deck.
// ============================================

/** The 16 Mahajanapadas, placed at their capitals (approx). */
const mahajanapadas: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'magadha', name: 'Magadha \u2014 cap. Rajgir (Girivraja)' }, geometry: { type: 'Point', coordinates: [85.42, 25.03] } },
    { type: 'Feature', properties: { id: 'kosala', name: 'Kosala \u2014 cap. Shravasti' }, geometry: { type: 'Point', coordinates: [82.03, 27.52] } },
    { type: 'Feature', properties: { id: 'vatsa', name: 'Vatsa \u2014 cap. Kausambi' }, geometry: { type: 'Point', coordinates: [81.39, 25.34] } },
    { type: 'Feature', properties: { id: 'avanti', name: 'Avanti \u2014 cap. Ujjain' }, geometry: { type: 'Point', coordinates: [75.78, 23.18] } },
    { type: 'Feature', properties: { id: 'vajji', name: 'Vajji \u2014 cap. Vaishali (republican)' }, geometry: { type: 'Point', coordinates: [85.13, 25.99] } },
    { type: 'Feature', properties: { id: 'anga', name: 'Anga \u2014 cap. Champa' }, geometry: { type: 'Point', coordinates: [87.04, 25.24] } },
    { type: 'Feature', properties: { id: 'kashi', name: 'Kashi \u2014 cap. Varanasi' }, geometry: { type: 'Point', coordinates: [83.01, 25.32] } },
    { type: 'Feature', properties: { id: 'kuru', name: 'Kuru \u2014 cap. Indraprastha' }, geometry: { type: 'Point', coordinates: [77.24, 28.61] } },
    { type: 'Feature', properties: { id: 'panchala', name: 'Panchala \u2014 cap. Ahichchhatra / Kampilya' }, geometry: { type: 'Point', coordinates: [79.13, 28.37] } },
    { type: 'Feature', properties: { id: 'matsya', name: 'Matsya \u2014 cap. Viratanagara' }, geometry: { type: 'Point', coordinates: [76.18, 27.42] } },
    { type: 'Feature', properties: { id: 'shurasena', name: 'Shurasena \u2014 cap. Mathura' }, geometry: { type: 'Point', coordinates: [77.67, 27.5] } },
    { type: 'Feature', properties: { id: 'chedi', name: 'Chedi \u2014 cap. Shuktimati' }, geometry: { type: 'Point', coordinates: [80.33, 25.48] } },
    { type: 'Feature', properties: { id: 'malla', name: 'Malla \u2014 cap. Kushinara / Pava (republican)' }, geometry: { type: 'Point', coordinates: [83.89, 26.74] } },
    { type: 'Feature', properties: { id: 'gandhara', name: 'Gandhara \u2014 cap. Taxila' }, geometry: { type: 'Point', coordinates: [72.79, 33.74] } },
    { type: 'Feature', properties: { id: 'kamboja', name: 'Kamboja \u2014 far northwest' }, geometry: { type: 'Point', coordinates: [71.5, 34.5] } },
    { type: 'Feature', properties: { id: 'asmaka', name: 'Asmaka \u2014 on the Godavari (only southern one)' }, geometry: { type: 'Point', coordinates: [77.9, 18.67] } },
  ],
};

/** Magadha\u2019s two capitals + Kalinga. */
const keySites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'rajgir', name: 'Rajgir \u2014 first Magadhan capital' }, geometry: { type: 'Point', coordinates: [85.42, 25.03] } },
    { type: 'Feature', properties: { id: 'pataliputra', name: 'Pataliputra \u2014 imperial capital (Ganga confluence)' }, geometry: { type: 'Point', coordinates: [85.14, 25.61] } },
    { type: 'Feature', properties: { id: 'kalinga', name: 'Kalinga (Dhauli) \u2014 the war of 261 BC' }, geometry: { type: 'Point', coordinates: [85.84, 20.19] } },
    { type: 'Feature', properties: { id: 'taxila-m', name: 'Taxila \u2014 NW provincial capital, trade gateway' }, geometry: { type: 'Point', coordinates: [72.79, 33.74] } },
    { type: 'Feature', properties: { id: 'sanchi', name: 'Sanchi \u2014 Ashokan stupa' }, geometry: { type: 'Point', coordinates: [77.74, 23.48] } },
  ],
};

/** Very simplified Mauryan extent at Ashoka\u2019s peak. */
const mauryanExtent: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'maurya-extent', name: 'Mauryan Empire under Ashoka (except extreme south)' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [66.0, 25.0], [62.0, 29.5], [66.0, 34.0], [71.0, 36.5],
          [77.0, 35.5], [80.0, 30.5], [88.0, 27.5], [92.0, 26.0],
          [91.5, 22.5], [86.5, 20.0], [83.0, 17.0], [79.5, 13.5],
          [76.5, 13.0], [74.5, 16.0], [72.5, 20.0], [68.5, 22.5],
          [66.0, 25.0],
        ]],
      },
    },
  ],
};

export const mauryaChapter: Chapter = {
  id: 'mahajanapadas-mauryas',
  subject: 'history',
  unit: 'Ancient',
  tags: ['ganga', 'pataliputra', 'rajgir', 'vaishali', 'magadha', 'kalinga', 'taxila', 'bihar'],
  title: 'Mahajanapadas \u2192 Mauryas',
  summary: '16 states, the rise of Magadha, and Ashoka\u2019s empire of Dhamma.',
  focus:
    'Sixteen Mahajanapadas contested the Gangetic plain; Magadha absorbed them all. The Mauryan climax \u2014 and the moral pivot of Indian history \u2014 happened on the map at Kalinga, 261 BC.',
  view: { center: [24.5, 81.0], zoom: 5 },
  basemap: 'paper',
  theme: { accent: '#8a5a00', mapBg: '#f7f1e2', tileUrl: '' },

  layers: [
    {
      id: 'mahajanapadas',
      name: '16 Mahajanapadas (capitals)',
      kind: 'vector',
      data: mahajanapadas,
      style: { color: '#8a5a00', weight: 2, fillColor: '#c08a1a', fillOpacity: 0.9, shadow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'maurya-extent',
      name: 'Mauryan Empire (Ashoka)',
      kind: 'vector',
      data: mauryanExtent,
      style: { color: '#7a3b10', weight: 1.5, fillColor: '#c98a4b', fillOpacity: 0.2, pattern: 'hatch' },
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'key-sites',
      name: 'Capitals & Kalinga',
      kind: 'vector',
      data: keySites,
      style: { color: '#b3261e', weight: 2, fillColor: '#b3261e', fillOpacity: 0.9, shadow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'The 16 Mahajanapadas are listed in Buddhist and Jain literature; the period is called the Second Urbanisation, and silver/copper punch-marked coins appear. States were of two kinds: monarchical and republican. Vajji (Vaishali) was the most important republic; the Lichchhavis of Vaishali are called the first republic.',
      linkedLayerId: 'mahajanapadas',
    },
    {
      id: 'f2',
      text: 'The real contest was among four: Magadha, Kosala, Vatsa, and Avanti. Magadha (capital Rajgir) won \u2014 founded by Brihadratha/Jarasandha, its growth began under the Haryanka dynasty, expanded under the Shishunagas and Nandas, and peaked under the Mauryas.',
      linkedLayerId: 'mahajanapadas',
      linkedFeatureId: 'magadha',
    },
    {
      id: 'f3',
      text: 'Haryanka kings to remember: Bimbisara (matrimonial alliances, annexed Anga), Ajatashatru (war with Vajji, first Buddhist council patronage), Udayin (founded Pataliputra at the Ganga\u2013Son confluence \u2014 moving the capital from hill-ringed Rajgir to the river highway).',
      linkedLayerId: 'key-sites',
    },
    {
      id: 'f4',
      text: 'The Nandas (344\u2013323 BC) under Dhanananda were fabulously rich and unpopular \u2014 the empire Alexander\u2019s soldiers refused to face. Chandragupta Maurya (324/321\u2013297 BC), guided by Kautilya, overthrew them, then defeated Seleucus Nicator, gaining territories up to the Hindu Kush.',
    },
    {
      id: 'f5',
      text: 'Ashoka (273\u2013232 BC) ruled nearly the whole subcontinent except the extreme south \u2014 including Afghanistan, Baluchistan, Kashmir and the Nepal valleys. The Kalinga War (261 BC, 9th regnal year) converted him: from Bherighosha (drum of war) to Dhammaghosha (drum of righteousness). He embraced Buddhism under Upagupta and sent Mahendra and Sanghamitra to Ceylon with a Bodhi sapling.',
      linkedLayerId: 'key-sites',
      linkedFeatureId: 'kalinga',
    },
    {
      id: 'f6',
      text: 'Edicts cheat-sheet: Major Rock Edict XIII describes the Kalinga victory and names five Greek kings (Antiochus, Ptolemy, Magas, Antigonus, Alexander of Epirus); Edict IV = Dhammaghosha over Bherighosha; Edict II mentions the Pandyas, Cholas and Keralaputras plus medical care for humans and animals; Pillar Edict VII sums up Ashoka\u2019s Dhamma work.',
    },
    {
      id: 'f7',
      text: 'Ashoka\u2019s Dhamma was not a sect \u2014 it was a civic code: respect elders, mercy to slaves and servants, truth, non-violence, tolerance of all sects. Dhamma Mahamatras were a special cadre appointed to spread it (Rock Edict V).',
    },
  ],

  events: [
    {
      id: 'e1',
      date: '-0600',
      label: '16 states',
      description: '6th century BC: sixteen Mahajanapadas contest north India. Second urbanisation; punch-marked coins.',
      showLayers: ['mahajanapadas'],
      hideLayers: ['maurya-extent', 'key-sites'],
      view: { center: [25.5, 80.0], zoom: 5 },
    },
    {
      id: 'e2',
      date: '-0544',
      label: 'Haryanka rise',
      description: 'Bimbisara and Ajatashatru make Magadha supreme among the four great rivals (Kosala, Vatsa, Avanti fall in line). Udayin founds Pataliputra.',
      showLayers: ['mahajanapadas', 'key-sites'],
      hideLayers: ['maurya-extent'],
      view: { center: [25.4, 85.2], zoom: 7 },
    },
    {
      id: 'e3',
      date: '-0321',
      label: 'Chandragupta',
      description: 'Chandragupta Maurya, with Kautilya, topples Dhanananda; later defeats Seleucus Nicator and takes the northwest.',
      showLayers: ['key-sites', 'maurya-extent'],
      hideLayers: ['mahajanapadas'],
      view: { center: [27.0, 78.0], zoom: 5 },
    },
    {
      id: 'e4',
      date: '-0261',
      label: 'Kalinga War',
      description: 'Ashoka\u2019s 9th regnal year. The bloodbath at Kalinga turns conquest into Dhamma \u2014 Bherighosha to Dhammaghosha (Rock Edict XIII).',
      showLayers: ['maurya-extent', 'key-sites'],
      hideLayers: ['mahajanapadas'],
      view: { center: [20.2, 85.8], zoom: 7 },
    },
    {
      id: 'e5',
      date: '-0185',
      label: 'Dynasty ends',
      description: 'The last Maurya, Brihadratha, is assassinated by his general Pushyamitra Shunga. The first pan-Indian empire dissolves.',
      showLayers: ['maurya-extent'],
      hideLayers: ['mahajanapadas'],
      view: { center: [24.5, 81.0], zoom: 5 },
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Which four Mahajanapadas fought the final struggle for supremacy in the 6th\u20134th centuries BC?',
      options: [
        'Kashi, Anga, Kuru, Panchala',
        'Magadha, Kosala, Vatsa, Avanti',
        'Gandhara, Kamboja, Matsya, Chedi',
        'Vajji, Malla, Shurasena, Asmaka',
      ],
      answerIndex: 1,
      explanation: 'Magadha vs Kosala vs Vatsa vs Avanti \u2014 Magadha emerged the most powerful and prosperous kingdom of north India, absorbing the rest.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click Vaishali \u2014 seat of the Vajji confederacy, the most important republic (and the Lichchhavis, the \u201cfirst republic\u201d).',
      answer: { lat: 25.99, lng: 85.13, toleranceKm: 90 },
      explanation: 'Vaishali, north of the Ganga in Bihar. Note it sits directly across the river from Magadha \u2014 which is why Ajatashatru\u2019s wars targeted it.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click Kalinga (Dhauli) \u2014 site of the 261 BC war that changed Ashoka.',
      answer: { lat: 20.19, lng: 85.84, toleranceKm: 120 },
      explanation: 'Kalinga, on the Odisha coast. Fought in Ashoka\u2019s 9th regnal year; Rock Edict XIII records the horror and the turn to Dhamma.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Which Major Rock Edict mentions Ashoka\u2019s victory over Kalinga AND names five Greek kings?',
      options: ['Edict II', 'Edict IV', 'Edict XIII', 'Pillar Edict VII'],
      answerIndex: 2,
      explanation: 'Rock Edict XIII \u2014 the Kalinga edict \u2014 names Antiochus of Syria, Ptolemy of Egypt, Magas of Cyrene, Antigonus of Macedon and Alexander of Epirus as recipients of Dhamma victory. Edict IV is Dhammaghosha-over-Bherighosha; Edict II mentions southern kingdoms and medical care.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'Ashoka embraced Buddhism under the influence of the monk:',
      options: ['Moggaliputta Tissa', 'Upagupta', 'Mahendra', 'Nagasena'],
      answerIndex: 1,
      explanation: 'Upagupta. Ashoka then sent his son Mahendra and daughter Sanghamitra to Ceylon as missionaries, carrying a sapling of the Bodhi tree.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'The Mauryan empire under Ashoka covered the whole subcontinent EXCEPT:',
      options: ['Afghanistan', 'Kashmir', 'The extreme south', 'Baluchistan'],
      answerIndex: 2,
      explanation: 'Only the extreme south (Chola\u2013Pandya country) stayed out \u2014 Edict II treats them as friendly neighbours. Afghanistan, Baluchistan, Kashmir and the Nepal valleys were inside.',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click Pataliputra \u2014 the capital founded by Udayin at a river confluence.',
      answer: { lat: 25.61, lng: 85.14, toleranceKm: 80 },
      explanation: 'Pataliputra (Patna), at the Ganga\u2013Son confluence. Udayin moved the capital here from hill-ringed Rajgir \u2014 rivers beat hills once an empire needs highways.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Punch-marked coins of the Mahajanapada era were made of:',
      options: ['Gold and silver', 'Silver and copper', 'Copper and iron', 'Only gold'],
      answerIndex: 1,
      explanation: 'Silver and copper punch-marked coins mark the second urbanisation \u2014 India\u2019s first true money economy.',
    },
  ],
};

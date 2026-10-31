import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// THE NORTHWEST GATEWAY \u2014 MEDIEVAL BATTLES (712\u20131576)
//
// Concept:
//   "For 500 years, control of India was decided in one narrow
//   corridor \u2014 Khyber to Delhi. The Sultanate was born at Tarain
//   (1192) and died a few miles away at Panipat (1526)."
//
// Sources: Delhi Sultanate + Mughals Prelims decks (MS Academy).
// ============================================

const DELHI: [number, number] = [28.61, 77.21];

/** Battle sites along and around the corridor. */
const battles: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'sindh-712', name: '712: Muhammad-bin-Qasim defeats Dahir (Battle of Rewar, Sindh)' }, geometry: { type: 'Point', coordinates: [68.9, 27.72] } },
    { type: 'Feature', properties: { id: 'somnath-1025', name: '1025: Mahmud of Ghazni sacks Somnath (Kathiawar coast)' }, geometry: { type: 'Point', coordinates: [70.4, 20.89] } },
    { type: 'Feature', properties: { id: 'tarain', name: '1191 & 1192: Battles of Tarain \u2014 Prithviraj vs Muhammad Ghori' }, geometry: { type: 'Point', coordinates: [76.94, 29.79] } },
    { type: 'Feature', properties: { id: 'panipat-1', name: '21 Apr 1526: First Panipat \u2014 Babur kills Ibrahim Lodi' }, geometry: { type: 'Point', coordinates: [76.97, 29.39] } },
    { type: 'Feature', properties: { id: 'khanwa', name: '1527: Khanwa \u2014 Babur defeats Rana Sanga' }, geometry: { type: 'Point', coordinates: [77.42, 27.13] } },
    { type: 'Feature', properties: { id: 'chausa', name: '1539: Chausa \u2014 Sher Khan destroys Humayun\u2019s army' }, geometry: { type: 'Point', coordinates: [83.9, 25.51] } },
    { type: 'Feature', properties: { id: 'kanauj-1540', name: '1540: Bilgram/Kanauj \u2014 Humayun exiled; Sur Empire begins' }, geometry: { type: 'Point', coordinates: [79.92, 27.05] } },
    { type: 'Feature', properties: { id: 'panipat-2', name: '1556: Second Panipat \u2014 Bairam Khan (for Akbar) vs Hemu' }, geometry: { type: 'Point', coordinates: [76.97, 29.42] } },
    { type: 'Feature', properties: { id: 'haldighati', name: '1576: Haldighati \u2014 Man Singh (Mughal) vs Rana Pratap' }, geometry: { type: 'Point', coordinates: [73.69, 24.89] } },
    { type: 'Feature', properties: { id: 'chittor', name: '1568: Fall of Chittor \u2014 key to central Rajasthan (Jaimal & Patta)' }, geometry: { type: 'Point', coordinates: [74.63, 24.88] } },
  ],
};

/** The invasion corridor: Ghazni \u2192 Khyber \u2192 Punjab \u2192 Delhi. */
const corridor: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'nw-corridor', name: 'Invasion corridor: Ghazni \u2192 Khyber \u2192 Punjab \u2192 Delhi' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [68.42, 33.55], // Ghazni
          [71.08, 34.08], // Khyber pass
          [73.05, 33.6],  // Rawalpindi area
          [74.35, 31.55], // Lahore
          [75.86, 30.9],  // Ludhiana
          [76.94, 29.79], // Tarain
          [76.97, 29.39], // Panipat
          [DELHI[1], DELHI[0]],
        ],
      },
    },
  ],
};

/** Tripartite-struggle anchor + power centres. */
const powerCentres: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'kannauj', name: 'Kannauj \u2014 prize of the Tripartite Struggle (Pratiharas / Palas / Rashtrakutas)' }, geometry: { type: 'Point', coordinates: [79.92, 27.05] } },
    { type: 'Feature', properties: { id: 'delhi-sultanate', name: 'Delhi \u2014 seat of Sultanate (1206\u20131526) & Mughals' }, geometry: { type: 'Point', coordinates: [DELHI[1], DELHI[0]] } },
    { type: 'Feature', properties: { id: 'ghazni-city', name: 'Ghazni \u2014 Mahmud\u2019s base (17 raids, 1000\u20131027)' }, geometry: { type: 'Point', coordinates: [68.42, 33.55] } },
    { type: 'Feature', properties: { id: 'sasaram', name: 'Sasaram \u2014 Sher Shah Suri\u2019s capital/tomb (Sur Empire)' }, geometry: { type: 'Point', coordinates: [84.03, 24.95] } },
  ],
};

export const medievalGatewayChapter: Chapter = {
  id: 'medieval-gateway-battles',
  subject: 'history',
  unit: 'Medieval',
  tags: ['delhi', 'panipat', 'punjab', 'gujarat', 'somnath', 'aravalli', 'khyber', 'agra'],
  title: 'Medieval India: Gateway Battles',
  summary: '712\u20131576: Sindh, Somnath, Tarain, Panipat, Khanwa, Haldighati \u2014 one corridor, five centuries.',
  focus:
    'The Delhi Sultanate was born on the battlefield of Tarain (1192) and ended a few miles away at Panipat (1526). Learn the corridor once and every medieval battle question becomes a map question.',
  view: { center: [28.0, 76.0], zoom: 5 },
  basemap: 'paper',
  theme: { accent: '#7a1f2b', mapBg: '#f7efe6' },

  layers: [
    {
      id: 'corridor',
      name: 'NW invasion corridor',
      kind: 'vector',
      data: corridor,
      style: { color: '#7a1f2b', weight: 3, dashArray: '8 5' , flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'battles',
      name: 'Battle sites',
      kind: 'vector',
      data: battles,
      style: { color: '#7a1f2b', weight: 2, fillColor: '#b3261e', fillOpacity: 0.9, shadow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'power-centres',
      name: 'Power centres',
      kind: 'vector',
      data: powerCentres,
      style: { color: '#3b2a6b', weight: 2, fillColor: '#5b46a8', fillOpacity: 0.9, shadow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Before the Turks: the Tripartite Struggle. Pratiharas (west), Palas (Bengal) and Rashtrakutas (Deccan) fought a three-way, century-long contest for Kannauj \u2014 the symbolic capital of north India. All three exhausted themselves, opening the door to invaders.',
      linkedLayerId: 'power-centres',
      linkedFeatureId: 'kannauj',
    },
    {
      id: 'f2',
      text: '712 AD: Al-Hajjaj, governor of Iraq, sent Muhammad-bin-Qasim, who defeated Dahir of Sindh at the Battle of Rewar. Qasim called Multan \u201cthe City of Gold\u201d. His end was grim \u2014 recalled and tortured to death after Hajjaj\u2019s fall.',
      linkedLayerId: 'battles',
      linkedFeatureId: 'sindh-712',
    },
    {
      id: 'f3',
      text: 'Mahmud of Ghazni raided India 17 times (1000\u20131027) for plunder, not empire \u2014 climaxing with the sack of the Somnath temple on the Kathiawar coast in 1025. Contrast with Muhammad of Ghori, who came to STAY.',
      linkedLayerId: 'battles',
      linkedFeatureId: 'somnath-1025',
    },
    {
      id: 'f4',
      text: 'Tarain, the double battle: 1191 \u2014 Prithviraj Chauhan defeats Ghori. 1192 \u2014 Ghori returns and crushes the combined Rajput forces. Turkish rule in India begins with the Second Battle of Tarain; Ghori\u2019s slave Qutb-ud-din Aibak founds the Sultanate in 1206. (Iltutmish later won his own battle of Tarain, c. 1215, against Yaldauz.)',
      linkedLayerId: 'battles',
      linkedFeatureId: 'tarain',
    },
    {
      id: 'f5',
      text: 'Sultanate = five dynasties: Slave/Mamluk (1206\u201390), Khalji (1290\u20131320), Tughlaq (1320\u201314), Sayyid (1414\u201351), Lodi (1451\u20131526). It ended when Babur defeated and killed Ibrahim Lodi at the FIRST Battle of Panipat, 21 April 1526 \u2014 born at Tarain, dead at Panipat, a few miles apart.',
    },
    {
      id: 'f6',
      text: 'Babur\u2019s follow-up: Khanwa (1527) against Rana Sanga of Mewar \u2014 same tactics as Panipat (artillery + tulughma flanking) \u2014 secured the Mughal foothold against the Rajput confederacy.',
      linkedLayerId: 'battles',
      linkedFeatureId: 'khanwa',
    },
    {
      id: 'f7',
      text: 'The Sur interruption: Sher Khan smashed Humayun at Chausa (1539) and again at Bilgram/Kanauj (1540), exiling him 15 years. Sher Shah Suri built the Sur Empire from Sasaram \u2014 and the Grand Trunk Road. Humayun returned in 1555, then died in 1556 falling down his library stairs.',
      linkedLayerId: 'battles',
      linkedFeatureId: 'chausa',
    },
    {
      id: 'f8',
      text: 'Second Panipat (1556): 13-year-old Akbar\u2019s regent Bairam Khan defeats Hemu Vikramaditya, wazir of Adil Shah, leading the Afghan forces. Akbar had been crowned at Kalanaur the same year. The Mughal restoration is sealed on the SAME battlefield as 1526.',
      linkedLayerId: 'battles',
      linkedFeatureId: 'panipat-2',
    },
    {
      id: 'f9',
      text: 'Akbar in Rajasthan: Chittor \u2014 \u201cthe key to central Rajasthan\u201d \u2014 fell in 1568 after a 6-month siege (Jaimal and Patta commanded; Udai Singh withdrew to the hills). Ranthambhore and Kalinjar followed. At Haldighati (1576), Man Singh\u2019s Mughal army severely defeated Rana Pratap of Mewar \u2014 who nonetheless fought on from the hills.',
      linkedLayerId: 'battles',
      linkedFeatureId: 'haldighati',
    },
  ],

  events: [
    {
      id: 'e1',
      date: '0712',
      label: 'Sindh falls',
      description: 'Muhammad-bin-Qasim defeats Dahir at Rewar. The Arab conquest stays confined to Sindh \u2014 but the door is marked.',
      showLayers: ['battles'],
      hideLayers: ['power-centres'],
      view: { center: [27.5, 68.9], zoom: 6 },
    },
    {
      id: 'e2',
      date: '1025',
      label: 'Somnath sacked',
      description: 'Mahmud of Ghazni\u2019s 16th raid reaches the Somnath temple on the Kathiawar coast. Plunder, not conquest.',
      showLayers: ['battles', 'corridor'],
      view: { center: [21.5, 71.0], zoom: 6 },
    },
    {
      id: 'e3',
      date: '1192',
      label: 'Second Tarain',
      description: 'Ghori crushes Prithviraj\u2019s Rajput coalition. Turkish rule begins; Aibak will found the Sultanate in 1206.',
      showLayers: ['battles', 'corridor'],
      view: { center: [29.5, 76.9], zoom: 7 },
    },
    {
      id: 'e4',
      date: '1526-04-21',
      label: 'First Panipat',
      description: 'Babur\u2019s guns and tulughma destroy Ibrahim Lodi. The Sultanate \u2014 born at Tarain \u2014 dies a few miles away.',
      showLayers: ['battles', 'corridor'],
      view: { center: [29.4, 77.0], zoom: 7 },
    },
    {
      id: 'e5',
      date: '1527',
      label: 'Khanwa',
      description: 'Babur defeats Rana Sanga\u2019s Rajput confederacy using the Panipat playbook.',
      showLayers: ['battles'],
      view: { center: [27.1, 77.4], zoom: 7 },
    },
    {
      id: 'e6',
      date: '1540',
      label: 'Sur Empire',
      description: 'After Chausa (1539), Sher Khan finishes Humayun at Bilgram/Kanauj. Sher Shah rules from Sasaram; Humayun wanders 15 years.',
      showLayers: ['battles', 'power-centres'],
      view: { center: [26.0, 82.0], zoom: 6 },
    },
    {
      id: 'e7',
      date: '1556',
      label: 'Second Panipat',
      description: 'Bairam Khan, regent for 13-year-old Akbar, defeats Hemu. Mughal power is restored on the same field as 1526.',
      showLayers: ['battles', 'corridor'],
      view: { center: [29.4, 77.0], zoom: 7 },
    },
    {
      id: 'e8',
      date: '1576',
      label: 'Haldighati',
      description: 'Man Singh defeats Rana Pratap in the Aravalli pass. Mewar resists from the hills, but Rajasthan\u2019s plains are Mughal.',
      showLayers: ['battles'],
      view: { center: [24.9, 73.7], zoom: 8 },
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'The Delhi Sultanate is said to have been \u201cborn at Tarain and buried at Panipat\u201d because:',
      options: [
        'Both battles were fought against the Rajputs',
        'Turkish rule began with the 2nd Battle of Tarain (1192) and the last Sultan, Ibrahim Lodi, was killed at the 1st Battle of Panipat (1526) \u2014 fields only a few miles apart',
        'Both towns were Sultanate capitals',
        'Both battles were won by artillery',
      ],
      answerIndex: 1,
      explanation: 'Ghori\u2019s 1192 victory at Tarain opened Turkish rule; Babur\u2019s 1526 victory at Panipat killed Ibrahim Lodi and ended it. The two battlefields sit within a short march of each other on the same corridor to Delhi.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click Panipat \u2014 the field of the 1526 and 1556 battles.',
      answer: { lat: 29.39, lng: 76.97, toleranceKm: 70 },
      explanation: 'Panipat guards the last flat approach to Delhi \u2014 which is why decisive battles keep landing here (1526 Babur\u2013Lodi, 1556 Bairam Khan\u2013Hemu, and 1761 later still).',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Who represented 13-year-old Akbar at the Second Battle of Panipat (1556), and against whom?',
      options: [
        'Man Singh, against Rana Pratap',
        'Bairam Khan, against Hemu Vikramaditya',
        'Todar Mal, against Sher Khan',
        'Abul Fazl, against Adil Shah',
      ],
      answerIndex: 1,
      explanation: 'Regent Bairam Khan commanded for Akbar against Hemu, the wazir of Adil Shah leading the Afghan forces. Akbar had been crowned at Kalanaur in 1556 aged 13 years 4 months.',
    },
    {
      id: 'q4',
      type: 'map_click',
      question: 'Click Somnath \u2014 the temple Mahmud of Ghazni sacked in 1025 AD.',
      answer: { lat: 20.89, lng: 70.4, toleranceKm: 120 },
      explanation: 'Somnath stands on the Kathiawar (Saurashtra) coast of Gujarat. Ghazni raided 17 times for plunder \u2014 he never tried to rule India, unlike Ghori.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'Put Humayun\u2019s disasters in order:',
      options: [
        'Kanauj (1540) \u2192 Chausa (1539)',
        'Chausa (1539) \u2192 Bilgram/Kanauj (1540) \u2192 15-year exile',
        'Khanwa (1527) \u2192 Chausa (1539)',
        'Panipat (1526) \u2192 Kanauj (1540)',
      ],
      answerIndex: 1,
      explanation: 'Sher Khan destroyed Humayun\u2019s army at Chausa in 1539, then finished him at Bilgram (Battle of Kanauj/the Ganges) in 1540 \u2014 Humayun lost his kingdom and wandered 15 years while the Sur Empire ruled from Sasaram.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Muhammad-bin-Qasim (712 AD) defeated which ruler, at which battle?',
      options: [
        'Prithviraj at Tarain',
        'Dahir of Sindh at the Battle of Rewar',
        'Jaipal at Waihind',
        'Rana Sanga at Khanwa',
      ],
      answerIndex: 1,
      explanation: 'Qasim, sent by Al-Hajjaj the governor of Iraq, beat Dahir at Rewar and took Sindh; he called Multan \u201cthe City of Gold\u201d. He was later recalled and tortured to death.',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click Haldighati \u2014 the 1576 pass battle between Man Singh and Rana Pratap.',
      answer: { lat: 24.89, lng: 73.69, toleranceKm: 90 },
      explanation: 'Haldighati is an Aravalli pass near Udaipur in Mewar. Rana Pratap was severely defeated but never submitted, fighting on from the hills.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'The Tripartite Struggle was fought for control of:',
      options: ['Delhi', 'Ujjain', 'Kannauj', 'Pataliputra'],
      answerIndex: 2,
      explanation: 'Kannauj \u2014 contested for over a century by the Gurjara-Pratiharas, the Palas of Bengal, and the Rashtrakutas of the Deccan. Their mutual exhaustion cleared the stage for the Turkish invasions.',
    },
    {
      id: 'q9',
      type: 'mcq',
      question: 'Which fort, considered \u201cthe key to central Rajasthan\u201d, fell to Akbar in 1568 after a six-month siege defended by Jaimal and Patta?',
      options: ['Ranthambhore', 'Chittor', 'Kalinjar', 'Mehrangarh'],
      answerIndex: 1,
      explanation: 'Chittor. Rana Udai Singh retired to the hills leaving Jaimal and Patta in command. Ranthambhore (\u201cthe most powerful fortress in Rajasthan\u201d) and Kalinjar fell soon after.',
    },
  ],
};

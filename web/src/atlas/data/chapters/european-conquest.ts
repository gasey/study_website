import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// EUROPEANS IN INDIA \u2014 SETTLEMENTS & WARS (1498\u20131819)
//
// Concept:
//   "Five flags on one coastline. Learn each power's port pairs
//   (Portuguese\u2013Goa, Dutch\u2013Pulicat, English\u2013Madras/Bombay/
//   Calcutta, French\u2013Pondicherry, Danes\u2013Tranquebar) and the
//   wars are just the ports fighting each other inland."
//
// Source: HISTORY \u2014 Modern India (MS Academy) deck.
// ============================================

const portugueseSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'calicut', name: 'Calicut \u2014 Vasco da Gama lands, 1498; welcomed by the Zamorin' }, geometry: { type: 'Point', coordinates: [75.78, 11.25] } },
    { type: 'Feature', properties: { id: 'cochin-p', name: 'Cochin \u2014 first Portuguese HQ (factories also at Cannanore)' }, geometry: { type: 'Point', coordinates: [76.24, 9.93] } },
    { type: 'Feature', properties: { id: 'goa-p', name: 'Goa \u2014 taken from Bijapur 1510 (Albuquerque); HQ from 1530; first printing press 1556' }, geometry: { type: 'Point', coordinates: [73.83, 15.5] } },
    { type: 'Feature', properties: { id: 'diu', name: 'Diu \u2014 Portuguese fort commanding the Gujarat coast' }, geometry: { type: 'Point', coordinates: [70.99, 20.71] } },
    { type: 'Feature', properties: { id: 'daman', name: 'Daman \u2014 Portuguese enclave (with Goa & Diu till 1961)' }, geometry: { type: 'Point', coordinates: [72.83, 20.4] } },
  ],
};

const dutchDanishSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'masulipatnam', name: 'Masulipatnam \u2014 Dutch control 1605' }, geometry: { type: 'Point', coordinates: [81.13, 16.17] } },
    { type: 'Feature', properties: { id: 'pulicat', name: 'Pulicat \u2014 chief Dutch settlement, 1610' }, geometry: { type: 'Point', coordinates: [80.32, 13.42] } },
    { type: 'Feature', properties: { id: 'tranquebar', name: 'Tranquebar (near Tanjore) \u2014 Danish factory, 1620' }, geometry: { type: 'Point', coordinates: [79.85, 11.03] } },
    { type: 'Feature', properties: { id: 'serampore', name: 'Serampore (near Calcutta) \u2014 principal Danish settlement; missionary press' }, geometry: { type: 'Point', coordinates: [88.34, 22.75] } },
  ],
};

const englishSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'surat-e', name: 'Surat \u2014 first English factory, 1613 (after Battle of Surat 1612; Thomas Roe at Jahangir\u2019s court 1615)' }, geometry: { type: 'Point', coordinates: [72.83, 21.17] } },
    { type: 'Feature', properties: { id: 'madras-e', name: 'Madras \u2014 Fort St. George, 1639\u201340' }, geometry: { type: 'Point', coordinates: [80.28, 13.08] } },
    { type: 'Feature', properties: { id: 'bombay-e', name: 'Bombay \u2014 Portuguese dowry to Charles II (1662) \u2192 Company 1668 \u2192 HQ 1687' }, geometry: { type: 'Point', coordinates: [72.83, 18.94] } },
    { type: 'Feature', properties: { id: 'calcutta-e', name: 'Calcutta \u2014 Job Charnock at Sutanati 1690; Fort William 1700 (zamindari of Sutanati, Govindpur, Kalikata)' }, geometry: { type: 'Point', coordinates: [88.36, 22.57] } },
  ],
};

const frenchSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'pondicherry', name: 'Pondicherry \u2014 founded 1674; nerve centre of French India' }, geometry: { type: 'Point', coordinates: [79.83, 11.93] } },
    { type: 'Feature', properties: { id: 'chandernagore-f', name: 'Chandernagore \u2014 French Bengal post (taken by Clive, 1757)' }, geometry: { type: 'Point', coordinates: [88.38, 22.87] } },
  ],
};

const warSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'st-thome', name: 'St. Thome (1746) \u2014 1st Carnatic War: Dupleix\u2019s French rout the Carnatic Nawab' }, geometry: { type: 'Point', coordinates: [80.28, 13.03] } },
    { type: 'Feature', properties: { id: 'wandiwash', name: 'Wandiwash (1760) \u2014 3rd Carnatic War: Eyre Coote crushes Lally; French power ends' }, geometry: { type: 'Point', coordinates: [79.62, 12.51] } },
    { type: 'Feature', properties: { id: 'srirangapatna', name: 'Srirangapatna \u2014 Tipu\u2019s capital; died here in the 4th Anglo-Mysore War, 1799' }, geometry: { type: 'Point', coordinates: [76.68, 12.42] } },
    { type: 'Feature', properties: { id: 'wadgaon', name: 'Wadgaon (1779) \u2014 1st Anglo-Maratha War: English defeated; Convention of Wadgaon' }, geometry: { type: 'Point', coordinates: [73.66, 18.75] } },
  ],
};

export const europeanConquestChapter: Chapter = {
  id: 'european-conquest',
  subject: 'history',
  unit: 'Modern',
  tags: ['goa', 'calicut', 'bombay', 'madras', 'calcutta', 'bengal', 'carnatic', 'deccan', 'hooghly', 'coasts'],
  title: 'Europeans: Ports to Power',
  summary: 'Five flags, one coastline \u2014 settlements, Carnatic, Mysore & Maratha wars.',
  focus:
    'Five European flags on one coastline. Learn each power\u2019s port pairs \u2014 Portuguese\u2013Goa, Dutch\u2013Pulicat, English\u2013Madras/Bombay/Calcutta, French\u2013Pondicherry, Danes\u2013Tranquebar \u2014 and the wars of conquest are just those ports fighting their way inland.',
  view: { center: [15.5, 78.0], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#31597e', mapBg: '#edf2f6' },

  layers: [
    { id: 'portuguese', name: 'Portuguese (1498\u2013)', kind: 'vector', data: portugueseSites, style: { color: '#2e7d5b', weight: 2, fillColor: '#2e7d5b', markerRadius: 6 }, defaultOn: true, labelKey: 'name' },
    { id: 'dutch-danish', name: 'Dutch & Danes', kind: 'vector', data: dutchDanishSites, style: { color: '#b0632c', weight: 2, fillColor: '#b0632c', markerRadius: 6 }, defaultOn: true, labelKey: 'name' },
    { id: 'english', name: 'English presidencies', kind: 'vector', data: englishSites, style: { color: '#b3261e', weight: 2, fillColor: '#b3261e', markerRadius: 7, glow: true }, defaultOn: true, labelKey: 'name' },
    { id: 'french', name: 'French (1664\u2013)', kind: 'vector', data: frenchSites, style: { color: '#5b46a8', weight: 2, fillColor: '#5b46a8', markerRadius: 6 }, defaultOn: true, labelKey: 'name' },
    { id: 'war-sites', name: 'Wars of conquest', kind: 'vector', data: warSites, style: { color: '#7a1f2b', weight: 2, fillColor: '#7a1f2b', markerRadius: 7, glow: true }, defaultOn: false, labelKey: 'name' },
  ],

  facts: [
    {
      id: 'f1',
      text: 'PORTUGUESE: Vasco da Gama reached CALICUT in 1498 (welcomed by the Zamorin, resented by Arab traders); returned 1501. Almeida (Governor 1505) pushed the BLUE WATER POLICY \u2014 mastery of the Indian Ocean; ALBUQUERQUE took GOA from Bijapur in 1510 (the first European-held Indian territory since Alexander); Nino da Cunha moved HQ Cochin\u2192Goa in 1530. They brought tobacco cultivation and India\u2019s first printing press (Goa, 1556).',
      linkedLayerId: 'portuguese',
    },
    {
      id: 'f2',
      text: 'DUTCH: the VOC formed 1602; Masulipatnam 1605, PULICAT 1610, Surat 1616, Cochin 1663 \u2014 spice-focused, and eventually squeezed out (Battle of Bedara vs the English, 1759). DANES: company founded 1616; TRANQUEBAR (1620) near Tanjore and SERAMPORE near Calcutta \u2014 remembered for missionaries more than trade; sold out to Britain in 1845.',
      linkedLayerId: 'dutch-danish',
    },
    {
      id: 'f3',
      text: 'ENGLISH: Charter from Elizabeth I on 31 December 1600 to the \u201cGovernor and Company of Merchants of London trading into the East Indies\u201d. Battle of Surat 1612 beat the Portuguese at sea \u2192 Jahangir allowed the SURAT factory (1613); Sir THOMAS ROE (1615) at Jahangir\u2019s court as James I\u2019s ambassador. Madras/Fort St. George 1639\u201340; BOMBAY came as Portuguese dowry to Charles II (1662) \u2192 Company 1668 \u2192 HQ 1687; JOB CHARNOCK\u2019s Sutanati treaty 1690 \u2192 zamindari of Sutanati, Govindpur, Kalikata (1698) \u2192 FORT WILLIAM 1700 = Calcutta.',
      linkedLayerId: 'english',
    },
    {
      id: 'f4',
      text: 'FRENCH: Colbert\u2019s Compagnie des Indes Orientales, 1664, under Louis XIV; PONDICHERRY founded 1674 \u2014 the nerve centre; reorganized 1720 as the Perpetual Company, strengthened under Lenoir and Dumas, weaponized under DUPLEIX.',
      linkedLayerId: 'french',
    },
    {
      id: 'f5',
      text: 'CARNATIC WARS \u2014 the Anglo-French duel: 1st (1746\u201348): French take Madras; Battle of ST. THOME \u2014 Dupleix\u2019s small French force routs the Carnatic Nawab\u2019s army; Treaty of Aix-la-Chapelle (Austrian Succession in the background). 2nd (1749\u201354): puppet politics \u2014 French back Muzaffar Jung (Hyderabad) + Chanda Sahib (Carnatic), English back Nasir Jung + Muhammad Ali; Clive\u2019s side wins; Treaty of Pondicherry/Godehu 1754. 3rd (1756\u201363): Lally takes Fort St. David but is crushed at WANDIWASH (1760, Eyre Coote); Treaty of Paris 1763 returns Pondicherry as a trading post \u2014 French political power in India is finished.',
      linkedLayerId: 'war-sites',
    },
    {
      id: 'f6',
      text: 'ANGLO-MYSORE WARS: 1st (1767\u201369) \u2014 HAIDAR ALI beats the English; Treaty of Madras. 2nd (1780\u201384) \u2014 Treaty of Mangalore under Warren Hastings. 3rd (1790\u201392) \u2014 Cornwallis vs TIPU; Treaty of Srirangapatna halves Mysore. 4th (1799) \u2014 Wellesley storms SRIRANGAPATNA; Tipu dies fighting. Mysore falls to Subsidiary Alliance.',
      linkedLayerId: 'war-sites',
      linkedFeatureId: 'srirangapatna',
    },
    {
      id: 'f7',
      text: 'ANGLO-MARATHA WARS: 1st (1775\u201382) \u2014 English humiliated at WADGAON (Convention of Wadgaon, 1779), then Treaty of SALBAI (1782) abandoning Raghunath Rao. 2nd (1803\u201305) \u2014 after the Peshwa\u2019s Subsidiary Alliance Treaty of BASSEIN (1802), the Marathas are beaten; Treaty of Rajghat with the Holkars (1805). 3rd (1817\u201319) \u2014 fought around Lord Hastings\u2019 PINDARI campaign; Maratha power extinguished, British paramountcy complete.',
      linkedLayerId: 'war-sites',
    },
  ],

  events: [
    { id: 'e1', date: '1498', label: 'Vasco da Gama', description: 'Calicut, 1498 \u2014 the sea route to India opens. The Zamorin welcomes; the Arab traders bristle.', showLayers: ['portuguese'], hideLayers: ['war-sites'], view: { center: [11.25, 75.78], zoom: 6 } },
    { id: 'e2', date: '1510', label: 'Goa taken', description: 'Albuquerque seizes Goa from Bijapur \u2014 Portuguese HQ and the anchor of the Estado da India.', showLayers: ['portuguese'], view: { center: [15.5, 73.83], zoom: 7 } },
    { id: 'e3', date: '1613', label: 'Surat factory', description: 'After beating the Portuguese at sea (1612), the English get Jahangir\u2019s leave for a Surat factory; Thomas Roe follows in 1615.', showLayers: ['english'], view: { center: [21.17, 72.83], zoom: 6 } },
    { id: 'e4', date: '1674', label: 'Pondicherry', description: 'Fran\u00e7ois Martin founds Pondicherry \u2014 the French nerve centre and the English\u2019s future rival.', showLayers: ['french', 'english'], view: { center: [12.5, 80.0], zoom: 6 } },
    { id: 'e5', date: '1700', label: 'Fort William', description: 'Sutanati + Govindpur + Kalikata become fortified Calcutta \u2014 seat of the eastern presidency.', showLayers: ['english'], view: { center: [22.57, 88.36], zoom: 8 } },
    { id: 'e6', date: '1760', label: 'Wandiwash', description: 'Eyre Coote destroys Lally\u2019s French army \u2014 the decisive battle of the Carnatic wars. Paris (1763) leaves France a trader, not a power.', showLayers: ['war-sites'], view: { center: [12.51, 79.62], zoom: 7 } },
    { id: 'e7', date: '1799', label: 'Tipu falls', description: 'Wellesley storms Srirangapatna; Tipu Sultan dies at the breach. Mysore enters Subsidiary Alliance.', showLayers: ['war-sites'], view: { center: [12.42, 76.68], zoom: 7 } },
    { id: 'e8', date: '1818', label: 'Paramountcy', description: 'Third Anglo-Maratha war ends (1817\u201319) with the Pindaris crushed and the Peshwa deposed \u2014 Britain is paramount in India.', showLayers: ['war-sites'], view: { center: [18.75, 73.66], zoom: 6 } },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Match power \u2192 chief settlement. Which pair is WRONG?',
      options: [
        'Dutch \u2014 Pulicat',
        'Danes \u2014 Tranquebar',
        'French \u2014 Goa',
        'Portuguese \u2014 Cochin (early HQ)',
      ],
      answerIndex: 2,
      explanation: 'Goa was PORTUGUESE (taken 1510); the French nerve centre was Pondicherry (founded 1674). Dutch\u2013Pulicat, Danes\u2013Tranquebar/Serampore, Portuguese\u2013Cochin-then-Goa are correct.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click Calicut \u2014 where Vasco da Gama landed in 1498.',
      answer: { lat: 11.25, lng: 75.78, toleranceKm: 110 },
      explanation: 'Calicut (Kozhikode) on the Malabar coast, ruled by the Zamorin. The sea route around the Cape rewired world trade \u2014 and India\u2019s history.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Bombay came to the English East India Company as:',
      options: [
        'A conquest from the Marathas',
        'Portuguese dowry to Charles II (1662), transferred to the Company in 1668',
        'A gift from Jahangir to Thomas Roe',
        'Part of the Treaty of Paris',
      ],
      answerIndex: 1,
      explanation: 'Catherine of Braganza\u2019s dowry \u2192 Crown 1662 \u2192 Company 1668 (for \u00a310 a year) \u2192 western HQ from 1687, replacing Surat.',
    },
    {
      id: 'q4',
      type: 'map_click',
      question: 'Click Wandiwash \u2014 the 1760 battle that finished French power in India.',
      answer: { lat: 12.51, lng: 79.62, toleranceKm: 110 },
      explanation: 'Eyre Coote crushed Count de Lally at Wandiwash (Vandavasi), Tamil Nadu. The Treaty of Paris (1763) returned Pondicherry \u2014 but only as a trading post.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'In the SECOND Carnatic War, the French under Dupleix backed:',
      options: [
        'Nasir Jung and Muhammad Ali',
        'Muzaffar Jung (Hyderabad) and Chanda Sahib (Carnatic)',
        'The Nizam and the Peshwa',
        'Haidar Ali and Tipu',
      ],
      answerIndex: 1,
      explanation: 'French: Muzaffar Jung + Chanda Sahib; English: Nasir Jung + Muhammad Ali. Clive\u2019s side prevailed \u2014 Treaty of Pondicherry/Godehu, 1754, and Dupleix was recalled.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Sequence the Anglo-Mysore treaties: 1st, 2nd, 3rd wars ended respectively with:',
      options: [
        'Mangalore \u2192 Madras \u2192 Srirangapatna',
        'Madras \u2192 Mangalore \u2192 Srirangapatna',
        'Srirangapatna \u2192 Madras \u2192 Mangalore',
        'Madras \u2192 Srirangapatna \u2192 Mangalore',
      ],
      answerIndex: 1,
      explanation: 'Treaty of Madras (1769, after Haidar Ali WON) \u2192 Treaty of Mangalore (1784) \u2192 Treaty of Srirangapatna (1792, Mysore halved). The 4th war (1799) ended with Tipu\u2019s death, no treaty needed.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'The Convention of Wadgaon (1779) is notable because:',
      options: [
        'The French surrendered Pondicherry',
        'The English were DEFEATED by the Marathas and signed on losing terms',
        'Tipu ceded half his kingdom',
        'The Pindaris were disbanded',
      ],
      answerIndex: 1,
      explanation: 'A rare English humiliation \u2014 in the 1st Anglo-Maratha War. The Treaty of Salbai (1782) later restored the balance, with the English dropping Raghunath Rao\u2019s cause.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Which Subsidiary Alliance treaty pulled the Peshwa under British protection and triggered the 2nd Anglo-Maratha War?',
      options: ['Treaty of Salbai', 'Treaty of Bassein (1802)', 'Treaty of Rajghat', 'Treaty of Surat'],
      answerIndex: 1,
      explanation: 'Bassein, 1802 \u2014 Peshwa Baji Rao II signed Wellesley\u2019s Subsidiary Alliance; Scindia and Bhonsle fought and lost (1803\u201305). Rajghat (1805) settled the Holkars.',
    },
  ],
};

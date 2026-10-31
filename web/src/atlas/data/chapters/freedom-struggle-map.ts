import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// FREEDOM STRUGGLE ON THE MAP (1857\u20131947)
//
// Concept:
//   "1857 was a map of garrison towns; Gandhi\u2019s movements were
//   a map of villages and salt pans. Pin each centre to its
//   leader and each satyagraha to its place \u2014 that pairing IS
//   the exam."
//
// Source: HISTORY \u2014 Modern India (MS Academy) deck.
// ============================================

/** 1857 revolt centres with leaders \u2014 the classic pairing table. */
const revoltCentres: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'barrackpore', name: 'Barrackpore \u2014 Mangal Pandey, 34th Native Infantry (29 Mar 1857)' }, geometry: { type: 'Point', coordinates: [88.37, 22.76] } },
    { type: 'Feature', properties: { id: 'meerut', name: 'Meerut \u2014 outbreak, 10 May 1857' }, geometry: { type: 'Point', coordinates: [77.71, 28.98] } },
    { type: 'Feature', properties: { id: 'delhi-1857', name: 'Delhi \u2014 Bahadur Shah II & General Bakht Khan' }, geometry: { type: 'Point', coordinates: [77.23, 28.66] } },
    { type: 'Feature', properties: { id: 'lucknow', name: 'Lucknow \u2014 Begum Hazrat Mahal, Birjis Qadir, Ahmadullah' }, geometry: { type: 'Point', coordinates: [80.95, 26.85] } },
    { type: 'Feature', properties: { id: 'kanpur', name: 'Kanpur \u2014 Nana Sahib, Tantia Tope, Azimullah Khan' }, geometry: { type: 'Point', coordinates: [80.33, 26.45] } },
    { type: 'Feature', properties: { id: 'jhansi', name: 'Jhansi \u2014 Rani Laxmibai' }, geometry: { type: 'Point', coordinates: [78.57, 25.45] } },
    { type: 'Feature', properties: { id: 'bareilly', name: 'Bareilly \u2014 Khan Bahadur' }, geometry: { type: 'Point', coordinates: [79.42, 28.36] } },
    { type: 'Feature', properties: { id: 'allahabad-1857', name: 'Allahabad \u2014 Liaqat Ali' }, geometry: { type: 'Point', coordinates: [81.85, 25.44] } },
    { type: 'Feature', properties: { id: 'arrah', name: 'Jagdishpur/Arrah (Bihar) \u2014 Kunwar Singh' }, geometry: { type: 'Point', coordinates: [84.42, 25.47] } },
    { type: 'Feature', properties: { id: 'faizabad', name: 'Faizabad \u2014 Maulvi Ahmadullah' }, geometry: { type: 'Point', coordinates: [82.15, 26.77] } },
  ],
};

/** Gandhian era sites. */
const gandhiSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'champaran', name: 'Champaran 1917 \u2014 first Civil Disobedience (indigo tinkathia)' }, geometry: { type: 'Point', coordinates: [84.92, 26.65] } },
    { type: 'Feature', properties: { id: 'kheda', name: 'Kheda 1918 \u2014 first Non-Cooperation (revenue withheld)' }, geometry: { type: 'Point', coordinates: [72.68, 22.75] } },
    { type: 'Feature', properties: { id: 'amritsar', name: 'Jallianwala Bagh, Amritsar \u2014 13 Apr 1919' }, geometry: { type: 'Point', coordinates: [74.88, 31.62] } },
    { type: 'Feature', properties: { id: 'chauri-chaura', name: 'Chauri Chaura \u2014 Feb 1922, NCM withdrawn' }, geometry: { type: 'Point', coordinates: [83.6, 26.65] } },
    { type: 'Feature', properties: { id: 'sabarmati', name: 'Sabarmati Ashram, Ahmedabad \u2014 march starts 12 Mar 1930' }, geometry: { type: 'Point', coordinates: [72.58, 23.06] } },
    { type: 'Feature', properties: { id: 'dandi', name: 'Dandi \u2014 salt law broken, 6 Apr 1930' }, geometry: { type: 'Point', coordinates: [72.79, 20.88] } },
    { type: 'Feature', properties: { id: 'bombay-1942', name: 'Bombay \u2014 Quit India resolution, 8 Aug 1942 (\u201cDo or Die\u201d)' }, geometry: { type: 'Point', coordinates: [72.81, 18.96] } },
  ],
};

/** Dandi March: Sabarmati \u2192 Dandi, ~375\u2013385 km. */
const dandiMarch: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'dandi-march', name: 'Dandi March \u2014 Gandhi + 78 followers, 12 Mar \u2013 6 Apr 1930' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [72.58, 23.06], // Sabarmati
          [72.62, 22.75],
          [72.9, 22.3],
          [72.95, 21.7],
          [72.85, 21.2],
          [72.79, 20.88], // Dandi
        ],
      },
    },
  ],
};

export const freedomStruggleChapter: Chapter = {
  id: 'freedom-struggle-map',
  subject: 'history',
  unit: 'Modern',
  tags: ['delhi', 'bengal', 'calcutta', 'bombay', 'gujarat', 'champaran', 'punjab', 'bihar'],
  title: 'Freedom Struggle on the Map',
  summary: '1857 centres & leaders; Champaran to Dandi to Quit India.',
  focus:
    'Two map-layers of resistance: 1857\u2019s garrison towns each paired with a leader, and Gandhi\u2019s satyagrahas each pinned to a village. Centre\u2013leader and movement\u2013place pairings are what exams actually test.',
  view: { center: [24.5, 79.0], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#1a6b3c', mapBg: '#eef5ef' },

  layers: [
    {
      id: 'revolt-1857',
      name: '1857 revolt centres',
      kind: 'vector',
      data: revoltCentres,
      style: { color: '#8a1c1c', weight: 2, fillColor: '#b3261e', fillOpacity: 0.9, shadow: true , flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'gandhi-sites',
      name: 'Gandhian movement sites',
      kind: 'vector',
      data: gandhiSites,
      style: { color: '#1a6b3c', weight: 2, fillColor: '#1a6b3c', fillOpacity: 0.9, shadow: true },
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'dandi-march',
      name: 'Dandi March route (1930)',
      kind: 'vector',
      data: dandiMarch,
      style: { color: '#1a6b3c', weight: 3, dashArray: '2 6' },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: '1857 causes: Awadh annexed (1856) for \u201cmaladministration\u201d, Jhansi via Doctrine of Lapse (Dalhousie, 1848\u201356: no adopted heir allowed); sepoy grievances (low pay, ceiling at subedar, racial discrimination); social reforms + missionaries; economic drain. Immediate spark: the Enfield cartridge greased with cow and pig fat.',
      linkedLayerId: 'revolt-1857',
    },
    {
      id: 'f2',
      text: 'Sequence: 19th NI at Berhampur refuses the cartridge \u2192 Mangal Pandey (34th NI) fires at his sergeant-major at Barrackpore and is hanged \u2192 the revolt proper breaks out at MEERUT on 10 May 1857 \u2192 sepoys reach Delhi and declare Bahadur Shah Zafar Emperor of India.',
      linkedLayerId: 'revolt-1857',
      linkedFeatureId: 'meerut',
    },
    {
      id: 'f3',
      text: 'Centre \u2192 leader pairs (learn as a table): Delhi \u2013 Bahadur Shah II + Gen. Bakht Khan; Lucknow \u2013 Begum Hazrat Mahal; Kanpur \u2013 Nana Sahib with Tantia Tope & Azimullah Khan; Jhansi \u2013 Rani Laxmibai; Bareilly \u2013 Khan Bahadur; Allahabad \u2013 Liaqat Ali; Jagdishpur/Arrah \u2013 Kunwar Singh; Faizabad \u2013 Maulvi Ahmadullah.',
      linkedLayerId: 'revolt-1857',
    },
    {
      id: 'f4',
      text: 'Consequence: Government of India Act 1858 abolished Company rule \u2014 the Crown ruled directly. (Also remember Wellesley\u2019s Subsidiary Alliance and Dalhousie\u2019s Doctrine of Lapse as the annexation machinery that fed the revolt.)',
    },
    {
      id: 'f5',
      text: 'Gandhi\u2019s laboratory: Champaran 1917 = FIRST civil disobedience (indigo planters\u2019 tinkathia); Kheda 1918 = FIRST non-cooperation (crop failure \u2192 revenue withheld under the revenue code). Then Jallianwala Bagh (13 Apr 1919) and Khilafat fed into the Non-Cooperation Movement (1920\u201322), financed by the Tilak Swarajya Fund.',
      linkedLayerId: 'gandhi-sites',
    },
    {
      id: 'f6',
      text: 'Chauri Chaura, February 1922: a mob burnt a police station; Gandhi withdrew the Non-Cooperation Movement at its height \u2014 the most argued-about decision of the era, and the cause of the Swarajist split.',
      linkedLayerId: 'gandhi-sites',
      linkedFeatureId: 'chauri-chaura',
    },
    {
      id: 'f7',
      text: 'Civil Disobedience began 12 March 1930: Gandhi + 78 chosen followers walked ~375 km from Sabarmati Ashram to Dandi on the Gujarat seacoast and broke the salt law on 6 April. Salt was genius: the one tax every villager paid.',
      linkedLayerId: 'dandi-march',
    },
    {
      id: 'f8',
      text: 'Quit India: the AICC met at Bombay on 8 August 1942 and passed the resolution \u2014 \u201cDo or Die\u201d. Leadership was jailed within hours; the movement went leaderless and underground. Gandhi fasted 21 days (Feb\u2013Mar 1943) against the repression.',
      linkedLayerId: 'gandhi-sites',
      linkedFeatureId: 'bombay-1942',
    },
  ],

  events: [
    {
      id: 'e1',
      date: '1857-03-29',
      label: 'Mangal Pandey',
      description: 'Barrackpore: Mangal Pandey of the 34th NI fires on his sergeant-major; he is hanged. The 19th NI at Berhampur had already refused the cartridge.',
      showLayers: ['revolt-1857'],
      hideLayers: ['gandhi-sites', 'dandi-march'],
      view: { center: [22.76, 88.37], zoom: 8 },
    },
    {
      id: 'e2',
      date: '1857-05-10',
      label: 'Meerut rises',
      description: 'The revolt breaks out at Meerut; sepoys march on Delhi and proclaim Bahadur Shah Zafar Emperor of India.',
      showLayers: ['revolt-1857'],
      hideLayers: ['gandhi-sites', 'dandi-march'],
      view: { center: [28.8, 77.4], zoom: 7 },
    },
    {
      id: 'e3',
      date: '1858-08-02',
      label: 'Crown rule',
      description: 'Government of India Act 1858: Company rule abolished; the British Crown governs directly.',
      showLayers: ['revolt-1857'],
      view: { center: [25.5, 80.0], zoom: 5 },
    },
    {
      id: 'e4',
      date: '1917-04-10',
      label: 'Champaran',
      description: 'Gandhi\u2019s first civil disobedience in India \u2014 for indigo cultivators against the tinkathia system.',
      showLayers: ['gandhi-sites'],
      hideLayers: ['revolt-1857'],
      view: { center: [26.65, 84.92], zoom: 7 },
    },
    {
      id: 'e5',
      date: '1919-04-13',
      label: 'Jallianwala Bagh',
      description: 'Dyer\u2019s massacre at Amritsar. With the Khilafat issue and post-war distress, it lights the fuse of Non-Cooperation (1920\u201322).',
      showLayers: ['gandhi-sites'],
      view: { center: [31.62, 74.88], zoom: 8 },
    },
    {
      id: 'e6',
      date: '1922-02-05',
      label: 'Chauri Chaura',
      description: 'Mob violence at a police station; Gandhi withdraws Non-Cooperation at its peak.',
      showLayers: ['gandhi-sites'],
      view: { center: [26.65, 83.6], zoom: 8 },
    },
    {
      id: 'e7',
      date: '1930-03-12',
      label: 'Dandi March',
      description: 'Sabarmati \u2192 Dandi, ~375 km, 78 followers, 25 days. Salt law broken 6 April; Civil Disobedience begins.',
      showLayers: ['gandhi-sites', 'dandi-march'],
      view: { center: [22.0, 72.7], zoom: 7 },
    },
    {
      id: 'e8',
      date: '1942-08-08',
      label: 'Quit India',
      description: 'AICC at Bombay passes the Quit India resolution. \u201cDo or Die.\u201d Leaders jailed within hours.',
      showLayers: ['gandhi-sites'],
      hideLayers: ['dandi-march'],
      view: { center: [18.96, 72.81], zoom: 8 },
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'map_click',
      question: 'Click Meerut \u2014 where the Revolt of 1857 broke out on 10 May.',
      answer: { lat: 28.98, lng: 77.71, toleranceKm: 70 },
      explanation: 'Meerut\u2019s sepoys rose on 10 May 1857 and marched overnight to Delhi to proclaim Bahadur Shah Zafar emperor. Barrackpore (Mangal Pandey) was the prologue, Meerut the outbreak.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Match the WRONG pair \u2014 1857 centre : leader.',
      options: [
        'Kanpur : Nana Sahib',
        'Lucknow : Begum Hazrat Mahal',
        'Bareilly : Kunwar Singh',
        'Faizabad : Maulvi Ahmadullah',
      ],
      answerIndex: 2,
      explanation: 'Bareilly was led by Khan Bahadur. Kunwar Singh led at Jagdishpur/Arrah in Bihar. The rest are correct pairs \u2014 and every one of them is a past exam question.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'The immediate cause of the 1857 revolt was:',
      options: [
        'The annexation of Awadh',
        'The Enfield rifle cartridges greased with cow and pig fat (plus the bone-dust-in-atta rumour)',
        'The Doctrine of Lapse',
        'Low sepoy salaries',
      ],
      answerIndex: 1,
      explanation: 'Awadh, Lapse, and pay were underlying causes; the greased cartridge was the spark. The 19th NI at Berhampur refused it first; Mangal Pandey (34th NI) fired the first shot at Barrackpore.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Champaran (1917) and Kheda (1918) are called, respectively, Gandhi\u2019s first ______ and first ______ in India.',
      options: [
        'Non-cooperation; civil disobedience',
        'Civil disobedience; non-cooperation',
        'Satyagraha; hartal',
        'Fast; strike',
      ],
      answerIndex: 1,
      explanation: 'Champaran = first CIVIL DISOBEDIENCE (defying the indigo tinkathia system); Kheda = first NON-COOPERATION (peasants withholding revenue after crop failure). The order trips people up \u2014 anchor each to its place on the map.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click Dandi \u2014 where Gandhi broke the salt law on 6 April 1930.',
      answer: { lat: 20.88, lng: 72.79, toleranceKm: 90 },
      explanation: 'Dandi, a village on the Gujarat seacoast, ~375 km from Sabarmati Ashram. Gandhi walked 25 days with 78 chosen followers to pick up a handful of salt.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Why did Gandhi withdraw the Non-Cooperation Movement in February 1922?',
      options: [
        'The British granted dominion status',
        'The Chauri Chaura incident, where a mob burnt policemen in a police station',
        'The Khilafat issue was resolved',
        'Congress ordered him to',
      ],
      answerIndex: 1,
      explanation: 'Chauri Chaura convinced Gandhi the masses weren\u2019t ready for non-violent struggle. The withdrawal split the movement \u2014 Swarajists (council entry) vs no-changers.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'The Quit India resolution was passed on 8 August 1942 by the AICC meeting at:',
      options: ['Calcutta', 'Lahore', 'Bombay', 'Karachi'],
      answerIndex: 2,
      explanation: 'Bombay (Gowalia Tank). \u201cDo or Die.\u201d The entire leadership was arrested within hours, and the movement went underground.',
    },
    {
      id: 'q8',
      type: 'map_click',
      question: 'Click Jhansi \u2014 Rani Laxmibai\u2019s centre, annexed earlier under the Doctrine of Lapse.',
      answer: { lat: 25.45, lng: 78.57, toleranceKm: 80 },
      explanation: 'Jhansi, in Bundelkhand. Dalhousie\u2019s Doctrine of Lapse (no adopted heirs) had annexed it \u2014 the policy grievance and the 1857 leader meet in one place.',
    },
    {
      id: 'q9',
      type: 'mcq',
      question: 'Which Act followed directly from the 1857 revolt?',
      options: [
        'Regulating Act 1773',
        'Government of India Act 1858 \u2014 Crown rule replaces Company rule',
        'Indian Councils Act 1909',
        'Government of India Act 1935',
      ],
      answerIndex: 1,
      explanation: 'The GoI Act 1858 abolished East India Company rule and began the British Raj \u2014 direct government through the Crown\u2019s representatives.',
    },
  ],
};

import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// FORESTS & PROTECTED AREAS OF INDIA
//
// Concept:
//   India protects nature in concentric layers. Wildlife
//   sanctuaries protect species. National parks protect
//   landscapes. Tiger reserves protect apex predators
//   (and everything they eat). Biosphere reserves protect
//   whole ecosystems with humans in them.
//
// Key 2023-2025 numbers verified:
//   - Forest + tree cover: 25.17% of India (ISFR 2023)
//   - Forest cover alone: 21.76%
//   - National parks: 106-109 (sources vary; ISFR 2023)
//   - Tiger reserves: 58 (as of 2025)
//   - Biosphere reserves: 18 (12 in UNESCO MAB)
//   - Wild tigers: 3,682 (2022 census) = ~70-75% of world
//   - Highest forest % cover: Lakshadweep (91.33%),
//     then Mizoram (85.34%), then A&N (81.62%)
//
// Sources: ISFR 2023 (Forest Survey of India), PIB,
// PMF IAS, Drishti IAS, Wikipedia (Project Tiger).
// ============================================

const biosphereReserves: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'nilgiri', name: 'Nilgiri Biosphere Reserve (1986, India\u2019s first; UNESCO MAB)' }, geometry: { type: 'Point', coordinates: [76.6700, 11.4000] } },
    { type: 'Feature', properties: { id: 'nanda-devi-br', name: 'Nanda Devi BR (UNESCO MAB)' }, geometry: { type: 'Point', coordinates: [79.9707, 30.3760] } },
    { type: 'Feature', properties: { id: 'sundarbans', name: 'Sundarbans BR (UNESCO MAB; world\u2019s largest mangrove)' }, geometry: { type: 'Point', coordinates: [88.9000, 21.9500] } },
    { type: 'Feature', properties: { id: 'gulf-mannar', name: 'Gulf of Mannar BR (UNESCO MAB)' }, geometry: { type: 'Point', coordinates: [79.0000, 9.0000] } },
    { type: 'Feature', properties: { id: 'manas', name: 'Manas BR (UNESCO MAB; Assam)' }, geometry: { type: 'Point', coordinates: [90.9000, 26.7000] } },
    { type: 'Feature', properties: { id: 'nokrek', name: 'Nokrek BR (UNESCO MAB; Meghalaya)' }, geometry: { type: 'Point', coordinates: [90.3000, 25.4500] } },
    { type: 'Feature', properties: { id: 'simlipal', name: 'Simlipal BR (UNESCO MAB; Odisha)' }, geometry: { type: 'Point', coordinates: [86.3000, 21.7500] } },
    { type: 'Feature', properties: { id: 'khangchendzonga', name: 'Khangchendzonga BR (UNESCO MAB; Sikkim)' }, geometry: { type: 'Point', coordinates: [88.1475, 27.7025] } },
    { type: 'Feature', properties: { id: 'pachmarhi', name: 'Pachmarhi BR (UNESCO MAB; MP)' }, geometry: { type: 'Point', coordinates: [78.4300, 22.4700] } },
    { type: 'Feature', properties: { id: 'achanakmar', name: 'Achanakmar-Amarkantak BR (UNESCO MAB; Chhattisgarh\u2013MP)' }, geometry: { type: 'Point', coordinates: [81.7800, 22.4500] } },
    { type: 'Feature', properties: { id: 'agasthyamalai', name: 'Agasthyamalai BR (UNESCO MAB; Kerala\u2013Tamil Nadu)' }, geometry: { type: 'Point', coordinates: [77.2500, 8.6000] } },
    { type: 'Feature', properties: { id: 'great-nicobar', name: 'Great Nicobar BR (UNESCO MAB)' }, geometry: { type: 'Point', coordinates: [93.8000, 7.0000] } },
  ],
};

const keyNationalParks: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'jim-corbett', name: 'Jim Corbett NP (1936) \u2014 India\u2019s oldest; first tiger reserve' }, geometry: { type: 'Point', coordinates: [78.7747, 29.5300] } },
    { type: 'Feature', properties: { id: 'kaziranga', name: 'Kaziranga NP (UNESCO WHS) \u2014 70% of world\u2019s one-horned rhinos' }, geometry: { type: 'Point', coordinates: [93.1700, 26.5775] } },
    { type: 'Feature', properties: { id: 'gir', name: 'Gir NP (Gujarat) \u2014 last home of Asiatic lion' }, geometry: { type: 'Point', coordinates: [70.9650, 21.1240] } },
    { type: 'Feature', properties: { id: 'ranthambore', name: 'Ranthambore NP (Rajasthan) \u2014 famous tiger reserve' }, geometry: { type: 'Point', coordinates: [76.4400, 26.0173] } },
    { type: 'Feature', properties: { id: 'bandipur', name: 'Bandipur NP (Karnataka) \u2014 Nilgiri complex' }, geometry: { type: 'Point', coordinates: [76.6300, 11.6700] } },
    { type: 'Feature', properties: { id: 'kanha', name: 'Kanha NP (MP) \u2014 inspiration for The Jungle Book' }, geometry: { type: 'Point', coordinates: [80.6100, 22.3300] } },
    { type: 'Feature', properties: { id: 'sundarban-np', name: 'Sundarban NP \u2014 swimming Bengal tigers' }, geometry: { type: 'Point', coordinates: [88.9000, 21.9500] } },
    { type: 'Feature', properties: { id: 'periyar', name: 'Periyar NP (Kerala) \u2014 elephant reserve' }, geometry: { type: 'Point', coordinates: [77.2400, 9.4600] } },
    { type: 'Feature', properties: { id: 'silent-valley', name: 'Silent Valley NP (Kerala) \u2014 saved from dam, 1980s' }, geometry: { type: 'Point', coordinates: [76.4300, 11.0800] } },
    { type: 'Feature', properties: { id: 'phawngpui-np', name: 'Phawngpui NP (Mizoram) \u2014 Blue Mountain' }, geometry: { type: 'Point', coordinates: [92.8333, 22.6333] } },
    { type: 'Feature', properties: { id: 'murlen-np', name: 'Murlen NP (Mizoram) \u2014 evergreen forest, near Champhai' }, geometry: { type: 'Point', coordinates: [93.2700, 23.6300] } },
  ],
};

const tigerReserves: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'dampa', name: 'Dampa TR (Mizoram, declared 1994) \u2014 ~500 km\u00b2 core' }, geometry: { type: 'Point', coordinates: [92.3667, 23.5670] } },
    { type: 'Feature', properties: { id: 'sundarbans-tr', name: 'Sundarbans TR' }, geometry: { type: 'Point', coordinates: [88.9000, 21.9500] } },
    { type: 'Feature', properties: { id: 'corbett-tr', name: 'Corbett TR \u2014 highest tiger population' }, geometry: { type: 'Point', coordinates: [78.7747, 29.5300] } },
    { type: 'Feature', properties: { id: 'nagarjunsagar', name: 'Nagarjunsagar-Srisailam TR (AP) \u2014 largest by area' }, geometry: { type: 'Point', coordinates: [78.9500, 16.4200] } },
    { type: 'Feature', properties: { id: 'bandipur-tr', name: 'Bandipur TR (Karnataka)' }, geometry: { type: 'Point', coordinates: [76.6300, 11.6700] } },
    { type: 'Feature', properties: { id: 'kanha-tr', name: 'Kanha TR (MP)' }, geometry: { type: 'Point', coordinates: [80.6100, 22.3300] } },
    { type: 'Feature', properties: { id: 'bandhavgarh', name: 'Bandhavgarh TR (MP)' }, geometry: { type: 'Point', coordinates: [80.9800, 23.7000] } },
    { type: 'Feature', properties: { id: 'periyar-tr', name: 'Periyar TR (Kerala)' }, geometry: { type: 'Point', coordinates: [77.2400, 9.4600] } },
  ],
};

const biodiversityHotspots: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'wghats', name: 'Western Ghats \u2013 Sri Lanka Hotspot' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [73.0, 21.0], [74.5, 20.0], [76.5, 12.5], [77.0, 8.5],
          [76.0, 8.5], [75.5, 11.0], [73.5, 15.5], [72.5, 19.0], [73.0, 21.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'ehimalaya', name: 'Eastern Himalayas Hotspot' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [88.0, 26.0], [92.5, 26.5], [97.0, 28.5], [97.0, 29.5],
          [92.0, 29.0], [88.5, 28.0], [88.0, 26.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'indoburma', name: 'Indo-Burma Hotspot \u2014 includes Mizoram' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [91.5, 26.0], [97.0, 26.0], [97.0, 21.5], [92.0, 21.5], [91.5, 26.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'sundaland', name: 'Sundaland Hotspot \u2014 Nicobar Islands' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [92.5, 9.0], [94.0, 9.0], [94.0, 6.5], [92.5, 6.5], [92.5, 9.0],
        ]],
      },
    },
  ],
};

const highForestStates: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'mizoram-fc', name: 'Mizoram \u2014 85.34% (2nd highest in India)', pct: 85.34 }, geometry: { type: 'Point', coordinates: [92.7, 23.5] } },
    { type: 'Feature', properties: { id: 'lakshadweep-fc', name: 'Lakshadweep \u2014 91.33% (highest)', pct: 91.33 }, geometry: { type: 'Point', coordinates: [72.0, 10.5] } },
    { type: 'Feature', properties: { id: 'anIsland-fc', name: 'A&N Islands \u2014 81.62%', pct: 81.62 }, geometry: { type: 'Point', coordinates: [92.8, 10.0] } },
    { type: 'Feature', properties: { id: 'arunachal-fc', name: 'Arunachal Pradesh \u2014 ~79%', pct: 79 }, geometry: { type: 'Point', coordinates: [94.5, 28.0] } },
    { type: 'Feature', properties: { id: 'meghalaya-fc', name: 'Meghalaya \u2014 ~76%', pct: 76 }, geometry: { type: 'Point', coordinates: [91.4, 25.6] } },
    { type: 'Feature', properties: { id: 'nagaland-fc', name: 'Nagaland \u2014 ~74%', pct: 74 }, geometry: { type: 'Point', coordinates: [94.5, 26.0] } },
  ],
};

export const forestsChapter: Chapter = {
  id: 'forests-protected-areas',
  subject: 'geography',
  unit: 'India Physical',
  tags: ['western-ghats', 'himalayas', 'purvanchal', 'islands', 'biodiversity'],
  title: 'Forests & Protected Areas',
  summary: 'India\u2019s forest cover, biodiversity hotspots, national parks, tiger reserves, and biosphere reserves.',
  focus:
    'India protects nature in concentric layers \u2014 sanctuaries for species, parks for landscapes, tiger reserves for whole food chains, biosphere reserves for ecosystems including humans. The northeast (especially Mizoram) carries the highest forest cover by percentage.',

  view: { center: [22.5, 80.0], zoom: 5 },
  basemap: 'physical',

  layers: [
    {
      id: 'hotspots',
      name: 'Biodiversity Hotspots in India',
      description: 'India has 4 of the world\u2019s 36 biodiversity hotspots: Western Ghats, Eastern Himalayas, Indo-Burma, Sundaland (Nicobar).',
      kind: 'vector',
      data: biodiversityHotspots,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#2d6a4f', fillColor: '#5fa580', fillOpacity: 0.4, weight: 1.5, pattern: 'dots' },
    },
    {
      id: 'biosphere-reserves',
      name: 'Biosphere Reserves (12 UNESCO MAB)',
      description: 'India has 18 biosphere reserves; 12 are part of UNESCO\u2019s Man and Biosphere network.',
      kind: 'vector',
      data: biosphereReserves,
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'national-parks',
      name: 'Key National Parks',
      description: 'India has ~106 national parks. These are the most exam-relevant ones (incl. Mizoram\u2019s Phawngpui and Murlen).',
      kind: 'vector',
      data: keyNationalParks,
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'tiger-reserves',
      name: 'Tiger Reserves (58)',
      description: 'As of 2025: 58 tiger reserves. India hosts ~3,682 wild tigers (2022) \u2014 ~70-75% of the world\u2019s.',
      kind: 'vector',
      data: tigerReserves,
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'high-forest-states',
      name: 'States with >75% Forest Cover',
      description: '8 states/UTs have over 75% forest cover \u2014 all but Lakshadweep & A&N are NE states.',
      kind: 'vector',
      data: highForestStates,
      defaultOn: true,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'India\u2019s total forest and tree cover is 25.17% of the geographical area (ISFR 2023). Forest cover alone is 21.76%; tree cover (small patches, agroforestry) is 3.41%. The National Forest Policy 1988 targets 33% \u2014 the country is still well below that.',
    },
    {
      id: 'f2',
      text: 'States with the highest forest cover by AREA: Madhya Pradesh (77,073 km\u00b2) leads, then Arunachal Pradesh (65,882 km\u00b2) and Chhattisgarh (55,812 km\u00b2). States with the highest forest cover by PERCENTAGE: Lakshadweep (91.33%), Mizoram (85.34%), Andaman & Nicobar (81.62%).',
      linkedLayerId: 'high-forest-states',
    },
    {
      id: 'f3',
      text: 'Eight states/UTs have over 75% forest cover: Lakshadweep, Mizoram, A&N Islands, Arunachal Pradesh, Nagaland, Meghalaya, Tripura, Manipur \u2014 mostly the northeast. The NE region as a whole has 67% forest cover, far above the national average.',
      linkedLayerId: 'high-forest-states',
    },
    {
      id: 'f4',
      text: 'Mizoram is in a special position. It has the maximum INCREASE in forest cover in ISFR 2023 (+242 km\u00b2) AND the 2nd highest cover by percentage. Combined with declining cover in neighbouring NE states, Mizoram is becoming the green anchor of the region.',
      linkedFeatureId: 'mizoram-fc',
    },
    {
      id: 'f5',
      text: 'Protected Areas in India come in four legal categories under the Wildlife Protection Act, 1972: National Parks (IUCN Cat II), Wildlife Sanctuaries (IUCN Cat IV), Conservation Reserves, and Community Reserves. Together they cover ~5.28% of India.',
    },
    {
      id: 'f6',
      text: 'India has approximately 106 National Parks (number varies slightly across sources and updates). Jim Corbett (Uttarakhand, established 1936) is the oldest. Madhya Pradesh has the most national parks. Hemis NP in Ladakh is the largest by area.',
      linkedLayerId: 'national-parks',
    },
    {
      id: 'f7',
      text: 'Project Tiger was launched on 1 April 1973 by PM Indira Gandhi after a 1972 census revealed only 1,800 tigers remained (from ~40,000 a century earlier). It started with 9 reserves; today there are 58 tiger reserves covering ~84,500 km\u00b2.',
      linkedLayerId: 'tiger-reserves',
    },
    {
      id: 'f8',
      text: 'India\u2019s 2022 tiger census counted 3,682 wild tigers \u2014 about 70-75% of the world\u2019s wild tiger population. Madhya Pradesh and Maharashtra have 6 tiger reserves each (the most). Corbett Tiger Reserve has the highest tiger population and density.',
      linkedLayerId: 'tiger-reserves',
    },
    {
      id: 'f9',
      text: 'Mizoram\u2019s Dampa Tiger Reserve (declared 1994) is in western Mizoram, bordering Bangladesh. Core area ~500 km\u00b2. It is the largest wildlife sanctuary in Mizoram. Tiger numbers here are low \u2014 the reserve has struggled with shifting cultivation and a border fence that blocks tiger movement.',
      linkedFeatureId: 'dampa',
    },
    {
      id: 'f10',
      text: 'India has 18 Biosphere Reserves; 12 of them are part of UNESCO\u2019s Man and Biosphere (MAB) network. Each has three concentric zones: Core (strictly protected), Buffer (research and tourism), and Transition (sustainable human use).',
      linkedLayerId: 'biosphere-reserves',
    },
    {
      id: 'f11',
      text: 'Nilgiri (Tamil Nadu \u2013 Karnataka \u2013 Kerala) was India\u2019s FIRST biosphere reserve (1986). It hosts the largest tiger population in South Asia across Bandipur, Nagarhole, Mudumalai, and Wayanad.',
      linkedFeatureId: 'nilgiri',
    },
    {
      id: 'f12',
      text: 'India has FOUR of the world\u2019s 36 biodiversity hotspots: (1) Western Ghats & Sri Lanka, (2) Eastern Himalayas, (3) Indo-Burma (which includes Mizoram and most of NE India), (4) Sundaland (the Nicobar Islands). Mizoram falls squarely in the Indo-Burma hotspot.',
      linkedLayerId: 'hotspots',
    },
    {
      id: 'f13',
      text: 'Famous one-off conservation facts often asked: Kaziranga (Assam, UNESCO WHS) hosts ~70% of the world\u2019s one-horned rhinos. Gir (Gujarat) is the only remaining home of the Asiatic lion. Sundarbans has the only swimming tigers (salt-adapted). Kanha (MP) inspired Kipling\u2019s Jungle Book. Silent Valley (Kerala) was saved from a dam in the 1980s.',
      linkedLayerId: 'national-parks',
    },
    {
      id: 'f14',
      text: 'Mizoram has 2 National Parks: Phawngpui (Blue Mountain) NP and Murlen NP. Phawngpui surrounds the highest peak in Mizoram. Murlen lies near Champhai in eastern Mizoram, with evergreen sub-tropical forest.',
      linkedLayerId: 'national-parks',
    },
    {
      id: 'f15',
      text: 'India\u2019s mangrove cover is ~4,992 km\u00b2 (0.15% of geographical area). The Sundarbans (West Bengal) is the world\u2019s largest mangrove forest. Mangroves are critical against cyclones, coastal erosion, and carbon storage.',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'According to ISFR 2023, which state has the highest forest cover by percentage of geographical area?',
      options: ['Mizoram', 'Lakshadweep', 'Arunachal Pradesh', 'Madhya Pradesh'],
      answerIndex: 1,
      explanation: 'Lakshadweep tops at 91.33%, then Mizoram (85.34%), then A&N Islands (81.62%). MP has the highest by AREA but lower by percentage. Be careful \u2014 UPSC loves to test the area-vs-percentage distinction.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Which state reported the maximum INCREASE in forest cover in ISFR 2023?',
      options: ['Gujarat', 'Mizoram', 'Odisha', 'Madhya Pradesh'],
      answerIndex: 1,
      explanation: 'Mizoram led with a +242 km\u00b2 increase in forest cover, followed by Gujarat (+180) and Odisha (+152). MP actually saw the LARGEST DECREASE (\u2212612 km\u00b2). Mizoram has become the green anchor of the NE.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click the location of Dampa Tiger Reserve.',
      answer: { lat: 23.57, lng: 92.37, toleranceKm: 80 },
      explanation: 'Dampa Tiger Reserve lies in western Mizoram, near the Bangladesh border. Declared in 1994 with a ~500 km\u00b2 core, it is the largest wildlife sanctuary in Mizoram.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Project Tiger was launched in:',
      options: ['1972', '1973', '1980', '2006'],
      answerIndex: 1,
      explanation: '1 April 1973, launched by PM Indira Gandhi after the 1972 Wildlife Protection Act and a census that found only 1,800 tigers left. By 2022, India had 3,682 wild tigers.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'How many of the world\u2019s 36 biodiversity hotspots are in India?',
      options: ['2', '3', '4', '5'],
      answerIndex: 2,
      explanation: 'India has 4 biodiversity hotspots: Western Ghats & Sri Lanka, Eastern Himalayas, Indo-Burma (includes Mizoram and most of NE India), and Sundaland (Nicobar Islands).',
    },
    {
      id: 'q6',
      type: 'map_click',
      question: 'Click the location of the Nilgiri Biosphere Reserve \u2014 India\u2019s first.',
      answer: { lat: 11.4, lng: 76.67, toleranceKm: 150 },
      explanation: 'Nilgiri BR (1986) spans Karnataka, Tamil Nadu, and Kerala. It contains Bandipur, Nagarhole, Mudumalai, and Wayanad \u2014 the largest tiger population in South Asia.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'Which biodiversity hotspot does Mizoram lie in?',
      options: ['Western Ghats', 'Eastern Himalayas', 'Indo-Burma', 'Sundaland'],
      answerIndex: 2,
      explanation: 'Mizoram is firmly in the Indo-Burma biodiversity hotspot \u2014 the largest of the four in India, covering most of NE India south of the Brahmaputra.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Which of the following is NOT a UNESCO World Heritage Site?',
      options: ['Kaziranga', 'Sundarbans', 'Manas', 'Bandhavgarh'],
      answerIndex: 3,
      explanation: 'Bandhavgarh is a famous tiger reserve in MP but NOT a UNESCO WHS. Kaziranga, Sundarbans, and Manas are all UNESCO Natural WHS.',
    },
  ],
};

import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// RESOURCES & INDUSTRIAL REGIONS OF THE WORLD
//
// Concept:
//   "Industry sits where its inputs are cheapest to assemble \u2014
//   so every great industrial region is parked on a coalfield,
//   an ore belt, or a port. Map the minerals and the factories
//   locate themselves."
//
// Source: Geography 2nd slide (GS-1 Unit 4, Part 2), Rf Ralte.
// ============================================

const industrialRegions: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'ruhr', name: 'Ruhr (Germany) \u2014 Europe\u2019s classic coal\u2013steel region' }, geometry: { type: 'Point', coordinates: [7.2, 51.5] } },
    { type: 'Feature', properties: { id: 'great-lakes', name: 'Great Lakes (N. America) \u2014 iron (Mesabi) + coal (Appalachia) meet on cheap water transport' }, geometry: { type: 'Point', coordinates: [-83.0, 42.5] } },
    { type: 'Feature', properties: { id: 'manchuria', name: 'Manchuria (NE China) \u2014 largest coal industry of China; Anshan iron & steel' }, geometry: { type: 'Point', coordinates: [123.4, 41.8] } },
    { type: 'Feature', properties: { id: 'kyushu', name: 'Northern Kyushu (Japan) \u2014 coal, iron & steel' }, geometry: { type: 'Point', coordinates: [130.7, 33.7] } },
    { type: 'Feature', properties: { id: 'chotanagpur', name: 'Chotanagpur plateau (India) \u2014 steel, cement, paper; Jamshedpur, Hazaribagh' }, geometry: { type: 'Point', coordinates: [85.8, 23.4] } },
    { type: 'Feature', properties: { id: 'delhi-ncr', name: 'Delhi NCR \u2014 textiles, pharma, consumer goods (Faridabad, Ghaziabad, Noida, Gurgaon)' }, geometry: { type: 'Point', coordinates: [77.2, 28.6] } },
  ],
};

const ironBelts: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'carajas', name: 'Carajas\u2013Itabira\u2013Minas Gerais (Brazil)' }, geometry: { type: 'Point', coordinates: [-49.9, -6.1] } },
    { type: 'Feature', properties: { id: 'ural-iron', name: 'Ural / Magnitogorsk (Russia\u2013Kazakhstan)' }, geometry: { type: 'Point', coordinates: [59.0, 53.4] } },
    { type: 'Feature', properties: { id: 'mesabi', name: 'Great Lakes\u2013Labrador (N. America)' }, geometry: { type: 'Point', coordinates: [-92.5, 47.5] } },
    { type: 'Feature', properties: { id: 'pilbara', name: 'Australia \u2014 Koolyanobbing, Iron Knob, Iron Duke' }, geometry: { type: 'Point', coordinates: [119.5, -30.9] } },
    { type: 'Feature', properties: { id: 'odisha-iron', name: 'India \u2014 Odisha\u2013Jharkhand belt: Sundergarh, Mayurbhanj; Noamundi & Gua (Singhbhum)' }, geometry: { type: 'Point', coordinates: [85.5, 22.3] } },
    { type: 'Feature', properties: { id: 'bailadila', name: 'India \u2014 Chhattisgarh: Durg, Dantewada, Bailadila' }, geometry: { type: 'Point', coordinates: [81.2, 18.7] } },
    { type: 'Feature', properties: { id: 'ballari', name: 'India \u2014 Karnataka: Sandur\u2013Hospet (Ballari), Kudremukh, Baba Budan hills' }, geometry: { type: 'Point', coordinates: [76.5, 15.1] } },
  ],
};

const coalFields: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'silesia', name: 'Europe \u2014 Ruhr, Upper Silesia, Durham/Cumberland' }, geometry: { type: 'Point', coordinates: [19.0, 50.3] } },
    { type: 'Feature', properties: { id: 'appalachia', name: 'USA \u2014 Appalachian fields (Kentucky, Illinois, Indiana\u2026)' }, geometry: { type: 'Point', coordinates: [-83.5, 37.8] } },
    { type: 'Feature', properties: { id: 'shansi', name: 'China \u2014 Shansi, Sichuan, Fushun, Shenyang' }, geometry: { type: 'Point', coordinates: [112.5, 37.8] } },
    { type: 'Feature', properties: { id: 'kuznetsk', name: 'Russia \u2014 Moscow, Ob & Lena basins, E. Siberia' }, geometry: { type: 'Point', coordinates: [87.1, 55.3] } },
    { type: 'Feature', properties: { id: 'damodar', name: 'India \u2014 Jharia, Bokaro, Raniganj (Damodar valley); Korba, Singrauli, Talcher, Neyveli, Singareni' }, geometry: { type: 'Point', coordinates: [86.4, 23.7] } },
    { type: 'Feature', properties: { id: 'nsw', name: 'Australia \u2014 Newcastle, Brisbane, Ipswich' }, geometry: { type: 'Point', coordinates: [151.7, -32.9] } },
  ],
};

const otherMinerals: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'chile-cu', name: 'COPPER \u2014 Chile (27% of world output): Escondida, Collahuasi; Peru next (10%)' }, geometry: { type: 'Point', coordinates: [-69.1, -24.3] } },
    { type: 'Feature', properties: { id: 'india-cu', name: 'COPPER (India) \u2014 Singhbhum (JH), Balaghat (MP), Jhunjhunu\u2013Alwar (RJ)' }, geometry: { type: 'Point', coordinates: [75.4, 27.9] } },
    { type: 'Feature', properties: { id: 'gulf-oil', name: 'PETROLEUM \u2014 the Persian Gulf: the world\u2019s densest reserves' }, geometry: { type: 'Point', coordinates: [50.5, 27.5] } },
    { type: 'Feature', properties: { id: 'india-oil', name: 'PETROLEUM (India) \u2014 Mumbai High, Assam (Digboi), Gujarat (Ankleshwar)' }, geometry: { type: 'Point', coordinates: [71.3, 19.3] } },
  ],
};

export const worldResourcesChapter: Chapter = {
  id: 'world-resources-industries',
  subject: 'geography',
  unit: 'World',
  tags: ['chotanagpur', 'coal', 'iron-ore', 'peninsular-plateau', 'ruhr', 'jharkhand', 'deccan'],
  title: 'World: Resources & Industry',
  summary: 'Why industry sits where it does \u2014 iron, coal, copper, oil belts mapped.',
  focus:
    'Industry sits where its inputs are cheapest to assemble \u2014 so every great industrial region is parked on a coalfield, an ore belt, or a port. Map the minerals first and the factory regions locate themselves.',
  view: { center: [22.0, 40.0], zoom: 2 },
  worldExtent: true,
  basemap: 'relief',
  theme: { accent: '#8a5a2b', mapBg: '#f2ede4' },

  layers: [
    { id: 'industrial-regions', name: 'Industrial regions', kind: 'vector', data: industrialRegions, style: { color: '#8a5a2b', weight: 2, fillColor: '#8a5a2b', markerRadius: 8, glow: true }, defaultOn: true, labelKey: 'name' },
    { id: 'iron-belts', name: 'Iron-ore belts', kind: 'vector', data: ironBelts, style: { color: '#b3261e', weight: 2, fillColor: '#b3261e', markerRadius: 6 }, defaultOn: true, labelKey: 'name' },
    { id: 'coal-fields', name: 'Coalfields', kind: 'vector', data: coalFields, style: { color: '#3d3833', weight: 2, fillColor: '#3d3833', markerRadius: 6 }, defaultOn: false, labelKey: 'name' },
    { id: 'other-minerals', name: 'Copper & petroleum', kind: 'vector', data: otherMinerals, style: { color: '#1f5fa8', weight: 2, fillColor: '#1f5fa8', markerRadius: 6 }, defaultOn: false, labelKey: 'name' },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Location factors, geographical: raw materials (steel near ore), power (coal/hydro/oil), transport (roads, rail, PORTS), labour (skilled or cheap \u2014 textiles chase workforces), water (iron & steel, textiles, chemicals are thirsty), flat land and moderate climate, market proximity (consumer goods).',
    },
    {
      id: 'f2',
      text: 'Non-geographical factors: capital and loans, investment climate, government policy (subsidised power, tax breaks, siting rules against pollution and over-clustering), pressure groups \u2014 and INDUSTRIAL INERTIA: the tendency of industry to stay put even after its original locational advantage is gone.',
    },
    {
      id: 'f3',
      text: 'Sector logic: PRIMARY industries (mining, forestry, agriculture) sit on the resource itself; SECONDARY (manufacturing) minimises assembly cost of materials + energy + labour; TERTIARY (services) follows market demand and population density. Industrialisation then grows the towns around it.',
    },
    {
      id: 'f4',
      text: 'Classic industrial regions: RUHR (Germany) \u2014 the coal\u2013steel template; GREAT LAKES (N. America) \u2014 Mesabi iron meets Appalachian coal on cheap lake transport; MANCHURIA \u2014 China\u2019s biggest coal industry, Anshan steel; NORTHERN KYUSHU \u2014 Japan\u2019s coal\u2013steel cradle; in India, the CHOTANAGPUR plateau (steel\u2013cement\u2013paper: Jamshedpur, Hazaribagh) and the market-driven DELHI NCR belt (textiles, leather, pharma, consumer goods).',
      linkedLayerId: 'industrial-regions',
    },
    {
      id: 'f5',
      text: 'IRON ORE (world reserves ~3,20,000 million tonnes): N. America (Great Lakes, Labrador), Russia\u2013Kazakhstan (Urals, Magnitogorsk), Brazil (Carajas, Itabira, Minas Gerais), Australia (Koolyanobbing, Iron Knob/Iron Duke), Europe (Lorraine, S. Wales), Africa (Transvaal, Liberia), China (Manchuria, Anshan).',
      linkedLayerId: 'iron-belts',
    },
    {
      id: 'f6',
      text: 'IRON ORE, India \u2014 ~95% of reserves in Odisha, Jharkhand, Chhattisgarh, Karnataka, Goa, TN, AP, Telangana. Belts: Odisha (Sundergarh, Mayurbhanj); Jharkhand (oldest mines \u2014 Noamundi & Gua in Singhbhum); Chhattisgarh (Durg, Dantewada, BAILADILA); Karnataka (Sandur\u2013Hospet in Ballari, Baba Budan hills, Kudremukh); plus Goa, Maharashtra (Chandrapur, Ratnagiri) and Tamil Nadu (Salem, Nilgiris).',
      linkedLayerId: 'iron-belts',
    },
    {
      id: 'f7',
      text: 'COAL \u2014 the most UNEVENLY distributed mineral; used for thermal power and smelting. China (Shansi, Fushun, Shenyang), USA (Appalachia: Kentucky, Illinois\u2026), Europe (Ruhr, Upper Silesia, Durham), Russia (Moscow, Ob & Lena basins), Australia (Newcastle), Africa (Transvaal, Natal). India: JHARIA, BOKARO, RANIGANJ on the Damodar; Korba, Singrauli, Talcher, Singareni; NEYVELI = lignite.',
      linkedLayerId: 'coal-fields',
    },
    {
      id: 'f8',
      text: 'COPPER \u2014 CHILE leads with ~27% of world output (Escondida and Collahuasi are among the biggest mines on earth); PERU next (~10%). India: Singhbhum (Jharkhand), Balaghat (MP), Jhunjhunu & Alwar (Rajasthan). Resources split: RENEWABLE (solar, wind \u2014 replenish fast) vs NON-RENEWABLE (coal, petroleum, gas \u2014 fixed stock, millennia to renew).',
      linkedLayerId: 'other-minerals',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: '\u201cIndustrial inertia\u201d means:',
      options: [
        'Industries always chase the cheapest labour',
        'Industries tend to stay in a location even after its original advantage has disappeared',
        'Government freezes on new factories',
        'The slowdown of heavy industry',
      ],
      answerIndex: 1,
      explanation: 'The predisposition of firms to avoid relocating even when the founding advantage (a coalfield, a port subsidy) is gone \u2014 sunk capital, linked suppliers and skilled labour hold them in place.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click the Ruhr \u2014 Europe\u2019s classic coal-and-steel industrial region.',
      answer: { lat: 51.5, lng: 7.2, toleranceKm: 500 },
      explanation: 'The Ruhr in western Germany: coal seams + Rhine transport + iron (initially local, later imported Lorraine/Swedish ore) = the template every textbook uses.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Roughly what share of India\u2019s iron-ore reserves lies in Odisha, Jharkhand, Chhattisgarh, Karnataka, Goa, TN, AP and Telangana together?',
      options: ['50%', '70%', '95%', '25%'],
      answerIndex: 2,
      explanation: 'About 95% \u2014 the peninsular shield holds the ore. Flagship mines: Noamundi & Gua (Singhbhum, Jharkhand \u2014 the oldest), Bailadila (Chhattisgarh), Sandur\u2013Hospet (Ballari, Karnataka).',
    },
    {
      id: 'q4',
      type: 'map_click',
      question: 'Click the Damodar valley coal belt \u2014 Jharia, Bokaro, Raniganj.',
      answer: { lat: 23.7, lng: 86.4, toleranceKm: 250 },
      explanation: 'The Damodar valley (Jharkhand\u2013West Bengal) is India\u2019s prime coking-coal store \u2014 which is exactly why the Chotanagpur industrial region (Jamshedpur!) sits beside it.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'The world\u2019s leading copper producer, with ~27% of output and the Escondida mine, is:',
      options: ['Peru', 'Chile', 'DR Congo', 'Australia'],
      answerIndex: 1,
      explanation: 'Chile \u2014 Escondida and Collahuasi are among the biggest mines on earth. Peru follows at ~10%. In India: Singhbhum, Balaghat, Jhunjhunu\u2013Alwar.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Neyveli (Tamil Nadu) is best known for:',
      options: ['Iron ore', 'Lignite coal', 'Copper', 'Bauxite'],
      answerIndex: 1,
      explanation: 'Neyveli mines LIGNITE (brown coal) feeding thermal power. The hard-coal heartland is the Damodar valley: Jharia, Bokaro, Raniganj.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'Which factor best explains the Great Lakes industrial region?',
      options: [
        'Cheap labour from the South',
        'Mesabi iron ore meeting Appalachian coal over cheap water transport',
        'Proximity to the Pacific ports',
        'Government subsidies alone',
      ],
      answerIndex: 1,
      explanation: 'Iron from the Mesabi range sailed down the lakes to meet Appalachian coal \u2014 assembly cost minimised on water, the cheapest transport. Same logic as the Ruhr and Chotanagpur.',
    },
  ],
};

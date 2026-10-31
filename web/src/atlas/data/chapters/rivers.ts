import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// RIVERS OF INDIA
//
// Concept:
//   India has two great river families. The Himalayan rivers
//   (Indus, Ganga, Brahmaputra) are snow-fed and perennial.
//   The Peninsular rivers (Godavari, Krishna, Kaveri, Narmada,
//   Tapi, Mahanadi) are rain-fed and seasonal. Origin determines
//   character: Himalayan = young, fast, fertile-floodplain;
//   Peninsular = old, mature, stable course.
//
// Coordinates traced from public references. Lines are
// simplified for educational clarity \u2014 they show the route,
// not exact channel.
// ============================================

// ---------- Himalayan River System ----------

const indusSystem: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'indus', name: 'Indus (origin: Mansarovar, Tibet)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [81.45, 30.65], [79.5, 32.5], [77.5, 33.8], [75.8, 34.5],
          [74.0, 34.0], [72.0, 33.0], [70.5, 30.0], [68.5, 27.0],
          [67.5, 24.0], [67.3, 23.5],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'jhelum', name: 'Jhelum' },
      geometry: {
        type: 'LineString',
        coordinates: [[75.2, 33.7], [74.4, 33.5], [73.3, 32.7], [72.0, 31.3]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'chenab', name: 'Chenab' },
      geometry: {
        type: 'LineString',
        coordinates: [[77.2, 32.7], [75.6, 33.0], [74.0, 32.3], [72.4, 30.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'ravi', name: 'Ravi' },
      geometry: {
        type: 'LineString',
        coordinates: [[77.0, 32.4], [75.7, 32.4], [74.9, 31.7], [73.5, 30.2]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'beas', name: 'Beas' },
      geometry: {
        type: 'LineString',
        coordinates: [[77.5, 32.4], [76.5, 31.8], [75.8, 31.0], [74.9, 30.7]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'satluj', name: 'Satluj' },
      geometry: {
        type: 'LineString',
        coordinates: [[81.4, 30.7], [79.0, 31.0], [76.8, 31.0], [75.5, 30.7], [74.0, 30.5]],
      },
    },
  ],
};

const gangaSystem: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'ganga', name: 'Ganga (origin: Gangotri Glacier)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [78.94, 30.99], [78.4, 30.0], [78.0, 29.5], [78.2, 28.5],
          [79.5, 27.5], [81.0, 26.5], [83.0, 25.5], [85.0, 25.4],
          [86.5, 25.3], [87.5, 24.6], [88.0, 24.0], [88.4, 23.0], [88.6, 22.0], [89.0, 21.6],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'yamuna', name: 'Yamuna (origin: Yamunotri Glacier)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [78.44, 30.99], [78.0, 30.5], [77.5, 29.5], [77.3, 28.5],
          [77.4, 27.5], [78.5, 26.5], [80.0, 26.0], [81.0, 25.7], [81.85, 25.43],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'chambal', name: 'Chambal (rises in Vindhyas, joins Yamuna)' },
      geometry: {
        type: 'LineString',
        coordinates: [[75.3, 22.4], [76.0, 24.0], [76.8, 25.0], [78.0, 26.5], [79.0, 26.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'son', name: 'Son (rises in Amarkantak, joins Ganga)' },
      geometry: {
        type: 'LineString',
        coordinates: [[81.75, 22.65], [82.0, 24.0], [83.5, 25.0], [84.9, 25.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'ghaghara', name: 'Ghaghara' },
      geometry: {
        type: 'LineString',
        coordinates: [[81.0, 30.2], [81.5, 29.0], [82.0, 27.5], [83.5, 26.0], [84.6, 25.7]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'gandak', name: 'Gandak' },
      geometry: {
        type: 'LineString',
        coordinates: [[83.7, 28.7], [84.0, 27.5], [84.5, 26.5], [85.0, 25.6]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'kosi', name: 'Kosi (Bihar\u2019s Sorrow)' },
      geometry: {
        type: 'LineString',
        coordinates: [[86.6, 28.0], [86.7, 27.0], [86.9, 26.0], [87.2, 25.4]],
      },
    },
  ],
};

const brahmaputraSystem: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'brahmaputra', name: 'Brahmaputra (Tibet: Tsangpo; Arunachal: Dihang)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [82.0, 30.7], [87.0, 29.3], [91.0, 29.5], [94.5, 29.5], [95.5, 28.5],
          [95.0, 27.7], [94.0, 27.5], [92.5, 27.0], [90.5, 26.5],
          [88.5, 26.0], [86.5, 25.5], [90.0, 24.0], [90.5, 23.5], [91.0, 22.8],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'subansiri', name: 'Subansiri (largest Brahmaputra tributary)' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.5, 28.8], [94.0, 28.0], [94.4, 27.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'manas', name: 'Manas' },
      geometry: {
        type: 'LineString',
        coordinates: [[91.0, 27.5], [90.8, 26.8], [90.7, 26.2]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'teesta', name: 'Teesta' },
      geometry: {
        type: 'LineString',
        coordinates: [[88.6, 28.0], [88.5, 27.0], [88.6, 26.3], [89.5, 25.8]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'barak', name: 'Barak (drains NE hills, joins Meghna in Bangladesh)' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.5, 24.5], [92.8, 24.8], [92.0, 24.8], [91.5, 24.5], [91.0, 24.0]],
      },
    },
  ],
};

// ---------- Peninsular River System (east-flowing) ----------

const eastFlowingPeninsular: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'mahanadi', name: 'Mahanadi (rises in Chhattisgarh)' },
      geometry: {
        type: 'LineString',
        coordinates: [[81.3, 20.1], [82.0, 20.5], [83.0, 21.0], [84.5, 20.7], [86.0, 20.5], [86.7, 20.3]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'godavari', name: 'Godavari \u2014 longest peninsular river ("Dakshin Ganga")' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [73.55, 19.96], [74.5, 20.0], [76.0, 19.5], [77.5, 19.0], [79.0, 18.7],
          [80.5, 18.3], [82.0, 17.7], [82.3, 16.9],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'krishna', name: 'Krishna (rises at Mahabaleshwar)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [73.65, 17.92], [75.0, 17.5], [76.5, 16.8], [78.0, 16.5], [79.5, 16.5], [80.8, 16.0], [81.0, 15.8],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'kaveri', name: 'Kaveri / Cauvery (rises in Talakaveri, Kodagu)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [75.5, 12.4], [76.5, 12.5], [77.5, 12.0], [78.5, 11.5], [79.5, 11.2], [79.8, 11.0],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tungabhadra', name: 'Tungabhadra (Krishna tributary)' },
      geometry: {
        type: 'LineString',
        coordinates: [[75.2, 13.5], [75.8, 14.5], [76.5, 15.3], [77.5, 16.0]],
      },
    },
  ],
};

// ---------- Peninsular West-flowing (the two that go the other way) ----------

const westFlowingPeninsular: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'narmada', name: 'Narmada (origin: Amarkantak) \u2014 flows in a rift valley' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [81.76, 22.67], [80.5, 22.5], [78.5, 22.5], [76.5, 22.3], [74.5, 22.0], [73.0, 21.8], [72.6, 21.7],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tapi', name: 'Tapi / Tapti (origin: Multai, MP)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [78.25, 21.77], [77.0, 21.5], [75.0, 21.3], [73.5, 21.2], [72.8, 21.3],
        ],
      },
    },
  ],
};

// ---------- Mizoram rivers ----------

const mizoramRivers: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'tlawng', name: 'Tlawng (Dhaleshwari) \u2014 longest river in Mizoram, ~185 km. Flows N to Barak.' },
      geometry: {
        type: 'LineString',
        coordinates: [[92.85, 22.95], [92.7, 23.4], [92.65, 23.9], [92.7, 24.3], [92.8, 24.7]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tuirial', name: 'Tuirial (Sonai) \u2014 hydropower; flows N to Barak.' },
      geometry: {
        type: 'LineString',
        coordinates: [[92.95, 23.3], [92.9, 23.8], [92.85, 24.2], [92.8, 24.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tuivawl', name: 'Tuivawl \u2014 NE-flowing; tributary of Barak.' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.1, 23.5], [93.0, 24.0], [92.95, 24.3]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'chhimtuipui', name: 'Chhimtuipui / Kolodyne / Kaladan \u2014 biggest river in Mizoram. Originates Myanmar, returns to Myanmar.' },
      geometry: {
        type: 'LineString',
        coordinates: [[93.5, 23.3], [93.2, 22.7], [92.9, 22.4], [92.8, 22.2], [93.0, 22.0], [93.3, 21.8]],
      },
    },
  ],
};

// ---------- Origin points ----------

const riverOrigins: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'mansarovar', name: 'Mansarovar Lake \u2014 origin of Indus, Satluj, Brahmaputra (region)' }, geometry: { type: 'Point', coordinates: [81.45, 30.65] } },
    { type: 'Feature', properties: { id: 'gangotri', name: 'Gangotri Glacier \u2014 origin of Ganga (Bhagirathi)' }, geometry: { type: 'Point', coordinates: [78.9398, 30.9947] } },
    { type: 'Feature', properties: { id: 'yamunotri', name: 'Yamunotri Glacier \u2014 origin of Yamuna' }, geometry: { type: 'Point', coordinates: [78.4434, 30.9939] } },
    { type: 'Feature', properties: { id: 'amarkantak', name: 'Amarkantak \u2014 origin of Narmada and Son' }, geometry: { type: 'Point', coordinates: [81.7616, 22.6707] } },
    { type: 'Feature', properties: { id: 'multai', name: 'Multai (MP) \u2014 origin of Tapi' }, geometry: { type: 'Point', coordinates: [78.2500, 21.7700] } },
    { type: 'Feature', properties: { id: 'mahabaleshwar', name: 'Mahabaleshwar \u2014 origin of Krishna' }, geometry: { type: 'Point', coordinates: [73.6500, 17.9200] } },
    { type: 'Feature', properties: { id: 'trimbak', name: 'Trimbakeshwar \u2014 origin of Godavari' }, geometry: { type: 'Point', coordinates: [73.5500, 19.9600] } },
    { type: 'Feature', properties: { id: 'talakaveri', name: 'Talakaveri \u2014 origin of Kaveri' }, geometry: { type: 'Point', coordinates: [75.5000, 12.4000] } },
    { type: 'Feature', properties: { id: 'sihawa', name: 'Sihawa (Chhattisgarh) \u2014 origin of Mahanadi' }, geometry: { type: 'Point', coordinates: [81.3000, 20.1000] } },
    { type: 'Feature', properties: { id: 'prayagraj', name: 'Prayagraj \u2014 confluence of Ganga & Yamuna' }, geometry: { type: 'Point', coordinates: [81.8463, 25.4358] } },
    { type: 'Feature', properties: { id: 'devprayag', name: 'Devprayag \u2014 Bhagirathi + Alaknanda = Ganga' }, geometry: { type: 'Point', coordinates: [78.6000, 30.1500] } },
  ],
};

// ---------- Chapter ----------

export const riversChapter: Chapter = {
  id: 'rivers-of-india',
  subject: 'geography',
  unit: 'India Physical',
  tags: ['ganga', 'indus', 'jhelum', 'chenab', 'ravi', 'beas', 'sutlej', 'brahmaputra', 'godavari', 'krishna', 'kaveri', 'hooghly', 'tlawng', 'kaladan', 'northern-plains'],
  title: 'Rivers of India',
  summary: 'The two great river families of India — and how their origin shapes their character.',
  focus:
    'Where a river is born decides what it is. Himalayan rivers (snow-fed, perennial, fertile floodplains) and Peninsular rivers (rain-fed, seasonal, mature stable courses) define almost every geography question about Indian water.',

  view: { center: [22.5, 80.0], zoom: 5 },
  basemap: 'physical',

  layers: [
    {
      id: 'indus-system',
      name: 'Indus System (5 tributaries)',
      description: 'Indus + Jhelum, Chenab, Ravi, Beas, Satluj. Indus Waters Treaty: India gets eastern three (Ravi, Beas, Satluj); Pakistan gets western three (Indus, Jhelum, Chenab).',
      kind: 'vector',
      data: indusSystem,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#3a6a9a', weight: 2.5 , flow: true },
    },
    {
      id: 'ganga-system',
      name: 'Ganga System',
      description: 'Ganga, Yamuna, and tributaries. Largest river basin in India.',
      kind: 'vector',
      data: gangaSystem,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#1d4f7a', weight: 3 , flow: true },
    },
    {
      id: 'brahmaputra-system',
      name: 'Brahmaputra System',
      description: 'Brahmaputra and major NE tributaries including Subansiri, Manas, Teesta, Barak.',
      kind: 'vector',
      data: brahmaputraSystem,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#2a8a8a', weight: 3 , flow: true },
    },
    {
      id: 'east-peninsular',
      name: 'East-flowing Peninsular Rivers',
      description: 'Mahanadi, Godavari, Krishna, Kaveri \u2014 all drain into the Bay of Bengal forming deltas.',
      kind: 'vector',
      data: eastFlowingPeninsular,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#8a5a3a', weight: 2.5 , flow: true },
    },
    {
      id: 'west-peninsular',
      name: 'West-flowing Peninsular Rivers',
      description: 'Only Narmada and Tapi flow west, through rift valleys, into the Arabian Sea. No deltas \u2014 estuaries.',
      kind: 'vector',
      data: westFlowingPeninsular,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#c46a3d', weight: 2.5, dashArray: '6 4' , flow: true },
    },
    {
      id: 'mizoram-rivers',
      name: 'Mizoram Rivers',
      description: 'Northward rivers join Barak \u2192 Brahmaputra. Southward rivers join Kolodyne \u2192 Bay of Bengal via Myanmar.',
      kind: 'vector',
      data: mizoramRivers,
      defaultOn: false,
      labelKey: 'name',
      style: { color: '#5a7a3a', weight: 2.5 , flow: true },
    },
    {
      id: 'origins',
      name: 'Origins & Key Confluences',
      description: 'Glacier sources, peninsular springs, and famous river confluences.',
      kind: 'vector',
      data: riverOrigins,
      defaultOn: true,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Indian rivers fall into two great families: Himalayan rivers (snow + glacier fed, perennial, long, with wide fertile floodplains) and Peninsular rivers (rain-fed, mostly seasonal, mature, stable courses cut into hard rock). India has 12 major river basins (catchment > 20,000 km\u00b2).',
    },
    {
      id: 'f2',
      text: 'The Indus rises near Lake Mansarovar in Tibet, enters India in Ladakh, then flows into Pakistan to the Arabian Sea. Its five main tributaries \u2014 Jhelum, Chenab, Ravi, Beas, Satluj \u2014 give the Punjab ("Land of Five Rivers") its name.',
      linkedLayerId: 'indus-system',
    },
    {
      id: 'f3',
      text: 'The Indus Waters Treaty (1960), brokered by the World Bank, gives the three eastern rivers (Ravi, Beas, Satluj) to India and the three western rivers (Indus, Jhelum, Chenab) primarily to Pakistan. India retains limited rights on the western rivers (run-of-river hydropower, navigation).',
      linkedLayerId: 'indus-system',
    },
    {
      id: 'f4',
      text: 'The Ganga begins as the Bhagirathi from the Gangotri Glacier. At Devprayag (Uttarakhand) it joins the Alaknanda and becomes the Ganga. The Ganga basin is the most densely populated river basin on Earth, supporting over 500 million people.',
      linkedLayerId: 'ganga-system',
      linkedFeatureId: 'devprayag',
    },
    {
      id: 'f5',
      text: 'The Yamuna originates from the Yamunotri Glacier, flows parallel to the Ganga, and joins it at Prayagraj (Allahabad) \u2014 the Sangam. Its right-bank tributaries (Chambal, Sind, Betwa, Ken) all rise in the Peninsular Plateau, making the Yamuna unusual: a Himalayan river fed largely by Peninsular tributaries.',
      linkedLayerId: 'ganga-system',
      linkedFeatureId: 'prayagraj',
    },
    {
      id: 'f6',
      text: 'The Brahmaputra is known as the Tsangpo in Tibet, the Siang/Dihang where it enters India in Arunachal, and the Brahmaputra in Assam. It takes a sharp U-turn around Namcha Barwa to enter India. Largest tributary: Subansiri. The Brahmaputra causes annual flooding in Assam because its Tibetan catchment receives snowmelt and monsoon rain simultaneously.',
      linkedLayerId: 'brahmaputra-system',
    },
    {
      id: 'f7',
      text: 'The Barak River drains the Northeast hill states and is the second-largest river system of NE India. It joins the Meghna in Bangladesh, which in turn meets the Brahmaputra-Ganga delta. Almost all of Mizoram\u2019s north-flowing rivers (Tlawng, Tuirial, Tuivawl) eventually reach the Brahmaputra system via the Barak.',
      linkedLayerId: 'brahmaputra-system',
      linkedFeatureId: 'barak',
    },
    {
      id: 'f8',
      text: 'Mizoram\u2019s longest river is the Tlawng (Dhaleshwari) \u2014 ~185 km, flows northward, joins the Barak in Assam. It was historically the main transport route used by the British when they arrived in 1890. The Tuirial is harnessed for hydropower.',
      linkedLayerId: 'mizoram-rivers',
      linkedFeatureId: 'tlawng',
    },
    {
      id: 'f9',
      text: 'Mizoram\u2019s biggest river is the Chhimtuipui (also Kolodyne or Kaladan). It originates in Chin state, Myanmar, enters Mizoram\u2019s southern districts (Saiha, Lawngtlai), and returns to Myanmar where it reaches the Bay of Bengal at Sittwe. India\u2019s Kaladan Multi-Modal Transit Transport Project uses this river to connect Mizoram to a deep-sea port in Myanmar.',
      linkedLayerId: 'mizoram-rivers',
      linkedFeatureId: 'chhimtuipui',
    },
    {
      id: 'f10',
      text: 'The Peninsular rivers are older than the Himalayan rivers and have reached "mature" stage \u2014 broad valleys, low gradients, stable courses. They mostly flow east into the Bay of Bengal, where they form large deltas: Mahanadi, Godavari, Krishna, and Kaveri.',
      linkedLayerId: 'east-peninsular',
    },
    {
      id: 'f11',
      text: 'The Godavari is the longest river in Peninsular India (~1,465 km) \u2014 called "Dakshin Ganga" (Ganga of the South). It rises at Trimbakeshwar near Nashik and drains parts of Maharashtra, Telangana, Andhra Pradesh. Major tributaries: Pravara, Manjira, Indravati, Pranhita.',
      linkedLayerId: 'east-peninsular',
      linkedFeatureId: 'godavari',
    },
    {
      id: 'f12',
      text: 'The Krishna rises at Mahabaleshwar in the Western Ghats and flows ~1,400 km through Maharashtra, Karnataka, Telangana, and Andhra Pradesh. Largest tributary: the Tungabhadra (which itself was the river around which Vijayanagara empire grew).',
      linkedLayerId: 'east-peninsular',
      linkedFeatureId: 'krishna',
    },
    {
      id: 'f13',
      text: 'The Kaveri / Cauvery rises at Talakaveri in Kodagu (Karnataka), flows through Karnataka and Tamil Nadu, and forms a delta near Thanjavur. Inter-state water sharing between Karnataka and Tamil Nadu has been one of India\u2019s longest-running river disputes.',
      linkedLayerId: 'east-peninsular',
      linkedFeatureId: 'kaveri',
    },
    {
      id: 'f14',
      text: 'Only two major Peninsular rivers flow WEST: the Narmada and the Tapi. Both flow through rift valleys (grabens) between Vindhya-Satpura ranges and drain into the Arabian Sea via estuaries, not deltas. The Narmada rises at Amarkantak (MP); the Tapi at Multai (MP).',
      linkedLayerId: 'west-peninsular',
    },
    {
      id: 'f15',
      text: 'The Narmada traditionally divides North India from South India and runs through a rift valley between the Vindhya range (north) and the Satpura range (south). At ~1,312 km it is the largest west-flowing Peninsular river. Tapi flows almost parallel, just south of Satpura.',
      linkedLayerId: 'west-peninsular',
      linkedFeatureId: 'narmada',
    },
    {
      id: 'f16',
      text: 'Why no west-flowing river deltas? The west-flowing Peninsular rivers fall into rift valleys with hard-rock margins and short distance to the sea \u2014 they don\u2019t spread sediment laterally. The Narmada and Tapi form estuaries instead of deltas.',
      linkedLayerId: 'west-peninsular',
    },
    {
      id: 'f17',
      text: 'Inland drainage: a few rivers don\u2019t reach the sea at all. The Luni in Rajasthan flows into the Rann of Kachchh. Streams from the Aravallis and the Sambhar Salt Lake area drain into inland basins. This is characteristic of the arid west.',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'What is the fundamental difference between Himalayan and Peninsular rivers?',
      options: [
        'Length \u2014 Himalayan rivers are always shorter',
        'Source \u2014 Himalayan rivers are snow/glacier-fed and perennial; Peninsular rivers are rain-fed and mostly seasonal',
        'Direction \u2014 Himalayan rivers flow only south; Peninsular rivers flow only east',
        'Width \u2014 Peninsular rivers are wider than Himalayan rivers',
      ],
      answerIndex: 1,
      explanation: 'Source determines everything else. Himalayan rivers (Indus, Ganga, Brahmaputra) are fed by snowmelt and glaciers so they flow year-round; Peninsular rivers (Godavari, Krishna, Kaveri, Narmada, Tapi, Mahanadi) depend on monsoon rainfall and shrink dramatically in dry seasons.',
    },
    {
      id: 'q2',
      type: 'map_click',
      question: 'Click the location of Amarkantak \u2014 origin of the Narmada and the Son rivers.',
      answer: { lat: 22.67, lng: 81.76, toleranceKm: 120 },
      explanation: 'Amarkantak (eastern Madhya Pradesh) is the rare twin-origin: the Narmada flows west from here to the Arabian Sea, while the Son flows east-then-north to join the Ganga.',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Which two major peninsular rivers flow westward into the Arabian Sea?',
      options: [
        'Krishna and Kaveri',
        'Godavari and Mahanadi',
        'Narmada and Tapi',
        'Indus and Yamuna',
      ],
      answerIndex: 2,
      explanation: 'Almost all Peninsular rivers flow east into the Bay of Bengal. The two exceptions are the Narmada and Tapi, which flow west through rift valleys between the Vindhyas and Satpuras into the Arabian Sea \u2014 and they form estuaries, not deltas.',
    },
    {
      id: 'q4',
      type: 'map_click',
      question: 'Click the location of Prayagraj (the Sangam), where the Ganga meets the Yamuna.',
      answer: { lat: 25.4358, lng: 81.8463, toleranceKm: 100 },
      explanation: 'Prayagraj (formerly Allahabad) sits at the confluence of the Ganga and Yamuna, sacred to Hindu tradition. The Saraswati is traditionally said to join here invisibly as the third river of the Triveni Sangam.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'Under the Indus Waters Treaty (1960), which three rivers are primarily allocated to Pakistan?',
      options: [
        'Ravi, Beas, Satluj',
        'Indus, Jhelum, Chenab',
        'Ganga, Yamuna, Sutlej',
        'Brahmaputra, Teesta, Barak',
      ],
      answerIndex: 1,
      explanation: 'The treaty gives India the three eastern rivers (Ravi, Beas, Satluj) and Pakistan the three western rivers (Indus, Jhelum, Chenab). India retains limited rights for run-of-river hydropower on the western rivers. The treaty has survived multiple wars and remains active.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'What is the longest river in Mizoram?',
      options: ['Chhimtuipui (Kolodyne)', 'Tuirial', 'Tlawng (Dhaleshwari)', 'Barak'],
      answerIndex: 2,
      explanation: 'The Tlawng (~185 km) is the longest river *within* Mizoram and flows north to join the Barak in Assam. The Chhimtuipui (Kolodyne) is the *biggest* river but originates in Myanmar and only passes through southern Mizoram before returning to Myanmar.',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click anywhere along the course of the Brahmaputra in Assam.',
      answer: { lat: 26.5, lng: 92.5, toleranceKm: 200 },
      explanation: 'The Brahmaputra enters India through Arunachal Pradesh (as the Siang/Dihang) after taking a U-turn around Namcha Barwa, then flows west across Assam before turning south into Bangladesh. Its annual floods are a defining feature of Assamese geography.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Why do most Peninsular rivers form deltas on the eastern coast but not on the western coast?',
      options: [
        'The western coast has no rivers reaching it',
        'East-flowing rivers (Mahanadi, Godavari, Krishna, Kaveri) cross broad gentle plains and deposit sediment; west-flowing rivers (Narmada, Tapi) drop into rift valleys with short hard-rock margins to the sea, forming estuaries instead',
        'The Bay of Bengal has stronger currents that build deltas',
        'Eastern coastal rivers are shorter than western ones',
      ],
      answerIndex: 1,
      explanation: 'Geology + gradient. East-flowing rivers traverse the wide Eastern Coastal Plain at low gradient, allowing sediment to fan out and build large deltas. West-flowing rivers run through fault-bounded rift valleys (the Narmada and Tapi grabens) and reach the Arabian Sea quickly through narrow estuaries.',
    },
    {
      id: 'q9',
      type: 'map_click',
      question: 'Click the origin of the Godavari \u2014 longest river of Peninsular India.',
      answer: { lat: 19.96, lng: 73.55, toleranceKm: 100 },
      explanation: 'The Godavari rises at Trimbakeshwar, near Nashik in the Western Ghats of Maharashtra. From there it flows southeast across the Deccan for ~1,465 km before meeting the Bay of Bengal in Andhra Pradesh \u2014 earning its nickname "Dakshin Ganga".',
    },
  ],
};

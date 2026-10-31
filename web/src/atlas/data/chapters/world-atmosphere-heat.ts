import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// THE ATMOSPHERE & EARTH'S HEAT ZONES
//
// Concept:
//   "Sunlight arrives at an angle \u2014 latitude decides everything.
//   Three heat zones on the map, five layers overhead, and one
//   heat budget keeping the whole planet in balance."
//
// Source: Geography 4th slide (Climatology 1), GS-1 Unit 4, Rf Ralte.
// ============================================

const band = (id: string, name: string, s: number, n: number): GeoJSON.Feature => ({
  type: 'Feature',
  properties: { id, name },
  geometry: { type: 'Polygon', coordinates: [[[-180, s], [180, s], [180, n], [-180, n], [-180, s]]] },
});

/** The three heat zones \u2014 defined by the sun's overhead reach. */
const heatZones: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    band('torrid', 'TORRID ZONE \u2014 between the tropics (23\u00bd\u00b0N\u201323\u00bd\u00b0S): overhead sun at least once a year', -23.5, 23.5),
    band('temperate-n', 'NORTH TEMPERATE ZONE (23\u00bd\u00b0\u201366\u00bd\u00b0N): slanting sun, moderate heat', 23.5, 66.5),
    band('temperate-s', 'SOUTH TEMPERATE ZONE (23\u00bd\u00b0\u201366\u00bd\u00b0S)', -66.5, -23.5),
    band('frigid-n', 'NORTH FRIGID ZONE (66\u00bd\u00b0\u201390\u00b0N): sun never far above horizon', 66.5, 90),
    band('frigid-s', 'SOUTH FRIGID ZONE (66\u00bd\u00b0\u201390\u00b0S)', -90, -66.5),
  ],
};

/** The key latitude lines. */
const keyLatitudes: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'cancer', name: 'Tropic of Cancer, 23\u00bd\u00b0N \u2014 crosses India through 8 states (and Mizoram!)' }, geometry: { type: 'LineString', coordinates: [[-180, 23.5], [180, 23.5]] } },
    { type: 'Feature', properties: { id: 'capricorn', name: 'Tropic of Capricorn, 23\u00bd\u00b0S' }, geometry: { type: 'LineString', coordinates: [[-180, -23.5], [180, -23.5]] } },
    { type: 'Feature', properties: { id: 'equator-l', name: 'Equator, 0\u00b0 \u2014 maximum annual insolation' }, geometry: { type: 'LineString', coordinates: [[-180, 0], [180, 0]] } },
    { type: 'Feature', properties: { id: 'arctic', name: 'Arctic Circle, 66\u00bd\u00b0N \u2014 midnight sun / polar night begins' }, geometry: { type: 'LineString', coordinates: [[-180, 66.5], [180, 66.5]] } },
  ],
};

export const atmosphereHeatChapter: Chapter = {
  id: 'world-atmosphere-heat',
  subject: 'geography',
  unit: 'World',
  tags: ['tropic-of-cancer', 'insolation', 'ozone', 'heat-budget', 'monsoon'],
  title: 'World: Atmosphere & Heat Zones',
  summary: 'Five layers overhead, three heat zones on the map, one heat budget.',
  focus:
    'Sunlight arrives at an angle \u2014 latitude decides everything. The torrid, temperate and frigid zones are just the geometry of the overhead sun; the atmosphere\u2019s five layers and the heat budget do the rest.',
  view: { center: [15.0, 30.0], zoom: 2 },
  worldExtent: true,
  basemap: 'relief',
  theme: { accent: '#c07a1a', mapBg: '#f6f0e2' },

  layers: [
    {
      id: 'heat-zones',
      name: 'Three heat zones',
      kind: 'vector',
      data: heatZones,
      style: { color: '#c07a1a', weight: 1, fillColor: '#e0a24e', fillOpacity: 0.18, pattern: 'dots' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'key-latitudes',
      name: 'Key latitudes',
      kind: 'vector',
      data: keyLatitudes,
      style: { color: '#b3261e', weight: 2, dashArray: '8 6' },
      defaultOn: true,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Atmosphere composition: nitrogen ~78%, oxygen ~21%, argon ~0.93%, CO\u2082 ~0.04% \u2014 but the climatic action lives in the minor players: WATER VAPOUR, particulate matter (dust as condensation nuclei), CO\u2082 and OZONE, which absorb and re-radiate heat.',
    },
    {
      id: 'f2',
      text: 'Five layers, ascending: TROPOSPHERE (up to ~18 km over the equator, ~8 km at poles \u2014 thickest where heating is greatest) \u2014 ALL weather (cyclones, clouds, rain) happens here; the TROPOPAUSE caps it. STRATOSPHERE (to 50 km): temperature RISES with height because ozone absorbs UV \u2014 jets fly in its calm lower reaches; the OZONOSPHERE spans the stratosphere and lower mesosphere. MESOSPHERE: coldest layer \u2014 meteors burn here. THERMOSPHERE/IONOSPHERE: radio waves reflect. EXOSPHERE: fades to space.',
    },
    {
      id: 'f3',
      text: 'INSOLATION = incoming solar radiation. Factors: (1) solar output \u2014 the ~11-year sunspot cycle swings it between ~1340 and 1380 W/m\u00b2; (2) ANGLE OF INCIDENCE \u2014 insolation falls as latitude rises (slanting rays spread over more area and cross more atmosphere); (3) duration of day; (4) distance from the sun \u2014 perihelion (Jan, nearest) vs aphelion (July, farthest); (5) transparency of the atmosphere.',
    },
    {
      id: 'f4',
      text: 'HEAT BUDGET: the earth keeps a constant temperature because heat received (insolation) exactly equals heat lost (terrestrial radiation). Of 100 units arriving: roughly a third is reflected straight back (ALBEDO \u2014 clouds, ice, dust); the rest is absorbed by atmosphere and surface, then returned as long-wave terrestrial radiation. The atmosphere is heated mainly FROM BELOW \u2014 by terrestrial radiation, conduction and convection \u2014 not directly by sunlight.',
    },
    {
      id: 'f5',
      text: 'The three heat zones are pure geometry: TORRID zone (23\u00bd\u00b0N\u201323\u00bd\u00b0S) \u2014 the overhead sun visits at least once a year; TEMPERATE zones (23\u00bd\u00b0\u201366\u00bd\u00b0) \u2014 never overhead, always slanting; FRIGID zones (66\u00bd\u00b0\u2013poles) \u2014 the sun barely climbs, and inside the polar circles you get midnight sun and polar night.',
      linkedLayerId: 'heat-zones',
    },
    {
      id: 'f6',
      text: 'The TROPIC OF CANCER threads India through eight states \u2014 Gujarat, Rajasthan, MP, Chhattisgarh, Jharkhand, West Bengal, Tripura and MIZORAM \u2014 the same line you saw in the Mizoram chapter. Latitude connects the world map to the home map.',
      linkedLayerId: 'key-latitudes',
      linkedFeatureId: 'cancer',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'All weather phenomena \u2014 cyclones, clouds, rain \u2014 occur in which layer?',
      options: ['Stratosphere', 'Troposphere', 'Mesosphere', 'Thermosphere'],
      answerIndex: 1,
      explanation: 'The troposphere \u2014 thickest (~18 km) over the equator because of stronger convection, ~8 km at the poles. The tropopause caps it; jets prefer the calm stratosphere above.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Temperature RISES with height in the stratosphere because:',
      options: [
        'It is closer to the sun',
        'Ozone absorbs ultraviolet radiation there',
        'Jet engines heat it',
        'CO\u2082 concentrates there',
      ],
      answerIndex: 1,
      explanation: 'The ozonosphere (spanning the stratosphere and lower mesosphere) absorbs harmful UV \u2014 warming the layer and shielding life. The mesosphere above is the coldest layer.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click anywhere on the Torrid Zone \u2014 the belt where the sun is overhead at least once a year.',
      answer: { lat: 0, lng: 20, toleranceKm: 2600 },
      explanation: 'Between the tropics, 23\u00bd\u00b0N to 23\u00bd\u00b0S. Overhead sun = maximum insolation = the engine room of the global circulation (Hadley cells, monsoons).',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Insolation DECREASES as latitude increases mainly because:',
      options: [
        'The poles are farther from the sun',
        'Slanting rays spread over a larger area and cross more atmosphere',
        'There is more ozone at the poles',
        'The earth spins slower at the poles',
      ],
      answerIndex: 1,
      explanation: 'Angle of incidence: oblique rays deliver less energy per unit area and lose more to a longer atmospheric path. Latitude and insolation vary inversely \u2014 the whole heat-zone map follows.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'The earth\u2019s heat budget means:',
      options: [
        'The earth slowly accumulates solar heat',
        'Heat received (insolation) equals heat emitted (terrestrial radiation), so overall temperature stays constant',
        'The oceans store all incoming heat',
        'Albedo equals insolation',
      ],
      answerIndex: 1,
      explanation: 'A perfect balance: intake = outflow, so the planet as a whole neither gains nor loses heat. Albedo is the ~third reflected straight back by clouds, ice and dust.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'The atmosphere is heated mainly by:',
      options: [
        'Direct absorption of incoming sunlight',
        'Terrestrial (long-wave) radiation from below, plus conduction and convection',
        'Ozone reactions',
        'Lightning',
      ],
      answerIndex: 1,
      explanation: 'The surface absorbs short-wave solar energy and re-emits long-wave radiation, which the lower atmosphere (water vapour, CO\u2082) traps \u2014 heating from BELOW. That\u2019s why temperature falls with height in the troposphere.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'The 11-year cycle affecting solar output (\u22481340\u20131380 W/m\u00b2) is the:',
      options: ['Milankovitch cycle', 'Sunspot cycle', 'El Ni\u00f1o cycle', 'Precession cycle'],
      answerIndex: 1,
      explanation: 'The sunspot cycle \u2014 one of five insolation factors, alongside angle of incidence, day length, sun\u2013earth distance (perihelion Jan / aphelion July) and atmospheric transparency.',
    },
  ],
};

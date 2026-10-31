import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// THE ATMOSPHERIC & OCEANIC ENGINE
// Pressure belts \u00b7 planetary winds \u00b7 ocean currents \u00b7 El Ni\u00f1o
//
// Concept:
//   "Seven pressure belts drive three wind systems; the winds
//   drag the ocean into great gyres \u2014 warm currents poleward,
//   cold currents equatorward. One engine, three visible layers."
//
// Source: Geography 5th slide (Climatology 2) + 6th slide
// (Oceanography), GS-1 Unit 4, Rf Ralte.
// ============================================

const band = (id: string, name: string, s: number, n: number): GeoJSON.Feature => ({
  type: 'Feature',
  properties: { id, name },
  geometry: {
    type: 'Polygon',
    coordinates: [[[-180, s], [180, s], [180, n], [-180, n], [-180, s]]],
  },
});

/** Low-pressure belts \u2014 rising air, rain. */
const lowBelts: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    band('eq-low', 'Equatorial Low (Doldrums) \u2014 rising hot air, thunderstorms', -5, 5),
    band('subpolar-low-n', 'Sub-polar Low (45\u00b0N\u2013Arctic Circle) \u2014 converging winds rise', 45, 66.5),
    band('subpolar-low-s', 'Sub-polar Low (45\u00b0S\u2013Antarctic Circle)', -66.5, -45),
  ],
};

/** High-pressure belts \u2014 sinking air, deserts / cold caps. */
const highBelts: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    band('subtrop-high-n', 'Sub-tropical High / Horse Latitudes (\u224830\u201335\u00b0N) \u2014 sinking air, world\u2019s hot deserts', 27, 36),
    band('subtrop-high-s', 'Sub-tropical High (\u224830\u201335\u00b0S)', -36, -27),
    band('polar-high-n', 'North Polar High \u2014 cold dense sinking air', 80, 90),
    band('polar-high-s', 'South Polar High', -90, -80),
  ],
};

/** Planetary winds \u2014 arrows drawn as short flowing lines. */
const winds: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    // NE trades (blow from subtropical high toward equator, deflected right)
    { type: 'Feature', properties: { id: 'ne-trade-1', name: 'NE Trade Winds (30\u00b0N \u2192 equator)' }, geometry: { type: 'LineString', coordinates: [[-40, 28], [-52, 18], [-62, 8]] } },
    { type: 'Feature', properties: { id: 'ne-trade-2', name: 'NE Trade Winds' }, geometry: { type: 'LineString', coordinates: [[150, 28], [138, 18], [128, 8]] } },
    // SE trades
    { type: 'Feature', properties: { id: 'se-trade-1', name: 'SE Trade Winds (30\u00b0S \u2192 equator)' }, geometry: { type: 'LineString', coordinates: [[-10, -28], [-22, -18], [-32, -8]] } },
    { type: 'Feature', properties: { id: 'se-trade-2', name: 'SE Trade Winds' }, geometry: { type: 'LineString', coordinates: [[170, -28], [158, -18], [148, -8]] } },
    // Westerlies
    { type: 'Feature', properties: { id: 'westerlies-n', name: 'Westerlies (SW \u2192 NE, 35\u201360\u00b0N)' }, geometry: { type: 'LineString', coordinates: [[-60, 38], [-40, 46], [-18, 52]] } },
    { type: 'Feature', properties: { id: 'westerlies-s', name: 'Roaring Forties \u2014 Westerlies (NW \u2192 SE, 35\u201360\u00b0S)' }, geometry: { type: 'LineString', coordinates: [[40, -38], [65, -46], [90, -52]] } },
    // Polar easterlies
    { type: 'Feature', properties: { id: 'polar-e-n', name: 'Polar Easterlies (NE \u2192 SW)' }, geometry: { type: 'LineString', coordinates: [[20, 78], [2, 71], [-12, 65]] } },
  ],
};

/** Warm currents \u2014 equator \u2192 poles. */
const warmCurrents: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'gulf-stream', name: 'Gulf Stream \u2192 North Atlantic Drift (warm)' }, geometry: { type: 'LineString', coordinates: [[-80, 25], [-74, 33], [-60, 40], [-40, 48], [-20, 54], [-5, 58]] } },
    { type: 'Feature', properties: { id: 'kuroshio', name: 'Kuroshio Current (warm, Japan)' }, geometry: { type: 'LineString', coordinates: [[124, 20], [130, 27], [138, 33], [150, 40]] } },
    { type: 'Feature', properties: { id: 'brazil', name: 'Brazil Current (warm) \u2014 S. Equatorial current splits at Brazil\u2019s shoulder' }, geometry: { type: 'LineString', coordinates: [[-34, -8], [-38, -16], [-42, -25], [-48, -33]] } },
    { type: 'Feature', properties: { id: 'agulhas', name: 'Agulhas Current (warm, E. Africa)' }, geometry: { type: 'LineString', coordinates: [[42, -22], [36, -30], [28, -36]] } },
    { type: 'Feature', properties: { id: 'e-australia', name: 'East Australian Current (warm)' }, geometry: { type: 'LineString', coordinates: [[155, -18], [154, -26], [151, -34]] } },
  ],
};

/** Cold currents \u2014 poles \u2192 equator. */
const coldCurrents: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'labrador', name: 'Labrador Current (cold) \u2014 meets Gulf Stream: Newfoundland fogs & fisheries' }, geometry: { type: 'LineString', coordinates: [[-58, 60], [-54, 52], [-50, 46]] } },
    { type: 'Feature', properties: { id: 'canary', name: 'Canary Current (cold)' }, geometry: { type: 'LineString', coordinates: [[-12, 40], [-16, 32], [-18, 24]] } },
    { type: 'Feature', properties: { id: 'benguela', name: 'Benguela Current (cold, SW Africa)' }, geometry: { type: 'LineString', coordinates: [[16, -34], [12, -26], [10, -18]] } },
    { type: 'Feature', properties: { id: 'humboldt', name: 'Peru / Humboldt Current (cold) \u2014 the El Ni\u00f1o stage' }, geometry: { type: 'LineString', coordinates: [[-74, -40], [-76, -28], [-80, -16], [-82, -6]] } },
    { type: 'Feature', properties: { id: 'oyashio', name: 'Oyashio Current (cold, NW Pacific)' }, geometry: { type: 'LineString', coordinates: [[158, 52], [150, 46], [144, 41]] } },
    { type: 'Feature', properties: { id: 'california', name: 'California Current (cold)' }, geometry: { type: 'LineString', coordinates: [[-126, 44], [-122, 36], [-117, 29]] } },
  ],
};

/** El Ni\u00f1o stage \u2014 the equatorial Pacific. */
const elNino: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'walker', name: 'Normal year: trades push warm water WEST \u2192 rain over Indonesia/Australia; cold upwelling off Peru' },
      geometry: { type: 'LineString', coordinates: [[-82, 0], [-120, 2], [-160, 0], [150, -2], [128, 0]] },
    },
    { type: 'Feature', properties: { id: 'peru-coast', name: 'Peru\u2013Ecuador coast \u2014 El Ni\u00f1o warming appears here (every 2\u20137 yrs)' }, geometry: { type: 'Point', coordinates: [-81, -5] } },
    { type: 'Feature', properties: { id: 'indo-pool', name: 'Indonesia\u2013N. Australia \u2014 normal-year warm pool & low pressure' }, geometry: { type: 'Point', coordinates: [128, -5] } },
  ],
};

export const windsCurrentsChapter: Chapter = {
  id: 'world-winds-currents',
  subject: 'geography',
  unit: 'World',
  tags: ['el-nino', 'monsoon', 'trade-winds', 'ocean-currents', 'heat-budget'],
  title: 'World: Winds, Belts & Currents',
  summary: 'Seven pressure belts \u2192 planetary winds \u2192 ocean gyres \u2192 El Ni\u00f1o.',
  focus:
    'One engine, three layers: pressure belts make the planetary winds, the winds drag the oceans into gyres (warm poleward, cold equatorward), and a hiccup in the Pacific limb of this engine is El Ni\u00f1o.',
  view: { center: [10.0, 20.0], zoom: 2 },
  worldExtent: true,
  basemap: 'relief',
  theme: { accent: '#1f5fa8', mapBg: '#e8f0f4' },

  layers: [
    {
      id: 'low-belts',
      name: 'Low-pressure belts',
      description: 'Doldrums + sub-polar lows \u2014 rising air, rain.',
      kind: 'vector',
      data: lowBelts,
      style: { color: '#c2452d', weight: 1, fillColor: '#e06a4e', fillOpacity: 0.18, pattern: 'wave' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'high-belts',
      name: 'High-pressure belts',
      description: 'Horse latitudes + polar highs \u2014 sinking air, deserts.',
      kind: 'vector',
      data: highBelts,
      style: { color: '#1f5fa8', weight: 1, fillColor: '#4a7fc0', fillOpacity: 0.16, pattern: 'dots' },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'winds',
      name: 'Planetary winds',
      description: 'Trades, westerlies, polar easterlies \u2014 watch the flow.',
      kind: 'vector',
      data: winds,
      style: { color: '#5b8a2e', weight: 3, flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'warm-currents',
      name: 'Warm currents',
      description: 'Equator \u2192 poles: Gulf Stream, Kuroshio, Brazil, Agulhas\u2026',
      kind: 'vector',
      data: warmCurrents,
      style: { color: '#d1495b', weight: 3.5, flow: true, glow: true },
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'cold-currents',
      name: 'Cold currents',
      description: 'Poles \u2192 equator: Labrador, Canary, Benguela, Humboldt\u2026',
      kind: 'vector',
      data: coldCurrents,
      style: { color: '#2d7dd2', weight: 3.5, flow: true, glow: true },
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'el-nino',
      name: 'El Ni\u00f1o stage',
      description: 'The equatorial Pacific see-saw.',
      kind: 'vector',
      data: elNino,
      style: { color: '#b0632c', weight: 2.5, dashArray: '6 6', flow: true, markerRadius: 8 },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Air has weight \u2014 that weight is atmospheric pressure; isobars join points of equal pressure. Warm air expands, gets lighter and rises (low pressure); cold air compresses, densifies and sinks (high pressure). Wind is simply air moving from high to low.',
    },
    {
      id: 'f2',
      text: 'Seven belts, alternating: Equatorial Low (intense heating, rising air, daily thunderstorms \u2014 the calm \u201cdoldrums\u201d); Sub-tropical Highs to ~35\u00b0 (air sinking after the Hadley circuit \u2014 hot deserts and the \u201chorse latitudes\u201d); Sub-polar Lows (45\u00b0\u2013polar circles, where sub-tropical and polar winds converge and rise); Polar Highs (cold dense sinking air).',
      linkedLayerId: 'high-belts',
    },
    {
      id: 'f3',
      text: 'Tri-cellular model: the HADLEY cell (largest, equator to ~30\u201340\u00b0) drives the trade winds; the FERREL cell (middle, moves opposite \u2014 \u201clike a cog in a machine\u201d between the other two) gives the westerlies; the POLAR cell (smallest, weakest) gives the polar easterlies.',
    },
    {
      id: 'f4',
      text: 'Coriolis: because Earth\u2019s surface spins fastest at the equator, moving air and water deflect RIGHT in the northern hemisphere and LEFT in the southern. That is why the trades arrive as NE trades (north) and SE trades (south), and why ocean gyres spin clockwise in the north and anticlockwise in the south.',
      linkedLayerId: 'winds',
    },
    {
      id: 'f5',
      text: 'Trade winds are descending and stable at their origin (sub-tropical highs); where the two hemispheres\u2019 trades meet at the equator, the air rises into storms. Their eastern flanks ride over cool ocean and stay dry \u2014 which is why deserts hug the western coasts of continents in the trade-wind belt.',
      linkedLayerId: 'winds',
    },
    {
      id: 'f6',
      text: 'Currents come in two families: WARM (originate near the equator, flow poleward, high surface temperature) and COLD (originate polewards, flow toward the equator). Drivers: planetary winds (the biggest), Coriolis, temperature (an ~8 cm sea-surface gradient from equator to mid-latitudes!), salinity (denser saline water sinks), and coastline shape.',
      linkedLayerId: 'warm-currents',
    },
    {
      id: 'f7',
      text: 'Name-drop set for prelims \u2014 warm: Gulf Stream\u2192North Atlantic Drift, Kuroshio, Brazil (the South Equatorial current splits in two on Brazil\u2019s shoulder), Agulhas, East Australian. Cold: Labrador, Canary, Benguela, Peru/Humboldt, Oyashio, California. Where Labrador meets the Gulf Stream: fog + the great Newfoundland fishing grounds.',
      linkedLayerId: 'cold-currents',
    },
    {
      id: 'f8',
      text: 'Normal Pacific year: high pressure sits off Peru, low over Indonesia/N. Australia \u2014 strong easterly trades push warm water west (rain in Indonesia), while cold nutrient-rich water UPWELLS off Peru (rich fisheries).',
      linkedLayerId: 'el-nino',
    },
    {
      id: 'f9',
      text: 'EL NI\u00d1O year (irregular, every 2\u20137 years, avg ~3\u20134): pressure drops over the central Pacific and South America\u2019s coast, trades weaken, the Peru current runs warm, upwelling collapses \u2014 rain shifts to the Peruvian coast while Indonesia/Australia (and often the Indian monsoon) dry out. LA NI\u00d1A is the cold overcorrection of the same see-saw.',
      linkedLayerId: 'el-nino',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Arrange the pressure belts from equator to pole:',
      options: [
        'Equatorial Low \u2192 Sub-polar Low \u2192 Sub-tropical High \u2192 Polar High',
        'Equatorial Low \u2192 Sub-tropical High \u2192 Sub-polar Low \u2192 Polar High',
        'Sub-tropical High \u2192 Equatorial Low \u2192 Polar High \u2192 Sub-polar Low',
        'Equatorial High \u2192 Sub-tropical Low \u2192 Sub-polar High \u2192 Polar Low',
      ],
      answerIndex: 1,
      explanation: 'Low\u2013High\u2013Low\u2013High, alternating: Equatorial Low (0\u20135\u00b0) \u2192 Sub-tropical High (\u224830\u201335\u00b0) \u2192 Sub-polar Low (45\u00b0\u2013polar circle) \u2192 Polar High. The wind systems blow between them.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Which cell of the tri-cellular model is the largest, and which winds does it drive?',
      options: [
        'Ferrel cell \u2014 westerlies',
        'Polar cell \u2014 polar easterlies',
        'Hadley cell \u2014 the trade winds',
        'Walker cell \u2014 monsoons',
      ],
      answerIndex: 2,
      explanation: 'The Hadley cell (equator to ~30\u201340\u00b0) is the largest and powers the trades. Ferrel is the middle \u201ccog\u201d (westerlies); Polar is the smallest and weakest (easterlies).',
    },
    {
      id: 'q3',
      type: 'mcq',
      question: 'Coriolis deflection sends moving air and currents:',
      options: [
        'Left in the northern hemisphere, right in the southern',
        'Right in the northern hemisphere, left in the southern',
        'Always toward the equator',
        'Always toward the poles',
      ],
      answerIndex: 1,
      explanation: 'Right in the north, left in the south \u2014 because the surface rotates faster at the equator. Hence NE/SE trades, and gyres clockwise (N) / anticlockwise (S).',
    },
    {
      id: 'q4',
      type: 'map_click',
      question: 'Click the Peru (Humboldt) cold current \u2014 the stage on which El Ni\u00f1o plays out.',
      answer: { lat: -15.0, lng: -79.0, toleranceKm: 1200 },
      explanation: 'The cold Humboldt current runs up South America\u2019s west coast. Its upwelling feeds the anchovy fisheries \u2014 exactly what an El Ni\u00f1o year shuts down.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'In a NORMAL (non-El Ni\u00f1o) year over the Pacific:',
      options: [
        'Low pressure off Peru; warm water piles up off Ecuador',
        'High pressure off Peru, low over Indonesia; trades push warm water west and cold water upwells off Peru',
        'The trade winds reverse and blow west to east',
        'Upwelling occurs off Australia',
      ],
      answerIndex: 1,
      explanation: 'Normal year = Peru high + Indonesian low \u2192 strong easterly trades \u2192 warm pool and thunderstorms in the west, cold nutrient-rich upwelling off Peru. El Ni\u00f1o weakens or reverses this.',
    },
    {
      id: 'q6',
      type: 'map_click',
      question: 'Click where the warm Gulf Stream and the cold Labrador current meet \u2014 fog and fisheries off Newfoundland.',
      answer: { lat: 46.0, lng: -50.0, toleranceKm: 1100 },
      explanation: 'Off Newfoundland the Labrador current collides with the Gulf Stream: dense fogs, and one of the world\u2019s richest fishing grounds where cold and warm waters mix.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'El Ni\u00f1o events recur roughly every:',
      options: ['Every year', '2 to 7 years (avg ~3\u20134)', 'Exactly every 11 years', 'Once a century'],
      answerIndex: 1,
      explanation: 'Irregular, every 2\u20137 years, averaging once every 3\u20134 years. When it comes, upwelling off Peru collapses and global rainfall patterns \u2014 including the Indian monsoon \u2014 shift.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Warm currents generally flow ______ and circulate ______ in the northern hemisphere.',
      options: [
        'Poleward; clockwise',
        'Equatorward; clockwise',
        'Poleward; anticlockwise',
        'Equatorward; anticlockwise',
      ],
      answerIndex: 0,
      explanation: 'Warm currents originate near the equator and carry heat poleward; northern-hemisphere gyres turn clockwise (Coriolis right-deflection), southern ones anticlockwise.',
    },
  ],
};

import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// THE RESTLESS EARTH \u2014 MOUNTAINS, QUAKES, VOLCANOES
//
// Concept:
//   "One map explains 68% of all earthquakes: the Pacific Ring
//   of Fire. Where plates converge you get fold mountains,
//   quakes and volcanoes together \u2014 the same boundary, three
//   phenomena."
//
// Source: Geography 3rd slide (GS-1 Unit 4 \u2014 Important
// geographical phenomena), Rf Ralte.
// ============================================

/** Pacific Ring of Fire \u2014 drawn as two arcs around the Pacific rim. */
const ringOfFire: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'rof-west', name: 'Ring of Fire \u2014 western arc (NZ \u2192 Japan \u2192 Aleutians)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [178.0, -40.0], [175.0, -30.0], [170.0, -20.0], [160.0, -10.0],
          [150.0, -6.0], [140.0, -2.0], [128.0, 2.0], [124.0, 8.0],
          [122.0, 14.0], [122.0, 20.0], [124.0, 26.0], [130.0, 32.0],
          [140.0, 36.0], [145.0, 42.0], [152.0, 48.0], [160.0, 53.0],
          [170.0, 55.0], [180.0, 55.0],
        ],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'rof-east', name: 'Ring of Fire \u2014 eastern arc (Alaska \u2192 Andes)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [-180.0, 55.0], [-170.0, 54.0], [-160.0, 56.0], [-150.0, 60.0],
          [-140.0, 59.0], [-130.0, 52.0], [-125.0, 45.0], [-122.0, 38.0],
          [-115.0, 28.0], [-105.0, 18.0], [-95.0, 12.0], [-85.0, 8.0],
          [-80.0, 2.0], [-78.0, -8.0], [-72.0, -20.0], [-70.0, -32.0],
          [-72.0, -44.0], [-74.0, -52.0],
        ],
      },
    },
  ],
};

/** Alpine\u2013Himalayan (Mid-Continental) earthquake belt. */
const alpideBelt: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'alpide', name: 'Alpine\u2013Himalayan belt \u2014 Alps \u2192 Turkey \u2192 Iran \u2192 Himalaya \u2192 Indonesia' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [-8.0, 37.0], [3.0, 40.0], [10.0, 45.0], [20.0, 42.0],
          [30.0, 39.0], [44.0, 38.0], [52.0, 35.0], [62.0, 34.0],
          [72.0, 35.0], [80.0, 30.0], [88.0, 28.0], [95.0, 27.0],
          [98.0, 20.0], [98.0, 10.0], [102.0, 2.0], [110.0, -6.0],
          [118.0, -8.5], [126.0, -8.0],
        ],
      },
    },
  ],
};

/** Mid-Atlantic Ridge \u2014 divergent boundary / fissure volcanism. */
const midAtlantic: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'mar', name: 'Mid-Atlantic Ridge \u2014 divergent boundary (fissure volcanoes)' },
      geometry: {
        type: 'LineString',
        coordinates: [
          [-18.0, 64.5], [-25.0, 55.0], [-30.0, 45.0], [-38.0, 35.0],
          [-44.0, 25.0], [-46.0, 15.0], [-44.0, 5.0], [-30.0, -5.0],
          [-22.0, -15.0], [-18.0, -25.0], [-15.0, -35.0], [-14.0, -45.0],
        ],
      },
    },
  ],
};

/** The four great fold-mountain systems (convergent boundaries). */
const foldMountains: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'himalaya-w', name: 'Himalayas (Asia) \u2014 fold, convergent boundary' }, geometry: { type: 'Point', coordinates: [84.0, 28.5] } },
    { type: 'Feature', properties: { id: 'alps-w', name: 'Alps (Europe) \u2014 fold' }, geometry: { type: 'Point', coordinates: [10.0, 46.5] } },
    { type: 'Feature', properties: { id: 'rockies-w', name: 'Rockies (North America) \u2014 fold' }, geometry: { type: 'Point', coordinates: [-110.0, 45.0] } },
    { type: 'Feature', properties: { id: 'andes-w', name: 'Andes (South America) \u2014 fold, longest chain' }, geometry: { type: 'Point', coordinates: [-70.0, -25.0] } },
  ],
};

/** Block mountains (horsts) \u2014 tension + faulting. */
const blockMountains: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'sierra-nevada', name: 'Sierra Nevada (N. America) \u2014 block mountain / horst' }, geometry: { type: 'Point', coordinates: [-119.0, 37.5] } },
    { type: 'Feature', properties: { id: 'black-forest', name: 'Black Forest (Germany) \u2014 block mountain; Rhine rift = graben' }, geometry: { type: 'Point', coordinates: [8.2, 48.2] } },
  ],
};

export const restlessEarthChapter: Chapter = {
  id: 'world-restless-earth',
  subject: 'geography',
  unit: 'World',
  tags: ['himalayas', 'ring-of-fire', 'earthquakes', 'plate-boundaries', 'aravalli'],
  title: 'World: The Restless Earth',
  summary: 'Ring of Fire, quake belts, fold vs block mountains, volcanism.',
  focus:
    'The Circum-Pacific \u201cRing of Fire\u201d alone accounts for ~68% of all earthquakes \u2014 quakes, volcanoes and young fold mountains all cluster on the same convergent plate boundaries.',
  view: { center: [15.0, 60.0], zoom: 2 },
  worldExtent: true,
  basemap: 'physical',
  theme: { accent: '#c2452d', mapBg: '#f3ede2' },

  layers: [
    {
      id: 'ring-of-fire',
      name: 'Pacific Ring of Fire',
      description: '~68% of all earthquakes; dense volcano chain.',
      kind: 'vector',
      data: ringOfFire,
      style: { color: '#c2452d', weight: 4, flow: true, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'alpide-belt',
      name: 'Alpine\u2013Himalayan belt',
      description: 'The second great quake belt \u2014 runs through India.',
      kind: 'vector',
      data: alpideBelt,
      style: { color: '#b0632c', weight: 3.5, flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'mid-atlantic',
      name: 'Mid-Atlantic Ridge',
      description: 'Divergent boundary \u2014 fissure-type volcanism.',
      kind: 'vector',
      data: midAtlantic,
      style: { color: '#4a5fa5', weight: 3, dashArray: '2 8', flow: true },
      defaultOn: false,
      labelKey: 'name',
    },
    {
      id: 'fold-mountains',
      name: 'Fold mountains',
      description: 'Himalaya, Alps, Rockies, Andes \u2014 convergent boundaries.',
      kind: 'vector',
      data: foldMountains,
      style: { color: '#2e7d5b', weight: 2, fillColor: '#2e7d5b', markerRadius: 8, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'block-mountains',
      name: 'Block mountains (horsts)',
      description: 'Sierra Nevada, Black Forest \u2014 tension + faulting.',
      kind: 'vector',
      data: blockMountains,
      style: { color: '#7a5aa8', weight: 2, fillColor: '#7a5aa8', markerRadius: 8 },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'Mountains cover ~27% of the world\u2019s land surface, supply up to 80% of the planet\u2019s fresh surface water, house ~12% of humanity (FAO) \u2014 and over 50% of people depend directly or indirectly on mountain resources.',
    },
    {
      id: 'f2',
      text: 'Three-way classification: FOLD mountains form at convergent plate boundaries (Himalayas, Alps, Rockies, Andes); BLOCK mountains form by tension and faulting \u2014 the uplifted block is a HORST, the dropped valley a GRABEN (Sierra Nevada, Black Forest); VOLCANIC mountains are \u201cmountains of accumulation\u201d built from erupted material.',
      linkedLayerId: 'fold-mountains',
    },
    {
      id: 'f3',
      text: 'Earthquake anatomy: energy releases at the FOCUS (hypocentre) inside the earth; the point on the surface directly above is the EPICENTRE. Most shallow quakes are sudden stress release along a fault rupture.',
    },
    {
      id: 'f4',
      text: 'Shadow zones \u2014 how we know the core: P-waves go missing between 103\u00b0 and 142\u00b0 from the epicentre; S-waves vanish beyond 103\u00b0 entirely (they cannot cross the liquid outer core). Beyond 142\u00b0 only P-waves reappear. The 103\u00b0\u2013142\u00b0 band is the shadow zone for BOTH wave types.',
    },
    {
      id: 'f5',
      text: 'The Circum-Pacific Belt \u2014 the \u201cPacific Ring of Fire\u201d \u2014 accounts for about 68% of all earthquakes and hugs heavily populated coasts. It is a chain of subduction zones: converging plates dive, melt, and feed explosive volcanoes.',
      linkedLayerId: 'ring-of-fire',
    },
    {
      id: 'f6',
      text: 'Volcanism 101: magma from the upper mantle reaches the surface as LAVA plus ash, gases and rock fragments. Eruption style (explosive vs effusive) depends on magma composition, gas content and volcano structure. Divergent boundaries produce fissure-type volcanoes and mid-ocean ridges; convergent boundaries produce subduction-zone volcanoes.',
      linkedLayerId: 'mid-atlantic',
    },
    {
      id: 'f7',
      text: 'Tsunami logic: an undersea quake suddenly displaces the water column; waves race across open ocean and rear up in shallow coastal water. Depth of focus sets the warning delay \u2014 roughly 60\u201390 seconds between P-wave arrival and the destructive shaking.',
    },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'The Pacific Ring of Fire accounts for approximately what share of all earthquakes?',
      options: ['25%', '45%', '68%', '90%'],
      answerIndex: 2,
      explanation: 'About 68% \u2014 the Circum-Pacific Belt is the planet\u2019s most important earthquake belt, and because it is a chain of subduction zones it also carries most active volcanoes.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'In block-mountain country, the uplifted block and the dropped rift valley are called, respectively:',
      options: ['Graben and horst', 'Horst and graben', 'Syncline and anticline', 'Butte and mesa'],
      answerIndex: 1,
      explanation: 'HORST = the raised block (the mountain, e.g. Black Forest, Sierra Nevada); GRABEN = the sunken rift between parallel faults. Tension + faulting, not folding.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click the Andes \u2014 the fold-mountain wall of South America on the Ring of Fire.',
      answer: { lat: -25.0, lng: -70.0, toleranceKm: 900 },
      explanation: 'The Andes run down South America\u2019s Pacific edge \u2014 where the Nazca plate subducts under South America. Fold mountains, earthquakes and volcanoes stacked on one boundary.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'The P-wave shadow zone appears as a band around the earth between:',
      options: [
        '0\u00b0 and 45\u00b0 from the epicentre',
        '45\u00b0 and 90\u00b0 from the epicentre',
        '103\u00b0 and 142\u00b0 from the epicentre',
        '142\u00b0 and 180\u00b0 from the epicentre',
      ],
      answerIndex: 2,
      explanation: '103\u00b0\u2013142\u00b0. S-waves disappear beyond 103\u00b0 altogether (liquid outer core blocks them); P-waves reappear beyond 142\u00b0. The overlap band is the shadow zone for both.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click the Black Forest \u2014 the classic European block mountain.',
      answer: { lat: 48.2, lng: 8.2, toleranceKm: 500 },
      explanation: 'The Black Forest in Germany is a horst; the Rhine rift valley beside it is the matching graben.',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Fissure-type volcanoes and mid-ocean ridges form at which kind of plate boundary?',
      options: ['Convergent', 'Divergent', 'Transform', 'Passive margin'],
      answerIndex: 1,
      explanation: 'Divergent boundaries \u2014 plates pull apart and magma wells up through fissures (e.g. the Mid-Atlantic Ridge). Convergent/subduction boundaries give the explosive Ring-of-Fire volcanoes instead.',
    },
    {
      id: 'q7',
      type: 'mcq',
      question: 'The point INSIDE the earth where quake energy is released, and the surface point directly above it, are:',
      options: [
        'Epicentre; focus',
        'Focus (hypocentre); epicentre',
        'Fault; scarp',
        'Node; antinode',
      ],
      answerIndex: 1,
      explanation: 'Focus/hypocentre = the release point at depth; epicentre = the surface point vertically above it, where shaking is usually strongest.',
    },
  ],
};

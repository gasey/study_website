import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// CLIMATE & MONSOON — first vertical slice
//
// Data here is deliberately small and hand-shaped.
// Real GeoJSON for states/climate-zones can be
// dropped in later; the chapter's shape stays the same.
// ============================================

/** Simplified climate zones — illustrative polygons covering broad regions of India.
 *  Coordinates are intentionally coarse; we're after recognition, not surveying. */
const climateZones: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'tropical-wet', name: 'Tropical Wet (Aw/Am)', color: '#2d6a4f' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [73.0, 8.5], [77.5, 8.0], [78.0, 12.5], [76.5, 15.5],
          [73.5, 16.5], [72.8, 13.0], [73.0, 8.5],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'tropical-dry', name: 'Tropical Dry (BSh)', color: '#c46a3d' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [70.5, 22.0], [76.0, 22.5], [78.0, 26.0], [75.0, 28.5],
          [70.0, 28.0], [68.5, 25.0], [70.5, 22.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'humid-subtropical', name: 'Humid Subtropical (Cwa)', color: '#52796f' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [78.0, 25.0], [88.0, 25.5], [90.0, 27.5], [85.0, 28.5],
          [78.5, 28.0], [78.0, 25.0],
        ]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'mountain', name: 'Mountain Climate (H)', color: '#6c757d' },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [74.0, 32.0], [80.0, 30.5], [88.0, 27.5], [95.0, 28.0],
          [97.0, 29.5], [89.0, 30.0], [78.0, 33.5], [74.0, 32.0],
        ]],
      },
    },
  ],
};

/** Southwest monsoon — two main branches. */
const swMonsoonArrows: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'arabian-sea-branch', name: 'Arabian Sea Branch', phase: 'sw' },
      geometry: {
        type: 'LineString',
        coordinates: [[68.0, 5.0], [72.0, 10.0], [73.5, 15.0], [73.0, 19.0], [72.5, 23.0]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'bay-of-bengal-branch', name: 'Bay of Bengal Branch', phase: 'sw' },
      geometry: {
        type: 'LineString',
        coordinates: [[90.0, 6.0], [88.0, 13.0], [88.5, 20.0], [85.0, 25.0], [80.0, 27.0], [75.0, 28.5]],
      },
    },
    {
      type: 'Feature',
      properties: { id: 'sw-deflected', name: 'Deflected Branch (Ganga Plain)', phase: 'sw' },
      geometry: {
        type: 'LineString',
        coordinates: [[88.5, 24.0], [83.0, 25.5], [78.0, 26.5], [74.0, 27.0]],
      },
    },
  ],
};

/** Northeast (retreating) monsoon. */
const neMonsoonArrows: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'ne-monsoon-main', name: 'Northeast Monsoon', phase: 'ne' },
      geometry: {
        type: 'LineString',
        coordinates: [[85.0, 27.0], [82.0, 22.0], [80.0, 17.0], [80.0, 12.0], [78.0, 9.0]],
      },
    },
  ],
};

/** A few key cities — useful spatial anchors for quizzes. */
const cities: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'mumbai', name: 'Mumbai' }, geometry: { type: 'Point', coordinates: [72.8777, 19.0760] } },
    { type: 'Feature', properties: { id: 'chennai', name: 'Chennai' }, geometry: { type: 'Point', coordinates: [80.2707, 13.0827] } },
    { type: 'Feature', properties: { id: 'kolkata', name: 'Kolkata' }, geometry: { type: 'Point', coordinates: [88.3639, 22.5726] } },
    { type: 'Feature', properties: { id: 'delhi', name: 'Delhi' }, geometry: { type: 'Point', coordinates: [77.1025, 28.7041] } },
    { type: 'Feature', properties: { id: 'jaisalmer', name: 'Jaisalmer' }, geometry: { type: 'Point', coordinates: [70.9083, 26.9157] } },
    { type: 'Feature', properties: { id: 'cherrapunji', name: 'Cherrapunji' }, geometry: { type: 'Point', coordinates: [91.7195, 25.2702] } },
    { type: 'Feature', properties: { id: 'thiruvananthapuram', name: 'Thiruvananthapuram' }, geometry: { type: 'Point', coordinates: [76.9366, 8.5241] } },
  ],
};

export const climateMonsoonChapter: Chapter = {
  id: 'climate-monsoon',
  subject: 'geography',
  unit: 'India Physical',
  tags: ['monsoon', 'el-nino', 'himalayas', 'western-ghats', 'tropic-of-cancer', 'trade-winds'],
  title: 'Climate & Monsoon',
  summary: 'India\u2019s climate zones, the southwest and northeast monsoons, and the key cities shaped by them.',
  view: { center: [22.5, 80.0], zoom: 5 },
  basemap: 'physical',
  focus: 'India\u2019s climate is the monsoon. Two seasonal winds reverse over the Indian Ocean, and that reversal shapes agriculture, settlement, and history.',
  layers: [
    {
      id: 'climate-zones',
      name: 'Climate Zones (Köppen)',
      description: 'Broad climate classification across India.',
      kind: 'vector',
      data: climateZones,
      defaultOn: true,
      labelKey: 'name',
      style: { color: '#3a7a7a', weight: 1.5, fillOpacity: 0.45, shadow: true },
    },
    {
      id: 'sw-monsoon',
      name: 'Southwest Monsoon',
      description: 'June\u2013September. The main rain-bearing wind system.',
      kind: 'vector',
      data: swMonsoonArrows,
      defaultOn: true,
      style: { color: '#1d4f7a', weight: 3.5 },
    },
    {
      id: 'ne-monsoon',
      name: 'Northeast Monsoon',
      description: 'October\u2013December. Brings rain mainly to Tamil Nadu.',
      kind: 'vector',
      data: neMonsoonArrows,
      defaultOn: false,
      style: { color: '#c46a3d', weight: 3.5, dashArray: '6 4' },
    },
    {
      id: 'cities',
      name: 'Reference Cities',
      description: 'Spatial anchors for monsoon and climate.',
      kind: 'vector',
      data: cities,
      defaultOn: true,
      labelKey: 'name',
    },
  ],
  facts: [
    {
      id: 'f1',
      text: 'India experiences a tropical monsoon climate, dominated by the seasonal reversal of winds over the Indian Ocean.',
    },
    {
      id: 'f2',
      text: 'The southwest monsoon (June\u2013September) accounts for about 75% of India\u2019s annual rainfall.',
      linkedLayerId: 'sw-monsoon',
    },
    {
      id: 'f3',
      text: 'The Arabian Sea branch strikes the Western Ghats first, producing heavy rain on the windward side and a rain-shadow on the leeward side (the Deccan Plateau).',
      linkedLayerId: 'sw-monsoon',
    },
    {
      id: 'f4',
      text: 'The Bay of Bengal branch advances along the Ganga plain and is deflected by the Himalayas, watering northern and eastern India.',
      linkedLayerId: 'sw-monsoon',
    },
    {
      id: 'f5',
      text: 'The northeast monsoon (October\u2013December) brings most of Tamil Nadu\u2019s rainfall, since the state lies in the rain-shadow of the Western Ghats during the southwest monsoon.',
      linkedLayerId: 'ne-monsoon',
    },
    {
      id: 'f6',
      text: 'Mawsynram and Cherrapunji in Meghalaya are among the wettest places on Earth, due to orographic lift from the Bay of Bengal branch hitting the Khasi Hills.',
      linkedFeatureId: 'cherrapunji',
    },
    {
      id: 'f7',
      text: 'Jaisalmer in the Thar Desert receives less than 200 mm of rainfall annually \u2014 a tropical dry climate.',
      linkedFeatureId: 'jaisalmer',
    },
  ],
  quiz: [
    {
      id: 'q1',
      type: 'map_click',
      question: 'Click the location that receives some of the highest rainfall in the world.',
      answer: { lat: 25.27, lng: 91.72, toleranceKm: 150 },
      explanation: 'Cherrapunji (and nearby Mawsynram) in Meghalaya \u2014 the Khasi Hills force the Bay of Bengal branch upward, producing extreme orographic rainfall.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'Which branch of the southwest monsoon first strikes the Western Ghats?',
      options: ['Bay of Bengal branch', 'Arabian Sea branch', 'Northeast monsoon', 'Western disturbance'],
      answerIndex: 1,
      explanation: 'The Arabian Sea branch hits the Western Ghats, producing heavy windward rainfall and a rain-shadow over the Deccan.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click the city that receives most of its annual rainfall from the northeast monsoon.',
      answer: { lat: 13.08, lng: 80.27, toleranceKm: 120 },
      explanation: 'Chennai \u2014 Tamil Nadu lies in the rain-shadow of the Western Ghats during the SW monsoon, so it depends on the retreating NE monsoon (Oct\u2013Dec).',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'What percentage of India\u2019s annual rainfall is delivered by the southwest monsoon?',
      options: ['About 25%', 'About 50%', 'About 75%', 'About 95%'],
      answerIndex: 2,
      explanation: 'Roughly 75% \u2014 the SW monsoon is the single most important climatic event of the Indian year.',
    },
    {
      id: 'q5',
      type: 'map_click',
      question: 'Click an area with a Tropical Dry (BSh) climate.',
      answer: { lat: 27.0, lng: 71.5, toleranceKm: 250 },
      explanation: 'The Thar Desert region in Rajasthan \u2014 hot, arid, less than 250 mm rainfall a year.',
    },
  ],
};

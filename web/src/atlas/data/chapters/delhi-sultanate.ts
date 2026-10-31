import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// DELHI SULTANATE \u2014 FIVE DYNASTIES (1206\u20131526)
//
// Concept:
//   "One city, five dynasties, 320 years. Every experiment \u2014
//   Alauddin's markets, Tughlaq's capital shift and token money,
//   Timur's sack \u2014 radiates out of Delhi and snaps back to it."
//
// Source: Medieval Indian History \u2014 Delhi Sultanate deck.
// ============================================

const sultanateSites: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    { type: 'Feature', properties: { id: 'delhi-s', name: 'Delhi \u2014 seat of all five dynasties; Qutub Minar begun by Aibak, finished by Iltutmish' }, geometry: { type: 'Point', coordinates: [77.23, 28.65] } },
    { type: 'Feature', properties: { id: 'lahore-s', name: 'Lahore \u2014 Aibak\u2019s first capital; he died here playing chaugan (1210)' }, geometry: { type: 'Point', coordinates: [74.35, 31.55] } },
    { type: 'Feature', properties: { id: 'daulatabad', name: 'Daulatabad (Devagiri) \u2014 Muhammad-bin-Tughlaq\u2019s capital experiment, 1327' }, geometry: { type: 'Point', coordinates: [75.21, 19.94] } },
    { type: 'Feature', properties: { id: 'multan-s', name: 'Multan \u2014 frontier province against the Mongols' }, geometry: { type: 'Point', coordinates: [71.47, 30.2] } },
    { type: 'Feature', properties: { id: 'agra-s', name: 'Agra \u2014 founded by Sikandar Lodi (1504) as his capital' }, geometry: { type: 'Point', coordinates: [78.01, 27.18] } },
  ],
};

/** MBT's infamous capital transfer \u2014 1500 km, twice. */
const capitalShift: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'shift-line', name: '1327: Delhi \u2192 Daulatabad (and back) \u2014 1,500+ km of forced march' },
      geometry: { type: 'LineString', coordinates: [[77.23, 28.65], [76.8, 26.9], [76.2, 24.8], [75.8, 22.5], [75.4, 21.0], [75.21, 19.94]] },
    },
  ],
};

/** Timur's 1398 invasion path. */
const timurPath: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'timur-line', name: '1398: Timur \u2014 Central Asia \u2192 Punjab \u2192 sack of Delhi (death blow to the Tughlaqs)' },
      geometry: { type: 'LineString', coordinates: [[69.2, 34.5], [71.5, 33.5], [73.1, 32.5], [74.35, 31.55], [75.9, 30.2], [77.23, 28.65]] },
    },
  ],
};

export const delhiSultanateChapter: Chapter = {
  id: 'delhi-sultanate',
  subject: 'history',
  unit: 'Medieval',
  tags: ['delhi', 'punjab', 'deccan', 'khyber', 'agra', 'panipat'],
  title: 'Delhi Sultanate: Five Dynasties',
  summary: 'Slave \u2192 Khalji \u2192 Tughlaq \u2192 Sayyid \u2192 Lodi \u2014 rulers, reforms, experiments.',
  focus:
    'One city, five dynasties, 320 years (1206\u20131526). The Sultanate\u2019s story is a set of experiments radiating from Delhi \u2014 Alauddin\u2019s market control, Tughlaq\u2019s capital shift and token currency \u2014 and every experiment snaps back to Delhi.',
  view: { center: [26.0, 76.5], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#5b46a8', mapBg: '#f1eef8' },

  layers: [
    {
      id: 'sultanate-sites',
      name: 'Capitals & key cities',
      kind: 'vector',
      data: sultanateSites,
      style: { color: '#5b46a8', weight: 2, fillColor: '#5b46a8', markerRadius: 7, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'capital-shift',
      name: 'MBT\u2019s capital shift (1327)',
      kind: 'vector',
      data: capitalShift,
      style: { color: '#b0632c', weight: 3, dashArray: '2 8', flow: true },
      defaultOn: true,
      labelKey: 'name',
    },
    {
      id: 'timur-path',
      name: 'Timur\u2019s invasion (1398)',
      kind: 'vector',
      data: timurPath,
      style: { color: '#b3261e', weight: 3, dashArray: '8 5', flow: true },
      defaultOn: false,
      labelKey: 'name',
    },
  ],

  facts: [
    {
      id: 'f1',
      text: 'The five dynasties in order: SLAVE/Mamluk (1206\u201390), KHALJI (1290\u20131320), TUGHLAQ (1320\u20131414), SAYYID (1414\u201351), LODI (1451\u20131526). Mnemonic: \u201cSlaves Keep The Sultan\u2019s Law\u201d.',
    },
    {
      id: 'f2',
      text: 'Qutb-ud-din AIBAK (1206\u201310): Ghori\u2019s Turkish slave, governor of his Indian lands, founder of the Slave dynasty; called \u201cLakh Baksh\u201d (giver of lakhs) for generosity; began the Qutub Minar (named for the sufi Qutbuddin Bakhtiyar Kaki); died at Lahore playing chaugan (horse polo). His incapable son Aram Shah lasted eight months.',
      linkedLayerId: 'sultanate-sites',
      linkedFeatureId: 'lahore-s',
    },
    {
      id: 'f3',
      text: 'ILTUTMISH (1211\u201336): the real consolidator \u2014 completed the Qutub Minar, introduced the silver TANKA and copper JITAL, organized the CHAHALGANI (corps of forty Turkish nobles), and saved India from Chingiz Khan by refusing refuge to the Khwarizm prince (1221). He nominated his daughter RAZIA (1236\u201340) \u2014 the first and only woman on the Delhi throne; her rise fell foul of the Forty.',
    },
    {
      id: 'f4',
      text: 'BALBAN (1266\u201387): broke the Chahalgani, ruled by \u201cblood and iron\u201d, enforced SIJDA (prostration) and PAIBOS (kissing the royal feet), introduced the Persian Nauroz festival, ran an efficient spy network, and championed Turkish-only nobility \u2014 theory of kingship: the Sultan as Zil-e-Ilahi, shadow of God.',
    },
    {
      id: 'f5',
      text: 'ALAUDDIN KHALJI (1296\u20131316): first Sultan with a large PERMANENT standing army paid in cash; introduced DAGH (horse branding) and HULIYA (soldier descriptive rolls); ruthless MARKET CONTROL \u2014 fixed prices, separate markets, the shahna-i-mandi inspector; land revenue raised to half the produce in the doab. His general Malik Kafur raided the deep south (Devagiri, Warangal, Madurai).',
    },
    {
      id: 'f6',
      text: 'MUHAMMAD-BIN-TUGHLAQ (1325\u201351): the Sultanate\u2019s great experimenter. (1) Capital transfer 1327: Delhi \u2192 Devagiri, renamed DAULATABAD, to control the south \u2014 the whole population force-marched 1,500+ km; water scarcity forced the return two years later. (2) TOKEN CURRENCY 1329: copper coins valued as silver, on the Chinese paper-money model \u2014 forgery exploded, the treasury emptied redeeming them. Brilliant ideas, broken execution.',
      linkedLayerId: 'capital-shift',
    },
    {
      id: 'f7',
      text: 'FIROZ SHAH TUGHLAQ (1351\u201388): the builder-welfare Sultan \u2014 canals, new towns (Firozabad, Hisar), employment bureau, Diwan-i-Khairat (charity); but he revived the jagir system and made the army hereditary, weakening the centre. After him: TIMUR, 1398 \u2014 the Chagatai Mongol sacked Delhi for three days against barely any opposition, and his withdrawal in 1399 was the death blow to the Tughlaqs.',
      linkedLayerId: 'timur-path',
    },
    {
      id: 'f8',
      text: 'Endgame: the SAYYIDS (1414\u201351, Khizr Khan \u2014 Timur\u2019s nominee) ruled a shrunken Delhi; the LODIS (Afghan, not Turkish) followed \u2014 Bahlol (1451\u201389), SIKANDAR (1489\u20131517, founded AGRA 1504, moved the capital there), and IBRAHIM (1517\u201326), whose harshness pushed Daulat Khan Lodi to invite Babur. First Battle of Panipat, 21 April 1526 \u2014 the Sultanate ends where the Gateway-Battles chapter picks up.',
    },
  ],

  events: [
    { id: 'e1', date: '1206', label: 'Aibak', description: 'Qutb-ud-din Aibak founds the Slave dynasty \u2014 the Delhi Sultanate begins. Capital at Lahore.', showLayers: ['sultanate-sites'], hideLayers: ['timur-path'], view: { center: [30.0, 75.5], zoom: 6 } },
    { id: 'e2', date: '1236', label: 'Razia', description: 'Iltutmish\u2019s daughter Razia takes the throne \u2014 the only woman Sultan of Delhi. The Forty bring her down by 1240.', view: { center: [28.65, 77.23], zoom: 7 } },
    { id: 'e3', date: '1296', label: 'Khalji zenith', description: 'Alauddin Khalji: standing army, dagh & huliya, market control; Malik Kafur raids to Madurai.', view: { center: [24.0, 77.0], zoom: 5 } },
    { id: 'e4', date: '1327', label: 'Capital shift', description: 'Muhammad-bin-Tughlaq marches Delhi to Daulatabad \u2014 and back. Token currency follows in 1329.', showLayers: ['capital-shift', 'sultanate-sites'], view: { center: [24.0, 76.0], zoom: 5 } },
    { id: 'e5', date: '1398', label: 'Timur sacks Delhi', description: 'Timur, head of the Chagatai Turks, plunders Delhi for three days \u2014 the Tughlaqs never recover.', showLayers: ['timur-path'], view: { center: [30.5, 74.0], zoom: 5 } },
    { id: 'e6', date: '1526-04-21', label: 'Panipat: the end', description: 'Ibrahim Lodi falls to Babur at Panipat. Five dynasties, 320 years \u2014 done.', hideLayers: ['timur-path'], view: { center: [29.39, 76.97], zoom: 7 } },
  ],

  quiz: [
    {
      id: 'q1',
      type: 'mcq',
      question: 'Arrange the five Sultanate dynasties in order:',
      options: [
        'Khalji \u2192 Slave \u2192 Tughlaq \u2192 Lodi \u2192 Sayyid',
        'Slave \u2192 Khalji \u2192 Tughlaq \u2192 Sayyid \u2192 Lodi',
        'Slave \u2192 Tughlaq \u2192 Khalji \u2192 Sayyid \u2192 Lodi',
        'Tughlaq \u2192 Khalji \u2192 Slave \u2192 Lodi \u2192 Sayyid',
      ],
      answerIndex: 1,
      explanation: 'Slave (1206\u201390) \u2192 Khalji (1290\u20131320) \u2192 Tughlaq (1320\u20131414) \u2192 Sayyid (1414\u201351) \u2192 Lodi (1451\u20131526). \u201cSlaves Keep The Sultan\u2019s Law\u201d.',
    },
    {
      id: 'q2',
      type: 'mcq',
      question: 'The silver tanka and copper jital were introduced by:',
      options: ['Aibak', 'Iltutmish', 'Balban', 'Alauddin Khalji'],
      answerIndex: 1,
      explanation: 'Iltutmish \u2014 also completer of the Qutub Minar, creator of the Chahalgani, and the Sultan who dodged Chingiz Khan in 1221. He nominated Razia as successor.',
    },
    {
      id: 'q3',
      type: 'map_click',
      question: 'Click Daulatabad (Devagiri) \u2014 Muhammad-bin-Tughlaq\u2019s ill-fated new capital.',
      answer: { lat: 19.94, lng: 75.21, toleranceKm: 130 },
      explanation: 'Daulatabad sits in the Deccan near Aurangabad \u2014 1,500+ km from Delhi. Chosen to control the south; abandoned within two years for want of water.',
    },
    {
      id: 'q4',
      type: 'mcq',
      question: 'Muhammad-bin-Tughlaq\u2019s token currency failed mainly because:',
      options: [
        'Gold ran out in the treasury',
        'The copper tokens were easy to forge, and people hoarded gold/silver',
        'The Mongols stole the mint',
        'Merchants refused all coins',
      ],
      answerIndex: 1,
      explanation: 'Modelled on Kublai Khan\u2019s paper money, the copper tokens were freely forged; when MBT redeemed them all in gold/silver, the treasury emptied. Brilliant idea, broken execution \u2014 his signature.',
    },
    {
      id: 'q5',
      type: 'mcq',
      question: 'Dagh (branding of horses) and huliya (descriptive rolls of soldiers) were military reforms of:',
      options: ['Balban', 'Alauddin Khalji', 'Firoz Shah Tughlaq', 'Sikandar Lodi'],
      answerIndex: 1,
      explanation: 'Alauddin Khalji \u2014 paired with the first cash-paid permanent standing army and his famous market-control system (fixed prices, shahna-i-mandi).',
    },
    {
      id: 'q6',
      type: 'mcq',
      question: 'Sijda and paibos (prostration and kissing the royal feet) were court ceremonies enforced by:',
      options: ['Iltutmish', 'Razia', 'Balban', 'Ibrahim Lodi'],
      answerIndex: 2,
      explanation: 'Balban \u2014 with the Nauroz festival, the spy system, the destruction of the Chahalgani, and the theory of the Sultan as Zil-e-Ilahi (shadow of God).',
    },
    {
      id: 'q7',
      type: 'map_click',
      question: 'Click Agra \u2014 founded in 1504 by Sikandar Lodi as his new capital.',
      answer: { lat: 27.18, lng: 78.01, toleranceKm: 90 },
      explanation: 'Sikandar Lodi moved the capital from Delhi to his new city of Agra \u2014 which is why Babur\u2019s Mughals inherited Agra as a power centre.',
    },
    {
      id: 'q8',
      type: 'mcq',
      question: 'Timur\u2019s 1398 invasion is significant because it:',
      options: [
        'Founded the Mughal empire directly',
        'Gave a death blow to the Tughlaq dynasty and left Delhi power shattered',
        'Was repelled by Firoz Shah',
        'Introduced gunpowder to India',
      ],
      answerIndex: 1,
      explanation: 'Timur sacked a nearly undefended Delhi for three days and withdrew in 1399. The Tughlaqs collapsed; his nominee Khizr Khan founded the Sayyid dynasty. (Timur\u2019s descendant Babur returned in 1526.)',
    },
  ],
};

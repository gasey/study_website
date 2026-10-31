import type { Chapter } from '../../types';
import type { FeatureCollection } from 'geojson';

// ============================================
// PARLIAMENT — Articles 79–108
//
// Authored concept:
//   "One building in Delhi, two houses, three readings —
//   but Parliament's reach runs the whole map: it can
//   legislate into the State List (Arts 249/252/253) and
//   redraw state boundaries itself."
//
// Content mined from olol: Lecture 3 (Parliament).pptx
// (Dr. F. Lalramhluni, MS Academy).
// ============================================

const SANSAD: [number, number] = [28.6172, 77.2082];

const seatOfParliament: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { id: 'sansad', name: 'Sansad Bhavan, New Delhi — President + Rajya Sabha + Lok Sabha (Art 79)' },
      geometry: { type: 'Point', coordinates: [SANSAD[1], SANSAD[0]] },
    },
  ],
};

export const polityParliamentChapter: Chapter = {
  id: 'polity-parliament',
  subject: 'polity',
  unit: 'Institutions',
  tags: ['delhi', 'constitution', 'parliament', 'states'],
  title: 'Parliament (Art 79–108)',
  summary: 'Structure, sessions, Speaker, devices of proceedings, Rajya Sabha vs Lok Sabha — and how Parliament reaches into the State List.',
  focus:
    'Art 79: Parliament = President + RS + LS. Track the numbers (250/238+12; 550 max, 543 filled; quorum 1/10) and the four routes into the State List: Emergency/356, Art 249 (RS \u2154 resolution), Art 252 (two+ states resolve), Art 253 (treaties).',
  view: { center: [26.5, 80.0], zoom: 5 },
  basemap: 'natgeo',
  theme: { accent: '#4a5fa5' },
  layers: [
    {
      id: 'sansad',
      name: 'Seat of Parliament',
      description: 'Sansad Bhavan — where all three components of Parliament converge.',
      kind: 'vector',
      data: seatOfParliament,
      style: { color: '#4a5fa5', markerRadius: 9, glow: true },
      defaultOn: true,
      labelKey: 'name',
    },
  ],
  facts: [
    { id: 'f1', text: 'Article 79: Parliament = President + Council of States (Rajya Sabha) + House of the People (Lok Sabha). The President is part of Parliament though not a member of either House — assent is mandatory for a Bill to become an Act.', linkedLayerId: 'sansad' },
    { id: 'f2', text: 'Article 80 — Rajya Sabha: max 250 = 238 representatives of states/UTs + 12 nominated by the President (literature, science, art, social service). State members are elected by elected MLAs via proportional representation by single transferable vote; seats allocated per the Fourth Schedule.' },
    { id: 'f3', text: 'Lok Sabha: constitutional max 550 (530 states + 20 UTs); currently 543 elected. UT members chosen by direct election under the UT (Direct Election to the House of the People) Act, 1965. Anglo-Indian nomination (2 members) removed by the 104th Amendment, effective Jan 2020.' },
    { id: 'f4', text: 'Article 83: Rajya Sabha is a continuing house — never dissolved; one-third retires every second year (6-year member term). Lok Sabha: 5 years from first meeting; extendable during Emergency one year at a time, not beyond 6 months after the proclamation ends.' },
    { id: 'f5', text: 'Four routes for Parliament into the State List: (1) National Emergency or President\u2019s Rule (Art 356); (2) Art 249 — RS resolution by \u2154 present & voting, in the national interest; (3) Art 252 — two or more state legislatures resolve; (4) Art 253 — implementing international treaties.' },
    { id: 'f6', text: 'Speaker: final interpreter of the Constitution/Rules/conventions inside the LS; casting vote only on a tie; presides over joint sittings; decides Money Bill status (final); decides Tenth-Schedule defection disqualifications; ex-officio chairman of the Indian Parliamentary Group.' },
    { id: 'f7', text: 'Speaker Pro Tem: senior-most LS member, appointed and sworn in by the President; administers oath to new members and enables election of the new Speaker, then the office ceases. Panel of Chairpersons: up to 10 members nominated by the Speaker.' },
    { id: 'f8', text: 'Leader of the House = the PM (or a minister of the LS the PM appoints). Leader of the Opposition = leader of the largest opposition party with at least one-tenth of total seats; salary and facilities equal to a Cabinet minister.' },
    { id: 'f9', text: 'Sessions: max gap between two sessions is 6 months; usually Budget (Feb–May), Monsoon (Jul–Sep), Winter (Nov–Dec). Adjournment suspends a sitting; adjournment sine die = indefinite; prorogation ends the session; dissolution applies to LS only.' },
    { id: 'f10', text: 'Devices: Question Hour is the first hour (starred = oral + supplementaries; unstarred = written; short-notice). Zero Hour — not in the Rules — is the gap between Question Hour and the agenda. Adjournment and censure motions: Lok Sabha only; censure does not force resignation (no-confidence does).' },
    { id: 'f11', text: 'Article 100: questions decided by majority of members present and voting; presiding officer votes only to break a tie. Quorum = one-tenth of the total membership of the House.' },
    { id: 'f12', text: 'Article 108 — joint sitting (summoned by the President; Speaker presides; LS\u2019s numbers usually prevail) when a Bill is rejected by the other House, the Houses disagree on amendments, or 6 months pass without passage. Never for a Money Bill.' },
    { id: 'f13', text: 'RS equal to LS: ordinary bills, President\u2019s election/impeachment, ordinances, all three emergencies, constitutional amendments. RS weaker: Money Bills (LS only; RS returns within 14 days), no vote on demands for grants, ministers collectively responsible to LS alone. RS special: Art 249 (State List) and Art 312 (new All-India Services); alone initiates VP\u2019s removal.' },
  ],
  events: [
    { id: 'e1', date: '1965', label: '1965 — UT Direct Election Act', description: 'Parliament prescribes direct election for Lok Sabha members from Union Territories.' },
    { id: 'e2', date: '2020-01', label: '2020 — Anglo-Indian seats end', description: 'The 104th Amendment (2019) removes the President\u2019s nomination of 2 Anglo-Indian members, effective January 2020.' },
    { id: 'e3', date: '2026-02', label: 'Budget Session (Feb–May)', description: 'First and longest session of the parliamentary year — the Union Budget is presented and voted.', showLayers: ['sansad'], view: { center: [28.617, 77.208], zoom: 11 } },
    { id: 'e4', date: '2026-07', label: 'Monsoon Session (Jul–Sep)', description: 'Second session — remember the rule: never more than 6 months between two sessions.' },
    { id: 'e5', date: '2026-11', label: 'Winter Session (Nov–Dec)', description: 'Third session closes the year — three sessions is convention, not a constitutional requirement.' },
  ],
  quiz: [
    {
      id: 'q1', type: 'mcq',
      question: 'Under Article 79, Parliament consists of:',
      options: ['Lok Sabha and Rajya Sabha only', 'President, Rajya Sabha and Lok Sabha', 'President, PM and both Houses', 'Speaker, Rajya Sabha and Lok Sabha'],
      answerIndex: 1,
      explanation: 'The President is a component of Parliament without being a member of either House — assent is mandatory for every Act.',
    },
    {
      id: 'q2', type: 'mcq',
      question: 'Maximum strength of the Rajya Sabha, and the nominated component?',
      options: ['238, with 10 nominated', '250, with 12 nominated', '245, with 15 nominated', '260, with 12 nominated'],
      answerIndex: 1,
      explanation: '250 = up to 238 state/UT representatives + 12 nominated for literature, science, art, social service (Art 80). Seats per the Fourth Schedule.',
    },
    {
      id: 'q3', type: 'mcq',
      question: 'Under Article 249, Parliament can legislate on a State List subject if:',
      options: ['The President orders it', 'The Rajya Sabha passes a resolution by two-thirds of members present and voting', 'The Supreme Court permits it', 'A majority of state legislatures consent'],
      answerIndex: 1,
      explanation: 'Art 249: RS resolution by \u2154 present & voting in the national interest. Other routes: Emergency/356, Art 252 (two+ states), Art 253 (treaties).',
    },
    {
      id: 'q4', type: 'mcq',
      question: 'Who decides, finally, whether a bill is a Money Bill?',
      options: ['The President', 'The Finance Minister', 'The Speaker of the Lok Sabha', 'The Chairman of the Rajya Sabha'],
      answerIndex: 2,
      explanation: 'The Speaker\u2019s decision is final. The Speaker also presides over joint sittings and decides Tenth-Schedule defection cases in the LS.',
    },
    {
      id: 'q5', type: 'mcq',
      question: 'A joint sitting under Article 108 can NEVER be summoned for:',
      options: ['An ordinary bill', 'A financial bill', 'A Money Bill', 'A constitutional amendment bill rejected by one House'],
      answerIndex: 2,
      explanation: 'Money Bills are excluded from Art 108 — the RS can only return them within 14 days. (Amendment bills also bypass joint sittings since both Houses must pass them, but the Article\u2019s express exclusion is the Money Bill.)',
    },
    {
      id: 'q6', type: 'mcq',
      question: 'The quorum to constitute a meeting of either House is:',
      options: ['One-fourth of total members', 'One-tenth of total members', 'One-third of total members', 'Fifty members'],
      answerIndex: 1,
      explanation: 'One-tenth of the total membership (Art 100 context). The presiding officer adjourns or suspends the sitting without quorum.',
    },
    {
      id: 'q7', type: 'map_click',
      question: 'Click the city where all three components of Parliament — President, Rajya Sabha, Lok Sabha — converge.',
      answer: { lat: SANSAD[0], lng: SANSAD[1], toleranceKm: 120 },
      explanation: 'New Delhi — Sansad Bhavan.',
    },
  ],
};

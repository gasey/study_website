import type { Chapter } from '../types';
import { climateMonsoonChapter } from './chapters/climate-monsoon';
import { plasseyChapter } from './chapters/battle-of-plassey';
import { physiographicDivisionsChapter } from './chapters/physiographic-divisions';
import { riversChapter } from './chapters/rivers';
import { mountainsChapter } from './chapters/mountains';
import { soilsChapter } from './chapters/soils';
import { forestsChapter } from './chapters/forests';
import { mizoramGeographyChapter } from './chapters/mizoram-geography';
import { indusValleyChapter } from './chapters/indus-valley';
import { mauryaChapter } from './chapters/mahajanapadas-mauryas';
import { medievalGatewayChapter } from './chapters/medieval-gateway-battles';
import { freedomStruggleChapter } from './chapters/freedom-struggle-map';
import { restlessEarthChapter } from './chapters/world-restless-earth';
import { windsCurrentsChapter } from './chapters/world-winds-currents';
import { vedicAgeChapter } from './chapters/vedic-age';
import { buddhismJainismChapter } from './chapters/buddhism-jainism';
import { delhiSultanateChapter } from './chapters/delhi-sultanate';
import { medievalSouthChapter } from './chapters/medieval-south';
import { europeanConquestChapter } from './chapters/european-conquest';
import { worldResourcesChapter } from './chapters/world-resources-industries';
import { atmosphereHeatChapter } from './chapters/world-atmosphere-heat';
import { polityConstitutionChapter } from './chapters/polity-making-of-constitution';
import { polityStatesReorgChapter } from './chapters/polity-states-reorganisation';
import { politySixthScheduleChapter } from './chapters/polity-sixth-schedule';
import { polityParliamentChapter } from './chapters/polity-parliament';
import { polityJudiciaryChapter } from './chapters/polity-judiciary';

// Register all chapters here. Adding a chapter = importing it + listing it.
export const chapters: Chapter[] = [
  physiographicDivisionsChapter,
  mountainsChapter,
  riversChapter,
  climateMonsoonChapter,
  soilsChapter,
  forestsChapter,
  mizoramGeographyChapter,
  restlessEarthChapter,
  windsCurrentsChapter,
  worldResourcesChapter,
  atmosphereHeatChapter,
  indusValleyChapter,
  vedicAgeChapter,
  mauryaChapter,
  buddhismJainismChapter,
  medievalGatewayChapter,
  delhiSultanateChapter,
  medievalSouthChapter,
  europeanConquestChapter,
  plasseyChapter,
  freedomStruggleChapter,
  polityConstitutionChapter,
  polityStatesReorgChapter,
  politySixthScheduleChapter,
  polityParliamentChapter,
  polityJudiciaryChapter,
];

export function getChapter(id: string): Chapter | undefined {
  return chapters.find((c) => c.id === id);
}

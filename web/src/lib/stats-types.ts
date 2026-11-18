export type StatsSource = {
  id: string;
  title: string;
  url: string;
  method: string;
  cadence: string;
};
export type StatsObservation = {
  place: string;
  name: string;
  period: string;
  value: number | null;
  rank: number | null;
  group: string;
  status: string;
};
export type StatsRelease = {
  id: string;
  edition: string;
  reference_period: string;
  source_url: string;
  methodology: string;
  publisher_date: string | null;
  fetched_at: string;
  published_at: string;
  note: string;
};
export type StatsFreshness = {
  last_checked_at: string | null;
  delayed: boolean;
  message: string | null;
};
export type StatsMetric = {
  id: string;
  title: string;
  code?: string;
  unit: string;
  category: string;
  definition: string;
  source_id: string;
  kind: "indicator" | "index";
  scope: "world" | "states";
  direction: string;
  methodology: string;
};
export type StatsCard = StatsMetric & {
  source: StatsSource;
  release: StatsRelease | null;
  observation: StatsObservation | null;
  freshness: StatsFreshness;
};
export type StatsSurvey = {
  id: string;
  title: string;
  source_url: string;
  description: string;
  appendix_url: string;
  tables?: { id: string; title: string; source_url: string }[];
  catalogue_status?: {
    changed: boolean;
    delayed: boolean;
    last_checked_at: string | null;
  };
  chapters: {
    id: string;
    title: string;
    source_url: string;
    brief?: string;
    figures?: {
      title: string;
      value: string;
      period: string;
      status: string;
      citation: string;
    }[];
  }[];
};
export type StatsOverview = {
  country: string;
  items: StatsCard[];
  surveys: StatsSurvey[];
};
export type StatsDetail = {
  metric: StatsMetric;
  source: StatsSource;
  release: StatsRelease | null;
  places: { id: string; title: string }[];
  history: StatsObservation[];
  observations: StatsObservation[];
  period: string | null;
  periods: string[];
  freshness: StatsFreshness;
};
export type StatsRankings = {
  items: StatsObservation[];
  total: number;
  offset?: number;
  coverage: number;
  india: StatsObservation | null;
  release: StatsRelease | null;
  derived: boolean;
  group: string | null;
  period: string | null;
  groups?: string[];
  periods?: string[];
};

// ============================================
// Core domain types. The whole app is built
// around this schema — adding a new chapter
// means producing one of these objects.
// ============================================

import type { FeatureCollection } from 'geojson';

export type SubjectId = 'geography' | 'history' | 'polity';

/** A single togglable layer within a chapter's map view. */
export type Layer =
  | {
      id: string;
      name: string;
      description?: string;
      kind: 'vector';
      /** Path under /public or an imported GeoJSON object. */
      data: FeatureCollection | string;
      style?: {
        color?: string;
        weight?: number;
        fillColor?: string;
        fillOpacity?: number;
        dashArray?: string;
        /** Optional SVG pattern fill: 'dots' | 'hatch' | 'wave' | 'cross'. */
        pattern?: 'dots' | 'hatch' | 'wave' | 'cross';
        /** Optional drop shadow for prominence. */
        shadow?: boolean;
        /** Animate the line dashes flowing in draw direction — rivers, marches, currents. */
        flow?: boolean;
        /** Soft outer glow — use for the chapter's hero features. */
        glow?: boolean;
        /** Marker size for point features (default 6). */
        markerRadius?: number;
      };
      /** Show this layer by default when the chapter opens. */
      defaultOn?: boolean;
      /** Optional: which property on each feature is the display name. */
      labelKey?: string;
    }
  | {
      id: string;
      name: string;
      description?: string;
      kind: 'raster';
      /** URL of the image overlay (in /public/maps/...). */
      url: string;
      /** SW + NE corners as [lat, lng]. */
      bounds: [[number, number], [number, number]];
      opacity?: number;
      defaultOn?: boolean;
    };

/** A fact tied to the chapter (right-panel content). */
export interface Fact {
  id: string;
  text: string;
  /** Optional: tie this fact to a layer or feature for highlight on hover. */
  linkedLayerId?: string;
  linkedFeatureId?: string;
}

/** A quiz item — one of several types. */
export type QuizItem =
  | {
      id: string;
      type: 'map_click';
      question: string;
      answer: { lat: number; lng: number; toleranceKm: number };
      explanation: string;
    }
  | {
      id: string;
      type: 'mcq';
      question: string;
      options: string[];
      answerIndex: number;
      explanation: string;
    };

/** A point on the chapter's timeline.
 *  Used for history chapters; optional otherwise. */
export interface TimelineEvent {
  id: string;
  /** ISO date or year string — sortable. e.g. "1756-06-20" or "1757". */
  date: string;
  /** Short label shown on the slider tick. */
  label: string;
  /** Full description shown when scrubbed to this event. */
  description: string;
  /** Optional: layers to switch ON when this event is the active one. */
  showLayers?: string[];
  /** Optional: layers to switch OFF when this event is the active one. */
  hideLayers?: string[];
  /** Optional: re-center the map. */
  view?: { center: [number, number]; zoom: number };
}

/** Optional per-chapter theme — chapter-aware color palette. */
export interface ChapterTheme {
  /** Accent color (active layer, buttons, highlights). */
  accent: string;
  /** Optional alternate map background tint. */
  mapBg?: string;
  /** Optional Leaflet tile URL — switch the basemap mood. */
  tileUrl?: string;
}

export interface Chapter {
  id: string;
  subject: SubjectId;
  title: string;
  /** One-line summary shown in the chapter list. */
  summary: string;
  /** The single concept this chapter exists to teach.
   *  Shown prominently when the chapter opens.
   *  Use this to keep authoring focused. */
  focus?: string;
  /** Initial map view when chapter opens. */
  view: { center: [number, number]; zoom: number };
  /** Basemap ID — see lib/basemaps.ts. Defaults to 'terrain'. */
  basemap?: string;
  /** True for world-scale chapters — unlocks world bounds & lower zoom. */
  worldExtent?: boolean;
  /** Sub-grouping inside a subject, e.g. 'Ancient', 'World', 'Mizoram'. */
  unit?: string;
  /** Concept tags — rivers, places, ranges. Shared tags connect chapters across subjects. */
  tags?: string[];
  layers: Layer[];
  facts: Fact[];
  quiz: QuizItem[];
  /** Optional timeline of events.
   *  When present, the chapter shows a scrubber and the map reflects the active event. */
  events?: TimelineEvent[];
  /** Optional per-chapter palette. */
  theme?: ChapterTheme;
}

export type Language = 'es' | 'en';
export type Theme = 'light' | 'dark';
export type Technique = 'tapestry' | 'intarsia' | 'c2c';
export type RouteName = 'home' | 'new' | 'projects' | 'drafts' | 'project' | 'more' | 'help' | 'about';

export interface Roi { x: number; y: number; w: number; h: number; }
export interface YarnColor { rgb: [number, number, number]; hex: string; }

export interface Draft {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  step: 1 | 2 | 3;
  patternImage: string | null;
  yarnImage: string | null;
  roi: Roi;
  colorCount: number;
  palette: YarnColor[];
  capacities: Array<number | null>;
  width: number;
  height: number;
  technique: Technique;
  hookIndex: number;
}

export interface GenerationResult {
  patternImage: string;
  labels: number[][];
  palette: YarnColor[];
  pixelCounts: number[];
  instructions: Record<Language, { rows: string; c2c: string }>;
  meters: Record<Technique, number[]>;
  dimensions: { rows: [number, number]; c2c: [number, number] };
  sourceHash: string;
}

export interface Project extends Draft {
  result: GenerationResult;
  completedStep: number;
  lastCompletedAt: string | null;
  notes: string;
}

export type ProjectStep = { text: string; label: string; colorIndexes: number[] };

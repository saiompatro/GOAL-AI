export interface Team {
  id: string;
  name: string;
  code: string | null;
  confederation: string | null;
}

export interface PlayerAttributes {
  pace: number;
  shooting: number;
  passing: number;
  defending: number;
}

export interface Player {
  id: string;
  teamId: string;
  teamName: string;
  name: string;
  position: string;
  overall: number;
  attrs: PlayerAttributes;
}

export interface ShapDriver {
  feature: string;
  value: number;
  shap: number;
}

export interface Prediction {
  id: string;
  home: string;
  away: string;
  pHome: number;
  pDraw: number;
  pAway: number;
  confidence: number;
  modelVersion: string;
  shap: ShapDriver[];
}

export interface Insight {
  entityType: "team" | "player" | "match";
  entityId: string;
  summaryText: string;
  model: string | null;
}

export interface MetricSnapshot {
  logLoss: number;
  brier: number;
  macroF1: number;
  accuracy: number;
}

export interface ModelMetric {
  val: MetricSnapshot;
  test: MetricSnapshot;
}

export type ModelKey = "lr" | "xgb" | "lgbm" | "nn" | "stack";

export interface FeatureImportance {
  feature: string;
  importance: number;
  note?: string;
}

export interface ModelRun {
  version: string;
  chosen: ModelKey;
  metrics: Record<ModelKey, ModelMetric>;
  confusion: number[][];
  featureImportance: FeatureImportance[];
}

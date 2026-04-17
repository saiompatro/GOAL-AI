import type {
  Insight,
  ModelRun,
  Player,
  Prediction,
  ShapDriver,
  Team,
} from "@/types/models";

const TEAM_SEED: Team[] = [
  { id: "1", name: "Brazil", code: "BRA", confederation: "CONMEBOL" },
  { id: "2", name: "Argentina", code: "ARG", confederation: "CONMEBOL" },
  { id: "3", name: "France", code: "FRA", confederation: "UEFA" },
  { id: "4", name: "Germany", code: "GER", confederation: "UEFA" },
  { id: "5", name: "Spain", code: "ESP", confederation: "UEFA" },
  { id: "6", name: "England", code: "ENG", confederation: "UEFA" },
  { id: "7", name: "Portugal", code: "POR", confederation: "UEFA" },
  { id: "8", name: "Netherlands", code: "NED", confederation: "UEFA" },
  { id: "9", name: "Morocco", code: "MAR", confederation: "CAF" },
  { id: "10", name: "Japan", code: "JPN", confederation: "AFC" },
];

function clampProbability(value: number): number {
  return Math.max(0.05, Math.min(0.82, value));
}

function seededHash(value: string): number {
  return [...value].reduce((acc, char) => (acc * 31 + char.charCodeAt(0)) >>> 0, 7);
}

export function synthesizePrediction(home: string, away: string, stage = "FIFA World Cup"): Prediction {
  const seed = Math.sin(seededHash(`${home}:${away}:${stage}`)) * 0.5;
  let pHome = clampProbability(0.45 + seed * 0.22);
  let pAway = clampProbability(0.35 - seed * 0.22);
  let pDraw = Math.max(0.08, 1 - pHome - pAway);
  const total = pHome + pAway + pDraw;

  pHome /= total;
  pAway /= total;
  pDraw /= total;

  const shap: ShapDriver[] = [
    { feature: "elo_diff", value: seed * 280, shap: seed * 0.32 },
    { feature: "top11_mean_diff", value: seed * 5.3, shap: seed * 0.21 },
    { feature: "home_win_rate_10", value: 0.55 + seed * 0.08, shap: 0.08 + seed * 0.05 },
    { feature: "h2h_home_wr", value: 0.5 + seed * 0.1, shap: seed * 0.06 },
    { feature: "neutral", value: 1, shap: -0.02 + seed * 0.02 },
  ];

  return {
    id: `${home}-${away}`.toLowerCase().replace(/\s+/g, "-"),
    home,
    away,
    pHome,
    pDraw,
    pAway,
    confidence: Math.max(pHome, pDraw, pAway),
    modelVersion: "demo",
    shap,
  };
}

export const demoTeams: Team[] = TEAM_SEED;

export const demoPredictions: Prediction[] = TEAM_SEED.flatMap((homeTeam, index) =>
  TEAM_SEED.slice(index + 1, index + 3).map((awayTeam) =>
    synthesizePrediction(homeTeam.name, awayTeam.name),
  ),
);

export const demoPlayers: Player[] = TEAM_SEED.flatMap((team) =>
  Array.from({ length: 11 }).map((_, index) => ({
    id: `${team.id}-p${index + 1}`,
    teamId: team.id,
    teamName: team.name,
    name: `${team.code ?? "TEAM"} Player ${index + 1}`,
    position: ["GK", "DF", "DF", "DF", "DF", "MF", "MF", "MF", "FW", "FW", "FW"][index] ?? "MF",
    overall: 75 + ((index * 3 + team.name.length) % 15),
    attrs: {
      pace: 70 + ((index * 5 + team.name.length) % 24),
      shooting: 68 + ((index * 4 + (team.code?.length ?? 0)) % 26),
      passing: 69 + ((index * 6 + team.name.length) % 23),
      defending: 61 + ((index * 7 + team.name.length) % 28),
    },
  })),
);

export const demoInsights: Insight[] = TEAM_SEED.map((team) => ({
  entityType: "team",
  entityId: team.id,
  summaryText: `${team.name} brings strong recent-form signals, credible squad quality, and enough attacking talent to stay dangerous across knockout-state game scripts.`,
  model: "demo",
}));

export const demoModelRun: ModelRun = {
  version: "v1",
  chosen: "stack",
  metrics: {
    lr: {
      val: { logLoss: 0.996, brier: 0.201, macroF1: 0.47, accuracy: 0.5 },
      test: { logLoss: 1.004, brier: 0.205, macroF1: 0.46, accuracy: 0.49 },
    },
    xgb: {
      val: { logLoss: 0.912, brier: 0.186, macroF1: 0.54, accuracy: 0.56 },
      test: { logLoss: 0.924, brier: 0.189, macroF1: 0.53, accuracy: 0.55 },
    },
    lgbm: {
      val: { logLoss: 0.918, brier: 0.187, macroF1: 0.53, accuracy: 0.55 },
      test: { logLoss: 0.928, brier: 0.19, macroF1: 0.53, accuracy: 0.55 },
    },
    nn: {
      val: { logLoss: 0.935, brier: 0.192, macroF1: 0.51, accuracy: 0.54 },
      test: { logLoss: 0.947, brier: 0.196, macroF1: 0.5, accuracy: 0.53 },
    },
    stack: {
      val: { logLoss: 0.901, brier: 0.183, macroF1: 0.55, accuracy: 0.57 },
      test: { logLoss: 0.908, brier: 0.185, macroF1: 0.55, accuracy: 0.57 },
    },
  },
  confusion: [
    [380, 120, 95],
    [160, 140, 155],
    [110, 130, 360],
  ],
  featureImportance: [
    { feature: "elo_diff", importance: 0.22 },
    { feature: "top11_mean_diff", importance: 0.14 },
    { feature: "star3_mean_diff", importance: 0.09 },
    { feature: "home_win_rate_10", importance: 0.08 },
    { feature: "away_win_rate_10", importance: 0.07 },
    { feature: "home_gd_10", importance: 0.06 },
    { feature: "is_wc", importance: 0.05, note: "tournament flag" },
    { feature: "h2h_home_wr", importance: 0.045 },
    { feature: "rest_home", importance: 0.04 },
    { feature: "neutral", importance: 0.035 },
  ],
};

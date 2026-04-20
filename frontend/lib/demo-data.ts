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

const DEMO_SQUADS: Record<
  string,
  Array<{ name: string; position: string; clubName: string; foot: string; base: number }>
> = {
  Brazil: [
    { name: "Alisson", position: "GK", clubName: "Liverpool", foot: "Right", base: 87 },
    { name: "Danilo", position: "DF", clubName: "Juventus", foot: "Right", base: 80 },
    { name: "Marquinhos", position: "DF", clubName: "Paris Saint-Germain", foot: "Right", base: 87 },
    { name: "Gabriel Magalhaes", position: "DF", clubName: "Arsenal", foot: "Left", base: 83 },
    { name: "Guilherme Arana", position: "DF", clubName: "Atletico Mineiro", foot: "Left", base: 79 },
    { name: "Bruno Guimaraes", position: "MF", clubName: "Newcastle United", foot: "Right", base: 85 },
    { name: "Joao Gomes", position: "MF", clubName: "Wolverhampton Wanderers", foot: "Right", base: 79 },
    { name: "Lucas Paqueta", position: "MF", clubName: "West Ham United", foot: "Left", base: 83 },
    { name: "Rodrygo", position: "FW", clubName: "Real Madrid", foot: "Right", base: 86 },
    { name: "Vinicius Junior", position: "FW", clubName: "Real Madrid", foot: "Right", base: 89 },
    { name: "Raphinha", position: "FW", clubName: "Barcelona", foot: "Left", base: 84 },
  ],
  Argentina: [
    { name: "Emiliano Martinez", position: "GK", clubName: "Aston Villa", foot: "Right", base: 86 },
    { name: "Nahuel Molina", position: "DF", clubName: "Atletico Madrid", foot: "Right", base: 82 },
    { name: "Cristian Romero", position: "DF", clubName: "Tottenham Hotspur", foot: "Right", base: 86 },
    { name: "Lisandro Martinez", position: "DF", clubName: "Manchester United", foot: "Left", base: 84 },
    { name: "Nicolas Tagliafico", position: "DF", clubName: "Lyon", foot: "Left", base: 80 },
    { name: "Enzo Fernandez", position: "MF", clubName: "Chelsea", foot: "Right", base: 85 },
    { name: "Alexis Mac Allister", position: "MF", clubName: "Liverpool", foot: "Right", base: 85 },
    { name: "Rodrigo De Paul", position: "MF", clubName: "Atletico Madrid", foot: "Right", base: 84 },
    { name: "Lionel Messi", position: "FW", clubName: "Inter Miami", foot: "Left", base: 90 },
    { name: "Julian Alvarez", position: "FW", clubName: "Manchester City", foot: "Right", base: 86 },
    { name: "Lautaro Martinez", position: "FW", clubName: "Inter", foot: "Right", base: 88 },
  ],
  France: [
    { name: "Mike Maignan", position: "GK", clubName: "AC Milan", foot: "Right", base: 87 },
    { name: "Jules Kounde", position: "DF", clubName: "Barcelona", foot: "Right", base: 85 },
    { name: "William Saliba", position: "DF", clubName: "Arsenal", foot: "Right", base: 86 },
    { name: "Dayot Upamecano", position: "DF", clubName: "Bayern Munich", foot: "Right", base: 84 },
    { name: "Theo Hernandez", position: "DF", clubName: "AC Milan", foot: "Left", base: 86 },
    { name: "Aurelien Tchouameni", position: "MF", clubName: "Real Madrid", foot: "Right", base: 86 },
    { name: "Eduardo Camavinga", position: "MF", clubName: "Real Madrid", foot: "Left", base: 85 },
    { name: "Antoine Griezmann", position: "FW", clubName: "Atletico Madrid", foot: "Left", base: 87 },
    { name: "Ousmane Dembele", position: "FW", clubName: "Paris Saint-Germain", foot: "Both", base: 86 },
    { name: "Kylian Mbappe", position: "FW", clubName: "Real Madrid", foot: "Right", base: 92 },
    { name: "Marcus Thuram", position: "FW", clubName: "Inter", foot: "Right", base: 84 },
  ],
  Germany: [
    { name: "Marc-Andre ter Stegen", position: "GK", clubName: "Barcelona", foot: "Right", base: 89 },
    { name: "Joshua Kimmich", position: "DF", clubName: "Bayern Munich", foot: "Right", base: 86 },
    { name: "Antonio Rudiger", position: "DF", clubName: "Real Madrid", foot: "Right", base: 86 },
    { name: "Jonathan Tah", position: "DF", clubName: "Bayer Leverkusen", foot: "Right", base: 83 },
    { name: "David Raum", position: "DF", clubName: "RB Leipzig", foot: "Left", base: 82 },
    { name: "Jamal Musiala", position: "MF", clubName: "Bayern Munich", foot: "Right", base: 88 },
    { name: "Ilkay Gundogan", position: "MF", clubName: "Barcelona", foot: "Right", base: 85 },
    { name: "Florian Wirtz", position: "MF", clubName: "Bayer Leverkusen", foot: "Right", base: 88 },
    { name: "Leroy Sane", position: "FW", clubName: "Bayern Munich", foot: "Left", base: 84 },
    { name: "Kai Havertz", position: "FW", clubName: "Arsenal", foot: "Left", base: 83 },
    { name: "Niclas Fullkrug", position: "FW", clubName: "Borussia Dortmund", foot: "Right", base: 81 },
  ],
  Spain: [
    { name: "Unai Simon", position: "GK", clubName: "Athletic Club", foot: "Right", base: 84 },
    { name: "Dani Carvajal", position: "DF", clubName: "Real Madrid", foot: "Right", base: 85 },
    { name: "Aymeric Laporte", position: "DF", clubName: "Al Nassr", foot: "Left", base: 84 },
    { name: "Robin Le Normand", position: "DF", clubName: "Atletico Madrid", foot: "Right", base: 83 },
    { name: "Alejandro Grimaldo", position: "DF", clubName: "Bayer Leverkusen", foot: "Left", base: 84 },
    { name: "Rodri", position: "MF", clubName: "Manchester City", foot: "Right", base: 91 },
    { name: "Pedri", position: "MF", clubName: "Barcelona", foot: "Right", base: 87 },
    { name: "Fabian Ruiz", position: "MF", clubName: "Paris Saint-Germain", foot: "Left", base: 83 },
    { name: "Lamine Yamal", position: "FW", clubName: "Barcelona", foot: "Left", base: 84 },
    { name: "Nico Williams", position: "FW", clubName: "Athletic Club", foot: "Right", base: 84 },
    { name: "Alvaro Morata", position: "FW", clubName: "AC Milan", foot: "Right", base: 82 },
  ],
  England: [
    { name: "Jordan Pickford", position: "GK", clubName: "Everton", foot: "Left", base: 83 },
    { name: "Kyle Walker", position: "DF", clubName: "Manchester City", foot: "Right", base: 83 },
    { name: "John Stones", position: "DF", clubName: "Manchester City", foot: "Right", base: 85 },
    { name: "Marc Guehi", position: "DF", clubName: "Crystal Palace", foot: "Right", base: 81 },
    { name: "Luke Shaw", position: "DF", clubName: "Manchester United", foot: "Left", base: 82 },
    { name: "Declan Rice", position: "MF", clubName: "Arsenal", foot: "Right", base: 87 },
    { name: "Jude Bellingham", position: "MF", clubName: "Real Madrid", foot: "Right", base: 90 },
    { name: "Phil Foden", position: "FW", clubName: "Manchester City", foot: "Left", base: 88 },
    { name: "Bukayo Saka", position: "FW", clubName: "Arsenal", foot: "Left", base: 88 },
    { name: "Harry Kane", position: "FW", clubName: "Bayern Munich", foot: "Right", base: 90 },
    { name: "Cole Palmer", position: "FW", clubName: "Chelsea", foot: "Left", base: 86 },
  ],
  Portugal: [
    { name: "Diogo Costa", position: "GK", clubName: "Porto", foot: "Right", base: 85 },
    { name: "Joao Cancelo", position: "DF", clubName: "Al Hilal", foot: "Right", base: 84 },
    { name: "Ruben Dias", position: "DF", clubName: "Manchester City", foot: "Right", base: 88 },
    { name: "Goncalo Inacio", position: "DF", clubName: "Sporting CP", foot: "Left", base: 82 },
    { name: "Nuno Mendes", position: "DF", clubName: "Paris Saint-Germain", foot: "Left", base: 84 },
    { name: "Bruno Fernandes", position: "MF", clubName: "Manchester United", foot: "Right", base: 88 },
    { name: "Vitinha", position: "MF", clubName: "Paris Saint-Germain", foot: "Right", base: 85 },
    { name: "Bernardo Silva", position: "MF", clubName: "Manchester City", foot: "Left", base: 88 },
    { name: "Rafael Leao", position: "FW", clubName: "AC Milan", foot: "Right", base: 86 },
    { name: "Cristiano Ronaldo", position: "FW", clubName: "Al Nassr", foot: "Right", base: 86 },
    { name: "Joao Felix", position: "FW", clubName: "Chelsea", foot: "Right", base: 82 },
  ],
  Netherlands: [
    { name: "Bart Verbruggen", position: "GK", clubName: "Brighton", foot: "Right", base: 80 },
    { name: "Denzel Dumfries", position: "DF", clubName: "Inter", foot: "Right", base: 83 },
    { name: "Virgil van Dijk", position: "DF", clubName: "Liverpool", foot: "Right", base: 89 },
    { name: "Matthijs de Ligt", position: "DF", clubName: "Manchester United", foot: "Right", base: 84 },
    { name: "Nathan Ake", position: "DF", clubName: "Manchester City", foot: "Left", base: 84 },
    { name: "Frenkie de Jong", position: "MF", clubName: "Barcelona", foot: "Right", base: 87 },
    { name: "Tijjani Reijnders", position: "MF", clubName: "AC Milan", foot: "Right", base: 83 },
    { name: "Xavi Simons", position: "MF", clubName: "RB Leipzig", foot: "Right", base: 84 },
    { name: "Cody Gakpo", position: "FW", clubName: "Liverpool", foot: "Right", base: 84 },
    { name: "Memphis Depay", position: "FW", clubName: "Corinthians", foot: "Right", base: 82 },
    { name: "Donyell Malen", position: "FW", clubName: "Borussia Dortmund", foot: "Right", base: 82 },
  ],
  Morocco: [
    { name: "Yassine Bounou", position: "GK", clubName: "Al Hilal", foot: "Left", base: 84 },
    { name: "Achraf Hakimi", position: "DF", clubName: "Paris Saint-Germain", foot: "Right", base: 86 },
    { name: "Nayef Aguerd", position: "DF", clubName: "West Ham United", foot: "Left", base: 81 },
    { name: "Romain Saiss", position: "DF", clubName: "Al Sadd", foot: "Left", base: 79 },
    { name: "Noussair Mazraoui", position: "DF", clubName: "Manchester United", foot: "Right", base: 82 },
    { name: "Sofyan Amrabat", position: "MF", clubName: "Fenerbahce", foot: "Right", base: 82 },
    { name: "Azzedine Ounahi", position: "MF", clubName: "Marseille", foot: "Right", base: 79 },
    { name: "Bilal El Khannouss", position: "MF", clubName: "Genk", foot: "Right", base: 77 },
    { name: "Hakim Ziyech", position: "FW", clubName: "Al Duhail", foot: "Left", base: 81 },
    { name: "Youssef En-Nesyri", position: "FW", clubName: "Fenerbahce", foot: "Left", base: 82 },
    { name: "Brahim Diaz", position: "FW", clubName: "Real Madrid", foot: "Left", base: 83 },
  ],
  Japan: [
    { name: "Zion Suzuki", position: "GK", clubName: "Parma", foot: "Right", base: 77 },
    { name: "Takehiro Tomiyasu", position: "DF", clubName: "Arsenal", foot: "Right", base: 82 },
    { name: "Ko Itakura", position: "DF", clubName: "Borussia Monchengladbach", foot: "Right", base: 79 },
    { name: "Shogo Taniguchi", position: "DF", clubName: "Sint-Truiden", foot: "Right", base: 76 },
    { name: "Hiroki Ito", position: "DF", clubName: "Bayern Munich", foot: "Left", base: 79 },
    { name: "Wataru Endo", position: "MF", clubName: "Liverpool", foot: "Right", base: 81 },
    { name: "Hidemasa Morita", position: "MF", clubName: "Sporting CP", foot: "Right", base: 79 },
    { name: "Daichi Kamada", position: "MF", clubName: "Crystal Palace", foot: "Right", base: 80 },
    { name: "Kaoru Mitoma", position: "FW", clubName: "Brighton", foot: "Right", base: 83 },
    { name: "Takefusa Kubo", position: "FW", clubName: "Real Sociedad", foot: "Left", base: 84 },
    { name: "Ayase Ueda", position: "FW", clubName: "Feyenoord", foot: "Right", base: 78 },
  ],
};

function demoPlayerProfile(
  team: Team,
  index: number,
  base: { name: string; position: string; clubName: string; foot: string; base: number },
): Player {
  const attributeBump = team.name.length % 5;
  const age = 23 + ((index + team.id.length) % 9);
  return {
    id: `${team.id}-p${index + 1}`,
    teamId: team.id,
    teamName: team.name,
    name: base.name,
    position: base.position,
    overall: base.base,
    clubName: base.clubName,
    age,
    potential: Math.min(94, base.base + 3),
    preferredFoot: base.foot,
    valueEur: (base.base - 68) * 3_500_000,
    wageEur: (base.base - 60) * 4_000,
    attrs: {
      pace: Math.min(95, base.base + (base.position === "FW" ? 5 : 1)),
      shooting: Math.min(94, base.base + (base.position === "FW" ? 4 : -2)),
      passing: Math.min(93, base.base + (base.position === "MF" ? 4 : 0)),
      defending: Math.max(38, base.base + (base.position === "DF" ? 5 : -8)),
      dribbling: Math.min(94, base.base + (base.position === "FW" || base.position === "MF" ? 4 : -1)),
      physic: Math.min(92, base.base + (base.position === "DF" ? 3 : 1)),
      heightCm: 176 + ((index * 2 + attributeBump) % 17),
      weightKg: 70 + ((index * 3 + attributeBump) % 14),
      internationalReputation: Math.min(5, Math.max(1, Math.round((base.base - 74) / 4))),
    },
    insightSummary: `${base.name} anchors ${team.name}'s lineup from ${base.clubName}, with a ${base.foot.toLowerCase()}-foot profile and a strong overall rating of ${base.base}.`,
  };
}

export const demoPlayers: Player[] = TEAM_SEED.flatMap((team) => {
  const squad = DEMO_SQUADS[team.name];
  if (!squad) {
    return [];
  }
  return squad.map((player, index) => demoPlayerProfile(team, index, player));
});

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

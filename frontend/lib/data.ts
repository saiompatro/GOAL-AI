import "server-only";

import { cache } from "react";

import {
  demoInsights,
  demoModelRun,
  demoPlayers,
  demoPredictions,
  demoTeams,
} from "@/lib/demo-data";
import { getSupabaseClient } from "@/lib/supabase";
import type {
  Insight,
  MetricSnapshot,
  ModelKey,
  ModelMetric,
  ModelRun,
  Player,
  PlayerAttributes,
  Prediction,
  ShapDriver,
  Team,
} from "@/types/models";

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function readNullableString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function readNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return fallback;
}

function normalizeTeam(row: unknown): Team | null {
  if (!isRecord(row)) {
    return null;
  }

  const id = readString(row.id);
  const name = readString(row.name);

  if (!id || !name) {
    return null;
  }

  return {
    id,
    name,
    code: readNullableString(row.code),
    confederation: readNullableString(row.confederation),
  };
}

function normalizeShap(value: unknown): ShapDriver[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => {
      if (!isRecord(item)) {
        return null;
      }

      return {
        feature: readString(item.feature, "unknown_feature"),
        value: readNumber(item.value),
        shap: readNumber(item.shap),
      } satisfies ShapDriver;
    })
    .filter((item): item is ShapDriver => item !== null);
}

function normalizePlayerAttributes(value: unknown): PlayerAttributes {
  if (!isRecord(value)) {
    return { pace: 0, shooting: 0, passing: 0, defending: 0 };
  }

  return {
    pace: readNumber(value.pace),
    shooting: readNumber(value.shooting),
    passing: readNumber(value.passing),
    defending: readNumber(value.defending),
  };
}

function normalizeMetricSnapshot(value: unknown): MetricSnapshot {
  if (!isRecord(value)) {
    return { logLoss: 0, brier: 0, macroF1: 0, accuracy: 0 };
  }

  return {
    logLoss: readNumber(value.log_loss ?? value.logLoss),
    brier: readNumber(value.brier),
    macroF1: readNumber(value.macro_f1 ?? value.macroF1),
    accuracy: readNumber(value.accuracy),
  };
}

function normalizeModelMetric(value: unknown): ModelMetric {
  if (!isRecord(value)) {
    return {
      val: { logLoss: 0, brier: 0, macroF1: 0, accuracy: 0 },
      test: { logLoss: 0, brier: 0, macroF1: 0, accuracy: 0 },
    };
  }

  return {
    val: normalizeMetricSnapshot(value.val),
    test: normalizeMetricSnapshot(value.test),
  };
}

function normalizeModelKey(value: unknown): ModelKey {
  const key = readString(value) as ModelKey;
  return key === "lr" || key === "xgb" || key === "lgbm" || key === "nn" || key === "stack"
    ? key
    : demoModelRun.chosen;
}

function normalizeMetrics(value: unknown): Record<ModelKey, ModelMetric> {
  if (!isRecord(value)) {
    return demoModelRun.metrics;
  }

  return {
    lr: normalizeModelMetric(value.lr),
    xgb: normalizeModelMetric(value.xgb),
    lgbm: normalizeModelMetric(value.lgbm),
    nn: normalizeModelMetric(value.nn),
    stack: normalizeModelMetric(value.stack),
  };
}

export const listTeams = cache(async (): Promise<Team[]> => {
  const supabase = getSupabaseClient();
  if (!supabase) {
    return demoTeams;
  }

  const result = await supabase.from("teams").select("id, name, code, confederation").order("name");
  const data = Array.isArray(result.data) ? result.data.map(normalizeTeam).filter((team): team is Team => team !== null) : [];

  return data.length ? data : demoTeams;
});

export const listPredictions = cache(async (): Promise<Prediction[]> => {
  const supabase = getSupabaseClient();
  if (!supabase) {
    return demoPredictions;
  }

  const predictionResult = await supabase
    .from("predictions")
    .select("id, match_id, p_home, p_draw, p_away, confidence, model_version, shap")
    .order("created_at", { ascending: false })
    .limit(40);

  if (!Array.isArray(predictionResult.data) || !predictionResult.data.length) {
    return demoPredictions;
  }

  const rows = predictionResult.data.filter(isRecord);
  const matchIds = rows.map((row) => readString(row.match_id)).filter(Boolean);

  const matchResult = await supabase.from("matches").select("id, home_id, away_id").in("id", matchIds);
  const matchRows = Array.isArray(matchResult.data) ? matchResult.data.filter(isRecord) : [];

  const teamIds = matchRows
    .flatMap((row) => [readString(row.home_id), readString(row.away_id)])
    .filter(Boolean);
  const uniqueTeamIds = [...new Set(teamIds)];
  const teamResult = await supabase.from("teams").select("id, name").in("id", uniqueTeamIds);
  const teamRows = Array.isArray(teamResult.data) ? teamResult.data.filter(isRecord) : [];

  const teamById = new Map<string, string>(
    teamRows
      .map((row) => [readString(row.id), readString(row.name)] as const)
      .filter(([id, name]) => id && name),
  );

  const matchesById = new Map<string, { homeId: string; awayId: string }>(
    matchRows
      .map((row) => [
        readString(row.id),
        { homeId: readString(row.home_id), awayId: readString(row.away_id) },
      ] as const)
      .filter(([id, match]) => id && match.homeId && match.awayId),
  );

  const predictions = rows
    .map((row) => {
      const matchId = readString(row.match_id);
      const match = matchesById.get(matchId);
      const home = match ? teamById.get(match.homeId) : null;
      const away = match ? teamById.get(match.awayId) : null;

      if (!match || !home || !away) {
        return null;
      }

      return {
        id: readString(row.id, `${home}-${away}`),
        home,
        away,
        pHome: readNumber(row.p_home),
        pDraw: readNumber(row.p_draw),
        pAway: readNumber(row.p_away),
        confidence: readNumber(row.confidence),
        modelVersion: readString(row.model_version, "v1"),
        shap: normalizeShap(row.shap),
      } satisfies Prediction;
    })
    .filter((prediction): prediction is Prediction => prediction !== null);

  return predictions.length ? predictions : demoPredictions;
});

export const listPlayers = cache(async (): Promise<Player[]> => {
  const supabase = getSupabaseClient();
  if (!supabase) {
    return demoPlayers;
  }

  const playerResult = await supabase
    .from("players")
    .select("id, team_id, name, position, overall, attrs")
    .order("overall", { ascending: false })
    .limit(300);

  if (!Array.isArray(playerResult.data) || !playerResult.data.length) {
    return demoPlayers;
  }

  const teams = await listTeams();
  const teamById = new Map(teams.map((team) => [team.id, team.name]));

  const players = playerResult.data
    .filter(isRecord)
    .map((row) => {
      const teamId = readString(row.team_id);
      const teamName = teamById.get(teamId);
      const id = readString(row.id);
      const name = readString(row.name);

      if (!id || !name || !teamId || !teamName) {
        return null;
      }

      return {
        id,
        teamId,
        teamName,
        name,
        position: readString(row.position, "MF"),
        overall: readNumber(row.overall),
        attrs: normalizePlayerAttributes(row.attrs),
      } satisfies Player;
    })
    .filter((player): player is Player => player !== null);

  return players.length ? players : demoPlayers;
});

export const listInsights = cache(async (entityType: Insight["entityType"]): Promise<Insight[]> => {
  const supabase = getSupabaseClient();
  if (!supabase) {
    return demoInsights.filter((insight) => insight.entityType === entityType);
  }

  const result = await supabase
    .from("insights")
    .select("entity_type, entity_id, summary_text, model")
    .eq("entity_type", entityType);

  if (!Array.isArray(result.data) || !result.data.length) {
    return demoInsights.filter((insight) => insight.entityType === entityType);
  }

  const insights = result.data
    .filter(isRecord)
    .map((row) => {
      const entityId = readString(row.entity_id);
      const summaryText = readString(row.summary_text);

      if (!entityId || !summaryText) {
        return null;
      }

      return {
        entityType,
        entityId,
        summaryText,
        model: readNullableString(row.model),
      } satisfies Insight;
    })
    .filter((insight): insight is Insight => insight !== null);

  return insights.length ? insights : demoInsights.filter((insight) => insight.entityType === entityType);
});

export const latestModelRun = cache(async (): Promise<ModelRun> => {
  const supabase = getSupabaseClient();
  if (!supabase) {
    return demoModelRun;
  }

  const result = await supabase
    .from("model_runs")
    .select("version, algo, metrics")
    .order("created_at", { ascending: false })
    .limit(1);

  const row = Array.isArray(result.data) ? result.data.find(isRecord) : null;
  if (!row) {
    return demoModelRun;
  }

  return {
    version: readString(row.version, demoModelRun.version),
    chosen: normalizeModelKey(row.algo),
    metrics: normalizeMetrics(row.metrics),
    confusion: demoModelRun.confusion,
    featureImportance: demoModelRun.featureImportance,
  };
});

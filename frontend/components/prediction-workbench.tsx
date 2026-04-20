"use client";

import { useMemo, useState } from "react";

import { synthesizePrediction } from "@/lib/demo-data";
import type { Prediction, Team } from "@/types/models";
import { ProbabilityBar } from "@/components/probability-bar";
import { ShapDrivers } from "@/components/shap-drivers";

interface PredictionWorkbenchProps {
  teams: Team[];
  predictions: Prediction[];
}

const defaultHome = "Brazil";
const defaultAway = "Argentina";

function pickPrediction(
  predictions: Prediction[],
  home: string,
  away: string,
  stage: string,
): Prediction {
  const hit = predictions.find(
    (prediction) =>
      (prediction.home === home && prediction.away === away) ||
      (prediction.home === away && prediction.away === home),
  );

  if (!hit) {
    return synthesizePrediction(home, away, stage);
  }

  if (hit.home === home) {
    return hit;
  }

  return {
    ...hit,
    home,
    away,
    pHome: hit.pAway,
    pAway: hit.pHome,
  };
}

export function PredictionWorkbench({ teams, predictions }: PredictionWorkbenchProps) {
  const homeFallback = teams.find((team) => team.name === defaultHome)?.name ?? teams[0]?.name ?? "";
  const awayFallback =
    teams.find((team) => team.name === defaultAway)?.name ??
    teams.find((team) => team.name !== homeFallback)?.name ??
    teams[0]?.name ??
    "";

  const [home, setHome] = useState(homeFallback);
  const [away, setAway] = useState(awayFallback);
  const [stage, setStage] = useState("FIFA World Cup");
  const [submitted, setSubmitted] = useState({
    home: homeFallback,
    away: awayFallback,
    stage: "FIFA World Cup",
  });

  const prediction = useMemo(
    () => pickPrediction(predictions, submitted.home, submitted.away, submitted.stage),
    [predictions, submitted],
  );

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Interactive Forecast</p>
            <h1>Match prediction</h1>
          </div>
          <p className="section-copy">
            The frontend prefers live cached Supabase predictions and falls back to a deterministic local scoring
            preview when a requested fixture is not already available.
          </p>
        </div>

        <div className="control-grid">
          <label className="field">
            <span>Home team</span>
            <select value={home} onChange={(event) => setHome(event.target.value)}>
              {teams.map((team) => (
                <option key={team.id} value={team.name}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Away team</span>
            <select value={away} onChange={(event) => setAway(event.target.value)}>
              {teams.map((team) => (
                <option key={team.id} value={team.name}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span>Stage</span>
            <select value={stage} onChange={(event) => setStage(event.target.value)}>
              <option>FIFA World Cup</option>
              <option>FIFA World Cup qualification</option>
              <option>Friendly</option>
              <option>UEFA Euro</option>
            </select>
          </label>

          <button
            className="primary-button"
            type="button"
            onClick={() => setSubmitted({ home, away, stage })}
            disabled={!home || !away || home === away}
          >
            Predict
          </button>
        </div>
      </section>

      <div className="two-column-grid">
        <section className="panel">
          <p className="eyebrow">Scored Fixture</p>
          <h2 className="matchup-title">
            {prediction.home} vs {prediction.away}
          </h2>
          <div className="triplet">
            <span>Home {(prediction.pHome * 100).toFixed(1)}%</span>
            <span>Draw {(prediction.pDraw * 100).toFixed(1)}%</span>
            <span>Away {(prediction.pAway * 100).toFixed(1)}%</span>
          </div>
          <ProbabilityBar pHome={prediction.pHome} pDraw={prediction.pDraw} pAway={prediction.pAway} />
          <div className="detail-list">
            <div className="detail-row">
              <span>Confidence</span>
              <strong>{(prediction.confidence * 100).toFixed(1)}%</strong>
            </div>
            <div className="detail-row">
              <span>Model version</span>
              <strong>{prediction.modelVersion}</strong>
            </div>
            <div className="detail-row">
              <span>Stage context</span>
              <strong>{submitted.stage}</strong>
            </div>
          </div>
        </section>

        <section className="panel">
          <p className="eyebrow">Explainability</p>
          <h2>Why this prediction?</h2>
          <p className="section-copy">
            Positive SHAP values push the forecast toward the home side. Negative values weaken the home-win case.
          </p>
          <ShapDrivers drivers={prediction.shap} />
        </section>
      </div>
    </div>
  );
}

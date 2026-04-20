"use client";

import { useEffect, useRef } from "react";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

interface ModelChartsProps {
  confusion: number[][];
  featureImportance: Array<{ feature: string; importance: number }>;
}

export function ModelCharts({ confusion, featureImportance }: ModelChartsProps) {
  const confusionRef = useRef<HTMLCanvasElement | null>(null);
  const importanceRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!confusionRef.current || !importanceRef.current) {
      return;
    }

    const confusionChart = new Chart(confusionRef.current, {
      type: "bar",
      data: {
        labels: ["Home", "Draw", "Away"],
        datasets: ["Home", "Draw", "Away"].map((label, index) => ({
          label: `Actual ${label}`,
          data: confusion[index] ?? [0, 0, 0],
          backgroundColor: ["rgba(34, 211, 238, 0.6)", "rgba(139, 151, 173, 0.6)", "rgba(167, 139, 250, 0.6)"][index],
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom",
            labels: { color: "#e6ecf5" },
          },
        },
        scales: {
          x: {
            ticks: { color: "#e6ecf5" },
            title: { display: true, text: "Predicted", color: "#8b97ad" },
          },
          y: {
            ticks: { color: "#e6ecf5" },
          },
        },
      },
    });

    const importanceChart = new Chart(importanceRef.current, {
      type: "bar",
      data: {
        labels: featureImportance.map((entry) => entry.feature),
        datasets: [
          {
            label: "mean(|SHAP|)",
            data: featureImportance.map((entry) => entry.importance),
            backgroundColor: "#22d3ee",
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: { ticks: { color: "#e6ecf5" } },
          y: { ticks: { color: "#e6ecf5" } },
        },
      },
    });

    return () => {
      confusionChart.destroy();
      importanceChart.destroy();
    };
  }, [confusion, featureImportance]);

  return (
    <div className="two-column-grid">
      <section className="panel chart-panel">
        <p className="eyebrow">Classification Health</p>
        <h2>Confusion matrix (test)</h2>
        <div className="chart-shell">
          <canvas ref={confusionRef} />
        </div>
      </section>

      <section className="panel chart-panel">
        <p className="eyebrow">Global Drivers</p>
        <h2>Feature importance</h2>
        <div className="chart-shell">
          <canvas ref={importanceRef} />
        </div>
      </section>
    </div>
  );
}

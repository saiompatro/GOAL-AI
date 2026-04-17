import { ProbabilityBar } from "@/components/probability-bar";
import { latestModelRun, listPredictions } from "@/lib/data";

export default async function DashboardPage() {
  const [predictions, modelRun] = await Promise.all([listPredictions(), latestModelRun()]);
  const chosenMetrics = modelRun.metrics[modelRun.chosen];
  const averageConfidence =
    predictions.reduce((total, prediction) => total + prediction.confidence, 0) / Math.max(predictions.length, 1);

  return (
    <div className="page-stack">
      <section className="hero-card">
        <p className="eyebrow">Portfolio Surface</p>
        <h1>GOAL AI</h1>
        <p className="hero-copy">
          FIFA World Cup match prediction, team scouting notes, player analysis, and interpretable model diagnostics in
          one portfolio-quality frontend.
        </p>
      </section>

      <section className="card-grid card-grid--three">
        <article className="panel">
          <p className="eyebrow">Chosen model</p>
          <h2>{modelRun.chosen.toUpperCase()}</h2>
          <div className="detail-list">
            <div className="detail-row">
              <span>Test log-loss</span>
              <strong>{chosenMetrics.test.logLoss.toFixed(3)}</strong>
            </div>
            <div className="detail-row">
              <span>Brier</span>
              <strong>{chosenMetrics.test.brier.toFixed(3)}</strong>
            </div>
            <div className="detail-row">
              <span>Accuracy</span>
              <strong>{(chosenMetrics.test.accuracy * 100).toFixed(1)}%</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <p className="eyebrow">Predicted fixtures</p>
          <h2>{predictions.length}</h2>
          <div className="detail-list">
            <div className="detail-row">
              <span>Model version</span>
              <strong>{modelRun.version}</strong>
            </div>
            <div className="detail-row">
              <span>Outputs</span>
              <strong>Home / Draw / Away</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <p className="eyebrow">Average confidence</p>
          <h2>{(averageConfidence * 100).toFixed(1)}%</h2>
          <div className="detail-list">
            <div className="detail-row">
              <span>Explainability</span>
              <strong>SHAP top drivers</strong>
            </div>
            <div className="detail-row">
              <span>Data source</span>
              <strong>Supabase or demo cache</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Preview Grid</p>
            <h2>Upcoming / predicted fixtures</h2>
          </div>
          <p className="section-copy">The migrated dashboard keeps the original fixture table while upgrading it to typed rendering and App Router navigation.</p>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Home</th>
                <th></th>
                <th>Away</th>
                <th>Probability mix</th>
                <th className="align-right">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {predictions.slice(0, 20).map((prediction) => (
                <tr key={prediction.id}>
                  <td>{prediction.home}</td>
                  <td className="table-muted">vs</td>
                  <td>{prediction.away}</td>
                  <td>
                    <div className="table-bar">
                      <ProbabilityBar
                        pHome={prediction.pHome}
                        pDraw={prediction.pDraw}
                        pAway={prediction.pAway}
                      />
                    </div>
                  </td>
                  <td className="align-right">{(prediction.confidence * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

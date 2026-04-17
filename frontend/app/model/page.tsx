import { ModelCharts } from "@/components/model-charts";
import { latestModelRun } from "@/lib/data";

export default async function ModelPage() {
  const modelRun = await latestModelRun();

  return (
    <div className="page-stack">
      <section className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Validation View</p>
            <h1>Model comparison</h1>
          </div>
          <p className="section-copy">
            The App Router migration keeps the original comparison surface intact: time-split model evaluation,
            confusion diagnostics, and SHAP-based global feature importance.
          </p>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Val log-loss</th>
                <th>Val Brier</th>
                <th>Val macro-F1</th>
                <th>Test log-loss</th>
                <th>Test Brier</th>
                <th>Test acc</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(modelRun.metrics).map(([key, metric]) => (
                <tr className={key === modelRun.chosen ? "table-row--highlight" : undefined} key={key}>
                  <td>
                    <strong>{key}</strong>
                  </td>
                  <td>{metric.val.logLoss.toFixed(3)}</td>
                  <td>{metric.val.brier.toFixed(3)}</td>
                  <td>{metric.val.macroF1.toFixed(3)}</td>
                  <td>{metric.test.logLoss.toFixed(3)}</td>
                  <td>{metric.test.brier.toFixed(3)}</td>
                  <td>{(metric.test.accuracy * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <ModelCharts confusion={modelRun.confusion} featureImportance={modelRun.featureImportance} />
    </div>
  );
}

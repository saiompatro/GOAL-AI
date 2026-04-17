import type { ShapDriver } from "@/types/models";

interface ShapDriversProps {
  drivers: ShapDriver[];
}

export function ShapDrivers({ drivers }: ShapDriversProps) {
  if (!drivers.length) {
    return <div className="empty-state">No SHAP drivers available yet.</div>;
  }

  const maxAbs = Math.max(...drivers.map((driver) => Math.abs(driver.shap)), 1);

  return (
    <div className="shap-list">
      {drivers.map((driver) => {
        const width = (Math.abs(driver.shap) / maxAbs) * 50;
        const positive = driver.shap >= 0;

        return (
          <div className="shap-row" key={`${driver.feature}-${driver.value}`}>
            <div className="shap-row__feature">{driver.feature}</div>
            <div className="shap-row__track">
              <span
                className={positive ? "shap-row__bar shap-row__bar--positive" : "shap-row__bar shap-row__bar--negative"}
                style={positive ? { left: "50%", width: `${width}%` } : { right: "50%", width: `${width}%` }}
              />
            </div>
            <div className="shap-row__value">{driver.shap >= 0 ? "+" : ""}{driver.shap.toFixed(3)}</div>
          </div>
        );
      })}
    </div>
  );
}

interface ProbabilityBarProps {
  pHome: number;
  pDraw: number;
  pAway: number;
}

export function ProbabilityBar({ pHome, pDraw, pAway }: ProbabilityBarProps) {
  return (
    <div className="probability-bar" aria-label="Prediction probabilities">
      <span
        className="probability-bar__segment probability-bar__segment--home"
        style={{ width: `${(pHome * 100).toFixed(1)}%` }}
        title={`Home ${(pHome * 100).toFixed(1)}%`}
      />
      <span
        className="probability-bar__segment probability-bar__segment--draw"
        style={{ width: `${(pDraw * 100).toFixed(1)}%` }}
        title={`Draw ${(pDraw * 100).toFixed(1)}%`}
      />
      <span
        className="probability-bar__segment probability-bar__segment--away"
        style={{ width: `${(pAway * 100).toFixed(1)}%` }}
        title={`Away ${(pAway * 100).toFixed(1)}%`}
      />
    </div>
  );
}

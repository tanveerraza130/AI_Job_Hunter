function ScoreMetric({
  label,
  value,
}: {
  label: string;
  value: number | null | undefined;
}) {
  return (
    <div className="mj-breakdown-item">
      <span>{label}</span>
      <strong>
        {value == null
          ? "—"
          : `${Number(value).toFixed(0)}%`}
      </strong>
    </div>
  );
}

interface JobCardScoreProps {
  score: number | null;
  skillScore: number | null | undefined;
  toolScore: number | null | undefined;
  jdMatch: number | null | undefined;
  titleMatch: number | null | undefined;
  penalty: number | null | undefined;
  scoreClassName: string;
}

export default function JobCardScore({
  score,
  skillScore,
  toolScore,
  jdMatch,
  titleMatch,
  penalty,
  scoreClassName,
}: JobCardScoreProps) {
  return (
    <div className="mj-score-panel">
      <div className={scoreClassName}>
        <strong>
          {score != null
            ? Math.round(score)
            : "—"}
        </strong>

        {score != null && (
          <span>%</span>
        )}
      </div>

      <span className="mj-score-label">
        AI MATCH
      </span>

      <div className="mj-breakdown">
        <div className="mj-breakdown-title">
          SCORE BREAKDOWN
        </div>

        <div className="mj-breakdown-grid">
          <ScoreMetric
            label="Skills"
            value={skillScore}
          />

          <ScoreMetric
            label="Tools"
            value={toolScore}
          />

          <ScoreMetric
            label="JD Match"
            value={jdMatch ?? 0}
          />

          <ScoreMetric
            label="Title Match"
            value={titleMatch ?? 0}
          />

          <ScoreMetric
            label="Penalty"
            value={penalty ?? 0}
          />
        </div>
      </div>
    </div>
  );
}

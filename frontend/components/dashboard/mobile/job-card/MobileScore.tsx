"use client";

import styles from "./MobileScore.module.css";

function clampScore(score: number | null): number {
  if (score == null || Number.isNaN(score)) {
    return 0;
  }

  return Math.max(0, Math.min(100, score));
}

interface Props {
  score: number | null;
}

export default function MobileScore({
  score,
}: Props) {
  const numericScore = clampScore(score);

  return (
    <div className={styles.scoreWrap}>
      <div
        className={styles.scoreRing}
        style={{
          background: `conic-gradient(
            #12a86d ${numericScore * 3.6}deg,
            #e4f5ee ${numericScore * 3.6}deg
          )`,
        }}
      >
        <div className={styles.scoreRingInner}>
          <strong>
            {score == null
              ? "—"
              : Math.round(numericScore)}
          </strong>

          {score != null && (
            <span>%</span>
          )}
        </div>
      </div>

      <span className={styles.scoreLabel}>
        Match
      </span>
    </div>
  );
}

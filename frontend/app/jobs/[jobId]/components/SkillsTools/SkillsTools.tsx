"use client";

import type { JobDetail, ScoreBreakdown } from "@/types/job";
import styles from "./SkillsTools.module.css";

type Props = {
  job: JobDetail;
  breakdown: ScoreBreakdown | null;
};

function clean(values: string[] | undefined) {
  return [...new Set((values ?? []).filter(Boolean))];
}

function Chips({
  items,
  empty,
}: {
  items: string[];
  empty: string;
}) {
  if (!items.length) {
    return <span className={styles.empty}>{empty}</span>;
  }

  return (
    <div className={styles.chips}>
      {items.slice(0, 12).map((item) => (
        <span key={item}>{item}</span>
      ))}
      {items.length > 12 && (
        <span className={styles.more}>
          +{items.length - 12} more
        </span>
      )}
    </div>
  );
}

export default function SkillsTools({
  job,
  breakdown,
}: Props) {
  const skills = clean(
    breakdown?.matched_skills?.length
      ? breakdown.matched_skills
      : job.skills,
  );

  const tools = clean(breakdown?.matched_tools);

  const missingSkills = clean(
    breakdown?.missing_skills,
  );

  const missingTools = clean(
    breakdown?.missing_tools,
  );

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>
            QUICK MATCH
          </span>
          <h2>Skills &amp; Tools</h2>
          <p>
            See the experience and platforms that match this
            opportunity.
          </p>
        </div>
      </div>

      <div className={styles.grid}>
        <div className={`${styles.card} ${styles.skills}`}>
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.icon}>✓</span>
              <strong>Matched Skills</strong>
            </div>
            <b>{skills.length}</b>
          </div>

          <Chips
            items={skills}
            empty="No matched skills available"
          />
        </div>

        <div className={`${styles.card} ${styles.tools}`}>
          <div className={styles.cardHeader}>
            <div>
              <span className={styles.icon}>◆</span>
              <strong>Matched Tools</strong>
            </div>
            <b>{tools.length}</b>
          </div>

          <Chips
            items={tools}
            empty="No matched tools available"
          />
        </div>

        {(missingSkills.length > 0 ||
          missingTools.length > 0) && (
          <div className={`${styles.gaps} ${styles.gapSkills}`}>
            <div className={styles.cardHeader}>
              <div>
                <span className={styles.gapIcon}>!</span>
                <strong>Skills to Review</strong>
              </div>
              <b>{missingSkills.length}</b>
            </div>

            <Chips
              items={missingSkills}
              empty="No major skill gaps identified"
            />
          </div>
        )}

        {(missingSkills.length > 0 ||
          missingTools.length > 0) && (
          <div className={`${styles.gaps} ${styles.gapTools}`}>
            <div className={styles.cardHeader}>
              <div>
                <span className={styles.gapIcon}>!</span>
                <strong>Tools to Review</strong>
              </div>
              <b>{missingTools.length}</b>
            </div>

            <Chips
              items={missingTools}
              empty="No major tool gaps identified"
            />
          </div>
        )}
      </div>
    </section>
  );
}

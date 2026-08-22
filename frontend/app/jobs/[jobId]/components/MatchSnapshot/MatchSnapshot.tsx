"use client";

import type { ReactNode } from "react";
import type { JobDetail, ScoreBreakdown } from "@/types/job";
import {
  Sparkles,
  Wrench,
  Clock3,
  TrendingUp,
  FileText,
} from "lucide-react";
import styles from "./MatchSnapshot.module.css";

type Props = {
  job: JobDetail;
  score: JobDetail["score"] | null | undefined;
  breakdown: ScoreBreakdown | null;
};

function items(
  primary: string[] | undefined,
  fallback: string[] | undefined = [],
) {
  return (primary?.length ? primary : fallback).slice(0, 8);
}

export default function MatchSnapshot({
  job,
  score,
  breakdown,
}: Props) {
  const skills = items(
    breakdown?.matched_skills,
    job.skills,
  );

  const tools = items(
    breakdown?.matched_tools,
  );

  const missingSkills = items(
    breakdown?.missing_skills,
  );

  const missingTools = items(
    breakdown?.missing_tools,
  );

  return (
    <section className={styles.snapshot}>

      <div className={styles.mobileOverallScore}>
        <div className={styles.mobileOverallScoreRing}>
          <div>
            <strong>
              {score?.overall_score != null
                ? Math.round(score.overall_score)
                : "—"}
            </strong>
            <span>%</span>
          </div>
        </div>

        <div className={styles.mobileOverallScoreText}>
          <span>OVERALL MATCH SCORE</span>

          <strong>
            {score?.overall_score != null
              ? `${Math.round(score.overall_score)}%`
              : "—"}
          </strong>

          <small>
            ✓{" "}
            {score?.overall_score != null &&
            score.overall_score >= 80
              ? "Excellent Match"
              : score?.overall_score != null &&
                score.overall_score >= 60
                ? "Strong Match"
                : "Needs Review"}
          </small>
        </div>
      </div>

      <div className={styles.heading}>
        <div>
          <div className={styles.eyebrowRow}>
            <span className={styles.sparkle}>✣</span>
            <span className={styles.eyebrow}>
              MATCH SNAPSHOT
            </span>
          </div>

          <h2>How this job matches you</h2>
        </div>
      </div>

      <div className={styles.metrics}>
        <Metric
          label="Skills"
          value={score?.skill_score}
          icon={<Sparkles />}
          tone="skills"
        />

        <Metric
          label="Tools"
          value={score?.tool_score}
          icon={<Wrench />}
          tone="tools"
        />

        <Metric
          label="Experience"
          value={score?.experience_score}
          icon={<Clock3 />}
          tone="experience"
        />

        <Metric
          label="Title Match"
          value={breakdown?.title_match}
          icon={<TrendingUp />}
          tone="title"
        />

        <Metric
          label="JD Match"
          value={breakdown?.jd_match}
          icon={<FileText />}
          tone="jd"
        />

        <div className={styles.mobileOnlyMetric}>
          <Metric
            label="Salary"
            value={100}
            icon={<FileText />}
            tone="jd"
          />
        </div>

        <div className={styles.mobileOnlyMetric}>
          <Metric
            label="Work Mode"
            value={100}
            icon={<FileText />}
            tone="jd"
          />
        </div>
      </div>

      <div className={styles.mobileSkillsTools}>
        <div className={styles.mobileSkillsHeader}>
          <span>✣</span>
          <strong>SKILLS & TOOLS</strong>
          <span className={styles.mobileSkillsChevron}>⌃</span>
        </div>

        <MatchGroup
          title="MATCHED SKILLS"
          items={skills}
          tone="green"
        />

        <MatchGroup
          title="MATCHED TOOLS"
          items={tools}
          tone="green"
        />

        <MatchGroup
          title="MISSING SKILLS"
          items={missingSkills}
          tone="red"
          empty="No major skill gaps identified"
        />

        <MatchGroup
          title="MISSING TOOLS"
          items={missingTools}
          tone="red"
          empty="No major tool gaps identified"
        />
      </div>

      <div className={styles.matchPanel}>
        <MatchGroup
          title="TOP MATCHED SKILLS"
          items={skills}
          tone="green"
        />

        <MatchGroup
          title="TOP MATCHED TOOLS"
          items={tools}
          tone="green"
        />

        <MatchGroup
          title="MISSING SKILLS"
          items={missingSkills}
          tone="red"
          empty="No major skill gaps identified"
        />

        <MatchGroup
          title="MISSING TOOLS"
          items={missingTools}
          tone="red"
          empty="No major tool gaps identified"
        />
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value?: number | null;
  icon: ReactNode;
  tone: "skills" | "tools" | "experience" | "title" | "jd";
}) {
  const metricScore =
    value == null
      ? null
      : Math.max(0, Math.min(100, Number(value)));

  return (
    <div className={`${styles.metric} ${styles[`metric-${tone}`]}`}>
      <div className={styles.metricTop}>
        <span className={styles.metricIcon}>
          {icon}
        </span>

        <span className={styles.metricLabel}>
          {label}
        </span>
      </div>

      <strong>
        {metricScore == null
          ? "—"
          : `${Math.round(metricScore)}%`}
      </strong>

      {metricScore != null && (
        <small>
          {metricScore >= 70
            ? "Strong match"
            : metricScore >= 50
              ? "Good match"
              : "Needs review"}
        </small>
      )}
    </div>
  );
}

function MatchGroup({
  title,
  items,
  tone,
  empty,
}: {
  title: string;
  items: string[];
  tone: "green" | "red";
  empty?: string;
}) {
  return (
    <div className={`${styles.group} ${styles[tone]}`}>
      <div className={styles.groupTitle}>
        <span className={styles.groupIcon}>
          {tone === "green" ? "✓" : "×"}
        </span>

        <strong>{title}</strong>
      </div>

      {items.length ? (
        <div className={styles.chips}>
          {items.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      ) : (
        <p>{empty || "None identified"}</p>
      )}
    </div>
  );
}

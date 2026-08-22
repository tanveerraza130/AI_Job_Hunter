"use client";

import {
  BriefcaseBusiness,
  Building2,
  Check,
  TrendingUp,
} from "lucide-react";

import type { DashboardSummary } from "@/types/job";

import styles from "./MobileStats.module.css";

interface Props {
  summary: DashboardSummary | null;
}

function StatCard({
  icon,
  label,
  value,
  accent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  accent?: "purple" | "green";
}) {
  return (
    <div className={styles.statCard}>
      <div
        className={`${styles.statIcon} ${
          accent === "green"
            ? styles.statIconGreen
            : styles.statIconPurple
        }`}
      >
        {icon}
      </div>

      <span className={styles.statLabel}>
        {label}
      </span>

      <strong
        className={
          accent === "green"
            ? styles.statValueGreen
            : styles.statValue
        }
      >
        {value}
      </strong>
    </div>
  );
}

export default function MobileStats({
  summary,
}: Props) {
  return (
    <section className={styles.statsCard}>
      <StatCard
        icon={<BriefcaseBusiness size={16} />}
        label="Matching jobs"
        value={
          summary?.total_jobs?.toLocaleString(
            "en-IN",
          ) || "0"
        }
      />

      <StatCard
        icon={<TrendingUp size={16} />}
        label="Avg match"
        value={
          summary?.average_score != null
            ? `${summary.average_score.toFixed(1)}%`
            : "—"
        }
      />

      <StatCard
        icon={<Check size={16} />}
        label="High match"
        value={
          summary?.high_match_jobs?.toLocaleString(
            "en-IN",
          ) || "0"
        }
        accent="green"
      />

      <StatCard
        icon={<Building2 size={16} />}
        label="Companies"
        value={
          summary?.companies_count?.toLocaleString(
            "en-IN",
          ) || "—"
        }
      />
    </section>
  );
}

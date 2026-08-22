import type { DashboardSummary } from "@/types/job";
import StatCard from "./StatCard";
import styles from "./DashboardStats.module.css";

interface DashboardStatsProps {
  summary: DashboardSummary | null;
}

export default function DashboardStats({
  summary,
}: DashboardStatsProps) {
  return (
    <section className={styles.stats} aria-label="Dashboard summary">
      <StatCard
        label="Matching Jobs"
        value={summary?.total_jobs?.toLocaleString("en-IN") ?? "0"}
        hint="Based on current filters"
      />

      <StatCard
        label="Average Match"
        value={`${summary?.average_score?.toFixed(1) ?? "0.0"}%`}
        hint="Average of current results"
      />

      <StatCard
        label="High Match"
        value={summary?.high_match_jobs?.toLocaleString("en-IN") ?? "0"}
        hint="Current results at ≥70%"
        emphasis
      />

      <StatCard
        label="Companies"
        value={summary?.companies_count?.toLocaleString("en-IN") ?? "0"}
        hint={`${summary?.locations_count?.toLocaleString("en-IN") ?? "0"} locations`}
      />
    </section>
  );
}

import styles from "./DashboardHero.module.css";

interface DashboardHeroProps {
  totalJobs: number;
}

export default function DashboardHero({
  totalJobs,
}: DashboardHeroProps) {
  return (
    <section className={styles.hero} aria-labelledby="dashboard-hero-title">
      <div className={styles.copy}>
        <div className={styles.eyebrow}>
          YOUR OPPORTUNITIES
        </div>

        <h1 id="dashboard-hero-title">
          Find your next role.
        </h1>

        <p>
          AI-ranked jobs based on your profile, skills and experience.
        </p>
      </div>

      <div className={styles.resultCount} aria-label={`${totalJobs.toLocaleString("en-IN")} matching jobs`}>
        <strong>{totalJobs.toLocaleString("en-IN")}</strong>
        <span>matching jobs</span>
      </div>
    </section>
  );
}

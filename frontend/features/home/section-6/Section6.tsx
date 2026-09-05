"use client";

import styles from "./Section6.module.css";


const handleBuildProfile = (
  event: React.MouseEvent<HTMLAnchorElement>,
) => {
  event.preventDefault();

  const token = localStorage.getItem("ai_job_hunter_token");

  window.location.href = token ? "/dashboard" : "/signup";
};

export default function Section6() {
  return (
    <section className={styles.section} id="get-started">
      <div className={styles.ambient} aria-hidden="true">
        <span className={styles.orbOne} />
        <span className={styles.orbTwo} />
        <span className={styles.gridGlow} />
      </div>

      <div className={styles.inner}>
        <div className={styles.eyebrow}>
          <span className={styles.dot} />
          The smarter way to job hunt
        </div>

        <h2>
          Your next great opportunity
          <span> is closer than you think.</span>
        </h2>

        <p>
          Stop jumping between job sites and repeating the same search.
          Build your profile once, let AI understand what you’re looking for,
          and discover opportunities matched to your skills, experience and goals.
        </p>

        <div className={styles.actions}>
          <a href="/signup" className={styles.primary} onClick={handleBuildProfile}>
            <span className={styles.primaryText}>Build Your Profile for Free</span>
            <span className={styles.arrow}>→</span>
          </a>
        </div>

        <div className={styles.trust}>
          <span>One profile</span>
          <i />
          <span>Smarter matches</span>
          <i />
          <span>Less searching</span>
        </div>
      </div>
    </section>
  );
}

"use client";

import styles from "./RocketCTA.module.css";


const handleStartJobSearch = (
  event: React.MouseEvent<HTMLAnchorElement>,
) => {
  event.preventDefault();

  const token = localStorage.getItem("ai_job_hunter_token");

  window.location.href = token ? "/dashboard" : "/signup";
};

export default function RocketCTA() {
  return (
    <section className={styles.section} aria-label="Start your job search">
      <div className={styles.container}>
        <div className={styles.rocket} aria-hidden="true">
          <img
            src="/rocket2.png"
            alt=""
            width="34"
            height="34"
            aria-hidden="true"
          />
        </div>

        <div className={styles.copy}>
          <p className={styles.eyebrow}>READY WHEN YOU ARE</p>
          <h2>Your next opportunity is closer than you think.</h2>
          <p>Let AI handle the search. You focus on the move.</p>
        </div>

        <a className={styles.cta} href="/signup" onClick={handleStartJobSearch}>
          Start Your Free Job Search
          <span>→</span>
        </a>
      </div>
    </section>
  );
}

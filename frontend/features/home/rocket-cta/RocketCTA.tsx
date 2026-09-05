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
          <svg
            width="34"
            height="34"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M21 3 3.8 10.2c-.8.35-.75 1.5.08 1.75l6.15 1.9 1.9 6.15c.25.83 1.4.88 1.75.08L21 3Z" />
            <path d="m10.1 13.85 5.15-5.15" />
            <path d="m10.1 13.85-.05 5.25" />
          </svg>
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

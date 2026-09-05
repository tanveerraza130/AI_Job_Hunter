"use client";

import styles from "./GlobalHeader.module.css";

const handleJoinFree = (
  event: React.MouseEvent<HTMLAnchorElement>,
) => {
  event.preventDefault();

  const token = localStorage.getItem("ai_job_hunter_token");

  window.location.href = token ? "/dashboard" : "/signup";
};

export default function GlobalHeader() {
  return (
    <header className={styles.header}>
      <div className={styles.inner}>

        <a className={styles.brand} href="#" aria-label="AI Job Hunter home">
          <span className={styles.mark}>✦</span>

          <span className={styles.brandCopy}>
            <strong>AI Job Hunter</strong>
            <small>Find what fits.</small>
          </span>
        </a>

        <nav className={styles.nav} aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#what-you-get">What you get</a>
          <a href="#apply-track">Apply &amp; track</a>
          <a href="#employers">For employers</a>
        </nav>

        <div className={styles.actions}>
          <a className={styles.signin} href="/login">
            Log In
          </a>

          <a className={styles.cta} href="/signup" onClick={handleJoinFree}>
            Join Free <span>→</span>
          </a>
        </div>

      </div>
    </header>
  );
}

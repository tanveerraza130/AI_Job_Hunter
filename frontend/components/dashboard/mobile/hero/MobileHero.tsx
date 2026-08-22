"use client";

import styles from "./MobileHero.module.css";

export default function MobileHero() {
  return (
    <section className={styles.hero}>
      <span className={styles.eyebrow}>
        YOUR OPPORTUNITIES
      </span>

      <h1>
        Find your next role.
      </h1>

      <p>
        AI-ranked jobs based on
        your profile, skills and
        experience.
      </p>
    </section>
  );
}

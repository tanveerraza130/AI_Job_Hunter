import styles from "./RocketCTA.module.css";

export default function RocketCTA() {
  return (
    <section className={styles.section} aria-label="Start your job search">
      <div className={styles.container}>
        <div className={styles.rocket} aria-hidden="true">↗</div>

        <div className={styles.copy}>
          <p className={styles.eyebrow}>READY WHEN YOU ARE</p>
          <h2>Your next opportunity is closer than you think.</h2>
          <p>Let AI handle the search. You focus on the move.</p>
        </div>

        <a className={styles.cta} href="#get-started">
          Start your search
          <span>→</span>
        </a>
      </div>
    </section>
  );
}

import styles from "./Section4.module.css";

export default function Section4() {
  return (
    <section className={styles.section} id="job-sources">
      <div className={styles.container}>
        <div className={styles.heading}>
          <p className={styles.eyebrow}>ONE SEARCH, MANY SOURCES</p>
          <h2>Multiple sources.<br />One place.</h2>
          <p>
            Stop jumping between job boards. AI Job Hunter brings relevant
            opportunities together in one focused view.
          </p>
        </div>

        <div className={styles.sourcePanel}>
          <div className={styles.sourceHeader}>
            <span>JOB SOURCES</span>
            <span>CONNECTED</span>
          </div>

          <div className={styles.sources}>
            <div className={styles.source}><b>in</b><span>LinkedIn</span><i>✓</i></div>
            <div className={styles.source}><b>N</b><span>Naukri</span><i>✓</i></div>
            <div className={styles.source}><b>J</b><span>Job boards</span><i>✓</i></div>
            <div className={styles.source}><b>+</b><span>More sources</span><i>✓</i></div>
          </div>

          <div className={styles.unified}>
            <span className={styles.pulse} />
            <div>
              <strong>One unified job feed</strong>
              <small>Relevant opportunities, together.</small>
            </div>
            <span className={styles.arrow}>→</span>
          </div>
        </div>
      </div>
    </section>
  );
}

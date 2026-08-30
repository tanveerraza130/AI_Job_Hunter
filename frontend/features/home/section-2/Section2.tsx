import styles from "./Section2.module.css";

export default function Section2() {
  return (
    <section
      id="how-it-works"
      className={styles.section}
      aria-labelledby="section-2-title"
    >
      <div className={styles.container}>

        {/* =====================================================
            LEFT — THE PROBLEM
            ===================================================== */}
        <div className={styles.problem}>

          <p className={styles.eyebrow}>
            The problem
          </p>

          <h2 id="section-2-title">
            Job search is frustrating
            <br />
            and time-consuming.
          </h2>

          <p className={styles.problemDescription}>
            Too many tabs. Too many searches.
            Too little of what actually fits.
          </p>

          <div className={styles.problemBody}>

            <div>
              <ul className={styles.problemList}>
                <li>
                  <span className={styles.problemIcon}>×</span>
                  Search multiple sites
                </li>

                <li>
                  <span className={styles.problemIcon}>×</span>
                  Try different keywords
                </li>

                <li>
                  <span className={styles.problemIcon}>×</span>
                  Check each job
                </li>

                <li>
                  <span className={styles.problemIcon}>×</span>
                  Filter manually
                </li>

                <li>
                  <span className={styles.problemIcon}>×</span>
                  Still miss the right ones
                </li>
              </ul>

              <div className={styles.problemTime}>
                1–2+ hours
              </div>
            </div>

            <div className={styles.personWrap}>
              <img
                src="/Job-seeker character.png"
                alt="Frustrated job seeker"
                className={styles.person}
              />
            </div>

          </div>
        </div>

        {/* =====================================================
            CENTER — VS
            ===================================================== */}
        <div className={styles.middle} aria-hidden="true">
          <div className={styles.vs}>
            VS
          </div>
        </div>

        {/* =====================================================
            RIGHT — THE SMARTER WAY
            ===================================================== */}
        <div className={styles.solution}>

          <p className={styles.eyebrow}>
            The smarter way
          </p>

          <h2>
            AI Job Hunter does the
            <br />
            hard work for you.
          </h2>

          <p className={styles.solutionDescription}>
            Tell us what matters. Let AI focus
            on opportunities that fit.
          </p>

          <div className={styles.solutionBody}>

            <div>
              <ul className={styles.solutionList}>
                <li>
                  <span className={styles.solutionIcon}>✓</span>
                  Open AI Job Hunter
                </li>

                <li>
                  <span className={styles.solutionIcon}>✓</span>
                  See AI-ranked matches
                </li>

                <li>
                  <span className={styles.solutionIcon}>✓</span>
                  Review &amp; apply
                </li>

                <li>
                  <span className={styles.solutionIcon}>✓</span>
                  Track progress
                </li>

                <li>
                  <span className={styles.solutionIcon}>✓</span>
                  Get the right opportunities
                </li>
              </ul>

              <div className={styles.solutionTime}>
                10–20 minutes
              </div>
            </div>

            <div className={styles.personWrap}>
              <img
                src="/AI Job Hunter person.png"
                alt="Happy job seeker using AI Job Hunter"
                className={styles.person}
              />
            </div>

          </div>
        </div>

      </div>
    </section>
  );
}

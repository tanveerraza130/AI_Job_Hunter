import styles from "./Section2.module.css";

export default function Section2() {
  return (
    <section className={styles.section}>
      <div className={styles.canvas}>

        {/* LEFT â€” LOCKED */}
      {/* LEFT PROBLEM TEXT — NEW BLOCK ONLY */}
      <div className={styles.leftProblemText}>
        <div className={styles.leftProblemBadge}>
          <span>!</span>
          THE PROBLEM
        </div>

        <h2>
          Your next job<br />
          shouldn’t require<br />
          <span>20 searches a day.</span>
        </h2>

        <strong>
          Different sites. Different titles. Different searches.
        </strong>

        <p>
          Same career goal — but you keep searching,<br />
          comparing and reopening the same kinds of<br />
          jobs again and again.
        </p>
      </div>

        <div className={styles.leftBlock}>
          <img
            src="/Job-seeker character.png"
            alt=""
            className={styles.sideImage}
          />
        </div>

        {/* CENTER â€” EVERYTHING MUST STAY INSIDE THIS CARD */}        {/* AI JOB HUNTER CENTER DESIGN START */}

        <div className={styles.centerBlock}>
                  <div className={styles.centerContent}>

          {/* =====================================================
              APPROVED AI JOB HUNTER CENTER DESIGN
              Everything remains inside centerBlock.
             ===================================================== */}

          <div className={styles.aiCenterVisual}>

            {/* CONNECTOR NETWORK */}
            <svg
              className={styles.aiCenterNetwork}
              viewBox="0 0 1000 600"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path
                className={styles.aiPink}
                d="M0 120 C190 120 305 150 430 300"
              />
              <path
                className={styles.aiPink}
                d="M0 220 C190 220 320 240 430 300"
              />
              <path
                className={styles.aiPink}
                d="M0 300 C190 300 320 300 430 300"
              />
              <path
                className={styles.aiPink}
                d="M0 380 C190 380 320 360 430 300"
              />
              <path
                className={styles.aiPink}
                d="M0 480 C190 480 305 445 430 300"
              />

              <path
                className={styles.aiGreen}
                d="M570 300 C695 150 810 120 1000 120"
              />
              <path
                className={styles.aiGreen}
                d="M570 300 C680 240 810 220 1000 220"
              />
              <path
                className={styles.aiGreen}
                d="M570 300 C680 300 810 300 1000 300"
              />
              <path
                className={styles.aiGreen}
                d="M570 300 C680 360 810 380 1000 380"
              />
              <path
                className={styles.aiGreen}
                d="M570 300 C695 445 810 480 1000 480"
              />
            </svg>

            {/* LEFT FLOATING NODES */}
            <div className={`${styles.aiNode} ${styles.aiPinkNode} ${styles.aiP1}`}>
              ⌕
            </div>

            <div className={`${styles.aiNode} ${styles.aiPinkNode} ${styles.aiP2}`}>
              ♙
            </div>

            <div className={`${styles.aiNode} ${styles.aiPinkNode} ${styles.aiP3}`}>
              ×
            </div>

            <div className={`${styles.aiNode} ${styles.aiPinkNode} ${styles.aiP4}`}>
              ⚙
            </div>

            <div className={`${styles.aiNode} ${styles.aiPinkNode} ${styles.aiP5}`}>
              ◉
            </div>

            {/* RIGHT FLOATING NODES */}
            <div className={`${styles.aiNode} ${styles.aiGreenNode} ${styles.aiG1}`}>
              ☷
            </div>

            <div className={`${styles.aiNode} ${styles.aiGreenNode} ${styles.aiG2}`}>
              ✓
            </div>

            <div className={`${styles.aiNode} ${styles.aiGreenNode} ${styles.aiG3}`}>
              ☷
            </div>

            <div className={`${styles.aiNode} ${styles.aiGreenNode} ${styles.aiG4}`}>
              ✓
            </div>

            <div className={`${styles.aiNode} ${styles.aiGreenNode} ${styles.aiG5}`}>
              ✓
            </div>

            {/* CENTRAL AI HUB */}
            <div className={styles.aiCenterHub}>

              <span className={`${styles.aiRing} ${styles.aiRing1}`} />
              <span className={`${styles.aiRing} ${styles.aiRing2}`} />
              <span className={`${styles.aiRing} ${styles.aiRing3}`} />

              <div className={styles.aiCore}>
                <span className={styles.aiSpark}>✦</span>
              </div>

            </div>

          </div>

          {/* CENTER COPY */}
          <div className={styles.aiCenterCopy}>

            <h2>AI Job Hunter</h2>

            <h3>Understands your profile</h3>

            <p>Searches. Matches. Ranks.</p>

          </div>

          {/* WHAT WE DO */}
          <div className={styles.aiWhatWeDo}>

            <h3>Here’s what we do</h3>

            <div className={styles.aiFeature}>

              <div className={styles.aiFeatureIcon}>
                ♙
              </div>

              <div>
                <strong>Understand your profile</strong>
                <span>
                  Skills, roles, experience, preferences
                </span>
              </div>

            </div>

            <div className={styles.aiFeature}>

              <div className={styles.aiFeatureIcon}>
                ⌕
              </div>

              <div>
                <strong>Search across multiple sources</strong>
                <span>
                  Naukri, LinkedIn, IIMJobs, and more
                </span>
              </div>

            </div>

            <div className={styles.aiFeature}>

              <div className={styles.aiFeatureIcon}>
                ▽
              </div>

              <div>
                <strong>Remove noise &amp; duplicates</strong>
                <span>
                  Clean, unique opportunities
                </span>
              </div>

            </div>

            <div className={styles.aiFeature}>

              <div className={styles.aiFeatureIcon}>
                ✦
              </div>

              <div>
                <strong>Rank by relevance</strong>
                <span>
                  AI matches that actually fit you
                </span>
              </div>

            </div>

          </div>

        </div>
        </div>

        {/* AI JOB HUNTER CENTER DESIGN END */}
{/* RIGHT â€” LOCKED */}
        <div className={styles.rightBlock}>
          <img
            src="/AI Job Hunter person.png"
            alt=""
            className={styles.sideImage}
          />
        </div>

      </div>
    </section>
  );
}

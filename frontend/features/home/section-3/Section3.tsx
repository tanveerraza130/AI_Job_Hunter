import styles from "./Section3.module.css";

const profileItems = [
  { label: "Skills", value: "CRM • Lifecycle Marketing • Retention" },
  { label: "Tools", value: "CleverTap • MoEngage • WebEngage" },
  { label: "Experience", value: "3–5+ years" },
  { label: "Location", value: "Gurgaon • Bangalore • Remote" },
  { label: "Career Preferences", value: "Growth • Leadership • Flexible Work" },
];

const matches = [
  {
    score: "94%",
    level: "Best Match",
    title: "CRM & MarTech Manager",
    company: "Google",
    location: "Bengaluru",
    freshness: "Last 1 hr",
    tone: "best",
  },
  {
    score: "91%",
    level: "Strong Match",
    title: "Retention Manager",
    company: "Swiggy",
    location: "Delhi NCR",
    freshness: "6 hrs ago",
    tone: "strong",
  },
  {
    score: "89%",
    level: "Strong Match",
    title: "Lifecycle Marketing Manager",
    company: "Amazon",
    location: "Gurgaon",
    freshness: "12 hrs ago",
    tone: "strong",
  },
  {
    score: "87%",
    level: "Good Match",
    title: "Growth & CRM Manager",
    company: "Microsoft",
    location: "Hyderabad",
    freshness: "1 day ago",
    tone: "good",
  },
];

const reasons = [
  "Context over keywords",
  "Fit over volume",
  "One result, once",
  "Freshness checked",
  "Clear match signals",
];

export default function Section3() {
  return (
    <section className={styles.section} id="profile-matching">
      <div className={styles.background} aria-hidden="true">
        <span className={styles.glowOne} />
        <span className={styles.glowTwo} />
        <span className={styles.grid} />
        <span className={`${styles.orbit} ${styles.orbitOne}`} />
        <span className={`${styles.orbit} ${styles.orbitTwo}`} />
      </div>

      <div className={styles.container}>
        <header className={styles.header}>
          <div className={styles.eyebrow}>
            <span className={styles.eyebrowDot} />
            THE BIG USP
          </div>

          <h2>
            One profile.
            <span> Every relevant opportunity.</span>
          </h2>

          <p>
            We understand your profile, match opportunities using AI,
            and show you what actually matters.
          </p>
        </header>

        <div className={styles.stage}>

          {/* PROFILE */}
          <div className={`${styles.panel} ${styles.profilePanel}`}>
            <div className={styles.panelTop}>
              <div>
                <span className={styles.panelKicker}>YOUR PROFILE</span>
                <h3>Your Profile</h3>
              </div>

              <span className={styles.active}>
                <i />
                Active
              </span>
            </div>

            <div className={styles.role}>
              <div className={styles.avatar}>T</div>

              <div>
                <strong>CRM Manager</strong>
                <span>Career profile</span>
              </div>
            </div>

            <div className={styles.profileList}>
              {profileItems.map((item) => (
                <div className={styles.profileItem} key={item.label}>
                  <span className={styles.profileIcon}>✦</span>

                  <span className={styles.profileCopy}>
                    <strong>{item.label}</strong>
                    <small>{item.value}</small>
                  </span>

                  <span className={styles.check}>✓</span>
                </div>
              ))}
            </div>

            <div className={styles.profileFooter}>
              <span>Profile strength</span>
              <strong>92%</strong>

              <div className={styles.progress}>
                <i />
              </div>
            </div>
          </div>

          {/* CONNECTOR LEFT */}
          <div className={`${styles.connector} ${styles.connectorLeft}`}>
            <span className={styles.connectorLine} />
            <i className={styles.particleOne} />
            <i className={styles.particleTwo} />
            <i className={styles.particleThree} />
          </div>

          {/* AI */}
          <div className={styles.aiArea}>
            <div className={styles.aiHalo}>
              <div className={`${styles.aiRing} ${styles.ringOne}`} />
              <div className={`${styles.aiRing} ${styles.ringTwo}`} />
              <div className={`${styles.aiRing} ${styles.ringThree}`} />

              <div className={styles.aiCore}>
                <span className={styles.aiSpark}>✦</span>
              </div>
            </div>

            <div className={styles.aiBadge}>
              <span />
              AI MATCHING
            </div>

            <h3>Understands your fit</h3>

            <p>
              Skills, experience, preferences
              <br />
              and career goals.
            </p>

            <div className={styles.aiSignals}>
              <span>Skills</span>
              <span>Experience</span>
              <span>Preferences</span>
            </div>
          </div>

          {/* CONNECTOR RIGHT */}
          <div className={`${styles.connector} ${styles.connectorRight}`}>
            <span className={styles.connectorLine} />
            <i className={styles.particleOne} />
            <i className={styles.particleTwo} />
            <i className={styles.particleThree} />
          </div>

          {/* MATCHES */}
          <div className={`${styles.panel} ${styles.matchesPanel}`}>
            <div className={styles.panelTop}>
              <div>
                <span className={styles.panelKicker}>AI-RANKED</span>
                <h3>Your best matches</h3>
              </div>

              <span className={styles.live}>
                <i />
                Live
              </span>
            </div>

            <div className={styles.matchList}>
              {matches.map((match, index) => (
                <div
                  className={`${styles.matchCard} ${styles[match.tone]}`}
                  key={match.title}
                >
                  <div className={styles.matchScore}>
                    <strong>{match.score}</strong>
                    <span>{match.level}</span>
                  </div>

                  <div className={styles.matchInfo}>
                    <strong>{match.title}</strong>

                    <span>
                      {match.company} · {match.location}
                    </span>

                    <small>{match.freshness}</small>
                  </div>

                  <div className={styles.matchRank}>
                    0{index + 1}
                  </div>
                </div>
              ))}
            </div>

            <div className={styles.moreMatches}>
              <span>More relevant opportunities</span>
              <b>→</b>
            </div>
          </div>

          {/* WHY IT WORKS */}
          <aside className={`${styles.whyCard} ${styles.whyCardFinal}`}>
            <div className={styles.whyHeader}>
              <span className={styles.whyIcon}>✦</span>

              <div>
                <span>WHY IT WORKS</span>
                <h3>Built around relevance.</h3>
              </div>
            </div>

            <div className={styles.reasons}>
              {reasons.map((reason, index) => (
                <div className={styles.reason} key={reason}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{reason}</strong>
                  <i>✓</i>
                </div>
              ))}
            </div>

            {/* CLOSING STATEMENT — INSIDE WHY IT WORKS CARD */}
            <div className={styles.bottomStatement}>
              <span />
              <p>
                You tell us what matters.
                <strong> AI finds what fits.</strong>
              </p>
              <span />
            </div>

          </aside>
        </div>
      </div>
    </section>
  );
}

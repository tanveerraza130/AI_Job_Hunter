import styles from "./Section5.module.css";

const stages = [
  ["Saved", "12"],
  ["Applied", "08"],
  ["Interview", "03"],
  ["Offer", "01"],
];

export default function Section5() {
  return (
    <section className={styles.section} id="application-tracking">
      <div className={styles.container}>
        <div className={styles.visual}>
          <div className={styles.window}>
            <div className={styles.windowTop}>
              <span>APPLICATIONS</span>
              <span>THIS MONTH</span>
            </div>

            <div className={styles.pipeline}>
              {stages.map(([label,count]) => (
                <div className={styles.stage} key={label}>
                  <span>{label}</span>
                  <strong>{count}</strong>
                </div>
              ))}
            </div>

            <div className={styles.progress}><span /></div>

            <div className={styles.status}>
              <i />
              <span>3 applications need attention</span>
              <b>View</b>
            </div>
          </div>
        </div>

        <div className={styles.copy}>
          <p className={styles.eyebrow}>STAY ON TOP OF EVERY MOVE</p>
          <h2>Track every step.<br />Never lose momentum.</h2>
          <p>
            Keep applications, interviews and opportunities organized in one
            simple view — so nothing gets forgotten.
          </p>

          <div className={styles.points}>
            <span>Applications</span>
            <span>Interviews</span>
            <span>Progress</span>
          </div>
        </div>
      </div>
    </section>
  );
}

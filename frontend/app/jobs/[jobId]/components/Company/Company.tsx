import type { JobDetail } from "@/types/job";
import styles from "./Company.module.css";

type Props = {
  job: JobDetail;
};

export default function Company({ job }: Props) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <span className={styles.eyebrow}>THE EMPLOYER</span>
        <h2>About {job.company || "the Company"}</h2>
      </div>

      <div className={styles.card}>
        <div className={styles.companyMark}>
          {(job.company || "C").trim().charAt(0).toUpperCase()}
        </div>

        <div>
          <h3>{job.company || "Company not disclosed"}</h3>
          <p>
            Company information beyond the employer name is not available
            in the current job data.
          </p>
        </div>
      </div>
    </section>
  );
}

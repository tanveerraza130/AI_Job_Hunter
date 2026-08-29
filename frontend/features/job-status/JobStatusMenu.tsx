import styles from "./jobStatus.module.css";
import type { JobStatus } from "./jobStatus.types";

type Props = {
  status: JobStatus;
  onChange: (status: JobStatus) => void;
};

export default function JobStatusMenu({ status, onChange }: Props) {
  return (
    <details className={styles.menu}>
      <summary className={styles.menuTrigger} aria-label="Update job status">
        ⋯
      </summary>

      <div className={styles.menuPanel}>
        <button
          type="button"
          className={status === "applied" ? styles.selected : ""}
          onClick={() => onChange("applied")}
        >
          ✓ Applied
        </button>

        <button
          type="button"
          className={status === "pending" ? styles.selected : ""}
          onClick={() => onChange("pending")}
        >
          Application pending
        </button>

        <button
          type="button"
          className={status === "not_relevant" ? styles.selected : ""}
          onClick={() => onChange("not_relevant")}
        >
          Not relevant
        </button>
      </div>
    </details>
  );
}

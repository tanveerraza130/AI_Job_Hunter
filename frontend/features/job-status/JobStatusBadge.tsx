import styles from "./jobStatus.module.css";
import type { JobStatus } from "./jobStatus.types";

type Props = {
  status: JobStatus;
};

const STATUS_LABELS: Partial<Record<JobStatus, string>> = {
  pending: "Application pending",
  applied: "Applied",
  not_relevant: "Not relevant",
};

export default function JobStatusBadge({ status }: Props) {
  const label = STATUS_LABELS[status];

  if (!label) {
    return null;
  }

  return (
    <span className={`${styles.badge} ${styles[status]}`}>
      <span className={styles.dot} aria-hidden="true" />
      {label}
    </span>
  );
}

import styles from "./jobStatus.module.css";

type Props = {
  onApplied: () => void;
  onNotYet: () => void;
};

export default function JobStatusPrompt({
  onApplied,
  onNotYet,
}: Props) {
  return (
    <div className={styles.prompt} role="dialog" aria-label="Application status">
      <div className={styles.promptTitle}>
        Did you apply for this job?
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.appliedButton}
          onClick={onApplied}
        >
          ✓ Yes, Applied
        </button>

        <button
          type="button"
          className={styles.notYetButton}
          onClick={onNotYet}
        >
          Not Yet
        </button>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import styles from "./jobStatus.module.css";

type Props = {
  onApplied: () => void;
  onNotYet: () => void;
  onNotRelevant: () => void;
  /** Optional: title text; defaults to "Did you apply for this job?" */
  title?: string;
};

export default function JobStatusPrompt({
  onApplied,
  onNotYet,
  onNotRelevant,
  title = "Did you apply for this job?",
}: Props) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Freeze background scroll while modal is open
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, []);

  // Close on Escape (treated as "Not Yet" — safe default, no state change)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onNotYet();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onNotYet]);

  if (!mounted) return null;

  return createPortal(
    <>
      <div
        className={styles.promptBackdrop}
        role="presentation"
        onClick={onNotYet}
      />
      <div
        className={styles.prompt}
        role="dialog"
        aria-modal="true"
        aria-label="Application status"
      >
        <div className={styles.promptTitle}>{title}</div>

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

          <button
            type="button"
            className={styles.notYetButton}
            onClick={onNotRelevant}
          >
            Not Relevant
          </button>
        </div>
      </div>
    </>,
    document.body,
  );
}

import type { ReactNode } from "react";
import styles from "./JobList.module.css";

export interface JobListProps {
  children?: ReactNode;
}

export default function JobList({ children }: JobListProps) {
  return (
    <section className={styles.root} data-ui="job-list">
      {children}
    </section>
  );
}

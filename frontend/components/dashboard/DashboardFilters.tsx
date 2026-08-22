import type { ReactNode } from "react";
import styles from "./DashboardFilters.module.css";

export interface DashboardFiltersProps {
  children?: ReactNode;
}

export default function DashboardFilters({ children }: DashboardFiltersProps) {
  return (
    <section className={styles.root} data-ui="dashboard-filters">
      {children}
    </section>
  );
}

"use client";

import styles from "./MobileTabs.module.css";
import {
  getStatusConfig,
  MOBILE_TAB_ORDER,
} from "@/features/job-status/jobStatus.config";

export type MobileTab =
  | "ALL"
  | "Not Applied"
  | "Saved"
  | "Pending"
  | "Applied"
  | "Interview"
  | "Offer"
  | "Rejected"
  | "Not Relevant";

interface Props {
  activeTab: MobileTab;
  setActiveTab: (value: MobileTab) => void;
  totalJobs: number;
  /** Optional: counts per status for badge display */
  countsByStatus?: Partial<Record<MobileTab, number>>;
}

export default function MobileTabs({
  activeTab,
  setActiveTab,
  totalJobs,
  countsByStatus = {},
}: Props) {
  return (
    <nav
      className={styles.tabs}
      aria-label="Job status"
    >
      <div className={styles.scroll}>
        {MOBILE_TAB_ORDER.map((apiValue) => {
          // "ALL" tab
          if (apiValue === "ALL") {
            const isActive = activeTab === "ALL";
            return (
              <button
                key="ALL"
                type="button"
                className={
                  isActive ? styles.tabActive : styles.tab
                }
                onClick={() => setActiveTab("ALL")}
              >
                All ({totalJobs.toLocaleString("en-IN")})
              </button>
            );
          }

          const cfg = getStatusConfig(apiValue);
          const tabValue = cfg.display as MobileTab;
          const isActive = activeTab === tabValue;
          const count = countsByStatus[tabValue];

          return (
            <button
              key={apiValue}
              type="button"
              className={
                isActive ? styles.tabActive : styles.tab
              }
              onClick={() => setActiveTab(tabValue)}
              style={
                isActive
                  ? { color: cfg.color, borderColor: cfg.color }
                  : undefined
              }
            >
              {cfg.icon} {cfg.display}
              {typeof count === "number" && count > 0 && (
                <span className={styles.badge}>{count}</span>
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

"use client";

import styles from "./MobileTabs.module.css";

type MobileTab =
  | "ALL"
  | "Saved"
  | "Applied"
  | "Interview";

interface Props {
  activeTab: MobileTab;
  setActiveTab: (value: MobileTab) => void;
  totalJobs: number;
}

export default function MobileTabs({
  activeTab,
  setActiveTab,
  totalJobs,
}: Props) {
  const tabs = [
    [
      "ALL",
      `All (${totalJobs.toLocaleString("en-IN")})`,
    ],
    ["Saved", "Saved"],
    ["Applied", "Applied"],
    ["Interview", "Interview"],
  ] as const;

  return (
    <nav
      className={styles.tabs}
      aria-label="Job status"
    >
      {tabs.map(([value, label]) => (
        <button
          key={value}
          type="button"
          className={
            activeTab === value
              ? styles.tabActive
              : styles.tab
          }
          onClick={() => setActiveTab(value)}
        >
          {label}
        </button>
      ))}
    </nav>
  );
}

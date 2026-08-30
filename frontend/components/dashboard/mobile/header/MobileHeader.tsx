"use client";

import { Bell, Sparkles } from "lucide-react";
import styles from "./MobileHeader.module.css";

export default function MobileHeader() {
  return (
    <header className={styles.header}>
      <button
        type="button"
        className={styles.menuButton}
        aria-label="Open menu"
      >
        <span />
        <span />
        <span />
      </button>

      <div className={styles.brand}>
        <div className={styles.logo}>
          <Sparkles size={17} />
        </div>

        <div className={styles.brandText}>
          <strong>AI Job Hunter</strong>
          <span>Find your next role.</span>
        </div>
      </div>

      <button
        type="button"
        className={styles.notificationButton}
        aria-label="Notifications"
      >
        <Bell size={20} />
        <i />
      </button>
    </header>
  );
}

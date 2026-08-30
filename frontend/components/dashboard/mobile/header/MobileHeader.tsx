"use client";

import {
  Bell,
  Sparkles,
  UserRound,
} from "lucide-react";
import styles from "./MobileHeader.module.css";

interface MobileHeaderProps {
  profileId: string;
}

function formatProfile(value: string): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function MobileHeader({
  profileId,
}: MobileHeaderProps) {
  function openProfile() {
    window.location.href = "/profile";
  }

  function logout() {
    localStorage.removeItem("ai_job_hunter_token");
    window.location.href = "/login";
  }

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

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.notificationButton}
          aria-label="Notifications"
        >
          <Bell size={20} />
          <i />
        </button>

        <button
          type="button"
          className={styles.profileButton}
          onClick={openProfile}
          aria-label={
            profileId
              ? `Manage ${formatProfile(profileId)} profile`
              : "Manage profile"
          }
          title={
            profileId
              ? formatProfile(profileId)
              : "Manage profile"
          }
        >
          <span className={styles.profileAvatar}>
            <UserRound size={17} />
          </span>
        </button>
      </div>
    </header>
  );
}

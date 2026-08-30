import {
  BriefcaseBusiness,
  Heart,
  History,
  Moon,
  Sparkles,
  UserRound,
  ChevronDown,
  LogOut,
} from "lucide-react";
import { useState } from "react";
import styles from "./DesktopHeader.module.css";

interface DesktopHeaderProps {
  profileId: string;
}

function formatProfile(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

const navigation = [
  { label: "Dashboard", active: true },
  { label: "Applications", icon: BriefcaseBusiness },
  { label: "Shortlisted", icon: Heart },
  { label: "History", icon: History },
  { label: "Saved Jobs", icon: Heart },
];

export default function DesktopHeader({
  profileId,
}: DesktopHeaderProps) {
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  function openProfile() {
    window.location.href = "/profile";
  }

  function logout() {
    localStorage.removeItem("ai_job_hunter_token");
    window.location.href = "/login";
  }

  return (
    <div className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <span
            className={styles.brandMark}
            aria-hidden="true"
          >
            <Sparkles
              size={17}
              strokeWidth={2.5}
            />
          </span>

          <div className={styles.brandCopy}>
            <span className={styles.brandName}>
              AI Job Hunter
            </span>

            <span className={styles.brandSubtitle}>
              Intelligent career matching
            </span>
          </div>
        </div>

        <nav
          className={styles.navigation}
          aria-label="Primary navigation"
        >
          {navigation.map(
            ({ label, icon: Icon, active }) => (
              <button
                key={label}
                type="button"
                className={`${styles.navItem} ${
                  active
                    ? styles.navItemActive
                    : ""
                }`}
                aria-current={
                  active ? "page" : undefined
                }
              >
                {Icon && (
                  <Icon
                    size={16}
                    strokeWidth={1.8}
                    aria-hidden="true"
                  />
                )}

                <span>{label}</span>
              </button>
            ),
          )}
        </nav>

        <div className={styles.profileArea}>
          <button
            type="button"
            className={styles.themeButton}
            aria-label="Toggle theme"
          >
            <Moon
              size={17}
              strokeWidth={1.8}
            />
          </button>

          <div className={styles.profileMenu}>
            <button
              type="button"
              className={styles.profileTrigger}
              onClick={() => setProfileMenuOpen((open) => !open)}
              aria-expanded={profileMenuOpen}
              aria-label="Open profile menu"
              title="Manage your profile"
            >
              <span className={styles.profileAvatar}>
                <UserRound
                  size={16}
                  strokeWidth={1.9}
                  aria-hidden="true"
                />
              </span>

              <span className={styles.profileTriggerCopy}>
                <span className={styles.profileTriggerLabel}>
                  PROFILE
                </span>

                <span className={styles.profileValue}>
                  {profileId
                    ? formatProfile(profileId)
                    : "Your profile"}
                </span>
              </span>

              <ChevronDown
                size={15}
                strokeWidth={1.8}
                className={styles.profileChevron}
                aria-hidden="true"
              />
            </button>

            <div
              className={`${styles.profileActions} ${
                profileMenuOpen ? styles.profileActionsOpen : ""
              }`}
            >
              <button
                type="button"
                className={styles.profileAction}
                onClick={openProfile}
              >
                <UserRound size={15} />
                <span>Manage profile</span>
              </button>

              <button
                type="button"
                className={`${styles.profileAction} ${styles.logoutAction}`}
                onClick={logout}
              >
                <LogOut size={15} />
                <span>Sign out</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

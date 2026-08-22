import {
  BriefcaseBusiness,
  ChevronDown,
  Heart,
  History,
  Moon,
  Sparkles,
} from "lucide-react";
import styles from "./DesktopHeader.module.css";

interface DesktopHeaderProps {
  profileId: string;
  profiles: string[];
  onProfileChange: (profileId: string) => void;
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
  profiles,
  onProfileChange,
}: DesktopHeaderProps) {
  return (
    <div className={styles.header}>
      <div className={styles.inner}>
        <div className={styles.brand}>
          <span className={styles.brandMark} aria-hidden="true">
            <Sparkles size={17} strokeWidth={2.5} />
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
          {navigation.map(({ label, icon: Icon, active }) => (
            <button
              key={label}
              type="button"
              className={`${styles.navItem} ${
                active ? styles.navItemActive : ""
              }`}
              aria-current={active ? "page" : undefined}
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
          ))}
        </nav>

        <div className={styles.profileArea}>
          <button
            type="button"
            className={styles.themeButton}
            aria-label="Toggle theme"
          >
            <Moon size={17} strokeWidth={1.8} />
          </button>

          <label className={styles.profileSelect}>
            <BriefcaseBusiness
              size={14}
              strokeWidth={1.8}
              aria-hidden="true"
            />

            <select
              value={profileId}
              onChange={(event) =>
                onProfileChange(event.target.value)
              }
              aria-label="Select profile"
            >
              <option value="">Select profile</option>

              {profiles.map((profile) => (
                <option key={profile} value={profile}>
                  {formatProfile(profile)}
                </option>
              ))}
            </select>

            <ChevronDown
              size={14}
              aria-hidden="true"
              className={styles.chevron}
            />
          </label>
        </div>
      </div>
    </div>
  );
}

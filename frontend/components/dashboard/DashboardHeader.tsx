import DesktopHeader from "./DesktopHeader";
import styles from "./DashboardHeader.module.css";

export interface DashboardHeaderProps {
  profileId: string;
  onProfileChange?: (profileId: string) => void | Promise<void>;
}

export default function DashboardHeader({
  profileId,
  onProfileChange,
}: DashboardHeaderProps) {
  return (
    <header
      className={styles.root}
      data-ui="dashboard-header"
    >
      <DesktopHeader profileId={profileId} onProfileChange={onProfileChange} />
    </header>
  );
}

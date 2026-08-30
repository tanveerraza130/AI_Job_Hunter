import DesktopHeader from "./DesktopHeader";
import styles from "./DashboardHeader.module.css";

export interface DashboardHeaderProps {
  profileId: string;
}

export default function DashboardHeader({
  profileId,
}: DashboardHeaderProps) {
  return (
    <header
      className={styles.root}
      data-ui="dashboard-header"
    >
      <DesktopHeader profileId={profileId} />
    </header>
  );
}

import DesktopHeader from "./DesktopHeader";
import styles from "./DashboardHeader.module.css";

export interface DashboardHeaderProps {
  profileId: string;
  profiles: string[];
  onProfileChange: (profileId: string) => void;
}

export default function DashboardHeader({
  profileId,
  profiles,
  onProfileChange,
}: DashboardHeaderProps) {
  return (
    <header
      className={styles.root}
      data-ui="dashboard-header"
    >
      <DesktopHeader
        profileId={profileId}
        profiles={profiles}
        onProfileChange={onProfileChange}
      />
    </header>
  );
}

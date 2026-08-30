import { LockKeyhole, Mail, BriefcaseBusiness } from "lucide-react";
import styles from "./ProfileAccountCard.module.css";

interface Props {
  email: string;
  profileId: string;
}

function formatProfile(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function ProfileAccountCard({
  email,
  profileId,
}: Props) {
  return (
    <section className={styles.card}>
      <div className={styles.heading}>
        <div>
          <span className={styles.eyebrow}>ACCOUNT</span>
          <h2>Account identity</h2>
          <p>These details are tied to your account and cannot be changed here.</p>
        </div>
        <div className={styles.lockBadge}>
          <LockKeyhole size={14} />
          Locked
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.field}>
          <span>Email address</span>
          <div className={styles.readOnly}>
            <Mail size={17} />
            <strong>{email}</strong>
            <LockKeyhole size={14} />
          </div>
        </div>

        <div className={styles.field}>
          <span>Job profile</span>
          <div className={styles.readOnly}>
            <BriefcaseBusiness size={17} />
            <strong>{formatProfile(profileId)}</strong>
            <LockKeyhole size={14} />
          </div>
        </div>
      </div>
    </section>
  );
}

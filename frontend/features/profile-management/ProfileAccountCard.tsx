import {
  BriefcaseBusiness,
  LockKeyhole,
  Mail,
  ShieldCheck,
} from "lucide-react";
import styles from "./ProfileAccountCard.module.css";

interface Props {
  email: string;
  profileId: string;
}

function formatProfile(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase(),
    );
}

export default function ProfileAccountCard({
  email,
  profileId,
}: Props) {
  return (
    <section className={styles.card}>
      <div className={styles.heading}>
        <div>
          <span className={styles.eyebrow}>
            ACCOUNT
          </span>

          <h2>Account identity</h2>

          <p>
            Your account identity is protected
            and cannot be changed from this page.
          </p>
        </div>

        <div className={styles.lockBadge}>
          <LockKeyhole size={13} />
          Protected
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.field}>
          <span>Email address</span>

          <div className={styles.readOnly}>
            <Mail size={16} />
            <strong>
              {email}
            </strong>

            <LockKeyhole size={13} />
          </div>
        </div>

        <div className={styles.field}>
          <span>Assigned job profile</span>

          <div className={styles.readOnly}>
            <BriefcaseBusiness size={16} />

            <strong>
              {formatProfile(profileId)}
            </strong>

            <LockKeyhole size={13} />
          </div>
        </div>
      </div>

      <div className={styles.securityNote}>
        <ShieldCheck size={15} />

        <span>
          This profile is resolved from your
          authenticated account. Changing the
          URL cannot change the assigned profile.
        </span>
      </div>
    </section>
  );
}

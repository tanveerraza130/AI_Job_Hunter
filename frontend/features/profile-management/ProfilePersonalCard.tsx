import { UserRound, Phone } from "lucide-react";
import styles from "./ProfilePersonalCard.module.css";

interface Props {
  fullName: string;
  phone: string;
  onChange: (field: "full_name" | "phone", value: string) => void;
}

export default function ProfilePersonalCard({
  fullName,
  phone,
  onChange,
}: Props) {
  return (
    <section className={styles.card}>
      <div className={styles.heading}>
        <div>
          <span className={styles.eyebrow}>PERSONAL</span>
          <h2>Personal information</h2>
          <p>Keep your contact details current for your job search.</p>
        </div>
      </div>

      <div className={styles.grid}>
        <label className={styles.field}>
          <span>Full name</span>
          <div className={styles.inputWrap}>
            <UserRound size={17} />
            <input
              value={fullName}
              onChange={(event) =>
                onChange("full_name", event.target.value)
              }
              placeholder="Your full name"
              maxLength={150}
            />
          </div>
        </label>

        <label className={styles.field}>
          <span>Phone number</span>
          <div className={styles.inputWrap}>
            <Phone size={17} />
            <input
              value={phone}
              onChange={(event) =>
                onChange("phone", event.target.value)
              }
              placeholder="Your phone number"
              maxLength={30}
            />
          </div>
        </label>
      </div>
    </section>
  );
}

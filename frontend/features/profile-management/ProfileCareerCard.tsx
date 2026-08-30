import {
  MapPin,
  BriefcaseBusiness,
  Clock3,
  IndianRupee,
  FileText,
} from "lucide-react";
import styles from "./ProfileCareerCard.module.css";

interface Props {
  values: {
    preferred_location: string;
    role_level: string;
    experience_years: string;
    current_ctc_lpa: string;
    expected_ctc_lpa: string;
    resume_path: string;
  };
  onChange: (
    field:
      | "preferred_location"
      | "role_level"
      | "experience_years"
      | "current_ctc_lpa"
      | "expected_ctc_lpa"
      | "resume_path",
    value: string,
  ) => void;
}

function Field({
  icon: Icon,
  label,
  value,
  placeholder,
  onChange,
  type = "text",
}: {
  icon: typeof MapPin;
  label: string;
  value: string;
  placeholder: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className={styles.field}>
      <span>{label}</span>
      <div className={styles.inputWrap}>
        <Icon size={17} />
        <input
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
        />
      </div>
    </label>
  );
}

export default function ProfileCareerCard({
  values,
  onChange,
}: Props) {
  return (
    <section className={styles.card}>
      <div className={styles.heading}>
        <div>
          <span className={styles.eyebrow}>CAREER</span>
          <h2>Career preferences</h2>
          <p>These preferences help us keep your opportunities relevant.</p>
        </div>
      </div>

      <div className={styles.grid}>
        <Field
          icon={MapPin}
          label="Preferred location"
          value={values.preferred_location}
          placeholder="e.g. Mumbai"
          onChange={(value) => onChange("preferred_location", value)}
        />

        <Field
          icon={BriefcaseBusiness}
          label="Role level"
          value={values.role_level}
          placeholder="e.g. Manager"
          onChange={(value) => onChange("role_level", value)}
        />

        <Field
          icon={Clock3}
          label="Experience"
          value={values.experience_years}
          placeholder="e.g. 8 years"
          onChange={(value) => onChange("experience_years", value)}
        />

        <Field
          icon={IndianRupee}
          label="Current CTC (LPA)"
          value={values.current_ctc_lpa}
          placeholder="e.g. 18"
          type="number"
          onChange={(value) => onChange("current_ctc_lpa", value)}
        />

        <Field
          icon={IndianRupee}
          label="Expected CTC (LPA)"
          value={values.expected_ctc_lpa}
          placeholder="e.g. 24"
          type="number"
          onChange={(value) => onChange("expected_ctc_lpa", value)}
        />

        <Field
          icon={FileText}
          label="Resume"
          value={values.resume_path}
          placeholder="Resume file name"
          onChange={(value) => onChange("resume_path", value)}
        />
      </div>
    </section>
  );
}

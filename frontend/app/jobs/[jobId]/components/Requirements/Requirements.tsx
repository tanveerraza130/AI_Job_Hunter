import type { JobDetail, ScoreBreakdown } from "@/types/job";
import styles from "./Requirements.module.css";

type Props = {
  job: JobDetail;
  breakdown: ScoreBreakdown | null;
};

export default function Requirements({ job, breakdown }: Props) {
  const experience =
    job.experience_min != null || job.experience_max != null
      ? job.experience_min != null && job.experience_max != null
        ? `${job.experience_min}–${job.experience_max} years`
        : job.experience_min != null
          ? `${job.experience_min}+ years`
          : `Up to ${job.experience_max} years`
      : "Not disclosed";

  const skills = [
    ...(breakdown?.matched_skills ?? []),
    ...(breakdown?.missing_skills ?? []),
  ];

  const uniqueSkills = [...new Set(skills)].slice(0, 8);

  return (
    <section className={styles.section}>

      <div className={styles.grid}>
        <div className={styles.card}>
          <span>Experience</span>
          <strong>{experience}</strong>
        </div>

        <div className={styles.card}>
          <span>Employment</span>
          <strong>{job.employment_type || "Not disclosed"}</strong>
        </div>

        <div className={styles.card}>
          <span>Location</span>
          <strong>{job.location || "Not disclosed"}</strong>
        </div>
      </div>

      {uniqueSkills.length > 0 && (
        <div className={styles.skills}>
          <h3>Relevant skills</h3>
          <div className={styles.chips}>
            {uniqueSkills.map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

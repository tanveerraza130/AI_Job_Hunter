import styles from "./StatCard.module.css";

interface StatCardProps {
  label: string;
  value: string;
  hint: string;
  emphasis?: boolean;
}

export default function StatCard({
  label,
  value,
  hint,
  emphasis = false,
}: StatCardProps) {
  return (
    <article className={`${styles.card} ${emphasis ? styles.emphasis : ""}`}>
      <div className={styles.label}>{label}</div>
      <div className={styles.value}>{value}</div>
      <div className={styles.hint}>{hint}</div>
    </article>
  );
}

import styles from "./Responsibilities.module.css";

type Props = {
  paragraphs: string[];
};

export default function Responsibilities({ paragraphs }: Props) {
  const items = paragraphs
    .filter(Boolean)
    .slice(5, 11);

  return (
    <section className={styles.section}>

      <div className={styles.list}>
        {items.length ? (
          items.map((item, index) => (
            <div
              className={styles.item}
              key={`${index}-${item.slice(0, 30)}`}
            >
              <span>✓</span>
              <p>{item}</p>
            </div>
          ))
        ) : (
          <p className={styles.empty}>
            Responsibilities were not provided in the listing.
          </p>
        )}
      </div>
    </section>
  );
}

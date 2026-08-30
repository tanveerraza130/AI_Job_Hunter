import styles from "./BrandMarquee.module.css";

const brands = [
  {
    name: "Amazon",
    src: "/company-logos/amazon.svg",
    className: "amazon",
  },
  {
    name: "Flipkart",
    src: "/company-logos/flipkart.svg",
    className: "flipkart",
  },
  {
    name: "Myntra",
    src: "/company-logos/myntra.svg",
    className: "myntra",
  },
  {
    name: "Nykaa",
    src: "/company-logos/nykaa.svg",
    className: "nykaa",
  },
  {
    name: "Meesho",
    src: "/company-logos/meesho.png",
    className: "meesho",
  },
  {
    name: "Tata",
    src: "/company-logos/tata.svg",
    className: "tata",
  },
  {
    name: "Swiggy",
    src: "/company-logos/swiggy.png",
    className: "swiggy",
  },
  {
    name: "Zomato",
    src: "/company-logos/zomato.svg",
    className: "zomato",
  },
  {
    name: "IKEA",
    src: "/company-logos/ikea.svg",
    className: "ikea",
  },
];

function LogoGroup({ hidden = false }: { hidden?: boolean }) {
  return (
    <div
      className={styles.group}
      aria-hidden={hidden ? "true" : undefined}
    >
      {brands.map((brand) => (
        <div
          key={`${hidden ? "copy-" : ""}${brand.name}`}
          className={`${styles.logoItem} ${styles[brand.className]}`}
        >
          <img
            src={brand.src}
            alt={hidden ? "" : brand.name}
            aria-hidden={hidden}
          />
        </div>
      ))}
    </div>
  );
}

export default function BrandMarquee() {
  return (
    <section
      className={styles.section}
      aria-label="Companies"
    >
      <div className={styles.marquee}>
        <div className={styles.track}>
          <LogoGroup />
          <LogoGroup hidden />
        </div>

        <div className={styles.fadeLeft} />
        <div className={styles.fadeRight} />
      </div>
    </section>
  );
}

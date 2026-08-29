import styles from "./Footer.module.css";

const productLinks = [
  { label: "How it works", href: "#how-it-works" },
  { label: "What you get", href: "#what-you-get" },
  { label: "Apply & track", href: "#apply-track" },
];

const companyLinks = [
  { label: "For employers", href: "#employers" },
  { label: "Request access", href: "#get-started" },
];

const socialLinks = [
  { label: "LinkedIn", href: "#" },
  { label: "Instagram", href: "#" },
  { label: "X", href: "#" },
];

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.brandColumn}>
          <a className={styles.brand} href="#" aria-label="AI Job Hunter home">
            <span className={styles.brandMark}>✦</span>

            <span className={styles.brandCopy}>
              <strong>AI Job Hunter</strong>
              <small>Find what fits.</small>
            </span>
          </a>

          <p className={styles.description}>
            A smarter way to discover opportunities that fit your skills,
            experience and goals.
          </p>

          <div className={styles.socials}>
            {socialLinks.map((social) => (
              <a
                key={social.label}
                href={social.href}
                aria-label={social.label}
                className={styles.social}
              >
                {social.label}
              </a>
            ))}
          </div>
        </div>

        <nav className={styles.links} aria-label="Footer navigation">
          <div className={styles.linkGroup}>
            <h3>Product</h3>

            {productLinks.map((link) => (
              <a key={link.label} href={link.href}>
                {link.label}
              </a>
            ))}
          </div>

          <div className={styles.linkGroup}>
            <h3>Company</h3>

            {companyLinks.map((link) => (
              <a key={link.label} href={link.href}>
                {link.label}
              </a>
            ))}
          </div>

          <div className={styles.linkGroup}>
            <h3>Legal</h3>
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms</a>
          </div>
        </nav>
      </div>

      <div className={styles.bottom}>
        <span>© 2026 AI Job Hunter. All rights reserved.</span>

        <span className={styles.signature}>
          <i />
          Find what fits.
        </span>
      </div>
    </footer>
  );
}

"use client";

import { useState } from "react";
import styles from "./GlobalHeader.module.css";

const handleJoinFree = (
  event: React.MouseEvent<HTMLAnchorElement>,
) => {
  event.preventDefault();

  const token = localStorage.getItem("ai_job_hunter_token");

  window.location.href = token ? "/dashboard" : "/signup";
};

export default function GlobalHeader() {
  const [menuOpen, setMenuOpen] = useState(false);

  const closeMenu = () => setMenuOpen(false);

  return (
    <header className={styles.header}>
      <div className={styles.inner}>

        <a
          className={styles.brand}
          href="#"
          aria-label="AI Job Hunter home"
          onClick={closeMenu}
        >
          <span className={styles.mark}>✦</span>

          <span className={styles.brandCopy}>
            <strong>AI Job Hunter</strong>
            <small>Find what fits.</small>
          </span>
        </a>

        <nav className={styles.nav} aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#what-you-get">What you get</a>
          <a href="#apply-track">Apply &amp; track</a>
          <a href="#employers">For employers</a>
        </nav>

        <div className={styles.actions}>
          <a className={styles.signin} href="/login">
            Log In
          </a>

          <a className={styles.cta} href="/signup" onClick={handleJoinFree}>
            Join Free <span>→</span>
          </a>

          <button
            type="button"
            className={`${styles.menuButton} ${menuOpen ? styles.menuButtonOpen : ""}`}
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
        </div>

      </div>

      <div
        className={`${styles.mobileMenu} ${menuOpen ? styles.mobileMenuOpen : ""}`}
        aria-hidden={!menuOpen}
      >
        <nav aria-label="Mobile navigation">
          <a href="#how-it-works" onClick={closeMenu}>
            <span>How it works</span>
            <span>→</span>
          </a>
          <a href="#what-you-get" onClick={closeMenu}>
            <span>What you get</span>
            <span>→</span>
          </a>
          <a href="#apply-track" onClick={closeMenu}>
            <span>Apply &amp; track</span>
            <span>→</span>
          </a>
          <a href="#employers" onClick={closeMenu}>
            <span>For employers</span>
            <span>→</span>
          </a>
        </nav>

        <a
          className={styles.mobileMenuCta}
          href="/signup"
          onClick={(event) => {
            closeMenu();
            handleJoinFree(event);
          }}
        >
          Join Free <span>→</span>
        </a>
      </div>
    </header>
  );
}

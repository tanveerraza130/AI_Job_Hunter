"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./jobStatus.module.css";
import {
  getStatusConfig,
  STATUS_CONFIG,
} from "./jobStatus.config";
import type { JobStatus } from "./jobStatus.types";

type Props = {
  status: JobStatus | "not_applied";
  onChange: (
    status: JobStatus | "not_applied",
  ) => void | Promise<void>;
  /** Optional: compact mode for tight spaces */
  compact?: boolean;
  /** Optional: direction of dropdown */
  direction?: "up" | "down";
};

export default function JobStatusMenu({
  status,
  onChange,
  compact = false,
  direction = "down",
}: Props) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const currentConfig = getStatusConfig(status);

  // Close on outside click
  useEffect(() => {
    if (!open) return;

    const handler = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };

    const escHandler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", handler);
    document.addEventListener("keydown", escHandler);
    return () => {
      document.removeEventListener("mousedown", handler);
      document.removeEventListener("keydown", escHandler);
    };
  }, [open]);

  const handleSelect = async (
    value: JobStatus | "not_applied",
  ) => {
    setOpen(false);
    await onChange(value);
  };

  return (
    <div
      ref={containerRef}
      className={styles.menu}
      data-open={open ? "true" : "false"}
    >
      <button
        type="button"
        className={styles.menuTrigger}
        aria-label="Update job status"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        style={{
          background: currentConfig.bg,
          borderColor: currentConfig.border,
          color: currentConfig.color,
        }}
      >
        <span className={styles.triggerIcon}>
          {currentConfig.icon}
        </span>
        {!compact && (
          <span className={styles.triggerLabel}>
            {currentConfig.display}
          </span>
        )}
        <svg
          width="10"
          height="10"
          viewBox="0 0 12 12"
          className={
            open ? styles.chevronOpen : styles.chevron
          }
        >
          <path
            d="M2 4l4 4 4-4"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </button>

      {open && (
        <div
          className={styles.menuPanel}
          data-direction={direction}
          role="menu"
        >
          {STATUS_CONFIG.map((cfg) => {
            const isActive = cfg.apiValue === status;
            return (
              <button
                key={cfg.apiValue}
                type="button"
                role="menuitem"
                className={
                  isActive
                    ? styles.menuItemActive
                    : styles.menuItem
                }
                onClick={() => handleSelect(cfg.apiValue)}
                style={{
                  color: isActive ? cfg.color : undefined,
                }}
              >
                <span className={styles.menuIcon}>
                  {cfg.icon}
                </span>
                <span className={styles.menuLabel}>
                  {cfg.label}
                </span>
                {isActive && (
                  <span
                    className={styles.checkMark}
                    style={{ color: cfg.color }}
                  >
                    ✓
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

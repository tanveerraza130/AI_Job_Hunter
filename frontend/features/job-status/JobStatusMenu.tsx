"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import styles from "./jobStatus.module.css";
import { getStatusConfig, STATUS_CONFIG } from "./jobStatus.config";
import type { JobStatus } from "./jobStatus.types";

type Props = {
  status: JobStatus | "not_applied";
  onChange: (status: JobStatus | "not_applied") => void | Promise<void>;
  direction?: "up" | "down";
  /** Optional extra class applied to the trigger button (for host page styling). */
  triggerClassName?: string;
  /** Optional: called when user taps "Report as dead". */
  onReportDead?: () => void | Promise<void>;
};

const MOBILE_BREAKPOINT = 767;
const PANEL_WIDTH = 240;
const PANEL_MARGIN = 8;

function useIsMobile() {
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`);
    const update = () => setIsMobile(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return isMobile;
}

export default function JobStatusMenu({ status, onChange, triggerClassName, onReportDead }: Props) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [coords, setCoords] = useState<{
    top: number;
    left: number;
    placement: "up" | "down";
  } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();

  const currentConfig = useMemo(() => getStatusConfig(status), [status]);

  useEffect(() => setMounted(true), []);

  const computeCoords = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) return null;

    const rect = trigger.getBoundingClientRect();
    const panelHeightEstimate = 360;
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    // Flip up if not enough room below and there's more room above
    const placement: "up" | "down" =
      spaceBelow < panelHeightEstimate && spaceAbove > spaceBelow
        ? "up"
        : "down";

    // Horizontal: align right edge of panel with right edge of trigger,
    // but never let it go off the viewport.
    let left = rect.right - PANEL_WIDTH;
    if (left < PANEL_MARGIN) left = PANEL_MARGIN;
    if (left + PANEL_WIDTH > window.innerWidth - PANEL_MARGIN) {
      left = window.innerWidth - PANEL_WIDTH - PANEL_MARGIN;
    }

    const top = placement === "down" ? rect.bottom + 8 : rect.top - 8;

    return { top, left, placement };
  }, []);

  const handleToggle = () => {
    if (!open) {
      const next = computeCoords();
      if (next) setCoords(next);
    }
    setOpen((v) => !v);
  };

  const handleSelect = async (value: JobStatus | "not_applied") => {
    setOpen(false);
    await onChange(value);
  };

  const handleReportDead = async () => {
    setOpen(false);
    if (onReportDead) {
      await onReportDead();
    }
  };

  // Outside click + Escape
  useEffect(() => {
    if (!open) return;

    const onPointerDown = (e: MouseEvent | TouchEvent) => {
      const target = e.target as Node;
      if (containerRef.current?.contains(target)) return;
      if (panelRef.current?.contains(target)) return;
      setOpen(false);
    };

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };

    const onScrollOrResize = () => {
      const next = computeCoords();
      if (next) setCoords(next);
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("touchstart", onPointerDown);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);

    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("touchstart", onPointerDown);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [open, computeCoords]);

  const trigger = (
    <button
      ref={triggerRef}
      type="button"
      className={
        triggerClassName
          ? `${styles.menuTrigger} ${triggerClassName}`
          : styles.menuTrigger
      }
      aria-label="Update job status"
      aria-expanded={open}
      aria-haspopup="menu"
      onClick={handleToggle}
      style={{
        background: currentConfig.bg,
        borderColor: currentConfig.border,
        color: currentConfig.color,
      }}
    >
      <span className={styles.triggerLabel}>{currentConfig.display}</span>
      <svg
        width="10"
        height="10"
        viewBox="0 0 12 12"
        className={open ? styles.chevronOpen : styles.chevron}
        aria-hidden="true"
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
  );

  const menuItems = STATUS_CONFIG.map((cfg) => {
    const isActive = cfg.apiValue === status;
    return (
      <button
        key={cfg.apiValue}
        type="button"
        role="menuitem"
        className={isActive ? styles.menuItemActive : styles.menuItem}
        onClick={() => handleSelect(cfg.apiValue)}
        style={isActive ? { color: cfg.color } : undefined}
      >
        <span className={styles.menuLabel}>{cfg.label}</span>
        {isActive && (
          <span className={styles.checkMark} style={{ color: cfg.color }}>
            ✓
          </span>
        )}
      </button>
    );
  });

  // ---------- Desktop — portaled fixed dropdown ----------
  const desktopPanel =
    mounted &&
    !isMobile &&
    open &&
    coords &&
    createPortal(
      <div
        ref={panelRef}
        className={styles.menuPanel}
        style={{
          position: "fixed",
          top: coords.top,
          left: coords.left,
          width: PANEL_WIDTH,
          right: "auto",
          bottom: "auto",
          transform:
            coords.placement === "up" ? "translateY(-100%)" : "none",
        }}
        data-direction={coords.placement}
        role="menu"
      >
        {menuItems}

        {onReportDead && (
          <>
            <div className={styles.menuDivider} />
            <button
              type="button"
              role="menuitem"
              className={styles.menuItemReport}
              onClick={handleReportDead}
            >
              <span className={styles.menuLabel}>
                Report as dead
              </span>
            </button>
          </>
        )}
      </div>,
      document.body,
    );

  // ---------- Mobile — bottom sheet ----------
  const mobileSheet =
    mounted &&
    isMobile &&
    open &&
    createPortal(
      <>
        <div
          className={styles.sheetBackdrop}
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
        <div
          ref={panelRef}
          className={styles.sheet}
          role="menu"
          aria-label="Application status"
        >
          <div className={styles.sheetHandle} aria-hidden="true" />
          <div className={styles.sheetTitle}>Update status</div>
          <div className={styles.sheetList}>
            {STATUS_CONFIG.map((cfg) => {
              const isActive = cfg.apiValue === status;
              return (
                <button
                  key={cfg.apiValue}
                  type="button"
                  role="menuitem"
                  className={
                    isActive
                      ? `${styles.sheetItem} ${styles.sheetItemActive}`
                      : styles.sheetItem
                  }
                  onClick={() => handleSelect(cfg.apiValue)}
                  style={isActive ? { color: cfg.color } : undefined}
                >
                  <span className={styles.sheetItemLabel}>{cfg.label}</span>
                  {isActive && (
                    <span
                      className={styles.sheetCheck}
                      style={{ color: cfg.color }}
                    >
                      ✓
                    </span>
                  )}
                </button>
              );
            })}

            {onReportDead && (
              <>
                <div className={styles.sheetDivider} />
                <button
                  type="button"
                  role="menuitem"
                  className={styles.sheetItemReport}
                  onClick={handleReportDead}
                >
                  <span className={styles.sheetItemLabel}>
                    Report as dead
                  </span>
                </button>
              </>
            )}
          </div>
        </div>
      </>,
      document.body,
    );

  return (
    <div ref={containerRef} className={styles.menu} data-open={open}>
      {trigger}
      {isMobile ? mobileSheet : desktopPanel}
    </div>
  );
}

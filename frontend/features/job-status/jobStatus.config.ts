import type { JobStatus } from "./jobStatus.types";

export type StatusConfig = {
  /** API value (lowercase, snake_case) */
  apiValue: JobStatus | "not_applied";
  /** Human-readable label */
  label: string;
  /** Emoji or icon character */
  icon: string;
  /** Primary color (hex) */
  color: string;
  /** Background color (hex) */
  bg: string;
  /** Border color (hex) */
  border: string;
  /** Sort order in menus/tabs (lower = earlier) */
  order: number;
  /** Mobile display value (Title Case) */
  display: string;
};

/**
 * Single source of truth for all job statuses.
 * Order: [Not Applied, Saved, Pending, Applied, Interview, Offer, Rejected, Not Relevant]
 */
export const STATUS_CONFIG: StatusConfig[] = [
  {
    apiValue: "not_applied",
    display: "Not Applied",
    label: "Not Applied",
    icon: "",
    color: "#667085",
    bg: "#ffffff",
    border: "#c4cad3",
    order: 0,
  },
  {
    apiValue: "saved",
    display: "Saved",
    label: "Saved for later",
    icon: "",
    color: "#7c3aed",
    bg: "#f5f3ff",
    border: "#ddd6fe",
    order: 1,
  },
  {
    apiValue: "pending",
    display: "Pending",
    label: "Application pending",
    icon: "",
    color: "#9a5b00",
    bg: "#fff5df",
    border: "#f1d79f",
    order: 2,
  },
  {
    apiValue: "applied",
    display: "Applied",
    label: "Applied",
    icon: "",
    color: "#087b50",
    bg: "#e8f8f0",
    border: "#c7ead9",
    order: 3,
  },
  {
    apiValue: "interview",
    display: "Interview",
    label: "Interview scheduled",
    icon: "",
    color: "#0066cc",
    bg: "#e6f2ff",
    border: "#b8daff",
    order: 4,
  },
  {
    apiValue: "offer",
    display: "Offer",
    label: "Offer received",
    icon: "",
    color: "#047857",
    bg: "#ecfdf5",
    border: "#a7f3d0",
    order: 5,
  },
  {
    apiValue: "rejected",
    display: "Rejected",
    label: "Rejected",
    icon: "",
    color: "#b42318",
    bg: "#fef3f2",
    border: "#fecdca",
    order: 6,
  },
  {
    apiValue: "not_relevant",
    display: "Not Relevant",
    label: "Not relevant",
    icon: "",
    color: "#667085",
    bg: "#f2f4f7",
    border: "#dfe3e8",
    order: 7,
  },
];

/**
 * Get config for a given status (API value or display value).
 */
export function getStatusConfig(
  status: string | null | undefined,
): StatusConfig {
  if (!status) return STATUS_CONFIG[0]; // Not Applied

  const normalized = status.toLowerCase().replace(/[\s-]/g, "_");

  return (
    STATUS_CONFIG.find(
      (c) =>
        c.apiValue === normalized ||
        c.display.toLowerCase() === status.toLowerCase(),
    ) || STATUS_CONFIG[0]
  );
}

/** Tabs for mobile (compact list) */
export const MOBILE_TAB_ORDER: (JobStatus | "not_applied" | "ALL")[] = [
  "ALL",
  "not_applied",
  "saved",
  "pending",
  "applied",
  "interview",
  "offer",
  "rejected",
  "not_relevant",
];

/** Tabs for desktop (compact priority list) */
export const DESKTOP_TAB_ORDER: (JobStatus | "not_applied" | "ALL")[] = [
  "ALL",
  "not_applied",
  "saved",
  "applied",
  "interview",
  "offer",
  "rejected",
];

"use client";

import { useEffect, useState } from "react";

import {
  Bookmark,
  CalendarDays,
  ExternalLink,
  BriefcaseBusiness,
  Check,
  MapPin,
  Building2,
  Laptop2,
  IndianRupee,
  Clock3,
} from "lucide-react";

import type { ApplicationStatus } from "@/lib/api";
import type { JobDetail } from "@/types/job";
import { formatDisplayText } from "@/lib/display";

import styles from "./JobHeader.module.css";
import { setApplyAwaitingReturn } from "@/lib/applyReturnState";

type Props = {
  job: JobDetail;
  score: JobDetail["score"];
  status: ApplicationStatus | "not_applied";
  saving: boolean;
  saveApplication: (
    nextStatus: ApplicationStatus,
  ) => Promise<void>;
  showApplyPrompt?: boolean;
  onApplyConfirmed?: () => void;
  onApplyNotYet?: () => void;
  onApplyNotRelevant?: () => void;
  onApplyStarted?: () => void;
};

function formatDate(value?: string | null) {
  if (!value) return "Not disclosed";

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return "Not disclosed";
  }

  return parsed.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatExperience(
  min?: number | null,
  max?: number | null,
) {
  if (min == null && max == null) return "Not disclosed";
  if (min != null && max != null) return `${min}–${max} Yrs Exp`;
  if (min != null) return `${min}+ Yrs Exp`;
  return `Up to ${max} Yrs`;
}

function formatSalary(
  min?: number | null,
  max?: number | null,
  currency?: string | null,
) {
  if (min == null && max == null) return "Salary not disclosed";

  const symbol = currency || "₹";

  const money = (value: number) =>
    new Intl.NumberFormat("en-IN").format(value);

  if (min != null && max != null) {
    return `${symbol}${money(min)} – ${symbol}${money(max)}`;
  }

  if (min != null) return `From ${symbol}${money(min)}`;

  return `Up to ${symbol}${money(max as number)}`;
}

function companyInitials(company?: string | null) {
  if (!company) return "CO";

  const words = formatDisplayText(company)
    .trim()
    .split(/\s+/)
    .filter(Boolean);

  if (words.length === 1) {
    return words[0].slice(0, 2).toUpperCase();
  }

  return `${words[0][0]}${words[1][0]}`.toUpperCase();
}

export default function JobHeader({
  job,
  score,
  status,
  saving,
  saveApplication,
  onApplyStarted,
  showApplyPrompt,
  onApplyConfirmed,
  onApplyNotYet,
  onApplyNotRelevant,
}: Props) {
  const scoreValue =
    score?.overall_score != null
      ? score.overall_score
      : null;

  const scorePercent =
    scoreValue != null
      ? Math.max(0, Math.min(100, scoreValue))
      : 0;

  const roundedScore =
    scoreValue != null
      ? Math.round(scoreValue)
      : null;

  const matchLabel =
    scoreValue == null
      ? "Match unavailable"
      : scoreValue >= 80
        ? "Excellent Match"
        : scoreValue >= 60
          ? "Strong Match"
          : scoreValue >= 40
            ? "Good Match"
            : "Needs Review";

  const [desktopStatusOpen, setDesktopStatusOpen] =
    useState(false);

  const desktopStatusOptions: {
    value: ApplicationStatus;
    label: string;
  }[] = [
    { value: "saved", label: "Saved" },
    { value: "pending", label: "Application Pending" },
    { value: "applied", label: "Applied" },
    { value: "interview", label: "Interview" },
    { value: "offer", label: "Offer" },
    { value: "rejected", label: "Rejected" },
    { value: "not_relevant", label: "Not Relevant" },
  ];

  useEffect(() => {
    if (!desktopStatusOpen) return;

    function handleOutsideClick(event: PointerEvent) {
      const target = event.target as Node | null;
      const control = document.querySelector(
        ".desktop-job-status"
      );

      if (
        control &&
        target &&
        !control.contains(target)
      ) {
        setDesktopStatusOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setDesktopStatusOpen(false);
      }
    }

    document.addEventListener(
      "pointerdown",
      handleOutsideClick,
    );

    document.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        handleOutsideClick,
      );

      document.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, [desktopStatusOpen]);

  const desktopStatusLabel =
    status === "not_applied"
      ? "Not Applied"
      : desktopStatusOptions.find(
          (option) => option.value === status,
        )?.label || "Application Pending";

  return (
    <section className={styles.hero}>
      <div className={styles.heroMain}>
        <div
          className={`${styles.companyLogo} ${
            job.company?.trim().toUpperCase() === "OYO"
              ? styles.companyLogoOyo
              : ""
          }`}
        >
          {job.company?.trim().toUpperCase() === "OYO"
            ? "OYO"
            : companyInitials(job.company)}
        </div>

        <div className={styles.heroContent}>
          <h1 className={styles.title}>
            {formatDisplayText(job.title)}
          </h1>

          <div className={styles.companyLine}>
            <strong className={styles.companyName}>
              {job.company
                ? formatDisplayText(job.company)
                : "Company unavailable"}
            </strong>

            <span className={styles.companySeparator}>•</span>

            <span className={styles.locationInline}>
              <MapPin size={13} aria-hidden="true" />
              <span className={styles.locationText}>
                {job.location
                  ? formatDisplayText(job.location)
                  : "Location unavailable"}
              </span>
            </span>

            <span className={styles.companySeparator}>•</span>

            <span className={styles.workModeInline}>
              {job.job_url ? (
                <Building2 size={13} aria-hidden="true" />
              ) : (
                <Laptop2 size={13} aria-hidden="true" />
              )}
              {job.job_url ? "On-site" : "Remote"}
            </span>
          </div>

          <div className={styles.meta}>
            <span className={`${styles.metaPill} ${styles.metaPosted}`}>
              <CalendarDays size={13} aria-hidden="true" />
              {formatDate(job.posted_date)}
            </span>

            <span className={`${styles.metaPill} ${styles.metaEmployment}`}>
              <BriefcaseBusiness size={13} aria-hidden="true" />
              {job.employment_type || "Full-time"}
            </span>

            <span className={`${styles.metaPill} ${styles.metaExperience}`}>
              <Clock3 size={13} aria-hidden="true" />
              {formatExperience(
                job.experience_min,
                job.experience_max,
              )}
            </span>

            <span className={`${styles.metaPill} ${styles.metaSalary}`}>
              <IndianRupee size={13} aria-hidden="true" />
              {formatSalary(
                job.salary_min,
                job.salary_max,
                job.salary_currency,
              )}
            </span>
          </div>
        </div>

        <div className={`${styles.actions} mobile-job-header-actions`}>
          <button
            type="button"
            className={`${styles.saveButton} ${
              status === "saved"
                ? styles.saved
                : ""
            }`}
            onClick={() =>
              saveApplication("saved")
            }
            disabled={saving}
          >
            <Bookmark
              size={14}
              fill={
                status === "saved"
                  ? "currentColor"
                  : "none"
              }
            />

            {status === "saved"
              ? "Save"
              : "Save"}
          </button>

          <div className={`${styles.desktopStatus} desktop-job-status`}>
            <button
              type="button"
              className={styles.desktopStatusTrigger}
              aria-expanded={desktopStatusOpen}
              aria-haspopup="listbox"
              onClick={() =>
                setDesktopStatusOpen(
                  (open) => !open,
                )
              }
              disabled={saving}
            >
              <span>{desktopStatusLabel}</span>

              <span
                className={`${styles.desktopStatusChevron} ${
                  desktopStatusOpen
                    ? styles.desktopStatusChevronOpen
                    : ""
                }`}
                aria-hidden="true"
              >
                ⌄
              </span>
            </button>

            {desktopStatusOpen && (
              <div
                className={styles.desktopStatusMenu}
                role="listbox"
                aria-label="Job Status options"
              >
                {desktopStatusOptions.map(
                  (option) => (
                    <button
                      key={option.value}
                      type="button"
                      role="option"
                      aria-selected={
                        status === option.value
                      }
                      className={`${styles.desktopStatusOption} ${
                        status === option.value
                          ? styles.desktopStatusOptionSelected
                          : ""
                      }`}
                      onClick={() => {
                        setDesktopStatusOpen(false);
                        saveApplication(
                          option.value,
                        );
                      }}
                    >
                      {option.label}
                    </button>
                  ),
                )}
              </div>
            )}
            

          </div>

          {job.job_url && (
            <div className={styles.applyAction}>
              {showApplyPrompt && (
                <div
                  className={styles.applyPrompt}
                  role="dialog"
                  aria-label="Application status"
                >
                  <div className={styles.applyPromptTitle}>
                    Did you apply for this job?
                  </div>

                  <div className={styles.applyPromptActions}>
                    <button
                      type="button"
                      onClick={onApplyConfirmed}
                    >
                      ✓ Yes, Applied
                    </button>

                    <button
                      type="button"
                      onClick={onApplyNotYet}
                    >
                      Not Yet
                    </button>

                    <button
                      type="button"
                      onClick={onApplyNotRelevant}
                    >
                      Not Relevant
                    </button>
                  </div>
                </div>
              )}

              <button
                type="button"
                className={styles.applyButton}
                onClick={() => {
                  if (!job.job_url) {
                    return;
                  }

                  setApplyAwaitingReturn(job.job_id);
                  onApplyStarted?.();

                  window.open(
                    job.job_url,
                    "_blank",
                    "noopener,noreferrer",
                  );
                }}
              >
                Apply Now
                <ExternalLink size={13} />
              </button>
            </div>
          )}

        </div>
      </div>

      <div className={styles.scoreCard}>
        <div
          className={styles.scoreRing}
          style={
            {
              "--score": `${scorePercent}%`,
            } as React.CSSProperties
          }
        >
          <div className={styles.scoreRingInner}>
            <strong>
              {roundedScore ?? "—"}
            </strong>

            {roundedScore != null && (
              <span>%</span>
            )}
          </div>
        </div>

        <div className={styles.scoreInfo}>
          <span>Overall Match Score</span>

          <strong>
            {roundedScore != null
              ? `${roundedScore}%`
              : "—"}
          </strong>

          {scoreValue != null && (
            <small>
              <Check size={10} />
              {matchLabel}
            </small>
          )}
        </div>
      </div>
    </section>
  );
}

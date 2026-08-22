"use client";

import {
  Bookmark,
  CalendarDays,
  ExternalLink,
  BriefcaseBusiness,
  Check,
} from "lucide-react";

import type { ApplicationStatus } from "@/lib/api";
import type { JobDetail } from "@/types/job";
import { formatDisplayText } from "@/lib/display";

import styles from "./JobHeader.module.css";

type Props = {
  job: JobDetail;
  score: JobDetail["score"];
  status: ApplicationStatus;
  saving: boolean;
  saveApplication: (
    nextStatus?: ApplicationStatus,
  ) => Promise<void>;
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
            <strong>
              {job.company
                ? formatDisplayText(job.company)
                : "Company unavailable"}
            </strong>

            <span>•</span>

            <span>
              {job.location
                ? formatDisplayText(job.location)
                : "Location unavailable"}
            </span>

            <span>•</span>

            <span>
              {job.job_url ? "On-site" : ""}
            </span>
          </div>

          <div className={styles.meta}>
            <span className={styles.metaPill}>
              <CalendarDays size={12} />
              {formatDate(job.posted_date)}
            </span>

            <span className={styles.metaPill}>
              {job.employment_type || "Full-time"}
            </span>

            <span className={styles.metaPill}>
              <BriefcaseBusiness size={12} />
              {formatExperience(
                job.experience_min,
                job.experience_max,
              )}
            </span>

            <span className={styles.metaPill}>
              <span className={styles.rupee}>₹</span>
              {formatSalary(
                job.salary_min,
                job.salary_max,
                job.salary_currency,
              )}
            </span>
          </div>
        </div>

        <div className={styles.actions}>
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

          {job.job_url && (
            <a
              className={styles.applyButton}
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              Apply Now
              <ExternalLink size={13} />
            </a>
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

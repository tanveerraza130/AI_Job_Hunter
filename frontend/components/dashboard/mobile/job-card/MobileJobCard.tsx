"use client";

import { useState } from "react";

import Link from "next/link";

import {
  ArrowUpRight,
  Bookmark,
  BriefcaseBusiness,
  CalendarDays,
  ChevronRight,
  MapPin,
} from "lucide-react";

import type { Job } from "@/types/job";

import MobileScore from "./MobileScore";
import styles from "./MobileJobCard.module.css";

export type MobileStatus =
  | "Not Applied"
  | "Saved"
  | "Applied"
  | "Interview"
  | "Rejected"
  | "Offer";

const experience = (
  min?: number | null,
  max?: number | null,
) => {
  if (min == null && max == null) {
    return "—";
  }

  if (min != null && max != null) {
    return `${min}–${max} Yrs`;
  }

  if (min != null) {
    return `${min}+ Yrs`;
  }

  return `Up to ${max} Yrs`;
};

const postedDate = (
  value?: string | null,
) => {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const today = new Date();

  const startToday = new Date(
    today.getFullYear(),
    today.getMonth(),
    today.getDate(),
  );

  const startDate = new Date(
    date.getFullYear(),
    date.getMonth(),
    date.getDate(),
  );

  const diff =
    startToday.getTime() -
    startDate.getTime();

  const days = Math.round(
    diff / 86400000,
  );

  if (days <= 0) return "Today";
  if (days === 1) return "1d ago";
  if (days < 7) return `${days}d ago`;

  return date.toLocaleDateString(
    "en-IN",
    {
      day: "numeric",
      month: "short",
    },
  );
};

type Props = {
  job: Job;
  index: number;
  status: MobileStatus;
  onStatusChange: (
    jobId: string,
    status: MobileStatus,
  ) => Promise<void>;
  profileId: string;
};

function MobileJobCard({
  job,
  index,
  status,
  onStatusChange,
  profileId,
}: Props) {
  const score =
    job.overall_score;

  const breakdown =
    job.score_breakdown;

  const [showMore, setShowMore] =
    useState(false);

  const matchedSkills =
    breakdown?.matched_skills ?? [];

  const matchedTools =
    (
      breakdown as
        | {
            matched_tools?: string[];
          }
        | null
        | undefined
    )?.matched_tools ?? [];

  const INITIAL_VISIBLE_SKILLS = 2;
  const INITIAL_VISIBLE_TOOLS = 2;

  const visibleSkills = showMore
    ? matchedSkills
    : matchedSkills.slice(
        0,
        INITIAL_VISIBLE_SKILLS,
      );

  const visibleTools = showMore
    ? matchedTools
    : matchedTools.slice(
        0,
        INITIAL_VISIBLE_TOOLS,
      );

  const hiddenSkillsCount =
    Math.max(
      matchedSkills.length -
        INITIAL_VISIBLE_SKILLS,
      0,
    );

  const hiddenToolsCount =
    Math.max(
      matchedTools.length -
        INITIAL_VISIBLE_TOOLS,
      0,
    );

  const remainingCount =
    hiddenSkillsCount +
    hiddenToolsCount;

  const href =
    `/jobs/${encodeURIComponent(job.job_id)}` +
    `?profile_id=${encodeURIComponent(profileId)}`;

  const company =
    job.company ||
    "Company unavailable";

  return (
    <article className={styles.jobCard}>
      <div className={styles.jobCardTop}>
        <div className={styles.jobRank}>
          {index + 1}
        </div>

        <div className={styles.jobMain}>
          <div className={styles.jobTitleRow}>
            <Link
              href={href}
              className={styles.jobTitle}
            >
              {job.title || "Untitled role"}
            </Link>

            {score != null &&
              score > 50 && (
                <span className={styles.bestMatch}>
                  BEST MATCH
                </span>
            )}
          </div>

          <div className={styles.companyName}>
            {company}
          </div>

          <div className={styles.metaRow}>
            <span>
              <BriefcaseBusiness size={13} />
              {experience(
                job.experience_min,
                job.experience_max,
              )}
            </span>

            <span>
              <MapPin size={13} />
              {job.location || "India"}
            </span>

            <span>
              <CalendarDays size={13} />
              Full-time
            </span>
          </div>
        </div>

        <button
          type="button"
          className={`${styles.bookmarkButton} ${
            status === "Saved"
              ? styles.bookmarkActive
              : ""
          }`}
          aria-label={
            status === "Saved"
              ? "Remove saved status"
              : "Save job"
          }
          onClick={() =>
            onStatusChange(
              job.job_id,
              status === "Saved"
                ? "Not Applied"
                : "Saved",
            )
          }
        >
          <Bookmark
            size={17}
            fill={
              status === "Saved"
                ? "currentColor"
                : "none"
            }
          />
        </button>
      </div>

      <div className={styles.jobCardMiddle}>
        <div className={styles.jobDetails}>
          {matchedSkills.length > 0 && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>
                Skills
              </span>

              <div className={styles.jobTags}>
                {visibleSkills.map((skill) => (
                  <span
                    key={`skill-${skill}`}
                    className={styles.skillChip}
                    title={skill}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          )}

          {matchedTools.length > 0 && (
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>
                Tools
              </span>

              <div className={styles.jobTags}>
                {visibleTools.map((tool) => (
                  <span
                    key={`tool-${tool}`}
                    className={styles.toolChip}
                    title={tool}
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}

          {remainingCount > 0 && (
            <button
              type="button"
              className={styles.moreButton}
              onClick={() =>
                setShowMore((value) => !value)
              }
              aria-expanded={showMore}
            >
              {showMore
                ? "Show less"
                : `+${remainingCount} more`}
            </button>
          )}
        </div>

        <MobileScore score={score} />
      </div>

      <div className={styles.jobCardBottom}>
        <div className={styles.jobBottomLeft}>
          <span className={styles.posted}>
            {postedDate(job.posted_date)}
          </span>

          <Link
            href={href}
            className={styles.detailsLink}
          >
            View details
            <ChevronRight size={15} />
          </Link>
        </div>

        {job.job_url && (
          <a
            href={job.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.applyButton}
          >
            Apply now
            <ArrowUpRight size={15} />
          </a>
        )}
      </div>
    </article>
  );
}

export default MobileJobCard;

"use client";

import { useEffect, useState } from "react";

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
import JobStatusPrompt from "@/features/job-status/JobStatusPrompt";
import styles from "./MobileJobCard.module.css";

export type MobileStatus =
  | "Not Applied"
  | "Saved"
  | "Pending"
  | "Applied"
  | "Interview"
  | "Rejected"
  | "Offer"
  | "Not Relevant";

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

  const [moreCount, setMoreCount] =
    useState(0);

  const [
    waitingForApplyReturn,
    setWaitingForApplyReturn,
  ] = useState(false);

  const [
    showApplyPrompt,
    setShowApplyPrompt,
  ] = useState(false);

  useEffect(() => {
    if (!waitingForApplyReturn) {
      return;
    }

    const handleReturn = () => {
      if (document.visibilityState === "visible") {
        setShowApplyPrompt(true);
      }
    };

    window.addEventListener("focus", handleReturn);
    document.addEventListener(
      "visibilitychange",
      handleReturn,
    );

    return () => {
      window.removeEventListener(
        "focus",
        handleReturn,
      );
      document.removeEventListener(
        "visibilitychange",
        handleReturn,
      );
    };
  }, [waitingForApplyReturn]);

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

  const visibleSkills =
    matchedSkills.slice(
      0,
      INITIAL_VISIBLE_SKILLS +
        Math.min(moreCount, 3),
    );

  const visibleTools =
    matchedTools.slice(
      0,
      INITIAL_VISIBLE_TOOLS +
        Math.max(
          0,
          Math.min(
            moreCount -
              Math.max(
                matchedSkills.length -
                  INITIAL_VISIBLE_SKILLS,
                0,
              ),
            3,
          ),
        ),
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

  const totalHiddenCount =
    hiddenSkillsCount +
    hiddenToolsCount;

  const revealedCount =
    Math.min(
      moreCount,
      3,
      totalHiddenCount,
    );

  const remainingCount =
    Math.max(
      totalHiddenCount -
        revealedCount,
      0,
    );

  const href =
    `/jobs/${encodeURIComponent(job.job_id)}` +
    `?profile_id=${encodeURIComponent(profileId)}`;

  const company =
    job.company
      ? job.company
          .toLowerCase()
          .replace(/\b\w/g, (char) =>
            char.toUpperCase(),
          )
      : "Company unavailable";

  return (
    <article className={styles.jobCard}>
      <div className={styles.jobCardTop}>
        <div className={styles.jobCardTopLeft}>
          <div className={styles.jobRank}>
            {index + 1}
          </div>

          {score != null &&
            score > 50 && (
              <span className={styles.bestMatch}>
                BEST MATCH
              </span>
          )}
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

      <div className={styles.jobMain}>
        <div className={styles.jobTitleRow}>
          <Link
            href={href}
            className={styles.jobTitle}
          >
            {job.title || "Untitled role"}
          </Link>
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

      <section className={styles.jobCardMatchSection}>
        <div className={styles.jobCardMatchDetails}>
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

          {remainingCount > 0 &&
            moreCount < 3 && (
              <button
                type="button"
                className={styles.moreButton}
                onClick={() =>
                  setMoreCount((value) =>
                    Math.min(value + 1, 3),
                  )
                }
                aria-expanded={moreCount > 0}
              >
                +{remainingCount} more
              </button>
            )}
        </div>

        <div className={styles.jobCardMatchScore}>
          <MobileScore score={score} />
        </div>
      </section>

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
          <button
            type="button"
            className={styles.applyButton}
            onClick={(event) => {
              event.preventDefault();

              const applyUrl = job.job_url;

              if (!applyUrl) {
                return;
              }

              onStatusChange(
                job.job_id,
                "Pending",
              );

              window.open(
                applyUrl,
                "_blank",
                "noopener,noreferrer",
              );

              setWaitingForApplyReturn(true);
            }}
          >
            Apply now
            <ArrowUpRight size={15} />
          </button>
        )}
      </div>

      {showApplyPrompt && (
        <JobStatusPrompt
          onApplied={() => {
            onStatusChange(
              job.job_id,
              "Applied",
            );
            setShowApplyPrompt(false);
            setWaitingForApplyReturn(false);
          }}
          onNotYet={() => {
            onStatusChange(
              job.job_id,
              "Pending",
            );
            setShowApplyPrompt(false);
            setWaitingForApplyReturn(false);
          }}
          onNotRelevant={() => {
            onStatusChange(
              job.job_id,
              "Not Relevant",
            );
            setShowApplyPrompt(false);
            setWaitingForApplyReturn(false);
          }}
        />
      )}
    </article>
  );
}

export default MobileJobCard;

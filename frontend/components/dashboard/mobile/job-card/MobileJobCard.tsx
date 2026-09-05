"use client";

import { useEffect, useState } from "react";
import {
  getApplyReturnState,
  markApplyReturned,
  setApplyAwaitingReturn,
  clearApplyReturnState,
} from "@/lib/applyReturnState";

import Link from "next/link";

import {
  ArrowUpRight,
  Bookmark,
  BriefcaseBusiness,
  CalendarDays,
  ChevronDown,
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
  onJobOpen: (jobId?: string) => void;
};

function MobileJobCard({
  job,
  index,
  status,
  onStatusChange,
  profileId,
  onJobOpen,
}: Props) {
  const [statusOpen, setStatusOpen] = useState(false);

  const statusOptions: MobileStatus[] = [
    "Not Applied",
    "Saved",
    "Pending",
    "Applied",
    "Interview",
    "Offer",
    "Rejected",
    "Not Relevant",
  ];

  const statusLabel =
    status === "Pending"
      ? "Application Pending"
      : status;

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
    function checkApplyReturn() {
      if (document.visibilityState !== "visible") {
        return;
      }

      const shared = getApplyReturnState();

      if (!shared || shared.jobId !== String(job.job_id)) {
        return;
      }

      if (shared.promptRequired) {
        setShowApplyPrompt(true);
        setWaitingForApplyReturn(true);
        return;
      }

      if (shared.awaitingReturn) {
        const returned = markApplyReturned();

        if (
          returned?.jobId === String(job.job_id) &&
          returned.promptRequired
        ) {
          setShowApplyPrompt(true);
          setWaitingForApplyReturn(true);
        }
      }
    }

    function handleReturn() {
      checkApplyReturn();
    }

    checkApplyReturn();

    window.addEventListener("focus", handleReturn);
    window.addEventListener("pageshow", handleReturn);
    document.addEventListener(
      "visibilitychange",
      handleReturn,
    );

    return () => {
      window.removeEventListener("focus", handleReturn);
      window.removeEventListener("pageshow", handleReturn);
      document.removeEventListener(
        "visibilitychange",
        handleReturn,
      );
    };
  }, [job.job_id]);

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
    <article
      className={styles.jobCard}
      data-job-id={job.job_id}
    >
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
            onClick={() => onJobOpen(job.job_id)}
          >
            {job.title || "Untitled role"}
          </Link>
        </div>

        <div className={styles.companyName}>
          {company}
        </div>

        <div className={styles.metaRow}>
          <span>
            <BriefcaseBusiness
              size={13}
              style={{ color: "#2563eb" }}
            />
            {experience(
              job.experience_min,
              job.experience_max,
            )}
          </span>

          <span>
            <MapPin
              size={13}
              style={{ color: "#ef4444" }}
            />
            {job.location || "India"}
          </span>

          <span>
            <BriefcaseBusiness
              size={13}
              style={{ color: "#7c3aed" }}
            />
            Full-time
          </span>

          <span>
            <CalendarDays
              size={13}
              style={{ color: "#16a34a" }}
            />
            {postedDate(job.posted_date)}
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
        <Link
          href={href}
          className={styles.detailsLink}
          onClick={() => onJobOpen(job.job_id)}
        >
          Job Details
          <ChevronRight size={14} />
        </Link>

        <div className={styles.statusControl}>
          <button
            type="button"
            className={styles.statusButton}
            aria-expanded={statusOpen}
            aria-haspopup="listbox"
            onClick={() =>
              setStatusOpen((open) => !open)
            }
          >
            <span>{statusLabel}</span>
            <ChevronDown
              size={13}
              className={
                statusOpen
                  ? styles.statusChevronOpen
                  : ""
              }
            />
          </button>

          {statusOpen && (
            <div
              className={styles.statusMenu}
              role="listbox"
              aria-label="Job Status"
            >
              {statusOptions.map((option) => (
                <button
                  key={option}
                  type="button"
                  role="option"
                  aria-selected={status === option}
                  className={`${styles.statusOption} ${
                    status === option
                      ? styles.statusOptionSelected
                      : ""
                  }`}
                  onClick={async () => {
                    setStatusOpen(false);
                    await onStatusChange(
                      job.job_id,
                      option,
                    );
                  }}
                >
                  {option === "Pending"
                    ? "Application Pending"
                    : option}
                </button>
              ))}
            </div>
          )}
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

              setApplyAwaitingReturn(job.job_id);
              setWaitingForApplyReturn(true);
            }}
          >
            Apply Now
            <ArrowUpRight size={14} />
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
            clearApplyReturnState();
          }}
          onNotYet={() => {
            onStatusChange(
              job.job_id,
              "Pending",
            );
            setShowApplyPrompt(false);
            setWaitingForApplyReturn(false);
            clearApplyReturnState();
          }}
          onNotRelevant={() => {
            onStatusChange(
              job.job_id,
              "Not Relevant",
            );
            setShowApplyPrompt(false);
            setWaitingForApplyReturn(false);
            clearApplyReturnState();
          }}
        />
      )}
    </article>
  );
}

export default MobileJobCard;

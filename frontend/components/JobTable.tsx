"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowUpRight,
  Bookmark,
  BriefcaseBusiness,
  CalendarDays,
  MapPin,
} from "lucide-react";
import { getApplicationsBulk, updateApplication } from "@/lib/api";
import type { Job } from "@/types/job";
import { formatDisplayText } from "@/lib/display";

type ApplicationStatus =
  | "Not Applied"
  | "Saved"
  | "Applied"
  | "Interview"
  | "Rejected"
  | "Offer";

interface Props {
  jobs: Job[];
  profileId: string;
}

const displayStatus = (status?: string): ApplicationStatus => {
  if (status === "saved") return "Saved";
  if (status === "applied") return "Applied";
  if (status === "interview") return "Interview";
  if (status === "rejected") return "Rejected";
  if (status === "offer") return "Offer";
  return "Not Applied";
};

const apiStatus = (status: ApplicationStatus) =>
  status === "Applied"
    ? "applied"
    : status === "Interview"
      ? "interview"
      : status === "Rejected"
        ? "rejected"
        : status === "Offer"
          ? "offer"
          : "saved";

const formatDate = (value?: string | null) => {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Date unavailable";

  return date.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};

const experience = (
  min?: number | null,
  max?: number | null,
) => {
  if (min == null && max == null) return "Experience not disclosed";
  if (min != null && max != null) return `${min}–${max} yrs`;
  if (min != null) return `${min}+ yrs`;
  return `Up to ${max} yrs`;
};

const salary = (
  min?: number | null,
  max?: number | null,
  currency?: string | null,
) => {
  if (min == null && max == null) return "Salary not disclosed";

  const symbol = currency || "₹";
  const format = (value: number) =>
    new Intl.NumberFormat("en-IN", {
      maximumFractionDigits: 0,
    }).format(value);

  if (min != null && max != null) {
    return `${symbol}${format(min)} – ${symbol}${format(max)}`;
  }

  if (min != null) return `From ${symbol}${format(min)}`;
  return `Up to ${symbol}${format(max as number)}`;
};

const scoreClass = (score: number | null) => {
  if (score == null) return "mj-score mj-score-neutral";
  if (score >= 85) return "mj-score mj-score-high";
  if (score >= 70) return "mj-score mj-score-good";
  if (score >= 50) return "mj-score mj-score-mid";
  return "mj-score mj-score-low";
};

function ScoreMetric({
  label,
  value,
}: {
  label: string;
  value: number | null | undefined;
}) {
  const numericValue =
    value == null
      ? 0
      : Math.max(
          0,
          Math.min(100, Number(value)),
        );

  return (
    <div className="mj-score-metric">
      <span className="mj-score-metric-label">
        {label}
      </span>

      <strong className="mj-score-metric-value">
        {value == null
          ? "—"
          : `${Math.round(numericValue)}%`}
      </strong>

      <div
        className="mj-score-progress"
        aria-hidden="true"
      >
        <div
          className="mj-score-progress-fill"
          style={{
            width: `${numericValue}%`,
          }}
        />
      </div>
    </div>
  );
}

export default function JobTable({ jobs, profileId }: Props) {
  const [statusMap, setStatusMap] = useState<
    Record<string, ApplicationStatus>
  >({});
  const [filter, setFilter] = useState<
    "ALL" | "Saved" | "Applied" | "Interview"
  >("ALL");

  useEffect(() => {
    let cancelled = false;

    async function loadApplications() {
      if (!jobs.length || !profileId) {
        setStatusMap({});
        return;
      }

      try {
        const response =
          await getApplicationsBulk(
            jobs.map(
              (job) =>
                job.job_id,
            ),
            profileId,
          );

        if (cancelled) {
          return;
        }

        const next: Record<
          string,
          ApplicationStatus
        > = {};

        Object.entries(
          response.applications ||
            {},
        ).forEach(
          ([
            jobId,
            application,
          ]) => {
            next[jobId] =
              displayStatus(
                application.status,
              );
          },
        );

        setStatusMap(next);
      } catch {
        if (!cancelled) {
          setStatusMap({});
        }
      }
    }

    loadApplications();

    return () => {
      cancelled = true;
    };
  }, [jobs, profileId]);

  async function updateStatus(
    jobId: string,
    status: ApplicationStatus,
  ) {
    try {
      await updateApplication(jobId, {
        profile_id: profileId,
        status: apiStatus(status) as never,
      });

      setStatusMap((current) => ({
        ...current,
        [jobId]: status,
      }));
    } catch (error) {
      console.error(
        "Failed to update application status:",
        error,
      );
    }
  }

  const filtered = jobs.filter((job) => {
    if (filter === "ALL") return true;
    return (statusMap[job.job_id] || "Not Applied") === filter;
  });

  if (!jobs.length) {
    return (
      <div className="mj-empty">
        <div className="mj-empty-icon">⌕</div>
        <strong>No matching jobs found</strong>
        <span>Try changing your search or filters.</span>
      </div>
    );
  }

  return (
    <section className="mj-wrapper">

      <div className="mj-tabs">
        {(["ALL", "Saved", "Applied", "Interview"] as const).map(
          (value) => (
            <button
              key={value}
              type="button"
              onClick={() => setFilter(value)}
              className={
                filter === value
                  ? "mj-tab mj-tab-active"
                  : "mj-tab"
              }
            >
              {value === "ALL"
                ? `All (${jobs.length})`
                : value}
            </button>
          ),
        )}
      </div>

      <div className="mj-list">
        {filtered.map((job, index) => {
          const score = job.overall_score;
          const breakdown = job.score_breakdown;

          const skills = (
            breakdown?.matched_skills?.length
              ? breakdown.matched_skills
              : job.skills || []
          )
            .filter(Boolean)
            .slice(0, 6);

          const tools = (breakdown?.matched_tools || [])
            .filter(Boolean)
            .slice(0, 5);

          const totalSkills =
            breakdown?.matched_skills?.length ||
            job.skills?.length ||
            0;

          const totalTools =
            breakdown?.matched_tools?.length || 0;

          const status =
            statusMap[job.job_id] || "Not Applied";

          const href =
            `/jobs/${encodeURIComponent(job.job_id)}` +
            `?profile_id=${encodeURIComponent(profileId)}`;

          return (
            <article className="mj-card" key={job.job_id}>
              <div className="mj-job-details">
                <div className="mj-rank">
                  {String(index + 1).padStart(2, "0")}
                </div>

                <div className="mj-content">
                <div className="mj-title-row">
                  <Link href={href} className="mj-title">
                    {formatDisplayText(job.title)}
                  </Link>

                  {score != null && score > 50 && (
                    <span className="mj-best">
                      BEST MATCH
                    </span>
                  )}
                </div>

                <div className="mj-company">
                  {job.company
                    ? formatDisplayText(job.company)
                    : "Company unavailable"}
                </div>

                <div className="mj-meta">
                  <span>
                    <MapPin size={14} />
                    {job.location ? formatDisplayText(job.location) : "Location unavailable"}
                  </span>

                  <span>
                    <BriefcaseBusiness size={14} />
                    {experience(
                      job.experience_min,
                      job.experience_max,
                    )}
                  </span>

                  <span>
                    {salary(
                      job.salary_min,
                      job.salary_max,
                      job.salary_currency,
                    )}
                  </span>

                  <span>
                    <CalendarDays size={14} />
                    {formatDate(job.posted_date)}
                  </span>
                </div>

                <div className="mj-evidence">
                  <div className="mj-evidence-row">
                    <span className="mj-label">
                      SKILLS
                    </span>

                    <div className="mj-chips">
                      {skills.map((skill) => (
                        <span
                          className="mj-chip mj-chip-skill"
                          key={skill}
                        >
                          {formatDisplayText(skill)}
                        </span>
                      ))}

                      {totalSkills > skills.length && (
                        <span className="mj-more">
                          +{totalSkills - skills.length}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mj-evidence-row">
                    <span className="mj-label">
                      TOOLS
                    </span>

                    <div className="mj-chips">
                      {tools.map((tool) => (
                        <span
                          className="mj-chip mj-chip-tool"
                          key={tool}
                        >
                          {formatDisplayText(tool)}
                        </span>
                      ))}

                      {totalTools > tools.length && (
                        <span className="mj-more">
                          +{totalTools - tools.length}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
              </div>

              <div className="mj-score-panel">

                {/* SCORE SUMMARY */}
                <div className="mj-score-summary">
                  <div
                    className={scoreClass(score)}
                    aria-label={`AI Match ${
                      score != null
                        ? `${Math.round(score)}%`
                        : "not available"
                    }`}
                  >
                    <strong>
                      {score != null
                        ? Math.round(score)
                        : "—"}
                    </strong>

                    {score != null && (
                      <span>%</span>
                    )}
                  </div>

                  <span className="mj-score-label">
                    AI MATCH
                  </span>
                </div>

                {/* SCORE BREAKDOWN */}
                <div className="mj-score-breakdown">

                  <div className="mj-breakdown-title">
                    SCORE BREAKDOWN
                  </div>

                  <div className="mj-score-metrics">

                    <ScoreMetric
                      label="Skills Match"
                      value={job.skill_score}
                    />

                    <ScoreMetric
                      label="Tools Match"
                      value={job.tool_score}
                    />

                    <ScoreMetric
                      label="JD Match"
                      value={
                        breakdown?.jd_match ?? 0
                      }
                    />

                  </div>

                  <div className="mj-score-overall">
                    <span>
                      Overall Score
                    </span>

                    <strong>
                      {score != null
                        ? `${Math.round(score)}%`
                        : "—"}
                    </strong>
                  </div>

                </div>

              </div>

              <div className="mj-actions">
                <button
                  type="button"
                  className={
                    status === "Saved"
                      ? "mj-save mj-save-active"
                      : "mj-save"
                  }
                  title={
                    status === "Saved"
                      ? "Saved"
                      : "Save job"
                  }
                  onClick={() =>
                    updateStatus(job.job_id, "Saved")
                  }
                >
                  <Bookmark
                    size={15}
                    fill={
                      status === "Saved"
                        ? "currentColor"
                        : "none"
                    }
                  />
                </button>

                <select
                  value={status}
                  onChange={(event) =>
                    updateStatus(
                      job.job_id,
                      event.target.value as ApplicationStatus,
                    )
                  }
                  className="mj-status"
                  aria-label={`Application status for ${job.title}`}
                >
                  <option value="Not Applied">
                    Not Applied
                  </option>
                  <option value="Saved">Saved</option>
                  <option value="Applied">
                    Applied
                  </option>
                  <option value="Interview">
                    Interview
                  </option>
                  <option value="Rejected">
                    Rejected
                  </option>
                  <option value="Offer">Offer</option>
                </select>

                <Link
                  href={href}
                  className="mj-details"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View details
                  <ArrowUpRight size={14} />
                </Link>

                {job.job_url && (
                  <a
                    className="mj-apply"
                    href={job.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Apply now
                    <ArrowUpRight size={15} />
                  </a>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

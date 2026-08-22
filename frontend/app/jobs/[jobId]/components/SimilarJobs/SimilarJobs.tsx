"use client";

import { useEffect, useState } from "react";
import { getJobs } from "@/lib/api";
import type { Job } from "@/types/job";
import styles from "./SimilarJobs.module.css";

type Props = {
  currentJob: Job;
  profileId: string;
};

export default function SimilarJobs({
  currentJob,
  profileId,
}: Props) {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await getJobs({
          page: 1,
          page_size: 8,
          profile_id: profileId,
          min_score: 30,
          company: currentJob.company || undefined,
          sort: "score",
        });

        if (!cancelled) {
          setJobs(
            response.jobs
              .filter((job) => job.job_id !== currentJob.job_id)
              .slice(0, 4),
          );
        }
      } catch {
        if (!cancelled) {
          setJobs([]);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [currentJob.company, currentJob.job_id, profileId]);

  if (!jobs.length) {
    return null;
  }

  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <div>
          <span className={styles.eyebrow}>KEEP EXPLORING</span>
          <h2>Similar Jobs</h2>
        </div>

        <span className={styles.count}>
          {jobs.length} recommendations
        </span>
      </div>

      <div className={styles.grid}>
        {jobs.map((job) => (
          <a
            key={job.job_id}
            href={`/jobs/${encodeURIComponent(job.job_id)}`}
            className={styles.card}
          >
            <div className={styles.score}>
              {job.overall_score != null
                ? `${Math.round(job.overall_score)}%`
                : "—"}
            </div>

            <div className={styles.content}>
              <h3>{job.title}</h3>
              <p>{job.company}</p>
              <span>
                {job.location || "Location not disclosed"}
              </span>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
}

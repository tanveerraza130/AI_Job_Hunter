"use client";

import { use, useEffect, useMemo, useState } from "react";
import JobHeader from "./components/JobHeader/JobHeader";
import MatchSnapshot from "./components/MatchSnapshot/MatchSnapshot";
import JobDescription from "./components/JobDescription/JobDescription";
import Responsibilities from "./components/Responsibilities/Responsibilities";
import Requirements from "./components/Requirements/Requirements";
import Company from "./components/Company/Company";
import SimilarJobs from "./components/SimilarJobs/SimilarJobs";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { getApplication, getJobDetail, getMyProfile, updateApplication } from "@/lib/api";
import type { ApplicationStatus } from "@/lib/api";
import type { JobDetail, ScoreBreakdown } from "@/types/job";

function date(value?: string | null) { if (!value) return "Not disclosed"; const d = new Date(value); return Number.isNaN(d.getTime()) ? "Not disclosed" : d.toLocaleDateString("en-IN", { day:"numeric", month:"short", year:"numeric" }); }
function salary(min?: number | null,max?: number | null,currency?: string|null){if(min==null&&max==null)return"Salary not disclosed";const s=currency||"₹",f=(v:number)=>new Intl.NumberFormat("en-IN").format(v);if(min!=null&&max!=null)return`${s}${f(min)} – ${s}${f(max)}`;return min!=null?`From ${s}${f(min)}`:`Up to ${s}${f(max as number)}`;}
function experience(min?:number|null,max?:number|null){if(min==null&&max==null)return"Not disclosed";if(min!=null&&max!=null)return`${min}–${max} years`;return min!=null?`${min}+ years`:`Up to ${max} years`;}
function splitDescription(text?:string|null){
  if(!text) return ["No job description available."];
  const normalized = text.replace(/<br\s*\/?\s*>/gi,"\n").replace(/<\/li>/gi,"\n").replace(/<\/p>/gi,"\n").replace(/<\/(ul|ol)>/gi,"\n");
  if(typeof window !== "undefined") { const div=document.createElement("div"); div.innerHTML=normalized; return (div.textContent||"").replace(/\r/g,"").split(/\n+/).map(s=>s.replace(/\s+/g," ").trim()).filter(Boolean); }
  return normalized.replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim().split(/\n+/).filter(Boolean);
}
export default function JobDetailPage({ params }:{params:Promise<{jobId:string}>}){
  const {jobId}=use(params);
  const [profileId,setProfileId]=useState<string | null>(null);
  const [job,setJob]=useState<JobDetail|null>(null); const [loading,setLoading]=useState(true); const [error,setError]=useState<string|null>(null);
  const [status,setStatus]=useState<ApplicationStatus>("saved");
  const [openMobileSection, setOpenMobileSection] =
    useState<string | null>(null);

  function toggleMobileSection(section: string) {
    setOpenMobileSection((current) =>
      current === section ? null : section,
    );
  }
 const [notes,setNotes]=useState(""); const [saving,setSaving]=useState(false);
  useEffect(() => {
    let cancelled = false;

    async function loadJob() {
      try {
        setLoading(true);
        setError(null);

        const token = localStorage.getItem("ai_job_hunter_token");

        if (!token) {
          window.location.href = "/login";
          return;
        }

        /*
         * SECURITY / CONSISTENCY RULE:
         *
         * The authenticated user's saved profile is the
         * ONLY source of truth.
         *
         * Never use:
         * - URL profile_id
         * - client-selected profile
         * - hardcoded profile fallback
         */
        const profileResponse = await getMyProfile(token);

        if (cancelled) return;

        const authenticatedProfile =
          profileResponse.profile?.profile_id?.trim();

        if (!authenticatedProfile) {
          throw new Error(
            "Your account does not have an assigned job profile.",
          );
        }

        setProfileId(authenticatedProfile);

        const data = await getJobDetail(
          decodeURIComponent(jobId),
          authenticatedProfile,
        );

        if (cancelled) return;

        setJob(data);

        try {
          const application = await getApplication(
            data.job_id,
            authenticatedProfile,
          );

          if (application.application) {
            setStatus(application.application.status);
            setNotes(application.application.notes || "");
          }
        } catch (applicationError) {
          console.error(
            "Failed to load application status:",
            applicationError,
          );
        }
      } catch (loadError) {
        console.error(
          "Failed to load authenticated job detail:",
          loadError,
        );

        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Unable to load this job.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadJob();

    return () => {
      cancelled = true;
    };
  }, [jobId]);
  async function saveApplication(nextStatus:ApplicationStatus=status){if(!job||!profileId||saving)return;try{setSaving(true);const r=await updateApplication(job.job_id,{profile_id:profileId,status:nextStatus,applied_at:nextStatus==="applied"?new Date().toISOString():undefined,notes});setStatus(r.application.status);setNotes(r.application.notes||"");}catch(e){console.error(e);setError("Unable to save application changes.");}finally{setSaving(false);}}
  const score=job?.score; const breakdown:ScoreBreakdown|null=score?.score_breakdown??job?.score_breakdown??null; const paragraphs=useMemo(()=>splitDescription(job?.description),[job?.description]);
  if (loading || !profileId) {
    return (
      <main className="detail-shell">
        <div className="loading-panel">
          Loading job details…
        </div>
      </main>
    );
  }
  if(error||!job)return <main className="detail-shell"><div className="error-card"><h2>{error||"Job not found"}</h2><Link className="apply-now" href="/">Back to jobs</Link></div></main>;
  return (
    <main className="detail-shell">
      <Link href="/" className="back-link">
        <ArrowLeft size={15} />
        Back to jobs
      </Link>

      <JobHeader
        job={job}
        score={score}
        status={status}
        saving={saving}
        saveApplication={saveApplication}
      />

      <div className="job-detail-layout">
        <div className="job-detail-main">
          <MatchSnapshot
            job={job}
            score={score}
            breakdown={breakdown}
          />

          <div className="approved-job-content">

            <nav className="approved-job-tabs" aria-label="Job sections">
              <a className="approved-job-tab active" href="#about-role">
                Overview
              </a>

              <a className="approved-job-tab" href="#responsibilities">
                Responsibilities
              </a>

              <a className="approved-job-tab" href="#requirements">
                Requirements
              </a>

              <a className="approved-job-tab" href="#about-company">
                About Company
              </a>

              <a className="approved-job-tab" href="#match-breakdown">
                Match Breakdown
              </a>

              <a className="approved-job-tab" href="#similar-jobs">
                Similar Jobs
              </a>
            </nav>

            <div className="approved-job-content-body">

              <section
                id="about-role"
                className="approved-job-section approved-about-role"
              >
                <button
                  type="button"
                  className="approved-section-heading mobile-job-accordion-trigger"
                  aria-expanded={openMobileSection === "about-role"}
                  onClick={() => toggleMobileSection("about-role")}
                >
                  <div className="approved-section-icon">
                    ▣
                  </div>

                  <div>
                    <h2>About the Role</h2>
                    <p>
                      A concise overview of the opportunity, scope and expectations.
                    </p>
                  </div>
                </button>

                <div
                  className={`mobile-job-accordion-content ${
                    openMobileSection === "about-role"
                      ? "is-open"
                      : ""
                  }`}
                >
                  <div className="approved-component-content">
                    <JobDescription
                      paragraphs={paragraphs}
                    />
                  </div>
                </div>
              </section>

              <section
                id="responsibilities"
                className="approved-job-section"
              >
                <button
                  type="button"
                  className="approved-section-heading mobile-job-accordion-trigger"
                  aria-expanded={openMobileSection === "responsibilities"}
                  onClick={() => toggleMobileSection("responsibilities")}
                >
                  <div className="approved-section-icon">
                    ▧
                  </div>

                  <div>
                    <h2>Key Responsibilities</h2>
                  </div>
                </button>

                <div
                  className={`mobile-job-accordion-content ${
                    openMobileSection === "responsibilities"
                      ? "is-open"
                      : ""
                  }`}
                >
                  <div className="approved-component-content">
                    <Responsibilities
                      paragraphs={paragraphs}
                    />
                  </div>
                </div>
              </section>

              <section
                id="requirements"
                className="approved-job-section"
              >
                <button
                  type="button"
                  className="approved-section-heading mobile-job-accordion-trigger"
                  aria-expanded={openMobileSection === "requirements"}
                  onClick={() => toggleMobileSection("requirements")}
                >
                  <div className="approved-section-icon">
                    ♜
                  </div>

                  <div>
                    <h2>Key Requirements</h2>
                  </div>
                </button>

                <div
                  className={`mobile-job-accordion-content ${
                    openMobileSection === "requirements"
                      ? "is-open"
                      : ""
                  }`}
                >
                  <div className="approved-component-content">
                    <Requirements
                      job={job}
                      breakdown={breakdown}
                    />
                  </div>
                </div>
              </section>

              <div className="approved-content-divider" />

              <section
                id="about-company"
                className="approved-job-section approved-company-section"
              >
                <button
                  type="button"
                  className="approved-section-heading mobile-job-accordion-trigger"
                  aria-expanded={openMobileSection === "about-company"}
                  onClick={() => toggleMobileSection("about-company")}
                >
                  <div className="approved-section-icon">
                    ▣
                  </div>

                  <div>
                    <h2>About Company</h2>
                  </div>
                </button>

                <div
                  className={`mobile-job-accordion-content ${
                    openMobileSection === "about-company"
                      ? "is-open"
                      : ""
                  }`}
                >
                  <div className="approved-component-content">
                    <Company
                      job={job}
                    />
                  </div>
                </div>
              </section>

            </div>
          </div>
        </div>

        <aside className="job-detail-sidebar">
          <section className="detail-side-card">
            <div className="detail-side-heading">
              <span className="detail-side-icon">✦</span>
              <div>
                <h3>Job Highlights</h3>
              </div>
            </div>

            <div className="highlight-item">
              <strong>High match with your profile</strong>
              <span>
                Your skills match {Math.round(score?.overall_score ?? 0)}%
                of requirements
              </span>
            </div>
          </section>

          <section className="detail-side-card match-breakdown-card">
            <button
              type="button"
              className="detail-side-heading mobile-sidebar-accordion-trigger"
              aria-expanded={openMobileSection === "match-breakdown"}
              onClick={() =>
                toggleMobileSection("match-breakdown")
              }
            >
              <span className="detail-side-icon">◉</span>
              <h3>Match Score Breakdown</h3>
            </button>

            <div
              className={`mobile-sidebar-accordion-content ${
                openMobileSection === "match-breakdown"
                  ? "is-open"
                  : ""
              }`}
            >
              <div className="score-breakdown-layout">
              <div className="score-breakdown-donut">
                <div className="score-breakdown-donut-inner">
                  <strong>
                    {score?.overall_score != null
                      ? Math.round(score.overall_score)
                      : "—"}
                  </strong>
                  <span>%</span>
                </div>
              </div>

              <div className="score-breakdown-metrics">

                <ScoreBar
                  label="Skills Match"
                  value={score?.skill_score ?? 0}
                  className="score-green"
                />

                <ScoreBar
                  label="Tools Match"
                  value={score?.tool_score ?? 0}
                  className="score-blue"
                />

                <ScoreBar
                  label="Title Match"
                  value={breakdown?.title_match ?? 0}
                  className="score-purple"
                />

                <ScoreBar
                  label="JD Match"
                  value={breakdown?.jd_match ?? 0}
                  className="score-orange"
                />

              </div>
              </div>
            </div>
          </section>

          <section className="detail-side-card">
            <button
              type="button"
              className="detail-side-heading mobile-sidebar-accordion-trigger"
              aria-expanded={openMobileSection === "job-details"}
              onClick={() =>
                toggleMobileSection("job-details")
              }
            >
              <span className="detail-side-icon">▣</span>
              <h3>Job Details</h3>
            </button>

            <div
              className={`mobile-sidebar-accordion-content ${
                openMobileSection === "job-details"
                  ? "is-open"
                  : ""
              }`}
            >
              <div className="job-detail-meta">
              <div>
                <span>Job</span>
                <strong>{job.job_id}</strong>
              </div>

              <div>
                <span>Posted Date</span>
                <strong>{date(job.posted_date)}</strong>
              </div>

              <div>
                <span>Job Type</span>
                <strong>{job.employment_type || "Not disclosed"}</strong>
              </div>

              <div>
                <span>Experience</span>
                <strong>
                  {experience(job.experience_min, job.experience_max)}
                </strong>
              </div>

              <div>
                <span>Work Mode</span>
                <strong>
                  {"Not disclosed"}
                </strong>
              </div>

              <div>
                <span>Salary Range</span>
                <strong>
                  {salary(
                    job.salary_min,
                    job.salary_max,
                    job.salary_currency,
                  )}
                </strong>
              </div>

              <div>
                <span>Location</span>
                <strong>
                  {job.location || "Not disclosed"}
                </strong>
              </div>
              </div>
            </div>
          </section>

          <section className="detail-side-card share-card">
            <h3>Share this job</h3>

            <div className="share-actions">
              <button type="button" aria-label="Copy job link">↗</button>
              <button type="button" aria-label="Share on LinkedIn">in</button>
              <button type="button" aria-label="Share on X">𝕏</button>
              <button type="button" aria-label="Share on WhatsApp">◉</button>
              <button type="button" aria-label="Share by email">@</button>
            </div>
          </section>
        </aside>
      </div>

      <SimilarJobs
        currentJob={job}
        profileId={profileId}
      />

      <div className="mobile-bottom-actions">
        <button type="button" aria-label="Share job">
          ↗
        </button>

        {job.job_url && (
          <a
            href={job.job_url}
            target="_blank"
            rel="noreferrer"
          >
            Apply Now ↗
          </a>
        )}

        <button
          type="button"
          aria-label="Save job"
          onClick={() => saveApplication("saved")}
          disabled={saving}
        >
          ♡
        </button>
      </div>
    </main>
  );
}

function ScoreBar({label,value,className=""}:{label:string;value:number;className?:string}){const v=Math.max(0,Math.min(100,Number(value)||0));return <div className={`scorebar ${className}`}><div><span>{label}</span><b>{v.toFixed(0)}%</b></div><i><em style={{width:`${v}%`}}/></i></div>}

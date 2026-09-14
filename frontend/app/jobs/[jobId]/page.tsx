"use client";

import { useRouter } from "next/navigation";
import { use, useEffect, useMemo, useRef, useState } from "react";
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
import {
  publishApplicationStatus,
  subscribeApplicationStatus,
} from "@/lib/applicationStatusSync";
import {
  getApplyReturnState,
  markApplyReturned,
  setApplyAwaitingReturn,
  clearApplyReturnState,
} from "@/lib/applyReturnState";

function date(value?: string | null) { if (!value) return "Not disclosed"; const d = new Date(value); return Number.isNaN(d.getTime()) ? "Not disclosed" : d.toLocaleDateString("en-IN", { day:"numeric", month:"short", year:"numeric" }); }
function salary(min?: number | null,max?: number | null,currency?: string|null){if(min==null&&max==null)return"Salary not disclosed";const s=currency||"₹",f=(v:number)=>new Intl.NumberFormat("en-IN").format(v);if(min!=null&&max!=null)return`${s}${f(min)} – ${s}${f(max)}`;return min!=null?`From ${s}${f(min)}`:`Up to ${s}${f(max as number)}`;}
function experience(min?:number|null,max?:number|null){if(min==null&&max==null)return"Not disclosed";if(min!=null&&max!=null)return`${min}–${max} years`;return min!=null?`${min}+ years`:`Up to ${max} years`;}
function splitDescription(text?:string|null){
  if(!text) return ["No job description available."];
  const normalized = text.replace(/<br\s*\/?\s*>/gi,"\n").replace(/<\/li>/gi,"\n").replace(/<\/p>/gi,"\n").replace(/<\/(ul|ol)>/gi,"\n");
  if(typeof window !== "undefined") { const div=document.createElement("div"); div.innerHTML=normalized; return (div.textContent||"").replace(/\r/g,"").split(/\n+/).map(s=>s.replace(/\s+/g," ").trim()).filter(Boolean); }
  return normalized.replace(/<[^>]+>/g," ").replace(/\s+/g," ").trim().split(/\n+/).filter(Boolean);
}
export default function JobDetailPage({
  params,
}: {
  params: Promise<{ jobId: string }>;
}) {
  const router = useRouter();
  const {jobId}=use(params);

  const [profileId,setProfileId]=useState<string | null>(null);
  const [job,setJob]=useState<JobDetail|null>(null); const [loading,setLoading]=useState(true); const [error,setError]=useState<string|null>(null);
  const [status, setStatus] =
    useState<ApplicationStatus | "not_applied">(
      "not_applied",
    );

  /*
   * Keep Job Details synchronized with Dashboard and other
   * status-changing surfaces in the same browser tab.
   */
  useEffect(() => {
    if (!job?.job_id) return;

    return subscribeApplicationStatus((event) => {
      if (
        String(event.jobId) !==
        String(job.job_id)
      ) {
        return;
      }

      if (event.status === "not_applied") {
        setStatus("not_applied");
        setNotes("");
        return;
      }

      setStatus(event.status);
    });
  }, [job?.job_id]);

  const [openMobileSection, setOpenMobileSection] =
    useState<string | null>(null);

  
  /*
   * Apply-return state.
   *
   * React state controls rendering.
   * The ref is used only to synchronously arm the Apply flow
   * before window.open() can trigger browser focus changes.
   */
  const [showApplyPrompt, setShowApplyPrompt] =
    useState<string | null>(null);





  /*
   * ============================================================
   * JOB DETAILS APPLY → RETURN → CONFIRMATION
   * ============================================================
   *
   * Behaviour:
   *
   * 1. Apply Now arms this exact job synchronously.
   * 2. External portal opens.
   * 3. Browser returns/focuses this page.
   * 4. awaitingReturn is converted to promptRequired.
   * 5. Popup is shown.
   * 6. If popup already exists in shared localStorage,
   *    it is restored after a Job Details refresh.
   *
   * Exact job ID matching is mandatory.
   *
   * No polling.
   * No blur workaround.
   * No duplicate watcher.
   */
  /*
   * JOB DETAILS APPLY → RETURN → CONFIRMATION
   *
   * Shared localStorage is the source of truth.
   *
   * promptRequired:
   *   Persistent confirmation. Restores after refresh.
   *
   * awaitingReturn:
   *   Converted only when this Job Details page actually
   *   armed Apply for the exact current job.
   *
   * Exact job ID matching is mandatory.
   */
  /*
   * JOB DETAILS APPLY → RETURN → CONFIRMATION
   *
   * The watcher is mounted when Job Details loads.
   *
   * IMPORTANT:
   * waitingForApplyReturnRef is armed synchronously BEFORE
   * window.open(), so the browser cannot race React state/effect
   * registration.
   *
   * promptRequired is persistent and therefore survives refresh.
   */
  /*
   * ============================================================
   * JOB DETAILS APPLY → CONFIRMATION
   * ============================================================
   *
   * Important browser behaviour:
   *
   * window.open("_blank") does not reliably cause the original
   * Job Details page to receive focus/visibility events.
   *
   * Therefore we use:
   *
   *   1. focus / pageshow / visibilitychange
   *   2. a lightweight fallback poll
   *
   * The ref remains the gate for awaitingReturn, so an unrelated
   * localStorage state cannot create a popup.
   *
   * promptRequired remains persistent and therefore survives
   * Job Details refresh.
   */
  /*
   * ============================================================
   * JOB DETAILS APPLY → RETURN → CONFIRMATION
   * ============================================================
   *
   * Shared localStorage is the source of truth.
   *
   * Apply Now writes:
   *
   *   awaitingReturn = true
   *   promptRequired = false
   *
   * When Job Details is active again, we convert that state into:
   *
   *   awaitingReturn = false
   *   promptRequired = true
   *
   * The prompt then renders from showApplyPrompt.
   *
   * IMPORTANT:
   * Do NOT gate this conversion behind React state/ref.
   * The Apply state itself already contains the exact job ID.
   * This mirrors the working Dashboard behaviour.
   */
  /*
   * ============================================================
   * JOB DETAILS APPLY / RETURN CONFIRMATION
   * ============================================================
   *
   * The shared localStorage state is the source of truth.
   *
   * Dashboard and Job Details both use:
   *
   *   awaitingReturn
   *        ↓
   *   promptRequired
   *
   * Exact jobId matching prevents cross-job prompts.
   *
   * promptRequired is persistent, so a refresh keeps the
   * confirmation visible.
   */
  /*
   * ============================================================
   * JOB DETAILS APPLY RETURN
   *
   * This intentionally mirrors the WORKING Dashboard flow.
   *
   * Dashboard:
   *   Apply → awaitingReturn
   *   browser returns → markApplyReturned()
   *   promptRequired → show popup
   *
   * Job Details uses the same shared state.
   * The only difference is that there is one loaded `job`
   * instead of a `jobs[]` collection.
   * ============================================================
   */
  useEffect(() => {
    async function handleReturn() {
      /*
       * Same lifecycle guard as Dashboard.
       */
      if (document.visibilityState !== "visible") {
        return;
      }

      /*
       * Do not inspect Apply state until the actual Job Details
       * record has finished loading.
       */
      if (!job) {
        return;
      }

      const shared = getApplyReturnState();

      if (!shared) {
        return;
      }

      /*
       * Same protection as Dashboard's jobs.some().
       *
       * Always compare against the REAL loaded job.job_id.
       */
      if (
        String(job.job_id) !==
        String(shared.jobId)
      ) {
        return;
      }

      /*
       * Already converted to confirmation.
       *
       * This is the important refresh path.
       */
      if (shared.promptRequired) {
        setShowApplyPrompt(
          String(shared.jobId),
        );
        return;
      }

      /*
       * Apply was started and the browser has returned.
       *
       * First refresh the real application status from
       * the backend so Job Details and Dashboard reflect
       * any status already saved by the Apply flow.
       */
      if (shared.awaitingReturn) {
        const returned = markApplyReturned();

        if (
          returned?.promptRequired &&
          String(returned.jobId) ===
            String(job.job_id)
        ) {
          try {
            const application = await getApplication(
              job.job_id,
            );

            if (application.application) {
              const savedStatus =
                application.application.status;

              setStatus(savedStatus);
              setNotes(
                application.application.notes || "",
              );

              publishApplicationStatus(
                job.job_id,
                savedStatus,
              );

              setShowApplyPrompt(null);
              return;
            }

            setStatus("not_applied");
            setNotes("");

            publishApplicationStatus(
              job.job_id,
              "not_applied",
            );
          } catch (error) {
            console.error(
              "Failed to refresh application after Apply:",
              error,
            );
          }

          setShowApplyPrompt(
            String(returned.jobId),
          );
        }
      }
    }

    /*
     * Initial check.
     *
     * If Dashboard/another page already created promptRequired,
     * Job Details restores it once the job is loaded.
     */
    handleReturn();

    /*
     * Same browser return signals as Dashboard.
     */
    function handleApplyStateStorage(event: StorageEvent) {
      if (event.key !== "ai_job_hunter_apply_return") {
        return;
      }

      if (event.newValue === null) {
        setShowApplyPrompt(null);
      }
    }

    window.addEventListener(
      "focus",
      handleReturn,
    );

    window.addEventListener(
      "pageshow",
      handleReturn,
    );

    document.addEventListener(
      "visibilitychange",
      handleReturn,
    );

    window.addEventListener(
      "storage",
      handleApplyStateStorage,
    );

    return () => {
      window.removeEventListener(
        "focus",
        handleReturn,
      );

      window.removeEventListener(
        "pageshow",
        handleReturn,
      );

      document.removeEventListener(
        "visibilitychange",
        handleReturn,
      );

      window.removeEventListener(
        "storage",
        handleApplyStateStorage,
      );
    };
  }, [job]);

  const [mobileStatusOpen, setMobileStatusOpen] =
    useState(false);

  const mobileStatusOptions: {
    value: ApplicationStatus;
    label: string;
  }[] = [
    { value: "saved", label: "Saved" },
    { value: "pending", label: "Application pending" },
    { value: "applied", label: "Applied" },
    { value: "interview", label: "Interview" },
    { value: "offer", label: "Offer" },
    { value: "rejected", label: "Rejected" },
    { value: "not_relevant", label: "Not relevant" },
  ];

  function handleMobileStatusChange(
    nextStatus: ApplicationStatus,
  ) {
    setMobileStatusOpen(false);
    saveApplication(nextStatus);
  }

  function toggleMobileSection(section: string) {
    setOpenMobileSection((current) =>
      current === section ? null : section,
    );
  }

  // Close the mobile status menu when the user clicks/taps
  // anywhere outside the status control.
  useEffect(() => {
    if (!mobileStatusOpen) return;

    function mobileStatusOutsideClose(event: PointerEvent) {
      const target = event.target as Node | null;
      const statusControl = document.querySelector(
        ".job-details-mobile-status",
      );

      if (
        statusControl &&
        target &&
        !statusControl.contains(target)
      ) {
        setMobileStatusOpen(false);
      }
    }

    function mobileStatusEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobileStatusOpen(false);
      }
    }

    document.addEventListener(
      "pointerdown",
      mobileStatusOutsideClose,
    );

    document.addEventListener(
      "keydown",
      mobileStatusEscape,
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        mobileStatusOutsideClose,
      );

      document.removeEventListener(
        "keydown",
        mobileStatusEscape,
      );
    };
  }, [mobileStatusOpen]);

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
  async function saveApplication(
    nextStatus: ApplicationStatus,
  ) {
    if (!job || !profileId || saving) return;

    try {
      setSaving(true);
      setError(null);

      const response = await updateApplication(
        job.job_id,
        {
          status: nextStatus,
          applied_at:
            nextStatus === "applied"
              ? new Date().toISOString()
              : undefined,
          notes,
        },
      );

      const savedApplication =
        response.application;

      setStatus(savedApplication.status);
      setNotes(savedApplication.notes || "");

      publishApplicationStatus(
        job.job_id,
        savedApplication.status,
      );
    } catch (error) {
      console.error(
        "Failed to save application:",
        error,
      );

      setError(
        "Unable to save application changes.",
      );
    } finally {
      setSaving(false);
    }
  }
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
  if(error||!job)return <main className="detail-shell"><div className="error-card"><h2>{error||"Job not found"}</h2><button type="button" className="apply-now" onClick={() => router.push("/dashboard", { scroll: false })}>Back to jobs</button></div></main>;
  return (
    <main className="detail-shell">
      <button
        type="button"
        className="back-link"
        onClick={() => router.push("/dashboard", { scroll: false })}
      >
        <ArrowLeft size={15} />
        Back to jobs
      </button>

      <JobHeader
        job={job}
        score={score}
        status={status}
        saving={saving}
        saveApplication={saveApplication}
        showApplyPrompt={showApplyPrompt === String(job.job_id)}
        onApplyConfirmed={() => {
          saveApplication("applied");
          setShowApplyPrompt(null);
          clearApplyReturnState();
        }}
        onApplyNotYet={() => {
          saveApplication("pending");
          setShowApplyPrompt(null);
          clearApplyReturnState();
        }}
        onApplyNotRelevant={() => {
          saveApplication("not_relevant");
          setShowApplyPrompt(null);
          clearApplyReturnState();
        }}
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
          <section className="detail-side-card job-highlights-card">
            <button
              type="button"
              className="detail-side-heading mobile-sidebar-accordion-trigger"
              aria-expanded={openMobileSection === "job-highlights"}
              onClick={() =>
                toggleMobileSection("job-highlights")
              }
            >
              <span className="detail-side-icon">✦</span>
              <h3>Job Highlights</h3>
            </button>

            <div
              className={`mobile-sidebar-accordion-content ${
                openMobileSection === "job-highlights"
                  ? "is-open"
                  : ""
              }`}
            >
              <div className="highlight-item">
                <strong>High match with your profile</strong>
                <span>
                  Your skills match {Math.round(score?.overall_score ?? 0)}%
                  of requirements
                </span>
              </div>
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
              <div
                className="score-breakdown-donut"
                style={
                  {
                    "--breakdown-score": `${Math.max(
                      0,
                      Math.min(100, Math.round(score?.overall_score ?? 0)),
                    )}%`,
                  } as React.CSSProperties
                }
              >
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

      <div className="job-details-mobile-actions">

        <button
          type="button"
          className={`job-details-mobile-save ${
            status === "saved" ? "is-saved" : ""
          }`}
          aria-label={status === "saved" ? "Saved" : "Save job"}
          onClick={() => saveApplication("saved")}
          disabled={saving}
        >
          {status === "saved" ? "♥" : "♡"}
        </button>

        <div className="job-details-mobile-status">
          <button
            type="button"
            className="job-details-mobile-status-trigger"
            aria-expanded={mobileStatusOpen}
            aria-haspopup="listbox"
            aria-label="Job Status"
            onClick={() =>
              setMobileStatusOpen((open) => !open)
            }
            disabled={saving}
          >
            <span>
              {status === "saved" && "Saved"}
              {status === "pending" && "Application Pending"}
              {status === "applied" && "Applied"}
              {status === "interview" && "Interview"}
              {status === "offer" && "Offer"}
              {status === "rejected" && "Rejected"}
              {status === "not_relevant" && "Not Relevant"}
            </span>

            <span
              className={`job-details-mobile-status-chevron ${
                mobileStatusOpen ? "is-open" : ""
              }`}
              aria-hidden="true"
            >
              ⌄
            </span>
          </button>

          {mobileStatusOpen && (
            <div
              className="job-details-mobile-status-menu"
              role="listbox"
              aria-label="Job Status options"
            >
              {mobileStatusOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="option"
                  aria-selected={status === option.value}
                  className={`job-details-mobile-status-option ${
                    status === option.value
                      ? "is-selected"
                      : ""
                  }`}
                  onClick={() =>
                    handleMobileStatusChange(option.value)
                  }
                >
                  <span>{option.label}</span>

                  {status === option.value && (
                    <span
                      className="job-details-mobile-status-check"
                      aria-hidden="true"
                    >
                      ✓
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {job.job_url && (
          <button
            type="button"
            className="job-details-mobile-apply"
            onClick={() => {
              if (!job.job_url) {
                return;
              }
              const exactJobId = String(job.job_id);

              setApplyAwaitingReturn(
                exactJobId,
              );

              window.open(
                job.job_url,
                "_blank",
                "noopener,noreferrer",
              );
            }}
          >
            Apply Now ↗
          </button>
        )}

      </div>

    </main>
  );
}

function ScoreBar({label,value,className=""}:{label:string;value:number;className?:string}){const v=Math.max(0,Math.min(100,Number(value)||0));return <div className={`scorebar ${className}`}><div><span>{label}</span><b>{v.toFixed(0)}%</b></div><i><em style={{width:`${v}%`}}/></i></div>}

"use client";

import {
  ArrowUpRight,
  Bookmark,
  BriefcaseBusiness,
  SlidersHorizontal,
  UserRound,
} from "lucide-react";
import { useEffect, useState } from "react";

import {
  deleteApplication,
  getApplicationsBulk,
  updateApplication,
} from "@/lib/api";

import type { ApplicationStatus as ApiApplicationStatus } from "@/lib/api";

import type { DashboardPresentationProps } from "./DashboardDesktop";

import styles from "./DashboardMobile.module.css";
import MobileHeader from "./mobile/header/MobileHeader";
import MobileHero from "./mobile/hero/MobileHero";
import MobileSearch from "./mobile/search/MobileSearch";
import MobileFilters from "./mobile/filters/MobileFilters";
import MobileStats from "./mobile/stats/MobileStats";
import MobileTabs from "./mobile/tabs/MobileTabs";
import MobileJobCard from "./mobile/job-card/MobileJobCard";


type MobileProps = DashboardPresentationProps;

type MobileStatus =
  | "Not Applied"
  | "Saved"
  | "Pending"
  | "Applied"
  | "Interview"
  | "Rejected"
  | "Offer"
  | "Not Relevant";

type MobileTab =
  | "ALL"
  | "Applied"
  | "Not Applied"
  | "Saved";

const displayStatus = (
  status?: string,
): MobileStatus => {
  if (status === "saved") return "Saved";
  if (status === "pending") return "Pending";
  if (status === "applied") return "Applied";
  if (status === "interview") return "Interview";
  if (status === "rejected") return "Rejected";
  if (status === "offer") return "Offer";
  if (status === "not_relevant") return "Not Relevant";

  return "Not Applied";
};

const apiStatus = (
  status: MobileStatus,
): ApiApplicationStatus => {
  if (status === "Pending") return "pending";
  if (status === "Applied") return "applied";
  if (status === "Interview") return "interview";
  if (status === "Rejected") return "rejected";
  if (status === "Offer") return "offer";
  if (status === "Not Relevant") return "not_relevant";

  return "saved";
};

    
function formatProfileName(profileId: string) {
  return profileId
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}


export default function DashboardMobile(
  props: MobileProps,
) {
  const [
    statusMap,
    setStatusMap,
  ] = useState<
    Record<string, MobileStatus>
  >({});

  const [
    activeTab,
    setActiveTab,
  ] = useState<MobileTab>("ALL");

  useEffect(() => {
    let cancelled = false;

    async function loadApplications() {
      if (
        !props.jobs.length ||
        !props.profileId
      ) {
        setStatusMap({});
        return;
      }

      try {
        const response =
          await getApplicationsBulk(
            props.jobs.map(
              (job) => job.job_id,
            ),
          );

        if (cancelled) return;

        const next: Record<
          string,
          MobileStatus
        > = {};

        Object.entries(
          response.applications || {},
        ).forEach(
          ([jobId, application]) => {
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
  }, [
    props.jobs,
    props.profileId,
  ]);

  async function updateStatus(
    jobId: string,
    status: MobileStatus,
  ) {
    try {
      if (status === "Not Applied") {
        await deleteApplication(jobId);

        setStatusMap((current) => {
          const next = { ...current };
          delete next[jobId];
          return next;
        });

        return;
      }

      const response = await updateApplication(
        jobId,
        {
          status: apiStatus(status),
          applied_at:
            status === "Applied"
              ? new Date().toISOString()
              : null,
        },
      );

      const savedStatus =
        response.application?.status;

      if (savedStatus) {
        setStatusMap((current) => ({
          ...current,
          [jobId]: displayStatus(savedStatus),
        }));
      }
    } catch (error) {
      console.error(
        "Failed to update mobile application status:",
        error,
      );
    }
  }

  const filteredJobs =
    props.jobs.filter((job) => {
      if (activeTab === "ALL") {
        return true;
      }

      return (
        statusMap[job.job_id] ||
        "Not Applied"
      ) === activeTab;
    });

  const {
    filtersOpen,
    loading,
    jobs,
    totalJobs,
    loadMoreJobs,
  } = props;

  useEffect(() => {
    if (
      filtersOpen ||
      loading ||
      jobs.length >=
        totalJobs
    ) {
      return;
    }

    const sentinel =
      document.querySelector(
        "[data-mobile-load-more]",
      );

    if (!sentinel) {
      return;
    }

    const observer =
      new IntersectionObserver(
        (entries) => {
          if (
            entries[0]?.isIntersecting
          ) {
            void loadMoreJobs();
          }
        },
        {
          root: null,
          rootMargin: "700px 0px",
          threshold: 0,
        },
      );

    observer.observe(sentinel);

    return () => {
      observer.disconnect();
    };
  }, [
    filtersOpen,
    loading,
    jobs.length,
    totalJobs,
    loadMoreJobs,
  ]);

  return (
    <main className={styles.root}>
      <MobileHeader />

      <MobileHero />

      <section className={styles.searchSection}>
        <MobileSearch
          search={props.search}
          setSearch={props.setSearch}
        />

        <MobileFilters
          open={props.filtersOpen}
          activeFilters={
            props.activeFilters
          }
          filterOptions={
            props.filterOptions
          }

          company={props.company}
          locations={props.locations}
          skills={props.skills}
          tools={props.tools}
          portal={props.portal}

          relevance={props.relevance}
          sort={props.sort}

          postedDateFrom={
            props.postedDateFrom
          }
          postedDateTo={
            props.postedDateTo
          }

          setOpen={
            props.setFiltersOpen
          }

          setCompany={
            props.setCompany
          }
          setLocations={
            props.setLocations
          }
          setSkills={
            props.setSkills
          }
          setTools={
            props.setTools
          }
          setPortal={
            props.setPortal
          }
          setSort={
            props.setSort
          }

          toggleValue={
            props.toggleValue
          }
          toggleRelevance={
            props.toggleRelevance
          }
          datePreset={
            props.datePreset
          }

          clearFilters={
            props.clearFilters
          }
          applyFilters={
            props.applyMobileFilters
          }
        />


        <button
          type="button"
          className={`${styles.filterButton} ${
            props.activeFilters > 0
              ? styles.filterButtonActive
              : ""
          }`}
          onClick={() =>
            props.setFiltersOpen(
              (value) => !value,
            )
          }
        >
          <SlidersHorizontal size={17} />
          <span>Filters</span>

          {props.activeFilters > 0 && (
            <b>
              {props.activeFilters}
            </b>
          )}
        </button>
      </section>

      <MobileStats
        summary={props.summary}
      />

      <MobileTabs
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        totalJobs={props.totalJobs}
      />

      <section className={styles.jobsSection}>
        {props.loading &&
        props.jobs.length === 0 ? (
          <div className={styles.loading}>
            Loading your matches…
          </div>
        ) : props.totalJobs === 0 ? (

          <div className={styles.empty}>

            <strong>

              We’re working on it 🚀

            </strong>

        

            <span>

              We don’t have {formatProfileName(props.profileId)} jobs available yet.

              We’re working to add relevant opportunities for this profile soon.

            </span>

          </div>

        ) : filteredJobs.length === 0 ? (

          <div className={styles.empty}>

            <strong>

              No matching jobs

            </strong>

        

            <span>

              Try another tab or filter.

            </span>

          </div>
        ) : (
          filteredJobs.map(
            (job, index) => (
              <MobileJobCard
                key={job.job_id}
                job={job}
                index={index}
                status={
                  statusMap[job.job_id] ||
                  "Not Applied"
                }
                onStatusChange={
                  updateStatus
                }
                profileId={
                  props.profileId
                }
                onJobOpen={
                  props.onJobOpen
                }
              />
            ),
          )
        )}

        {props.jobs.length <
          props.totalJobs && (
          <div
            data-mobile-load-more
            className={
              styles.mobileLoadMore
            }
            aria-hidden="true"
          >
            {props.mobileLoadingMore && (
              <span
                className={
                  styles.mobileLoadMoreText
                }
              >
                Loading more jobs…
              </span>
            )}
          </div>
        )}
      </section>

      <nav
        className={styles.bottomNav}
        aria-label="Mobile navigation"
      >
        <button
          type="button"
          className={styles.bottomNavActive}
        >
          <BriefcaseBusiness size={19} />
          <span>Jobs</span>
        </button>

        <button
          type="button"
          className={styles.bottomNavItem}
          onClick={() =>
            setActiveTab("Saved")
          }
        >
          <Bookmark size={19} />
          <span>Saved</span>
        </button>

        <button
          type="button"
          className={styles.bottomNavItem}
          onClick={() =>
            setActiveTab("Applied")
          }
        >
          <ArrowUpRight size={19} />
          <span>Applied</span>
        </button>

        <button
          type="button"
          className={styles.bottomNavItem}
          onClick={() => {
            window.location.href = "/profile";
          }}
          aria-label="Manage profile"
        >
          <UserRound size={19} />
          <span>Profile</span>
        </button>
      </nav>
    </main>
  );
}

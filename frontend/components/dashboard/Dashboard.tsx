"use client";
import "./DashboardTokens.css";

import { useEffect, useRef, useState } from "react";
import { getDashboardSummary, getJobFilterOptions, getJobs, getProfiles } from "@/lib/api";
import type { DashboardSummary, Job, JobFilterOptions } from "@/types/job";
import DashboardMobile from "./DashboardMobile";
import DashboardDesktop from "./DashboardDesktop";
import styles from "./Dashboard.module.css";

const PAGE_SIZE = 20;

type Relevance = "all" | "gte_70" | "50_69" | "30_49" | "lt_30";
type SortMode = "score" | "newest" | "oldest";


function localDate(value: Date): string {
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [profiles, setProfiles] = useState<string[]>([]);
  const [profileId, setProfileId] = useState("");
  const [filterOptions, setFilterOptions] = useState<JobFilterOptions>({
    locations: [], skills: [], tools: [], portals: [], companies: [],
  });
  const [page, setPage] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filterRevision, setFilterRevision] = useState(0);
  const hasLoadedOnceRef = useRef(false);
  const [search, setSearch] = useState("");
  const [company, setCompany] = useState("");
  const [locations, setLocations] = useState<string[]>([]);
  const [skills, setSkills] = useState<string[]>([]);
  const [tools, setTools] = useState<string[]>([]);
  const [portal, setPortal] = useState("");
  const [relevance, setRelevance] = useState<Relevance[]>(["gte_70"]);
  const [sort, setSort] = useState<SortMode>("score");
  const [postedDateFrom, setPostedDateFrom] = useState("");
  const [postedDateTo, setPostedDateTo] = useState("");

  const requestId = useRef(0);
  const previousPageRef = useRef(1);

  const mobilePageRef = useRef(1);
  const mobileLoadingRef = useRef(false);

  const [mobileLoadingMore, setMobileLoadingMore] =
    useState(false);
  useEffect(() => {
    async function loadProfiles() {
      try {
        const data = await getProfiles();
        const next = data.profiles || [];
        setProfiles(next);
        if (next.length) setProfileId((current) => current || next[0]);
      } catch (error) {
        console.error("Failed to load profiles:", error);
      }
    }
    loadProfiles();
  }, []);

  useEffect(() => {
    if (!profileId) return;
    getJobFilterOptions(profileId)
      .then(setFilterOptions)
      .catch((error) => console.error("Failed to load filter options:", error));
  }, [profileId]);

  async function loadDashboard(isRefresh = false) {
    if (!profileId) return;
    const currentId = ++requestId.current;
    if (hasLoadedOnceRef.current || isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [dashboard, jobsData] = await Promise.all([
        getDashboardSummary(profileId, {
          search: search || undefined,
          company: company || undefined,
          location: locations,
          skill: skills,
          tool: tools,
          portal: portal || undefined,
          relevance,
          posted_date_from: postedDateFrom || undefined,
          posted_date_to: postedDateTo || undefined,
        }),
        getJobs({
          profile_id: profileId,
          page,
          page_size: PAGE_SIZE,
          search: search || undefined,
          company: company || undefined,
          location: locations,
          skill: skills,
          tool: tools,
          portal: portal || undefined,
          relevance,
          posted_date_from: postedDateFrom || undefined,
          posted_date_to: postedDateTo || undefined,
          sort,
        }),
      ]);

      if (currentId !== requestId.current) return;
      mobilePageRef.current = page;
      mobileLoadingRef.current = false;
      setMobileLoadingMore(false);

      setSummary(dashboard);
      setJobs(jobsData.jobs || []);
      setTotalJobs(jobsData.total || 0);
    } catch (error) {
      if (currentId !== requestId.current) return;
      console.error("Dashboard error:", error);
      setSummary(null);
      setJobs([]);
      setTotalJobs(0);
    } finally {
      if (currentId === requestId.current) {
        hasLoadedOnceRef.current = true;
        setLoading(false);
        setRefreshing(false);
      }
    }
  }

  async function loadMoreJobs() {
    if (!profileId) return;

    if (mobileLoadingRef.current) {
      return;
    }

    const nextPage =
      mobilePageRef.current + 1;

    const totalPages =
      Math.max(
        1,
        Math.ceil(
          totalJobs / PAGE_SIZE,
        ),
      );

    if (
      nextPage > totalPages ||
      jobs.length >= totalJobs
    ) {
      return;
    }

    const requestGeneration =
      requestId.current;

    mobileLoadingRef.current = true;
    setMobileLoadingMore(true);

    try {
      const jobsData = await getJobs({
        profile_id: profileId,
        page: nextPage,
        page_size: PAGE_SIZE,
        search: search || undefined,
        company: company || undefined,
        location: locations,
        skill: skills,
        tool: tools,
        portal: portal || undefined,
        relevance,
        posted_date_from:
          postedDateFrom || undefined,
        posted_date_to:
          postedDateTo || undefined,
        sort,
      });

      if (
        requestGeneration !==
        requestId.current
      ) {
        return;
      }

      const incoming =
        jobsData.jobs || [];

      if (!incoming.length) {
        mobilePageRef.current =
          nextPage;

        return;
      }

      setJobs((current) => {
        const existing =
          new Set(
            current.map(
              (job) => job.job_id,
            ),
          );

        const unique =
          incoming.filter(
            (job) =>
              !existing.has(
                job.job_id,
              ),
          );

        return [
          ...current,
          ...unique,
        ];
      });

      mobilePageRef.current =
        nextPage;

      if (
        jobsData.total !== undefined
      ) {
        setTotalJobs(
          jobsData.total,
        );
      }
    } catch (error) {
      console.error(
        "Failed to load more mobile jobs:",
        error,
      );
    } finally {
      if (
        requestGeneration ===
        requestId.current
      ) {
        mobileLoadingRef.current =
          false;

        setMobileLoadingMore(false);
      }
    }
  }

  useEffect(() => {
    if (!profileId) return;

    const timer = window.setTimeout(
      () => loadDashboard(false),
      search ? 250 : 0,
    );

    return () =>
      window.clearTimeout(timer);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId, page, search, filterRevision]);

  useEffect(() => {
    if (previousPageRef.current === page) return;
    previousPageRef.current = page;
    requestAnimationFrame(() => {
      document.querySelector(".mj-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [page, jobs.length]);

  // Automatic 10-second refresh disabled.
  // Dashboard refreshes only when filters/page/profile change.

  function applyDesktopFilterChange() {
    setPage(1);
    setFilterRevision((value) => value + 1);
  }

  function applyMobileFilters() {
    setPage(1);

    mobilePageRef.current = 1;
    mobileLoadingRef.current = false;
    setMobileLoadingMore(false);

    setFiltersOpen(false);
    setFilterRevision((value) => value + 1);
  }

  function clearFilters() {
    setSearch("");
    setCompany("");
    setLocations([]);
    setSkills([]);
    setTools([]);
    setPortal("");
    setRelevance(["gte_70"]);
    setSort("score");
    setPostedDateFrom("");
    setPostedDateTo("");

    setPage(1);

    mobilePageRef.current = 1;
    mobileLoadingRef.current = false;
    setMobileLoadingMore(false);

    setFiltersOpen(false);

    setFilterRevision(
      (value) => value + 1,
    );
  }

  function toggleValue(value: string, current: string[], setter: (values: string[]) => void) {
    setPage(1);
    setter(current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
    setFilterRevision((value) => value + 1);
  }

  function toggleRelevance(value: Relevance) {
    setPage(1);
    setFilterRevision((value) => value + 1);
    if (value === "all") {
      setRelevance(["all"]);
      return;
    }
    setRelevance((current) => {
      const currentBuckets = current.filter((item) => item !== "all");
      if (currentBuckets.includes(value)) {
        const next = currentBuckets.filter((item) => item !== value);
        return next.length ? next : ["all"];
      }
      return [...currentBuckets, value];
    });
  }

  function datePreset(mode: "today" | "yesterday" | "two" | "five" | "seven") {
    setPage(1);
    setFilterRevision((value) => value + 1);
    const now = new Date();
    if (mode === "yesterday") {
      const yesterday = new Date(now);
      yesterday.setDate(now.getDate() - 1);
      const value = localDate(yesterday);
      setPostedDateFrom(value);
      setPostedDateTo(value);
      return;
    }
    const days = mode === "today" ? 1 : mode === "two" ? 2 : mode === "five" ? 5 : 7;
    const start = new Date(now);
    start.setDate(now.getDate() - (days - 1));
    setPostedDateFrom(localDate(start));
    setPostedDateTo(localDate(now));
  }

  const activeFilters =
    Number(Boolean(search)) + Number(Boolean(company)) + locations.length + skills.length + tools.length +
    Number(Boolean(portal)) + Number(!relevance.includes("all")) + Number(sort !== "score") +
    Number(Boolean(postedDateFrom || postedDateTo));

  const totalPages = Math.max(1, Math.ceil(totalJobs / PAGE_SIZE));

  const presentationProps = {
    profileId,
    profiles,
    onProfileChange: setProfileId,
    totalJobs,
    summary,
    jobs,
    filterOptions,
    loading,
    refreshing,
    filtersOpen,
    search,
    company,
    locations,
    skills,
    tools,
    portal,
    relevance,
    sort,
    postedDateFrom,
    postedDateTo,
    activeFilters,
    totalPages,
    page,
    setFiltersOpen,
    applyMobileFilters,
    applyDesktopFilterChange,
    setSearch,
    setCompany,
    setLocations,
    setSkills,
    setTools,
    setPortal,
    setSort,
    setPostedDateFrom,
    setPostedDateTo,
    toggleValue,
    toggleRelevance,
    datePreset,
    clearFilters,
    loadMoreJobs,
    mobileLoadingMore,
    setPage,
  };

  return (
    <section className={styles.root} data-ui="dashboard">
      <div className={styles.desktopPresentation}>
        <DashboardDesktop {...presentationProps} />
      </div>
      <div className={styles.mobilePresentation}>
        <DashboardMobile {...presentationProps} />
      </div>
    </section>
  );
}

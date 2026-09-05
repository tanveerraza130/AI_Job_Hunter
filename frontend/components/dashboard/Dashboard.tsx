"use client";
import "./DashboardTokens.css";

import { useEffect, useRef, useState } from "react";
import { getDashboardSummary, getJobFilterOptions, getJobs, getMyProfile } from "@/lib/api";
import type { DashboardSummary, Job, JobFilterOptions } from "@/types/job";
import DashboardMobile from "./DashboardMobile";
import DashboardDesktop from "./DashboardDesktop";
import styles from "./Dashboard.module.css";
import {
  clearDashboardReturnState,
  readDashboardReturnState,
  saveDashboardReturnState,
} from "@/lib/dashboardReturnState";

const PAGE_SIZE = 20;
const DESKTOP_JOB_RETURN_KEY = "ai_job_hunter_desktop_job_return";

type Relevance = "all" | "gte_30" | "gte_70" | "50_69" | "30_49" | "lt_30";
type SortMode = "score" | "newest" | "oldest";


function localDate(value: Date): string {
  const local = new Date(value.getTime() - value.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

export default function Dashboard() {
  const [returnState] = useState(() =>
    readDashboardReturnState(),
  );

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [profileId, setProfileId] = useState("");
  const [profileReady, setProfileReady] = useState(false);
  const [filterOptions, setFilterOptions] = useState<JobFilterOptions>({
    locations: [], skills: [], tools: [], portals: [], companies: [],
  });
  const [page, setPage] = useState(() => {
    if (!returnState) return 1;

    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 700px)").matches;

    return isMobile
      ? 1
      : Math.max(1, returnState.page);
  });
  const [totalJobs, setTotalJobs] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [filterRevision, setFilterRevision] = useState(0);
  const hasLoadedOnceRef = useRef(false);
  const [search, setSearch] = useState(
    returnState?.search ?? "",
  );
  const [company, setCompany] = useState(
    returnState?.company ?? "",
  );
  const [locations, setLocations] = useState<string[]>(
    returnState?.locations ?? [],
  );
  const [skills, setSkills] = useState<string[]>(
    returnState?.skills ?? [],
  );
  const [tools, setTools] = useState<string[]>(
    returnState?.tools ?? [],
  );
  const [portal, setPortal] = useState(
    returnState?.portal ?? "",
  );
  const [relevance, setRelevance] = useState<Relevance[]>(
    returnState?.relevance ?? ["gte_30"],
  );
  const [sort, setSort] = useState<SortMode>(
    returnState?.sort ?? "newest",
  );
  const [postedDateFrom, setPostedDateFrom] = useState(
    returnState?.postedDateFrom ?? "",
  );
  const [postedDateTo, setPostedDateTo] = useState(
    returnState?.postedDateTo ?? "",
  );

  const requestId = useRef(0);
  const previousPageRef = useRef(1);
  const [initialDashboardLoaded, setInitialDashboardLoaded] =
    useState(false);

  const mobilePageRef = useRef(
    returnState?.mobilePage ?? 1,
  );
  const mobileRestoreTargetRef = useRef(
    returnState?.mobilePage ?? 1,
  );
  const mobileLoadingRef = useRef(false);

  const [mobileLoadingMore, setMobileLoadingMore] =
    useState(false);

  const onJobOpen = (jobId?: string) => {
    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 700px)").matches;

    const currentMobilePage = Math.max(
      1,
      mobilePageRef.current,
    );

    const currentPage = Math.max(
      1,
      page,
    );

    saveDashboardReturnState({
      page: currentPage,
      mobilePage: currentMobilePage,
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
      ...(isMobile && jobId
        ? {
            jobId,
            scrollY:
              typeof window !== "undefined"
                ? window.scrollY
                : 0,
          }
        : {}),
    });

    if (typeof window !== "undefined") {
      try {
        if (isMobile) {
          sessionStorage.removeItem(DESKTOP_JOB_RETURN_KEY);
        } else if (jobId) {
          sessionStorage.setItem(
            DESKTOP_JOB_RETURN_KEY,
            JSON.stringify({
              jobId,
              page: currentPage,
              scrollY: window.scrollY,
            }),
          );
        }
      } catch {}
    }
  };

  useEffect(() => {
    let cancelled = false;

    async function resolveAuthenticatedProfile() {
      const token = localStorage.getItem(
        "ai_job_hunter_token",
      );

      if (!token) {
        if (!cancelled) {
          setProfileId("");
          setProfileReady(false);
          setLoading(false);
        }
        return;
      }

      try {
        /*
         * HARD RULE:
         * The authenticated account's saved profile is the
         * only source of truth.
         *
         * URL profile_id is NEVER read as the active profile.
         */
        const response = await getMyProfile(token);

        if (cancelled) return;

        const authenticatedProfile =
          response.profile?.profile_id?.trim();

        if (!authenticatedProfile) {
          console.error(
            "Authenticated user has no saved job profile.",
          );

          setProfileId("");
          setProfileReady(false);
          setLoading(false);
          return;
        }

        /*
         * Resolve the profile BEFORE allowing any dashboard
         * data request to run.
         */
        setProfileId(authenticatedProfile);

        /*
         * Canonicalize only the URL.
         * Do NOT reload the page.
         */
        const url = new URL(window.location.href);

        if (
          url.searchParams.get("profile_id") !==
          authenticatedProfile
        ) {
          url.searchParams.set(
            "profile_id",
            authenticatedProfile,
          );

          window.history.replaceState(
            {},
            "",
            `${url.pathname}?${url.searchParams.toString()}`,
          );
        }

        /*
         * This is deliberately the final step.
         * Dashboard data effects are blocked until this becomes true.
         */
        setProfileReady(true);
      } catch (error) {
        if (!cancelled) {
          console.error(
            "Failed to load authenticated profile:",
            error,
          );

          setProfileId("");
          setProfileReady(false);
          setLoading(false);
        }
      }
    }

    resolveAuthenticatedProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!profileReady || !profileId) return;

    getJobFilterOptions(profileId)
      .then(setFilterOptions)
      .catch((error) => console.error("Failed to load filter options:", error));
  }, [profileReady, profileId]);

  async function loadDashboard(isRefresh = false) {
    if (!profileReady || !profileId) return;
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

      setInitialDashboardLoaded(true);
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
    if (!profileReady || !profileId) return;

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
    if (!profileReady || !profileId) return;

    const timer = window.setTimeout(
      () => loadDashboard(false),
      search ? 250 : 0,
    );

    return () =>
      window.clearTimeout(timer);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileReady, profileId, page, search, filterRevision]);

  /*
   * Desktop return restoration.
   *
   * Desktop keeps the exact job target in a separate sessionStorage key.
   * The existing dashboard return state remains unchanged for mobile.
   */
  const desktopRestoreStartedRef = useRef(false);

  useEffect(() => {
    if (!profileReady || !profileId) return;
    if (!initialDashboardLoaded) return;
    if (desktopRestoreStartedRef.current) return;

    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 700px)").matches;

    if (isMobile) return;

    let desktopReturn: {
      jobId?: string;
      page?: number;
      scrollY?: number;
    } | null = null;

    try {
      const raw = sessionStorage.getItem(DESKTOP_JOB_RETURN_KEY);

      if (raw) {
        const parsed = JSON.parse(raw);

        if (
          parsed &&
          typeof parsed.jobId === "string"
        ) {
          desktopReturn = parsed;
        }
      }
    } catch {}

    if (!desktopReturn?.jobId) return;

    const targetPage =
      typeof desktopReturn.page === "number" &&
      Number.isInteger(desktopReturn.page)
        ? Math.max(1, desktopReturn.page)
        : Math.max(1, returnState?.page ?? 1);

    if (page !== targetPage) {
      setPage(targetPage);
      return;
    }

    const jobId = desktopReturn.jobId;

    let attempts = 0;
    let cancelled = false;

    const restoreDesktopCard = () => {
      if (cancelled) return;

      const card = document.querySelector(
        `[data-job-id="${CSS.escape(jobId)}"]`,
      );

      if (card instanceof HTMLElement) {
        const absoluteTop =
          card.getBoundingClientRect().top + window.scrollY;

        window.scrollTo({
          top: Math.max(0, absoluteTop - 120),
          behavior: "instant",
        });

        desktopRestoreStartedRef.current = true;

        try {
          sessionStorage.removeItem(
            DESKTOP_JOB_RETURN_KEY,
          );
        } catch {}

        clearDashboardReturnState();
        return;
      }

      if (attempts >= 20) return;

      attempts += 1;
      window.requestAnimationFrame(restoreDesktopCard);
    };

    window.requestAnimationFrame(restoreDesktopCard);

    return () => {
      cancelled = true;
    };
  }, [
    profileReady,
    profileId,
    initialDashboardLoaded,
    jobs,
    returnState,
    page,
  ]);

  const mobileRestoreStartedRef = useRef(false);

  useEffect(() => {
    if (!profileReady || !profileId) return;
    if (!initialDashboardLoaded) return;
    if (mobileRestoreStartedRef.current) return;

    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 700px)").matches;

    if (!isMobile) return;

    const targetPage = Math.max(
      1,
      mobileRestoreTargetRef.current,
    );

    if (targetPage <= 1) return;
    if (mobilePageRef.current >= targetPage) return;

    mobileRestoreStartedRef.current = true;

    let cancelled = false;

    async function restoreMobilePages() {
      const requestGeneration = requestId.current;
      let restoredJobs = [...jobs];
      let restoredPage = mobilePageRef.current;

      try {
        while (
          !cancelled &&
          restoredPage < targetPage
        ) {
          const nextPage = restoredPage + 1;

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
            cancelled ||
            requestGeneration !== requestId.current
          ) {
            return;
          }

          const incoming = jobsData.jobs || [];

          if (incoming.length) {
            const existing = new Set(
              restoredJobs.map(
                (job) => job.job_id,
              ),
            );

            const unique = incoming.filter(
              (job) => !existing.has(job.job_id),
            );

            restoredJobs = [
              ...restoredJobs,
              ...unique,
            ];
          }

          restoredPage = nextPage;
        }

        if (
          cancelled ||
          requestGeneration !== requestId.current
        ) {
          return;
        }

        mobilePageRef.current = restoredPage;
        setJobs(restoredJobs);
        clearDashboardReturnState();
      } catch (error) {
        console.error(
          "Failed to restore mobile dashboard pages:",
          error,
        );
      }
    }

    restoreMobilePages();

    return () => {
      cancelled = true;
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileReady, profileId, initialDashboardLoaded]);

  useEffect(() => {
    if (previousPageRef.current === page) return;
    previousPageRef.current = page;
    requestAnimationFrame(() => {
      document.querySelector(".mj-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [page, jobs.length]);

  // Automatic 10-second refresh disabled.
  // Dashboard refreshes only when filters/page/profile change.

  useEffect(() => {
    if (!profileReady || !profileId) return;
    if (!initialDashboardLoaded) return;
    if (!returnState?.jobId) return;

    const isMobile =
      typeof window !== "undefined" &&
      window.matchMedia("(max-width: 700px)").matches;

    if (!isMobile) return;

    const jobId = returnState.jobId;
    const scrollY = returnState.scrollY ?? 0;

    let attempts = 0;
    let cancelled = false;

    const restoreJobPosition = () => {
      if (cancelled) return;

      const card = document.querySelector(
        `[data-job-id="${CSS.escape(jobId)}"]`,
      );

      if (card) {
        card.scrollIntoView({
          behavior: "instant",
          block: "center",
        });

        clearDashboardReturnState();
        return;
      }

      if (attempts >= 20) {
        window.scrollTo({
          top: scrollY,
          behavior: "instant",
        });

        clearDashboardReturnState();
        return;
      }

      attempts += 1;
      window.requestAnimationFrame(restoreJobPosition);
    };

    window.requestAnimationFrame(restoreJobPosition);

    return () => {
      cancelled = true;
    };
  }, [
    profileReady,
    profileId,
    initialDashboardLoaded,
    returnState,
  ]);

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
    setRelevance(["gte_30"]);
    setSort("newest");
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

  /*
   * SECURITY / CONSISTENCY GATE
   *
   * Never render the dashboard's job data while the
   * authenticated profile is unresolved.
   *
   * This prevents a manually supplied URL such as:
   * /dashboard?profile_id=crm_manager
   *
   * from ever triggering CRM Manager dashboard requests
   * for a Data Analyst account.
   */
  if (!profileReady || !profileId) {
    return (
      <main className={styles.root}>
        <div
          style={{
            minHeight: "60vh",
            display: "grid",
            placeItems: "center",
            padding: "40px 20px",
          }}
        >
          <div
            style={{
              textAlign: "center",
              color: "var(--ajh-color-text-muted)",
            }}
          >
            <div
              style={{
                fontSize: "14px",
                fontWeight: 600,
                color: "var(--ajh-color-text-primary)",
                marginBottom: "6px",
              }}
            >
              Preparing your dashboard
            </div>

            <div style={{ fontSize: "12px" }}>
              Loading your assigned job profile…
            </div>
          </div>
        </div>
      </main>
    );
  }

  const presentationProps = {
    profileId,
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
    onJobOpen,
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

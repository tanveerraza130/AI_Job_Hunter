"use client";

import type { Dispatch, SetStateAction } from "react";
import type { DashboardSummary, Job, JobFilterOptions } from "@/types/job";
import DashboardHeader from "./DashboardHeader";
import styles from "./DashboardDesktop.module.css";
import DashboardContent from "./DashboardContent";

export interface DashboardPresentationProps {
  profileId: string;
  totalJobs: number;
  summary: DashboardSummary | null;
  jobs: Job[];
  filterOptions: JobFilterOptions;
  loading: boolean;
  refreshing: boolean;
  filtersOpen: boolean;
  search: string;
  company: string;
  locations: string[];
  skills: string[];
  tools: string[];
  portal: string;
  relevance: ("all" | "gte_30" | "gte_70" | "50_69" | "30_49" | "lt_30")[];
  sort: "score" | "newest" | "oldest";
  postedDateFrom: string;
  postedDateTo: string;
  activeFilters: number;
  totalPages: number;
  page: number;
  setFiltersOpen: Dispatch<SetStateAction<boolean>>;
  setSearch: Dispatch<SetStateAction<string>>;
  setCompany: Dispatch<SetStateAction<string>>;
  setLocations: Dispatch<SetStateAction<string[]>>;
  setSkills: Dispatch<SetStateAction<string[]>>;
  setTools: Dispatch<SetStateAction<string[]>>;
  setPortal: Dispatch<SetStateAction<string>>;
  setSort: Dispatch<SetStateAction<"score" | "newest" | "oldest">>;
  setPostedDateFrom: Dispatch<SetStateAction<string>>;
  setPostedDateTo: Dispatch<SetStateAction<string>>;
  toggleValue: (value: string, current: string[], setter: (values: string[]) => void) => void;
  toggleRelevance: (value: "all" | "gte_30" | "gte_70" | "50_69" | "30_49" | "lt_30") => void;
  datePreset: (mode: "today" | "yesterday" | "two" | "five" | "seven") => void;
  clearFilters: () => void;
  applyMobileFilters: () => void;
  applyDesktopFilterChange: () => void;

  loadMoreJobs: () => Promise<void>;
  mobileLoadingMore: boolean;

  onJobOpen: () => void;

  setPage: Dispatch<SetStateAction<number>>;
}

export default function DashboardDesktop(props: DashboardPresentationProps) {
  return (
    <main className={styles.root}>
      <div className={styles.container}>
        <DashboardHeader
          profileId={props.profileId}
        />

        <DashboardContent {...props} />
      </div>
    </main>
  );
}

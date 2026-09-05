"use client";

import { CalendarDays, ChevronDown, Search, SlidersHorizontal, X } from "lucide-react";
import { formatDisplayText } from "@/lib/display";
import { useEffect, useRef, useState } from "react";
import JobTable from "@/components/JobTable";
import DashboardFilters from "./DashboardFilters";
import DashboardHero from "./DashboardHero";
import DashboardStats from "./DashboardStats";
import JobList from "./JobList";
import type { DashboardPresentationProps } from "./DashboardDesktop";
import styles from "./DashboardContent.module.css";

const RELEVANCE_OPTIONS = ["gte_30", "gte_70", "50_69", "30_49", "lt_30", "all"] as const;
const RELEVANCE_LABELS: Record<(typeof RELEVANCE_OPTIONS)[number], string> = {
  gte_30: "30%+", gte_70: "70%+", "50_69": "50–69%", "30_49": "30–49%", lt_30: "Below 30%", all: "All jobs",
};

    
function formatProfileName(profileId: string) {
  return profileId
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}


export default function DashboardContent(props: DashboardPresentationProps) {
  const { filtersOpen, setFiltersOpen } = props;
  const filterButtonRef = useRef<HTMLButtonElement | null>(null);
  const filterCardRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    if (!filtersOpen) return;

    function handleOutsideClick(event: PointerEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (filterCardRef.current?.contains(target)) return;
      if (filterButtonRef.current?.contains(target)) return;
      if (target instanceof Element && target.closest('[data-ui="dashboard-filters"]')) return;
      setFiltersOpen(false);
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setFiltersOpen(false);
    }

    document.addEventListener("pointerdown", handleOutsideClick, true);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("pointerdown", handleOutsideClick, true);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [filtersOpen, setFiltersOpen]);

  if (props.loading && props.jobs.length === 0) {
    return (
      <div className={styles.loadingCard}>
        <div className={styles.loadingSpinner} />
        <div>
          <div className={styles.loadingTitle}>Loading your matches</div>
          <div className={styles.loadingCopy}>Fetching the latest AI-ranked jobs…</div>
        </div>
      </div>
    );
  }

  return (
    <>
      <DashboardHero totalJobs={props.totalJobs} />

      <DashboardFilters>
        <section className={styles.searchPanel}>
          <div className={styles.searchRow}>
            <label className={styles.searchInput}>
              <Search size={17} />
              <input value={props.search} onChange={(event) => props.setSearch(event.target.value)} placeholder="Search jobs, skills or companies" aria-label="Search jobs" />
              {props.search && (
                <button type="button" className={styles.iconButton} aria-label="Clear search" onClick={() => props.setSearch("")}>
                  <X size={15} />
                </button>
              )}
            </label>
            <button
              ref={filterButtonRef}
              type="button"
              onPointerDown={(event) => event.stopPropagation()}
              data-ui="dashboard-filter-toggle"
              className={`${styles.filterToggle} ${props.filtersOpen || props.activeFilters > 0 ? styles.active : ""}`}
              onClick={() => props.setFiltersOpen((value) => !value)}
            >
              <SlidersHorizontal size={16} /> Filters
              {props.activeFilters > 0 && <span className={styles.filterCount}>{props.activeFilters}</span>}
              <ChevronDown size={14} className={props.filtersOpen ? styles.rotate : ""} />
            </button>
          </div>

          {props.filtersOpen && (
            <div ref={filterCardRef} className={styles.filterCard} onPointerDown={(event) => event.stopPropagation()}>
              <div className={styles.filterRow}>
                <label className={`${styles.field} ${styles.wide}`}><span>Company</span><input value={props.company} onChange={(event) => { props.setCompany(event.target.value); props.setPage(1); props.applyDesktopFilterChange(); }} placeholder="Search company" /></label>
                <label className={styles.field}><span>Sort</span><select value={props.sort} onChange={(event) => { props.setSort(event.target.value as "score" | "newest" | "oldest"); props.setPage(1); props.applyDesktopFilterChange(); }}><option value="score">Best match</option><option value="newest">Newest</option><option value="oldest">Oldest</option></select></label>
                <MultiSelect label="Relevance" options={RELEVANCE_OPTIONS.map((value) => RELEVANCE_LABELS[value])} values={props.relevance.map((value) => RELEVANCE_LABELS[value])} onToggle={(label) => {
                  const value = (Object.entries(RELEVANCE_LABELS) as [typeof RELEVANCE_OPTIONS[number], string][]).find(([, optionLabel]) => optionLabel === label)?.[0];
                  if (value) props.toggleRelevance(value);
                }} />
              </div>

              <div className={styles.filterRow}>
                <div className={styles.field}><span>Posted</span><div className={styles.presets}>
                  {([["today", "Today"], ["yesterday", "Yesterday"], ["two", "Last 2 days"], ["five", "Last 5 days"], ["seven", "Last 7 days"]] as const).map(([mode, label]) => <button key={mode} type="button" onClick={() => props.datePreset(mode)}>{label}</button>)}
                </div></div>
                <label className={styles.field}><span>From</span><div className={styles.date}><CalendarDays size={14} /><input type="date" value={props.postedDateFrom} max={props.postedDateTo || undefined} onChange={(event) => { props.setPostedDateFrom(event.target.value); props.setPage(1); props.applyDesktopFilterChange(); }} /></div></label>
                <label className={styles.field}><span>To</span><div className={styles.date}><CalendarDays size={14} /><input type="date" value={props.postedDateTo} min={props.postedDateFrom || undefined} onChange={(event) => { props.setPostedDateTo(event.target.value); props.setPage(1); props.applyDesktopFilterChange(); }} /></div></label>
              </div>

              <div className={styles.filterRow}>
                <MultiSelect label="Locations" options={props.filterOptions.locations} values={props.locations} onToggle={(value) => props.toggleValue(value, props.locations, props.setLocations)} />
                <MultiSelect label="Skills" options={props.filterOptions.skills} values={props.skills} onToggle={(value) => props.toggleValue(value, props.skills, props.setSkills)} />
                <MultiSelect label="Tools" options={props.filterOptions.tools} values={props.tools} onToggle={(value) => props.toggleValue(value, props.tools, props.setTools)} />
              </div>

              <div className={styles.footer}>
                <span>{props.activeFilters ? `${props.activeFilters} filters active` : "No filters applied"}{props.refreshing ? " • Updating…" : ""}</span>
                <div className={styles.footerActions}><button type="button" className={styles.ghostButton} onClick={props.clearFilters}><X size={14} /> Clear all</button><button type="button" className={styles.primaryButton} onClick={() => props.setFiltersOpen(false)}>Done</button></div>
              </div>
            </div>
          )}
        </section>
      </DashboardFilters>

      <DashboardStats summary={props.summary} />

      <JobList>
        {props.totalJobs === 0 ? (
          <section className={styles.profileEmptyState}>
            <div className={styles.profileEmptyIcon} aria-hidden="true">
              <span>✦</span>
            </div>

            <div className={styles.profileEmptyContent}>
              <div className={styles.profileEmptyEyebrow}>
                PROFILE MATCHING
              </div>

              <h2>
                We&apos;re working on your matches <span aria-hidden="true">🚀</span>
              </h2>

              <p>
                We don&apos;t have{" "}
                <strong>{formatProfileName(props.profileId)}</strong>{" "}
                jobs available yet.
              </p>

              <p className={styles.profileEmptySubcopy}>
                We&apos;re working to add relevant opportunities for this
                profile soon.
              </p>
            </div>
          </section>
        ) : (
          <section className={styles.jobsSection}>
            <JobTable
              jobs={props.jobs}
              profileId={props.profileId}
              totalJobs={props.totalJobs}
              onJobOpen={props.onJobOpen}
            />

            {props.totalJobs > 20 && (
              <div className={styles.pagination}>
                <button
                  type="button"
                  disabled={props.page <= 1}
                  onClick={() =>
                    props.setPage((current) =>
                      Math.max(1, current - 1),
                    )
                  }
                  className={styles.paginationButton}
                >
                  Previous
                </button>

                <span className={styles.paginationInfo}>
                  Page <strong>{props.page}</strong> of{" "}
                  <strong>{props.totalPages}</strong>
                </span>

                <button
                  type="button"
                  disabled={props.page >= props.totalPages}
                  onClick={() =>
                    props.setPage((current) =>
                      Math.min(props.totalPages, current + 1),
                    )
                  }
                  className={styles.paginationButton}
                >
                  Next
                </button>
              </div>
            )}
          </section>
        )}
      </JobList>
    </>
  );
}

function MultiSelect({ label, options, values, onToggle }: { label: string; options: string[]; values: string[]; onToggle: (value: string) => void }) {
  const [query, setQuery] = useState("");
  const multiSelectRef = useRef<HTMLDetailsElement | null>(null);

  useEffect(() => {
    function handleOutsideClick(event: PointerEvent) {
      const details = multiSelectRef.current;
      const target = event.target;
      if (!details || !details.open || !(target instanceof Node)) return;
      if (!details.contains(target)) details.open = false;
    }
    document.addEventListener("pointerdown", handleOutsideClick, true);
    return () => document.removeEventListener("pointerdown", handleOutsideClick, true);
  }, []);

  const filteredOptions = options.filter((option) => option.toLowerCase().includes(query.trim().toLowerCase()));
  return <details ref={multiSelectRef} className={styles.multi}>
    <summary><span>{label}{values.length ? ` (${values.length})` : ""}</span><ChevronDown size={14} /></summary>
    <div className={styles.menu}>
      <div className={styles.menuSearch}><Search size={14} /><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={`Search ${label.toLowerCase()}`} aria-label={`Search ${label}`} />{query && <button type="button" className={styles.menuSearchClear} onClick={() => setQuery("")} aria-label={`Clear ${label} search`}><X size={13} /></button>}</div>
      {filteredOptions.length ? filteredOptions.map((option) => <label key={option} className={styles.option}><input type="checkbox" checked={values.includes(option)} onChange={() => onToggle(option)} /><span>{formatDisplayText(option)}</span></label>) : <div className={styles.empty}>{query ? "No matching options" : "No options available"}</div>}
    </div>
  </details>;
}


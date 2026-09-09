"use client";

import {
  Check,
  ChevronDown,
  Filter,
  X,
} from "lucide-react";

import type { JobFilterOptions } from "@/types/job";

import { useState } from "react";

import styles from "./MobileFilters.module.css";

type Relevance =
  | "all"
  | "gte_30"
  | "gte_70"
  | "50_69"
  | "30_49"
  | "lt_30";

type OpenDropdown =
  | "sort"
  | "posted"
  | "portal"
  | "locations"
  | "skills"
  | "tools"
  | null;

type SortMode =
  | "score"
  | "newest"
  | "oldest";

type Props = {
  open: boolean;
  activeFilters: number;
  filterOptions: JobFilterOptions;

  company: string;
  locations: string[];
  skills: string[];
  tools: string[];
  portal: string;
  relevance: Relevance[];
  sort: SortMode;
  postedDateFrom: string;
  postedDateTo: string;

  setOpen: (open: boolean) => void;

  setCompany: React.Dispatch<
    React.SetStateAction<string>
  >;

  setLocations: React.Dispatch<
    React.SetStateAction<string[]>
  >;

  setSkills: React.Dispatch<
    React.SetStateAction<string[]>
  >;

  setTools: React.Dispatch<
    React.SetStateAction<string[]>
  >;

  setPortal: React.Dispatch<
    React.SetStateAction<string>
  >;

  setSort: React.Dispatch<
    React.SetStateAction<SortMode>
  >;

  toggleValue: (
    value: string,
    current: string[],
    setter: (
      values: string[],
    ) => void,
  ) => void;

  toggleRelevance: (
    value: Relevance,
  ) => void;

  datePreset: (
    mode:
      | "today"
      | "yesterday"
      | "two"
      | "five"
      | "seven",
  ) => void;

  clearFilters: () => void;
  applyFilters: () => void;
};

const relevanceOptions: {
  value: Relevance;
  label: string;
}[] = [
  {
    value: "gte_30",
    label: "30%+",
  },
  {
    value: "gte_70",
    label: "70%+",
  },
  {
    value: "50_69",
    label: "50–69%",
  },
  {
    value: "30_49",
    label: "30–49%",
  },
  {
    value: "lt_30",
    label: "<30%",
  },
];

function ChipGroup({
  label,
  values,
  options,
  open,
  onOpen,
  search,
  onSearchChange,
  onToggle,
}: {
  label: string;
  values: string[];
  options: string[];
  open: boolean;
  onOpen: () => void;
  search: string;
  onSearchChange: (value: string) => void;
  onToggle: (value: string) => void;
}) {
  if (!options.length) {
    return null;
  }

  const filteredOptions = options.filter((option) =>
    option
      .toLowerCase()
      .includes(search.toLowerCase()),
  );

  return (
    <section className={styles.section}>
      <button
        type="button"
        className={styles.dropdownHeader}
        onClick={onOpen}
        aria-expanded={open}
      >
        <span className={styles.dropdownTitle}>
          {label}
        </span>

        <span className={styles.dropdownMeta}>
          {values.length > 0 && (
            <span className={styles.selectedCount}>
              {values.length}
            </span>
          )}

          <ChevronDown
            size={17}
            className={
              open
                ? styles.chevronOpen
                : ""
            }
          />
        </span>
      </button>

      {open && (
        <div className={styles.dropdownPanel}>
          <div className={styles.dropdownSearchWrap}>
            <input
              type="search"
              className={styles.dropdownSearch}
              value={search}
              onChange={(event) =>
                onSearchChange(
                  event.target.value,
                )
              }
              placeholder={`Search ${label.toLowerCase()}`}
              aria-label={`Search ${label}`}
            />
          </div>

          <div className={styles.dropdownOptions}>
            {filteredOptions.length === 0 ? (
              <div className={styles.noResults}>
                No {label.toLowerCase()} found
              </div>
            ) : (
              filteredOptions.map((option) => {
                const selected =
                  values.includes(option);

                return (
                  <button
                    key={option}
                    type="button"
                    className={
                      selected
                        ? styles.checkboxOptionActive
                        : styles.checkboxOption
                    }
                    onClick={() =>
                      onToggle(option)
                    }
                  >
                    <span
                      className={
                        selected
                          ? `${styles.checkbox} ${styles.checkboxChecked}`
                          : styles.checkbox
                      }
                      aria-hidden="true"
                    >
                      {selected && (
                        <Check size={13} />
                      )}
                    </span>

                    <span
                      className={
                        styles.checkboxLabel
                      }
                    >
                      {option}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </section>
  );
}

export default function MobileFilters({
  open,
  activeFilters,
  filterOptions,
  company,
  locations,
  skills,
  tools,
  portal,
  relevance,
  sort,
  postedDateFrom,
  postedDateTo,
  setOpen,
  setCompany,
  setLocations,
  setSkills,
  setTools,
  setPortal,
  setSort,
  toggleValue,
  toggleRelevance,
  datePreset,
  clearFilters,
  applyFilters,
}: Props) {

  const [openDropdown, setOpenDropdown] =
    useState<OpenDropdown>(null);

  const [locationSearch, setLocationSearch] =
    useState("");

  const [skillsSearch, setSkillsSearch] =
    useState("");

  const [toolsSearch, setToolsSearch] =
    useState("");

  function toggleDropdown(
    dropdown: Exclude<OpenDropdown, null>,
  ) {
    setOpenDropdown((current) =>
      current === dropdown ? null : dropdown,
    );
  }

  function closeDropdown() {
    setOpenDropdown(null);
  }


  if (!open) {
    return null;
  }

  const postedActive =
    postedDateFrom || postedDateTo;

  return (
    <div
      className={styles.overlay}
      data-ui="dashboard-filters"
      role="presentation"
      onPointerDown={(event) => {
        if (event.target === event.currentTarget) {
          setOpen(false);
        }
      }}
    >
      <section
        className={styles.sheet}
        role="dialog"
        aria-modal="true"
        aria-label="Job filters"
      >
        <div className={styles.handle} />

        <header className={styles.header}>
          <div className={styles.headerTitle}>
            <span className={styles.filterIcon}>
              <Filter size={15} />
            </span>

            <div>
              <strong>Filters</strong>

              <span>
                Refine your job matches
              </span>
            </div>
          </div>

          <div className={styles.headerActions}>
            {activeFilters > 0 && (
              <button
                type="button"
                className={styles.clearTop}
                onClick={clearFilters}
              >
                Clear all
              </button>
            )}

            <button
              type="button"
              className={styles.closeButton}
              aria-label="Close filters"
              onClick={() =>
                setOpen(false)
              }
            >
              <X size={18} />
            </button>
          </div>
        </header>

        <div className={styles.content}>
          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <span>Sort</span>
            </div>

            <div className={styles.customDropdown}>
              <button
                type="button"
                className={styles.customDropdownButton}
                onClick={() =>
                  toggleDropdown("sort")
                }
                aria-expanded={
                  openDropdown === "sort"
                }
              >
                <span>
                  {sort === "score"
                    ? "Best match"
                    : sort === "newest"
                      ? "Newest first"
                      : "Oldest first"}
                </span>

                <ChevronDown
                  size={17}
                  className={
                    openDropdown === "sort"
                      ? styles.chevronOpen
                      : ""
                  }
                />
              </button>

              {openDropdown === "sort" && (
                <div className={styles.customDropdownMenu}>
                  {[
                    ["score", "Best match"],
                    ["newest", "Newest first"],
                    ["oldest", "Oldest first"],
                  ].map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      className={
                        sort === value
                          ? styles.customDropdownOptionActive
                          : styles.customDropdownOption
                      }
                      onClick={() => {
                        setSort(value as SortMode);
                        closeDropdown();
                      }}
                    >
                      {sort === value && (
                        <Check size={16} />
                      )}
                      <span>{label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <span>Relevance</span>
            </div>

            <div className={styles.quickGrid}>
              {relevanceOptions.map(
                (option) => {
                  const selected =
                    relevance.includes(
                      option.value,
                    );

                  return (
                    <button
                      key={option.value}
                      type="button"
                      className={
                        selected
                          ? styles.quickActive
                          : styles.quick
                      }
                      onClick={() =>
                        toggleRelevance(
                          option.value,
                        )
                      }
                    >
                      {option.label}
                    </button>
                  );
                },
              )}

              <button
                type="button"
                className={
                  relevance.includes("all")
                    ? styles.quickActive
                    : styles.quick
                }
                onClick={() =>
                  toggleRelevance("all")
                }
              >
                All
              </button>
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <span>Posted</span>

              {postedActive && (
                <b>Active</b>
              )}
            </div>

            <div className={styles.customDropdown}>
              <button
                type="button"
                className={styles.customDropdownButton}
                onClick={() =>
                  toggleDropdown("posted")
                }
                aria-expanded={
                  openDropdown === "posted"
                }
              >
                <span>
                  {postedActive
                    ? "Selected date range"
                    : "Any time"}
                </span>

                <ChevronDown
                  size={17}
                  className={
                    openDropdown === "posted"
                      ? styles.chevronOpen
                      : ""
                  }
                />
              </button>

              {openDropdown === "posted" && (
                <div className={styles.customDropdownMenu}>
                  <button
                    type="button"
                    className={styles.customDropdownOption}
                    onClick={() => {
                      datePreset("today");
                      closeDropdown();
                    }}
                  >
                    <span>Today</span>
                  </button>

                  <button
                    type="button"
                    className={styles.customDropdownOption}
                    onClick={() => {
                      datePreset("yesterday");
                      closeDropdown();
                    }}
                  >
                    <span>Yesterday</span>
                  </button>

                  <button
                    type="button"
                    className={styles.customDropdownOption}
                    onClick={() => {
                      datePreset("two");
                      closeDropdown();
                    }}
                  >
                    <span>Last 2 days</span>
                  </button>

                  <button
                    type="button"
                    className={styles.customDropdownOption}
                    onClick={() => {
                      datePreset("five");
                      closeDropdown();
                    }}
                  >
                    <span>Last 5 days</span>
                  </button>

                  <button
                    type="button"
                    className={styles.customDropdownOption}
                    onClick={() => {
                      datePreset("seven");
                      closeDropdown();
                    }}
                  >
                    <span>Last 7 days</span>
                  </button>
                </div>
              )}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <span>Company</span>
            </div>

            <input
              className={styles.input}
              value={company}
              onChange={(event) =>
                setCompany(
                  event.target.value,
                )
              }
              placeholder="Search company"
            />
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHeader}>
              <span>Portal</span>
            </div>

            <div className={styles.customDropdown}>
              <button
                type="button"
                className={styles.customDropdownButton}
                onClick={() =>
                  toggleDropdown("portal")
                }
                aria-expanded={
                  openDropdown === "portal"
                }
              >
                <span>
                  {portal || "All portals"}
                </span>

                <ChevronDown
                  size={17}
                  className={
                    openDropdown === "portal"
                      ? styles.chevronOpen
                      : ""
                  }
                />
              </button>

              {openDropdown === "portal" && (
                <div className={styles.customDropdownMenu}>
                  {[
                    "",
                    ...filterOptions.portals,
                  ].map((value) => (
                    <button
                      key={value || "all"}
                      type="button"
                      className={
                        portal === value
                          ? styles.customDropdownOptionActive
                          : styles.customDropdownOption
                      }
                      onClick={() => {
                        setPortal(value);
                        closeDropdown();
                      }}
                    >
                      {portal === value && (
                        <Check size={16} />
                      )}

                      <span>
                        {value === "linkedin"
                          ? "LinkedIn Jobs"
                          : value === "linkedin_post"
                            ? "LinkedIn Post"
                            : value || "All portals"}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </section>

          <ChipGroup
            label="Locations"
            values={locations}
            options={filterOptions.locations}
            open={openDropdown === "locations"}
            onOpen={() =>
              toggleDropdown("locations")
            }
            search={locationSearch}
            onSearchChange={setLocationSearch}
            onToggle={(value) =>
              toggleValue(
                value,
                locations,
                setLocations,
              )
            }
          />

          <ChipGroup
            label="Skills"
            values={skills}
            options={filterOptions.skills}
            open={openDropdown === "skills"}
            onOpen={() =>
              toggleDropdown("skills")
            }
            search={skillsSearch}
            onSearchChange={setSkillsSearch}
            onToggle={(value) =>
              toggleValue(
                value,
                skills,
                setSkills,
              )
            }
          />

          <ChipGroup
            label="Tools"
            values={tools}
            options={filterOptions.tools}
            open={openDropdown === "tools"}
            onOpen={() =>
              toggleDropdown("tools")
            }
            search={toolsSearch}
            onSearchChange={setToolsSearch}
            onToggle={(value) =>
              toggleValue(
                value,
                tools,
                setTools,
              )
            }
          />
        </div>

        <footer className={styles.footer}>
          <button
            type="button"
            className={styles.clearButton}
            onClick={clearFilters}
          >
            Clear
          </button>

          <button
            type="button"
            className={styles.applyButton}
            onClick={applyFilters}
          >
            {activeFilters > 0
              ? `Show ${activeFilters} active filters`
              : "Apply filters"}
          </button>
        </footer>
      </section>
    </div>
  );
}

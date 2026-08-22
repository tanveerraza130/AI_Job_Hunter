"use client";

import { Search, X } from "lucide-react";
import type { Dispatch, SetStateAction } from "react";
import styles from "./MobileSearch.module.css";

interface Props {
  search: string;
  setSearch: Dispatch<SetStateAction<string>>;
}

export default function MobileSearch({
  search,
  setSearch,
}: Props) {
  return (
    <label className={styles.searchBox}>
      <Search size={19} />

      <input
        value={search}
        onChange={(event) =>
          setSearch(event.target.value)
        }
        placeholder="Search jobs, skills or companies"
        aria-label="Search jobs"
      />

      {search && (
        <button
          type="button"
          onClick={() => setSearch("")}
          aria-label="Clear search"
        >
          <X size={15} />
        </button>
      )}
    </label>
  );
}

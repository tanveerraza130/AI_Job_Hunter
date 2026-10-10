export const DASHBOARD_RETURN_STATE_KEY =
  "ai_job_hunter_dashboard_return_state";

export type DashboardRelevance =
  | "all"
  | "gte_30"
  | "gte_70"
  | "50_69"
  | "30_49"
  | "lt_30";

export type DashboardSort =
  | "score"
  | "newest"
  | "oldest";

export type DashboardReturnState = {
  page: number;
  mobilePage: number;
  search: string;
  company: string;
  locations: string[];
  skills: string[];
  tools: string[];
  portal: string;
  relevance: DashboardRelevance[];
  sort: DashboardSort;
  postedDateFrom: string;
  postedDateTo: string;
  jobId?: string;
  scrollY?: number;
};

export function saveDashboardReturnState(
  state: DashboardReturnState,
) {
  if (typeof window === "undefined") return;

  try {
    localStorage.setItem(
      DASHBOARD_RETURN_STATE_KEY,
      JSON.stringify(state),
    );
  } catch {
    // Navigation must continue even if sessionStorage is unavailable.
  }
}

export function readDashboardReturnState():
  | DashboardReturnState
  | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = localStorage.getItem(
      DASHBOARD_RETURN_STATE_KEY,
    );

    if (!raw) return null;

    const parsed = JSON.parse(raw);

    if (
      !parsed ||
      !Number.isInteger(parsed.page) ||
      parsed.page < 1 ||
      !Number.isInteger(parsed.mobilePage) ||
      parsed.mobilePage < 1
    ) {
      return null;
    }

    return parsed as DashboardReturnState;
  } catch {
    return null;
  }
}

export function clearDashboardReturnState() {
  if (typeof window === "undefined") return;

  try {
    localStorage.removeItem(
      DASHBOARD_RETURN_STATE_KEY,
    );
  } catch {
    // Nothing else to do.
  }
}

import type {
  DashboardSummary,
  JobFilterOptions,
  JobListResponse,
  JobDetail,
} from "@/types/job";

const API_BASE_URL = "/api/v1";
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    },
  );

  if (!response.ok) {
    let message = `API Error: ${response.status}`;

    try {
      const errorData = await response.json();
      if (typeof errorData?.detail === "string") {
        message = errorData.detail;
      } else if (typeof errorData?.message === "string") {
        message = errorData.message;
      }
    } catch {
      try {
        const text = await response.text();
        if (text.trim()) {
          message = text.trim();
        }
      } catch {
        // Keep the HTTP status message.
      }
    }

    throw new Error(message);
  }

  const contentType =
    response.headers.get("content-type") || "";

  if (!contentType.includes("application/json")) {
    const text = await response.text();

    throw new Error(
      text.trim() || "Server returned an invalid response.",
    );
  }

  return response.json();
}

export async function getProfiles(): Promise<{
  profiles: string[];
}> {
  return apiRequest("/profiles");
}


export interface AuthenticatedProfileResponse {
  profile: {
    user_id: string;
    full_name: string;
    phone: string | null;
    profile_id: string;
    preferred_location: string;
    role_level: string;
    experience_years: string;
    current_ctc_lpa: number;
    expected_ctc_lpa: number;
    resume_path: string | null;
  } | null;
  profile_complete: boolean;
}

export async function getMyProfile(
  token: string,
): Promise<AuthenticatedProfileResponse> {
  return apiRequest("/profile", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export async function getDashboardSummary(
  profileId = "crm_manager",
  filters?: GetJobsParams,
): Promise<DashboardSummary> {
  const query = new URLSearchParams();

  query.set("profile_id", profileId);

  if (filters?.search?.trim()) {
    query.set(
      "search",
      filters.search.trim(),
    );
  }

  if (filters?.company?.trim()) {
    query.set(
      "company",
      filters.company.trim(),
    );
  }

  for (const value of filters?.location ?? []) {
    query.append("location", value);
  }

  if (filters?.portal?.trim()) {
    query.set(
      "portal",
      filters.portal.trim(),
    );
  }

  for (const value of filters?.skill ?? []) {
    query.append("skill", value);
  }

  for (const value of filters?.tool ?? []) {
    query.append("tool", value);
  }

    const relevanceValues =
      filters?.relevance ?? [];

    if (
      relevanceValues.length &&
      !relevanceValues.includes("all")
    ) {
      for (
        const value
        of relevanceValues
      ) {
        query.append(
          "relevance",
          value,
        );
      }
    }

  if (filters?.posted_date_from) {
    query.set(
      "posted_date_from",
      filters.posted_date_from,
    );
  }

  if (filters?.posted_date_to) {
    query.set(
      "posted_date_to",
      filters.posted_date_to,
    );
  }

  if (
    filters?.min_score !== undefined
  ) {
    query.set(
      "min_score",
      String(filters.min_score),
    );
  }

  return apiRequest<DashboardSummary>(
    `/dashboard/summary?${query.toString()}`,
  );
}

export interface GetJobsParams {
  page?: number;
  page_size?: number;
  profile_id?: string;
  search?: string;
  min_score?: number;
  location?: string[];
  company?: string;
  portal?: string;
  skill?: string[];
  tool?: string[];
  relevance?:
    | (
        | "all"
        | "gte_30"
        | "gte_70"
        | "50_69"
        | "30_49"
        | "lt_30"
      )[];
  posted_date_from?: string;
  posted_date_to?: string;
  sort?: "score" | "newest" | "oldest";
}

export async function getJobs(
  params?: GetJobsParams,
): Promise<JobListResponse> {
  const query = new URLSearchParams();

  query.set("page", String(params?.page ?? 1));
  query.set("page_size", String(params?.page_size ?? 20));

  if (params?.profile_id) {
    query.set("profile_id", params.profile_id);
  }

  if (params?.search?.trim()) {
    query.set("search", params.search.trim());
  }

  if (params?.min_score !== undefined) {
    query.set("min_score", String(params.min_score));
  }

  if (params?.company?.trim()) {
    query.set("company", params.company.trim());
  }

  if (params?.portal?.trim()) {
    query.set("portal", params.portal.trim());
  }

  for (const value of params?.location ?? []) {
    query.append("location", value);
  }

  for (const value of params?.skill ?? []) {
    query.append("skill", value);
  }

  for (const value of params?.tool ?? []) {
    query.append("tool", value);
  }

    const relevanceValues =
      params?.relevance ?? [];

    if (
      relevanceValues.length &&
      !relevanceValues.includes("all")
    ) {
      for (
        const value
        of relevanceValues
      ) {
        query.append(
          "relevance",
          value,
        );
      }
    }

  if (params?.posted_date_from) {
    query.set("posted_date_from", params.posted_date_from);
  }

  if (params?.posted_date_to) {
    query.set("posted_date_to", params.posted_date_to);
  }

  query.set("sort", params?.sort ?? "newest");

  return apiRequest<JobListResponse>(
    `/jobs?${query.toString()}`,
  );
}

export async function getJobFilterOptions(
  profileId: string,
): Promise<JobFilterOptions> {
  const query = new URLSearchParams();
  query.set("profile_id", profileId);

  return apiRequest<JobFilterOptions>(
    `/jobs/filter-options?${query.toString()}`,
  );
}

export async function getJobDetail(
  jobId: string,
  profileId = "crm_manager",
): Promise<JobDetail> {
  const query = new URLSearchParams();
  query.set("profile_id", profileId);

  return apiRequest<JobDetail>(
    `/jobs/${encodeURIComponent(jobId)}?${query.toString()}`,
  );
}

export type ApplicationStatus =
  | "saved"
  | "pending"
  | "applied"
  | "interview"
  | "rejected"
  | "offer"
  | "not_relevant";

export interface ApplicationRecord {
  job_id: string;
  profile_id: string;
  status: ApplicationStatus;
  applied_at: string | null;
  notes: string;
  updated_at: string;
  created_at: string;
}

export async function getApplication(
  jobId: string,
  profileId: string,
): Promise<{ application: ApplicationRecord | null }> {
  const query = new URLSearchParams();
  query.set("profile_id", profileId);

  return apiRequest(
    `/applications/${encodeURIComponent(jobId)}?${query.toString()}`,
  );
}

export async function getApplicationsBulk(
  jobIds: string[],
  profileId: string,
): Promise<{
  applications: Record<string, ApplicationRecord>;
}> {
  const query = new URLSearchParams();
  query.set("profile_id", profileId);

  for (const jobId of jobIds) {
    query.append("job_id", jobId);
  }

  return apiRequest(
    `/applications?${query.toString()}`,
  );
}

export async function updateApplication(
  jobId: string,
  payload: {
    profile_id: string;
    status: ApplicationStatus;
    applied_at?: string | null;
    notes?: string;
  },
): Promise<{ application: ApplicationRecord }> {
  return apiRequest(
    `/applications/${encodeURIComponent(jobId)}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
  );
}

export async function deleteApplication(
  jobId: string,
  profileId: string,
): Promise<{ success: boolean }> {
  const query = new URLSearchParams();
  query.set("profile_id", profileId);

  return apiRequest(
    `/applications/${encodeURIComponent(jobId)}?${query.toString()}`,
    {
      method: "DELETE",
    },
  );
}

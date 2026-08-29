export type JobStatus =
  | "saved"
  | "pending"
  | "applied"
  | "interview"
  | "rejected"
  | "offer"
  | "not_relevant";

export type JobStatusSource = "naukri" | "company" | "other";

export interface JobApplicationStatus {
  job_id: string;
  profile_id: string;
  status: JobStatus;
  applied_at: string | null;
  notes: string;
  updated_at: string;
  created_at: string;
}

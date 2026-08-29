import type { JobApplicationStatus, JobStatus } from "./jobStatus.types";

type ApplicationResponse = {
  application: JobApplicationStatus | null;
};

export async function getJobStatus(
  jobId: string,
  profileId: string,
): Promise<JobApplicationStatus | null> {
  const response = await fetch(
    `/api/v1/applications/${encodeURIComponent(jobId)}?profile_id=${encodeURIComponent(profileId)}`,
  );

  if (!response.ok) {
    throw new Error("Failed to load job status");
  }

  const data: ApplicationResponse = await response.json();
  return data.application;
}

export async function updateJobStatus(
  jobId: string,
  profileId: string,
  status: JobStatus,
): Promise<JobApplicationStatus> {
  const response = await fetch(
    `/api/v1/applications/${encodeURIComponent(jobId)}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        profile_id: profileId,
        status,
        applied_at: status === "applied" ? new Date().toISOString() : null,
        notes: "",
      }),
    },
  );

  if (!response.ok) {
    throw new Error("Failed to update job status");
  }

  const data: ApplicationResponse = await response.json();

  if (!data.application) {
    throw new Error("Application status was not returned");
  }

  return data.application;
}

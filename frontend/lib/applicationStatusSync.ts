import type { ApplicationStatus } from "@/lib/api";

export const APPLICATION_STATUS_EVENT =
  "ai-job-hunter-application-status";

export type ApplicationStatusEvent = {
  jobId: string;
  status: ApplicationStatus | "not_applied";
};

export function publishApplicationStatus(
  jobId: string,
  status: ApplicationStatus | "not_applied",
) {
  if (typeof window === "undefined") return;

  const detail: ApplicationStatusEvent = {
    jobId: String(jobId),
    status,
  };

  /*
   * CustomEvent is required because the browser's native
   * storage event does NOT fire in the same tab that changed
   * localStorage.
   */
  window.dispatchEvent(
    new CustomEvent(APPLICATION_STATUS_EVENT, {
      detail,
    }),
  );

  /*
   * localStorage keeps the latest status available when
   * navigating between pages or refreshing.
   */
  try {
    localStorage.setItem(
      `${APPLICATION_STATUS_EVENT}:${jobId}`,
      JSON.stringify({
        ...detail,
        updatedAt: Date.now(),
      }),
    );
  } catch {
    // Ignore storage failures; in-memory event still works.
  }
}

export function subscribeApplicationStatus(
  callback: (
    event: ApplicationStatusEvent,
  ) => void,
) {
  if (typeof window === "undefined") {
    return () => {};
  }

  const handler = (event: Event) => {
    const customEvent =
      event as CustomEvent<ApplicationStatusEvent>;

    if (!customEvent.detail?.jobId) return;

    callback(customEvent.detail);
  };

  window.addEventListener(
    APPLICATION_STATUS_EVENT,
    handler,
  );

  return () => {
    window.removeEventListener(
      APPLICATION_STATUS_EVENT,
      handler,
    );
  };
}

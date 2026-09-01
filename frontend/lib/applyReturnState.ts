export type ApplyReturnState = {
  jobId: string;
  awaitingReturn: boolean;
  promptRequired: boolean;
  createdAt: number;
};

const KEY = "ai_job_hunter_apply_return";

export function setApplyAwaitingReturn(jobId: string) {
  const state: ApplyReturnState = {
    jobId: String(jobId),
    awaitingReturn: true,
    promptRequired: false,
    createdAt: Date.now(),
  };

  localStorage.setItem(KEY, JSON.stringify(state));

  return state;
}

export function getApplyReturnState(): ApplyReturnState | null {
  try {
    const raw = localStorage.getItem(KEY);

    if (!raw) return null;

    const parsed = JSON.parse(raw) as Partial<ApplyReturnState>;

    if (!parsed?.jobId) return null;

    return {
      jobId: String(parsed.jobId),
      awaitingReturn: parsed.awaitingReturn === true,
      promptRequired: parsed.promptRequired === true,
      createdAt:
        typeof parsed.createdAt === "number"
          ? parsed.createdAt
          : Date.now(),
    };
  } catch {
    return null;
  }
}

export function markApplyReturned() {
  const current = getApplyReturnState();

  if (!current) return null;

  const next: ApplyReturnState = {
    ...current,
    awaitingReturn: false,
    promptRequired: true,
  };

  localStorage.setItem(KEY, JSON.stringify(next));

  return next;
}

export function clearApplyReturnState() {
  localStorage.removeItem(KEY);
}

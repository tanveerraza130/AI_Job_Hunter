/**
 * Local store of job IDs the current user has reported as dead.
 * Backend does the real hide-on-threshold work; this is for
 * immediate per-user hiding before the next refresh.
 *
 * Keyed by job_id. Cleared on logout.
 */

const KEY = "ai_job_hunter_reported_dead";

function readAll(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

function writeAll(ids: string[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(KEY, JSON.stringify(ids));
  } catch {
    /* quota exceeded — ignore */
  }
}

export function getReportedDeadIds(): Set<string> {
  return new Set(readAll());
}

export function isReportedDead(jobId: string): boolean {
  return getReportedDeadIds().has(String(jobId));
}

export function addReportedDeadId(jobId: string): void {
  const id = String(jobId);
  const current = readAll();
  if (!current.includes(id)) {
    current.push(id);
    writeAll(current);
  }
}

export function clearReportedDeadIds(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(KEY);
}

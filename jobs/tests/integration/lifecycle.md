# Job Registry Lifecycle

## Status Definitions

| Status     | Definition |
|------------|------------|
| **NEW**    | Job discovered but not yet delivered to the user. |
| **SEEN**   | Job has been successfully exported/delivered to the user. |
| **APPLIED** | User has explicitly marked the job as applied. |
| **REJECTED** | User has explicitly rejected the job. |
| **EXPIRED** | Job is no longer relevant (auto-expired by the system). |

## Lifecycle Transitions
Crawler discovers job
│
▼
┌─────────┐
│ NEW │
└────┬────┘
│
│ Exported (user receives it)
│
▼
┌─────────┐
│ SEEN │
└────┬────┘
│
│ User action
│
┌────┴────┐
▼ ▼
┌─────────┐ ┌──────────┐
│ APPLIED │ │ REJECTED │
└─────────┘ └──────────┘

│
│ Time expiry (30+ days with no update)
│
▼
┌─────────┐
│ EXPIRED │
└─────────┘

## Terminal States

`APPLIED`, `REJECTED`, and `EXPIRED` are terminal. No transitions are allowed from these states.

## Implementation Notes

- `NEW → SEEN` transition occurs automatically after a successful export.
- `mark_seen_many()` is used for bulk updates to minimize database calls.
- The SQL query uses `JobStatus` enum values and only updates rows with `status = 'NEW'`, protecting terminal states.
- All other transitions require explicit user or system action.
# SCAS V1 Module Boundaries

V1 uses a modular monolith with async workers for solver jobs.

## Modules

- `identity`: users, roles, JWT/SSO integration points.
- `tenancy`: tenant and school-level isolation configuration.
- `academics`: terms, programs, grade levels, sections, subjects, elective groups.
- `constraints`: constraint profiles and scheduling rules.
- `build_jobs`: lifecycle management (`queued`, `running`, `failed`, `succeeded`, `published`).
- `solver_core`: deterministic OR-Tools scheduling engine and room assignment.
- `conflict_center`: conflict artifacts and suggested resolutions.
- `schedule_versions`: draft/review/published schedule snapshots.
- `integrations`: SIS import/export connectors and run logs.
- `audit`: immutable trail of user actions and system transitions.

## Runtime Responsibilities

- API receives build requests and validates school rule context.
- Build job module persists request metadata and queues worker execution.
- Worker calls solver core with deterministic seed and returns artifacts.
- Conflict center computes room conflicts and action suggestions.
- Publish endpoint transitions succeeded artifacts to published versions.

## Scale Path (V2)

When concurrent schools increase, split these into services:

- `solver-service`
- `integration-service`
- `notification-service`

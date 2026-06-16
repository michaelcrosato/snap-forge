# Archive — parallel research run `opus-4-8` (2026-06-14)

**Status: HISTORICAL — do not edit.** This is a verbatim archive of the parallel research run on branch `research/opus-4-8-20260614-1049` (PR #1, closed as superseded on 2026-06-16). It is kept so the full parallel-run reasoning is preserved in `main`, not only the deltas that were salvaged. The branch is also retained.

**Canonical decisions live in [`../../adr-d1-first-vertical.md`](../../adr-d1-first-vertical.md) … [`../../adr-d5-multi-tenancy.md`](../../adr-d5-multi-tenancy.md).** Do not treat anything in this folder as current — it is a snapshot.

## Contents
- `decisions/` — the run's five ADRs (D1–D5) + summary README, in the original `docs/decisions/` layout (so internal relative links resolve).
- `open-questions.md`, `research-ledger.md` — the run's blocker list and granular evidence ledger.

## What was salvaged from this run into the canonical docs
Verified during the 2026-06-16 consolidation (see [`../../foundation-review-2026-06-15.md`](../../foundation-review-2026-06-15.md)):
- **D1** — Shopmonkey self-service-first integration → `adr-d1-first-vertical.md`
- **D5** — empirical RLS-breach CVE corpus (CVE-2025-48757 etc.) + per-vertical silo escalation → `adr-d5-multi-tenancy.md`
- **D2** — per-domain system-of-record → `adr-d2-system-of-record.md`
- the granular `OPUS-*` evidence rows → appended to `../../research-ledger.md`

## Honest caveat
This run reached the same five verdicts as the build-spike run. That convergence is **corroborating but correlated** (shared source prompts + model family), not independent validation. See [`../../uncertainty-register.md`](../../uncertainty-register.md).

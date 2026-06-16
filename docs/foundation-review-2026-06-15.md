# Foundation review & branch consolidation — 2026-06-15

_A hard-nosed review of every branch and open PR, a decision on what merges into `main`, and the resulting clean-up. The goal of this pass was the one the repo cares about most at this stage: **get the foundation right before any code is written.**_

Method: 8 parallel review/verification agents (both PRs read in full, the test suite actually executed, the two branches diffed head-to-head, and the load-bearing external claims re-verified against live sources/active repos) plus an adversarial red-team pass that argued *against* merging. Findings below were cross-checked against the committed files.

---

## 1. Verdict in one paragraph

The snap-forge research foundation is **real, not vibes** — every load-bearing external fact I could check verified against primary sources to the decimal (n8n's licence, Windmill's AGPL, the SWE-bench Pro numbers, the MCP CVEs, the Postgres RLS semantics). Two parallel research runs (PR #1 `research/opus-4-8` and PR #2 `research/build-spike-blueprint`) **independently converged** on the same five P0 decisions, which is corroborating — but note the convergence is *correlated* (shared prompts + model family), not fully independent. PR #2 is the deeper, buildable artifact and becomes the base; PR #1 is closed after **3 verified findings are salvaged** into the canonical docs. Five dead branches were deleted, and ~5,000 lines of un-integrated review scratch, committed agent "victory" notes, and assertion-free / wrong-database tests were dropped so they never enter `main`.

## 2. Branch & PR dispositions

| Branch / PR | Unique work | Disposition | Reason |
|---|---|---|---|
| `claude/compassionate-perlman-f00583` | 0 commits (tree ≡ `main`) | **Deleted** | Stale pointer, identical tree hash to `main`, local-only |
| `claude/confident-burnell-0106f4` | 0 commits | **Deleted** | ″ |
| `claude/elated-turing-42e151` | 0 commits | **Deleted** | ″ |
| `claude/inspiring-ellis-ccf2ea` | 0 commits | **Deleted** | ″ |
| `codex/deep-research-review-package` | 0 commits | **Deleted** | ″ — empty despite the name |
| **PR #1** `research/opus-4-8-20260614-1049` | 385 lines | **Close — 3 findings salvaged** | Sharper memos but no built code; collides with PR #2 on `open-questions.md` + `research-ledger.md`; mostly subsumed |
| **PR #2** `research/build-spike-blueprint` | 6,402 lines | **Merge — curated** | Real blueprint + verified research, wrapped around droppable scratch |

## 3. PR #1 vs PR #2 — head to head

Both reached identical verdicts on D1–D5 and both independently found the two load-bearing insights: (a) n8n's Sustainable Use Licence bars commercial multi-tenant resale → permissive/code-first orchestrator for SaaS; (b) `service_role`/`BYPASSRLS` means a pure in-process library gateway is refuted → enforce at the DB with `REVOKE` + `SECURITY DEFINER`.

| Decision | Better version | Note |
|---|---|---|
| D1 first vertical | **PR #1** | Shopmonkey self-service primary vs PR #2's Tekmetric-first (which PR #2's *own* reconciliation memo downgrades) |
| D2 system of record | **PR #1** | Explicit per-domain SoR vs binary "incumbent=SoR, Supabase=cache" |
| D3 workflow licence | PR #1 (slightly) | Both correct; PR #1 adds the credential-carve-out kill shot |
| D4 action gateway | **PR #2** | PR #1's memo is better-argued, but PR #2 **built and adversarially tested** the gateway |
| D5 multi-tenancy | tie | PR #1 has the CVE evidence; PR #2 has the implemented controls |

**Outcome:** keep PR #2's ADR set + blueprint as canonical (single `docs/adr-d*.md` scheme), backport PR #1's D1/D2/D5 deltas + evidence ledger.

## 4. Salvaged from PR #1 (now in the canonical docs)

1. **D1 — Shopmonkey self-service-first.** Removes the biggest D1 unknown (can a solo builder get write access). → `adr-d1-first-vertical.md`, `STATUS.md`, `open-questions.md` Q1.
2. **D5 — empirical RLS-breach evidence.** CVE-2025-48757 (170+ Supabase projects breached), RLS-engine CVEs, patch pins, per-vertical silo escalation. PR #2 had zero CVE citations. → `adr-d5-multi-tenancy.md`.
3. **D2 — per-domain system-of-record** + push/delta-poll/reconcile sync contract. → `adr-d2-system-of-record.md`.
4. **The granular evidence ledger** (`OPUS-D{n}-{nn}` rows with per-claim source/date/confidence). → appended to `research-ledger.md`.

## 5. Dropped from PR #2 (kept out of `main`)

| Dropped | Why |
|---|---|
| `docs/research-review/2026-06-14-deep-research/` (13 files) | Self-declared un-integrated holding pen; contains a **competing, contradictory blueprint** (`runs/03`, a 3-function saga + JWT-RLS vs the shipped monolith + GUC-RLS) and a 5-line tool-failure log |
| `.agents/sentinel/handoff.md` | Committed agent "Victory Confirmed" scratch — process exhaust that would enter history permanently |
| `tests/test_linters_adversarial.py`, `tests/test_new_bypasses.py` | **Theater**: 0 assertions; pass under pytest no matter what; they catalog 9 ways their own security linter is bypassable and ship them green |
| `tests/database/*.sql` (4 files) | Eyeball-only psql transcripts / DDL fixtures with no assertions; redundant |
| `tests/database/run_concurrency_test.py` | The only file with real assertions, **but** it hard-codes another project's database (`signalstack-sms-postgres-1` / `signalstack_sms`). It only "passed" because that sibling container happened to be running. The "Victory Auditor" verified against the wrong DB. |

The build-spike's **design** survives in `research/build_spike_blueprint.md`; only the broken test *harness* was removed. Re-introducing a test suite is a build-spike task (see §7), and must arrive with the schema-under-test in-repo + a docker-compose fixture + real assertions wired to exit codes.

## 6. Live-source verification of the load-bearing claims

| Claim (repo) | Verdict | Evidence |
|---|---|---|
| n8n Sustainable Use Licence bars multi-tenant SaaS/embed without commercial terms | **CONFIRMED** | raw `LICENSE.md`; n8n help-centre routes the agency/SaaS pattern to paid Enterprise/Embed |
| Activepieces MIT core + commercial `ee/`; Windmill **AGPLv3**; Trigger.dev / Node-RED Apache-2.0 | **CONFIRMED** | each project's actual LICENSE; Windmill copyleft trap is real |
| SWE-bench Pro Public ~40% top-model failure (gpt-5.4 xHigh 59.1%, slate intact) | **CONFIRMED** | live Scale SEAL board + morphllm match to the decimal |
| tau²-bench ~25pt solo→interactive drop; tau³ voice successor | **CONFIRMED** | arXiv 2506.07982 + Sierra |
| Long-context degrades before advertised window (NoLiMa, Chroma context-rot) | **CONFIRMED** (numbers are prior-gen — date-stamp them) | adobe-research/NoLiMa, Chroma |
| MCP CVEs (49596, 54136, 6514, EscapeRoute 53109/53110); "99 CVEs 2025"; Twilio alpha MCP | **CONFIRMED** | Tenable/Check Point/JFrog/Cymulate; Microsoft blog; `twilio-labs/mcp` (106★) |
| Tekmetric partner API at `api.tekmetric.com`, gated | **CONFIRMED** (terms genuinely unverifiable from outside — correctly logged as a blocker) | tekmetric.com/integrations |
| Postgres RLS + `FORCE RLS` + `SECURITY DEFINER` non-superuser writer model | **CONFIRMED** — strongest part; the `set_config(...,true)` + `nullif('')` pooler defence is the correct answer | PostgreSQL + Supabase docs |
| **"AI does not reliably build large integrated systems"** | **OVERSTATED** | METR 50%-task horizon ~14.5h doubling every 4–7mo; Codex 25h runs; ~89% SWE-bench Verified with context engineering. Small-blocks still correct — but for *reviewability / audit / rollback* economics, not a hard capability wall |

## 7. Required follow-ups before the first build spike

These are logged in `open-questions.md` (Q1, Q8, Q9) and are the conditions for the foundation to be *build-ready*, not just *clean*:

1. **Confirm Shopmonkey write scope** on the entry plan before building (Q1). The gateway hard-requires writes; if write is partner-gated, the build order changes.
2. **Fix the blueprint's auth model** (Q8): fixtures must set `request.jwt.claims` JSON so `auth.uid()` resolves, or the blueprint's own tests fail on real Supabase. Rebuild the test harness in-repo with real assertions + a docker-compose fixture.
3. **Resolve the tenant-context + two-blueprint fork** (Q9): pick JWT-claim RLS vs the session GUC, and the monolithic gateway vs the request→approve→execute split; make the SQL match the ADR prose.
4. **Enforce audit immutability** (not just assert it): add a trigger/constraint preventing UPDATE/DELETE on `audit.audit_logs`, a `tenant_id` FK, and an optional per-tenant hash chain — required for the PHI/cannabis verticals the ADRs steer toward.
5. **Soften thesis claim (b)** in the research report toward its own "scoping dominates" wording, and date-stamp the NoLiMa/Chroma numbers as prior-generation.

## 8. What "clean" means now

`main` after this consolidation: the research report + peer critique + reverification, one ADR set (`docs/adr-d1..d5`), one `open-questions.md`, one `research-ledger.md` (with PR #1's evidence backbone folded in), the build-spike blueprint + its open-questions resolution, and this review. No duplicate ADR trees, no committed agent scratch, no theater tests, no foreign-project dependencies. `.gitignore` now excludes orchestration scratch and Python caches so process exhaust can't leak back in.

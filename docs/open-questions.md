# snap-forge — open questions & unresolved risks

_Run: `research/opus-4-8-20260614-1049` · MODEL_ID `opus-4-8` · MODE `research-only` · 2026-06-14._
_Companion to the P0 decision memos in `decisions/` and the evidence table in `research-ledger.md`._

This file holds what research **cannot** settle in this run: items that can only be settled by building, P1 decisions deferred past the P0 exit, build-time confirmations, and blockers. Per the protocol, blocked items are written here rather than looped on.

---

## Run parameters (set at Loop 0)
- **MODEL_ID:** opus-4-8
- **FIRST_VERTICAL:** auto-repair _(provisional — formally tested in decision D1)_
- **MODE:** research-only → **Section 6 build-spikes are disabled.** Anything classed SETTLE-BY-BUILDING is logged here, not built.
- **BUDGET:** MAX_LOOPS_PER_DECISION = 3; SESSION_WALL_CLOCK = 4h.

## Loop 0 triage result (risk register reconciled against the existing docs)
P0 decisions D1–D5 were all classed **RESEARCHABLE** (sent to the loop) except the portion of D4 noted below. No seed risks were dropped or merged; D6–D10 remain **P1** and are deferred past the P0 exit (Section 5a only requires P0 ADRs).

The existing docs (`snap-forge-research-report.md`, `peer-proposal-critique.md`, `reverification-2026-06-14.md`) already settle the **thesis-level** claims (small blocks > monolith; context-window-as-glue refuted; adopt-the-substrate; the typed-action-gateway spine). The P0 loop targets the **decision-grade gaps** those docs left open — most importantly the n8n commercial-license question (D3), which is the most likely architecture-changer.

---

## SETTLE-BY-BUILDING (research cannot resolve; would need a Section 6 spike — disabled this run)

Research **did** settle the gateway's *enforcement mechanism* (D4 → library-for-logic + DB-level REVOKE + SECURITY DEFINER writer role; not pure-library). What remains genuinely build-only is *ergonomics and grain under a real write*. Build the reference block **QR-scan → `inventory.adjust_quantity` → SMS** through the full spine to settle:

- **D4-SBB-1 — Write-path cost.** Real p99 latency + ergonomics of routing every write through SECURITY DEFINER RPCs vs direct table writes. If intolerable for bulk/low-latency paths, enforce only money/PHI/compliance/destructive writes at the DB layer and leave trivial writes to the library.
- **D4-SBB-2 — Action vs transaction grain.** Whether audit+outbox-in-one-transaction forces "one action = one transaction" to be coarser than "one action per block."
- **D4-SBB-3 — Approval-gate composition.** Whether `pending → approved → committed` composes cleanly with the SECURITY DEFINER write path or needs a staging table.

**→ Build this slice first if MODE flips to research-then-spike. It is also the recommended next build step regardless (see [`decisions/README.md`](decisions/README.md)).**

## Owner decisions (research-surfaced; need a human call, not more research)
- **D3 — n8n license budget.** The orchestrator default moved to **Activepieces (MIT) / Trigger.dev (Apache-2.0)** because n8n's Sustainable Use License bars free commercial multi-tenant use (see [ADR-D3](decisions/ADR-D3-workflow-engine-license.md)). **If n8n's node ecosystem is wanted anyway, that requires budgeting a paid n8n Enterprise/Embed license** — an owner decision. Alternatively, request written confirmation from n8n GmbH that snap-forge's specific architecture qualifies for the free license.
- **D5 — regulated-vertical isolation sign-off.** Whether pooled shared-schema RLS is contractually acceptable for any future PHI/Metrc tenant, or whether those tenants must be siloed (project-per-tenant). Needs a compliance/risk call before taking a regulated client.

## Build-time confirmations (not research — confirm when the vertical/client is picked)
- **Shopmonkey plan tier + write scope** — confirm directly with Shopmonkey that API access (especially **write** scope, needed for the action gateway) is included on the entry ($199) plan and is not certified-partner-only. _(D1 flip condition.)_
- **Tekmetric access** — file the request early (~2–3 week approval, granted at Tekmetric's discretion). _(D1.)_
- **Per-state Metrc requirements & deadlines** — re-confirm for the specific state when a cannabis client is taken (NY manual-reporting sunset was May 5 2026; re-check current). _(Report §11.)_
- **Exact incumbent API endpoints + webhook/CDC capability** — Tekmetric / Dutchie / OpenEMR concrete endpoints, auth, rate limits, webhook coverage, `updatedDateStart`-style delta params — confirm at integration time. _(Sharpened by D2; Tekmetric has only narrow webhooks + hourly sync.)_

## Deferred P1 decisions (revisit after P0 build step starts)
- **D6** AI runtime boundary — build-time only vs HITL assistant vs limited runtime proposer.
- **D7** MCP/tooling boundary — dev-time/reference vs production dependency. _(Report §4 leans dev-time/human-supervised; not yet a formal ADR.)_
- **D8** AI-authored-code governance — tests, review gates, static analysis, rollback, branch policy.
- **D9** Compliance boundary — PHI, PCI, Metrc, message approval, data retention. _(Report §7 covers the gates; not yet a per-action ADR.)_
- **D10** Operational burden — self-host vs managed; small-business support model.

## Parallel-agent reconciliation (Section 8)
A second agent is running this same protocol concurrently on branch **`research/gemini-3-5-flash-20260614-1043`** (seen via `git worktree list`). **No single ledger is authoritative until reconciled by claim ID.** Before any build step, merge this run's `research-ledger.md` with that branch's by stable claim ID and adjudicate any contradictory A–E labels. This run's IDs are namespaced `OPUS-*` to keep the merge clean.

---

_Blockers encountered during the run get appended below (Section 9)._

# Project status

**Stage: research & foundation.** No application code yet. The current work is research, critique, decision memos, and build-spike scoping so the first implementation starts from explicit constraints rather than assumptions.

## Done

- **Landscape + market scan + build-vs-adopt blueprint** — [`snap-forge-research-report.md`](snap-forge-research-report.md). Verdict: build small single-purpose blocks; adopt the substrate; treat the AI context window as human-in-the-loop glue, not the unattended integration backbone.
- **Critique of three peer architecture proposals** — [`peer-proposal-critique.md`](peer-proposal-critique.md). Verdict: the typed-action-registry + approval-gate discipline is the peer proposal idea worth importing.
- **Clean re-verification** — [`reverification-2026-06-14.md`](reverification-2026-06-14.md). Live repo/platform data and MCP approval-gate guidance were folded into the blueprint.
- **Decision memos D1-D5** — formalized first vertical, system-of-record boundary, workflow-engine licensing, action-gateway boundary, and tenant-isolation model.
- **Research ledger and blocker list** — [`research-ledger.md`](research-ledger.md) tracks the verified claims and classifications; [`open-questions.md`](open-questions.md) tracks partner/commercial/build-spike blockers.
- **Parallel research reconciliation** — the sibling `research/opus-4-8-20260614-1049` worktree's open questions were reconciled into the ledger and blocker list, including D4's build-spike caveat and deferred P1 decisions D6-D10.

## Current Branch and Run

- **Branch:** `research/gemini-3-5-flash-20260614-1043`
- **Mode:** research-only
- **First vertical:** `auto-repair`
- **First reference workflow:** `QR/bin scan -> gateway-approved inventory adjustment -> system-of-record update -> staff/customer notification`

## Current Decisions

1. **First vertical:** Auto repair, with Tekmetric as the first incumbent to evaluate.
2. **System of record:** Incumbent system remains authoritative; Supabase is an operational projection, audit log, and outbox.
3. **Workflow engine:** n8n is acceptable for single-tenant/internal deployments; multi-tenant SaaS should use a permissive/code-first runtime or a commercial agreement.
4. **Gateway:** Every mutation and high-risk side effect goes through a typed action gateway with audit, idempotency, and approval rules.
5. **Tenancy:** Start with shared Postgres + tenant-scoped RLS + direct-write revocation + runtime service-role restrictions.

## Next Step

Run the first build spike:

1. Acquire Tekmetric partner/API documentation or choose a mock incumbent adapter if access is delayed.
2. Scaffold Supabase local development.
3. Implement one `inventory.adjust_quantity` action contract with RLS, revoked direct writes, RPC/gateway path, audit log, outbox event, and approval queue.
4. Add tests that prove direct writes fail, cross-tenant access fails, approved gateway writes succeed, and duplicate idempotency keys do not double-apply.
5. Pick the first orchestration runtime based on the deployment model: n8n for client-owned/internal, Trigger.dev/Node-RED/custom outbox worker for SaaS.

## Open for Review

The foundation is still deliberately reviewable. The highest-risk assumptions are now isolated in [`open-questions.md`](open-questions.md), especially Tekmetric partner terms, workflow-engine licensing by deployment model, gateway ergonomics under a real write, Supavisor/session behavior, and the deferred P1 decisions D6-D10.

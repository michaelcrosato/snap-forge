# Project status

**Stage: research & foundation.** No application code yet. The current work is research, critique, decision memos, and build-spike scoping so the first implementation starts from explicit constraints rather than assumptions.

## Done

- **Landscape + market scan + build-vs-adopt blueprint** — [`snap-forge-research-report.md`](snap-forge-research-report.md). Verdict: build small single-purpose blocks; adopt the substrate; treat the AI context window as human-in-the-loop glue, not the unattended integration backbone.
- **Critique of three peer architecture proposals** — [`peer-proposal-critique.md`](peer-proposal-critique.md). Verdict: the typed-action-registry + approval-gate discipline is the peer proposal idea worth importing.
- **Clean re-verification** — [`reverification-2026-06-14.md`](reverification-2026-06-14.md). Live repo/platform data and MCP approval-gate guidance were folded into the blueprint.
- **Decision memos D1-D5** — formalized first vertical, system-of-record boundary, workflow-engine licensing, action-gateway boundary, and tenant-isolation model.
- **Research ledger and blocker list** — [`research-ledger.md`](research-ledger.md) tracks the verified claims and classifications; [`open-questions.md`](open-questions.md) tracks partner/commercial/build-spike blockers.
- **Parallel research reconciliation (2026-06-15)** — the sibling `research/opus-4-8-20260614-1049` run produced a full ADR set + granular evidence ledger. Its deferred P1 decisions (D6-D10) plus its load-bearing unique findings — Shopmonkey self-service primary (D1), the empirical RLS-breach CVE corpus (D5), and the per-domain system-of-record model (D2) — were salvaged into the canonical ADRs and ledger; that branch is now closed as superseded. Full disposition: [`foundation-review-2026-06-15.md`](foundation-review-2026-06-15.md).

## Current Branch and Run

- **Branch:** `main` — consolidated 2026-06-15 from `research/build-spike-blueprint`, with verified findings salvaged from `research/opus-4-8-20260614-1049`
- **Mode:** research-only
- **First vertical:** `auto-repair`
- **First reference workflow:** `QR/bin scan -> gateway-approved inventory adjustment -> system-of-record update -> staff/customer notification`

## Current Decisions

1. **First vertical:** Auto repair. First **integration** is **Shopmonkey** (self-service API keys, no partner gate); **Tekmetric** is the approval-gated secondary (~2–3 week access lead time), filed in parallel. See [`adr-d1-first-vertical.md`](adr-d1-first-vertical.md).
2. **System of record:** Incumbent system remains authoritative; Supabase is an operational projection, audit log, and outbox.
3. **Workflow engine:** n8n is acceptable for single-tenant/internal deployments; multi-tenant SaaS should use a permissive/code-first runtime or a commercial agreement.
4. **Gateway:** Every mutation and high-risk side effect goes through a typed action gateway with audit, idempotency, and approval rules.
5. **Tenancy:** Start with shared Postgres + tenant-scoped RLS + direct-write revocation + runtime service-role restrictions.

## Next Step

Run the first build spike:

1. Build against the **Shopmonkey** self-service sandbox first (confirm the entry plan includes **write** scope); file the Tekmetric partner/API access request in parallel; a mock incumbent adapter is the fallback if both slip.
2. Scaffold Supabase local development.
3. Implement one `inventory.adjust_quantity` action contract with RLS, revoked direct writes, RPC/gateway path, audit log, outbox event, and approval queue.
4. Add tests that prove direct writes fail, cross-tenant access fails, approved gateway writes succeed, and duplicate idempotency keys do not double-apply.
5. Pick the first orchestration runtime based on the deployment model: n8n for client-owned/internal, Trigger.dev/Node-RED/custom outbox worker for SaaS.

## Open for Review

The foundation is still deliberately reviewable. The highest-risk assumptions are now isolated in [`open-questions.md`](open-questions.md), especially Tekmetric partner terms, workflow-engine licensing by deployment model, gateway ergonomics under a real write, Supavisor/session behavior, and the deferred P1 decisions D6-D10.

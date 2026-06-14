# ADR-D4 — Typed action-gateway contract (library vs service vs node)

- **Verdict:** MODIFY · **Confidence:** high
- **Classification:** B (modify-compose) · **Role:** the spine — enforcement model for all writes
- **Independent verification:** supported · **Has a SETTLE-BY-BUILDING tail** (see below + [open-questions](../open-questions.md))
- **Run:** `research/opus-4-8-20260614-1049` · 2026-06-14 · ledger IDs `OPUS-D4-*`

## Decision
Keep the gateway **logic** as a thin in-process library/module (the doc's altitude is right), but make the chokepoint **invariant** real in the **database**, not in app code. The right axis is **in-process vs in-database**, not library-vs-service.

## Claim tested
> "Build the typed-action gateway as a thin MODULE inside a modular monolith (not a separate service). Every block performs one typed action; nothing writes to the core or calls out except through the gateway." — testing the **chokepoint invariant** in snap-forge's real topology (orchestrator + Edge Functions + webhook handlers all sharing one Postgres).

## Load-bearing sources
1. **Supabase Postgres Roles / service_role** — https://supabase.com/docs/guides/database/postgres/roles — `service_role` carries **BYPASSRLS** and is what backend callers (Edge Functions, webhooks, orchestrator DB node) use. A library a sibling process never imports cannot bind it ⇒ **pure-library invariant refuted**.
2. **PostgREST 12 — Database Authorization** — https://docs.postgrest.org/en/v12/explanations/db_authz.html — `REVOKE EXECUTE ... FROM PUBLIC`, selective table grants, and **SECURITY DEFINER** functions create a bottleneck where writes happen exclusively through controlled function interfaces. The DB is the authoritative authorization layer.
3. **PostgreSQL — Row Security** — https://www.postgresql.org/docs/current/ddl-rowsecurity.html — BYPASSRLS bypasses **row security only**, *not* the GRANT/REVOKE table-privilege system; a BYPASSRLS role still needs table privileges. (The nuance that makes the DB-level fix valid.)

## Evidence for (library-for-logic is correct)
- In-process logic = no network hop, atomic ACID transactions in one DB without 2PC, single deployable. Permission/validate/idempotency/audit/approval **logic** belongs in-process.
- The single-typed-action contract maps onto the mature **command-bus/CQRS write side**; audit+event maps onto the **transactional outbox** (AWS Prescriptive Guidance). Not novel risk.

## Evidence against (why the invariant needs more than a library)
- **service_role/BYPASSRLS is a second write path by construction** — Edge Functions/webhooks/orchestrator hold the key and write straight to tables; the library never executes.
- **PEP/PDP principle:** "every unprotected pathway is a potential bypass." A library PEP only covers callers that link it; it cannot bind processes that don't import it.
- **Even a network service doesn't guarantee the invariant** — anyone holding `service_role` can connect to Postgres directly and bypass it too. Service-vs-library is the wrong axis.
- **The one-action-per-block discipline has real friction** the doc glosses: (a) low-latency/bulk **reads** forced through a write-style contract is an anti-pattern (CQRS exists to let the read side bypass it); (b) a business transaction spanning multiple actions needs them in **one** DB transaction, pushing toward a coarser "one action = one transaction" grain; (c) **bulk** ops modeled as N single actions are pathological — you need first-class bulk actions / set-based RPCs.

## The surviving design (verified)
- **Logic:** thin in-process library/module.
- **Invariant:** REVOKE INSERT/UPDATE/DELETE on core tables from `anon`/`authenticated`/and the role the orchestrator/Edge-Functions/webhooks use; grant writes **only** to a dedicated writer role exercised through **SECURITY DEFINER** functions (one per typed action) that write the audit row + emit the outbox event in the **same transaction**. Then "nothing writes except through the gateway" is *physically* true.
- **Escape hatches** so the discipline doesn't generate ugly workarounds: (i) **reads** go through RLS/SELECT grants directly (CQRS read side), not the typed-action contract; (ii) first-class **bulk** actions / set-based RPCs; (iii) a typed action may be a **multi-statement** SECURITY DEFINER function for atomic multi-step business transactions.

## Falsification attempt
Tried hardest to falsify the doc's chokepoint invariant: can a thin library guarantee "nothing writes except through the gateway" with orchestrator + Edge Functions + webhooks on one Postgres? **Refuted** (service_role bypass). Also tried to falsify the inverse "you must make it a network service" → **also not required** (a service is bypassable by the same key). Only **DB-level enforcement** closes every path.

## Independent verification
Verifier independently confirmed the full causal chain: service_role bypasses RLS (Supabase) → but BYPASSRLS bypasses **RLS policies only, not GRANT/REVOKE** (PostgreSQL official) → service_role is **not a superuser** (Supabase discussion #36362) → therefore table-level REVOKE **does** bind service_role, proven by the real-world `42501 permission denied` pattern after `ALTER DEFAULT PRIVILEGES ... REVOKE ... FROM ... service_role`, with SECURITY DEFINER functions as the documented controlled write path. Verdict **supported**. No primary-source contradiction found.

## What would flip this
1. snap-forge **guarantees a single process owns all DB writes** (orchestrator/Edge-Functions/webhooks never hold a DB-writing credential; they call the gateway's RPC for every write) → a library + discipline could suffice and DB-level REVOKE becomes belt-and-suspenders.
2. A built reference block shows wrapping **every** write in a SECURITY DEFINER RPC is intolerable for bulk/low-latency hot paths → enforce only money/PHI/compliance/destructive writes at the DB layer, leave trivial writes to the library (a partial MODIFY).
3. Supabase removes the service_role-BYPASSRLS model → the "second write path" evidence weakens.
> Nothing realistic flips it back to "pure library guarantees the invariant" — that is refuted on the primary docs.

## SETTLE-BY-BUILDING (research cannot resolve — MODE=research-only, logged to open-questions)
1. Real **p99 latency / ergonomic cost** of routing every write through SECURITY DEFINER RPCs vs direct table writes — measure on one reference block before committing to "every write."
2. Whether **audit+outbox-in-one-transaction** forces "one action = one transaction" to be coarser than "one action per block."
3. Whether the **approval gate** (`pending → approved → committed`) composes cleanly with the SECURITY DEFINER write path or needs a staging table.

## Recommendation
MODIFY report §9 item 3 + the spine box to the two-layer statement above (logic = in-process library; invariant = DB grants + SECURITY DEFINER write functions + outbox; explicit read/bulk/multi-step escape hatches). **Build ONE reference block (`inventory.adjust_quantity`) end-to-end through the full library + SECURITY-DEFINER path first; do not generalize the contract until that exists.**

# ADR-D4: Action-Gateway Contract and Boundary

- **Status**: DECISION-GRADE for contract; SPIKE-REQUIRED for implementation mechanics
- **Verdict**: MODIFY `database-level-rpc-gate`
- **Confidence level**: High for gateway requirement; medium for PL/pgSQL-first implementation until benchmarked
- **Date**: 2026-06-14

## Goal
Define the typed action gateway that keeps AI-authored blocks, UI clients, and background jobs from performing unchecked writes or side effects.

## Decision
Implement a **database-enforced action gateway** as the default mutation path:

1. **Typed action contracts**: Every mutation or external side effect starts as a named action with schema, actor, tenant, idempotency key, risk class, reads, writes, emits, and approval policy.
2. **Direct write lockdown**: Revoke direct `INSERT`, `UPDATE`, and `DELETE` grants from runtime-facing roles on operational tables. Expose mutations through narrowly granted RPC/functions and/or a server-side gateway that calls those functions.
3. **Audit in the transaction**: Every approved mutation writes an audit row and, when needed, an outbox event in the same database transaction as the projection change.
4. **Approval gate**: Money movement, PHI, compliance writes, destructive/bulk actions, and AI-authored outbound messages must create an approval request and return `PENDING_APPROVAL` until a human approves.
5. **Privileged functions with guardrails**: Prefer `SECURITY INVOKER` where possible. Use `SECURITY DEFINER` only for narrowly scoped functions with explicit tenant checks, fixed `search_path`, least-privilege grants, and tests for bypass behavior.
6. **No runtime `service_role` in blocks**: Runtime blocks must not hold Supabase service-role credentials. Admin keys are restricted to migrations and tightly controlled back-office jobs.

## Evidence Table

| Source | Evidence | Decision impact |
|---|---|---|
| Supabase API security docs | Grants determine which roles can access tables/views/functions over the Data API; RLS then controls row visibility. | Use grants and RLS together; do not rely on application convention alone. |
| PostgREST RPC docs | Exposed PostgreSQL functions can be invoked under `/rpc` and can abstract state changes. | Supports RPC-style mutation boundary. |
| Supabase function docs | `SECURITY DEFINER` is powerful and requires a fixed `search_path`; `SECURITY INVOKER` is the default/best practice. | Gateway functions need careful implementation rules, not blanket definer functions. |
| Supabase RLS/key docs | Service keys can bypass RLS and must not be exposed to customers or browsers. | Runtime blocks cannot hold service-role credentials if the gateway is meant to be authoritative. |
| MCP tool spec | The MCP spec says a human should be able to deny tool invocations and recommends clear confirmation prompts. | Supports hard approval gates for high-risk snap-forge actions. |
| OWASP LLM Top 10 | Excessive agency and prompt injection risks require limiting what model-driven systems can do. | AI suggests actions; deterministic gateway decides whether they can execute. |

## Falsification Attempt

### Thesis
Enforce the gateway only in TypeScript Edge Functions because TypeScript is easier to write and test than PL/pgSQL.

### Result: REFUTED AS THE ONLY BOUNDARY
TypeScript Edge Functions are useful orchestration glue, but they are not sufficient as the sole enforcement boundary. If runtime code has direct table grants or service-role credentials, a block can bypass the gateway by accident or through AI-authored boilerplate. Database grants/RLS/functions create a stronger default-deny boundary for normal runtime roles. TypeScript remains useful for validation ergonomics, external API calls, and outbox workers, but the database must still reject direct unauthorized mutations.

## Known Contradictions
- PL/pgSQL can be harder for AI coding agents and reviewers than TypeScript. Keep functions small, generated from typed contracts where possible, and covered by migration tests.
- `SECURITY DEFINER` can become its own bypass if written carelessly. Keep privileged functions in a small, reviewed surface area.
- Service-role/admin credentials can still bypass controls. The design relies on credential isolation plus static analysis and CI checks to prevent runtime use.

## What New Evidence Would Flip This Decision
1. Supabase introduces first-class immutable mutation hooks or audit policies that run for every table mutation and cannot be bypassed by runtime roles.
2. A build spike proves PL/pgSQL RPCs are too slow or too hard to maintain, and an equivalent database-enforced grant boundary can be maintained with invoker functions plus TypeScript validation.
3. The product scope changes to single-tenant/local-only with no AI-authored writes, no regulated data, and no high-risk side effects.

## Build Spike Requirements
1. Create one `inventory.adjust_quantity` action contract.
2. Generate or hand-write the minimum SQL migration: tables, RLS, revoked direct writes, RPC, audit log, outbox event.
3. Add tests proving direct table writes fail for runtime roles and the RPC succeeds only with valid actor/tenant/idempotency inputs.
4. Add static checks that reject runtime `service_role` usage and direct operational table mutations from block code.

## Primary Sources
1. [Supabase: Securing your API](https://supabase.com/docs/guides/api/securing-your-api)
2. [Supabase: Database Functions](https://supabase.com/docs/guides/database/functions)
3. [Supabase: Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
4. [PostgREST: Functions as RPC](https://docs.postgrest.org/en/v12/references/api/functions.html)
5. [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
6. [OWASP Top 10 for LLM Applications](https://genai.owasp.org/)

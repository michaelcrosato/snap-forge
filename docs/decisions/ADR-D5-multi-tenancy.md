# ADR-D5 — Multi-tenancy & isolation model

- **Verdict:** MODIFY · **Confidence:** high
- **Classification:** B (modify-compose) · **Role:** isolation/security model
- **Independent verification:** the bare "RLS is sufficient" claim was **refuted as stated** → confirms the MODIFY
- **Run:** `research/opus-4-8-20260614-1049` · 2026-06-14 · ledger IDs `OPUS-D5-*`

## Decision
Keep shared-schema RLS (`tenant_id` + policies) as the **pool-model baseline for non-regulated verticals**, but stop treating it as *sufficient on its own*. Add mandatory **service_role discipline**, CI RLS-coverage linting, patched Postgres, and a **per-vertical escalation** to schema-/db-per-tenant (silo) for regulated data.

## Claim tested
> "Per-business isolation via Postgres Row-Level Security (shared schema, `tenant_id`, RLS policies) is sufficient for snap-forge's multi-tenant isolation, including for regulated data."

## Load-bearing sources
1. **Supabase — Row Level Security (incl. "Bypassing RLS")** — https://supabase.com/docs/guides/database/postgres/row-level-security — verbatim: "Supabase provides special Service keys, which can be used to bypass RLS." The backend tier (action-gateway + blocks) runs as `service_role` ⇒ **RLS is not the boundary for that tier**. Also documents the performance fixes (`(select auth.uid())`, index `tenant_id`, `TO authenticated`).
2. **CVE-2025-48757 (CVSS 9.3)** — https://mattpalmer.io/posts/2025/05/CVE-2025-48757/ — missing/insufficient RLS exposed PII, API keys, payment data across **170+ production Lovable+Supabase projects**. The "forgot/under-scoped RLS = breach" failure mode is **empirical**, on this exact stack.
3. **AWS SaaS Lens — Tenant Isolation** + **Supabase HIPAA Projects** — https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/tenant-isolation.html · https://supabase.com/docs/guides/platform/hipaa-projects — a tenant-boundary crossing is "potentially unrecoverable"; compliance routinely pushes tenants to **silo**; Supabase's own HIPAA model operates at the **project** level (BAA on Team/Enterprise + add-on, "High Compliance" config; not self-hosted). The compliance unit of isolation is the **project, not the row**.

## Evidence for (RLS is a sound baseline — for end-user requests)
- Shared-schema RLS is the first-class Supabase pattern and maps to AWS's "pool" model (a valid, cost/agility-optimal partitioning model) — sound for **JWT-bearing end-user requests**.
- Supabase's secure-by-default hardening reduces the "forgot RLS" footgun: RLS on by default (dashboard tables), the **Splinter** linter flags `0013_rls_disabled_in_public`, owner alerts for RLS-disabled exposed tables.
- RLS-at-scale performance is solved when you follow the advisory: `(select auth.uid())` ~179ms→9ms; indexing tenant column ~171ms→<0.1ms; `TO authenticated` ~170ms→<0.1ms.

## Evidence against (why "sufficient" is refuted)
- **service_role bypasses RLS by design.** snap-forge's gateway + server-side blocks run elevated; any query they run ignores `tenant_id` policies. A single missing tenant-filter in a service_role path = full cross-tenant breach with **zero DB-level backstop**.
- **Shared-schema failure mode is real and recurrent** — CVE-2025-48757 (at scale, in production).
- **The engine itself can leak across the RLS boundary** — CVE-2024-10976 (wrong policy under subqueries/role/plan reuse), CVE-2025-8713 (optimizer statistics leak RLS-hidden rows). Correctness is contingent on staying patched (≥17.1/16.5 and ≥17.6/16.10).
- **Regulated posture** — AWS SaaS Lens + Supabase's own HIPAA productization treat **project/silo** as the compliance unit, not the row. Shared-schema-RLS is weaker than the vendors themselves recommend for PHI.

## Falsification attempt
Tried to **confirm** the doc: that disciplined shared-schema RLS (on-by-default + Splinter + perf-optimized policies) fully closes the gap even for regulated data. **Failed** on two independent points: (1) the gateway/blocks run as `service_role`, which bypasses RLS — RLS gives **zero** isolation for the very tier doing most cross-tenant-capable work; (2) for regulated verticals both AWS and Supabase treat project/silo as the compliance unit. CVE-2025-48757 shows the failure mode is empirical, not theoretical.

## Independent verification
Verifier independently fetched Supabase's RLS doc (verbatim service-key bypass), the api-keys + roles docs (service_role = BYPASSRLS, not a superuser), and the CVE-2025-48757 primary disclosure. Found the genuine nuance that if a **user JWT** is attached, the client adheres to that user's RLS even under a service key — but this does **not** rescue the claim because snap-forge's elevated paths are server-to-server with **no** user JWT. Verdict: the bare "sufficient" claim is **refuted**, which is exactly what MODIFY asserts.

## What would flip this
- **Back to CONFIRM (RLS sufficient everywhere):** the gateway/blocks are redesigned to **never** use service_role for tenant data — every path runs under a per-request authenticated role (RLS in force) or a dedicated **non-BYPASSRLS** role + `set_config('request.jwt.claims')` / tenant-scoped role so RLS is always evaluated — **and** regulated verticals get documented sign-off that pooled isolation meets BAA/Metrc obligations.
- **Toward REFUTE / silo-mandatory:** a regulator, Metrc requirement, or customer BAA explicitly requires physical/database-level isolation.
- **Key uncertainty to resolve:** the exact DB-role/credential model the action-gateway uses against Supabase (ties directly to [D4](ADR-D4-gateway-contract.md)).

## Recommendation
Keep shared-schema RLS as default for **non-regulated** verticals (auto-repair). Mandate: (1) **service_role discipline** — service_role for narrow admin/system jobs only; gateway/blocks access tenant data via a per-tenant-scoped path (authenticated role with JWT, or a dedicated non-BYPASSRLS role + `set_config` tenant context), never an unscoped service_role query; test it adversarially. (2) **Defense-in-depth** — Splinter `0013` as a CI gate, RLS-on-by-default, performance-correct policies, pinned/patched Postgres (≥17.6/16.10). (3) **Per-vertical escalation** — for PHI/HIPAA and cannabis/Metrc, escalate to **project-per-tenant (silo)** or at minimum schema-per-tenant (bridge), aligned with Supabase HIPAA "High Compliance" projects and AWS silo guidance. Net: confirm RLS as a **layer**, refute RLS-as-sole-boundary, make isolation strength a **per-vertical** decision.

> **Cross-link:** the D4 DB-level write enforcement (REVOKE direct writes + SECURITY DEFINER writer role) is also the strongest compensating control for the service_role bypass here. Design D4 and D5 together.

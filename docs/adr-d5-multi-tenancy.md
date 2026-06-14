# ADR-D5: Multi-Tenancy and Runtime Security Model

- **Status**: DECISION-GRADE for initial tenant model; SPIKE-REQUIRED for pooler/session behavior
- **Verdict**: MODIFY `multi-layered-tenant-isolation`
- **Confidence level**: High for RLS/service-role risks; medium for Supavisor-specific session-reset behavior until tested
- **Date**: 2026-06-14

## Goal
Define the first security model for isolating client data, keeping runtime blocks least-privileged, and preventing AI-authored code from accidentally crossing tenant boundaries.

## Decision
Start with **single shared Postgres + tenant-scoped rows + RLS**, hardened by operational controls:

1. **Tenant key everywhere**: Every tenant-owned operational table includes `tenant_id` and uses RLS policies keyed to the authenticated actor's tenant membership.
2. **Force RLS where appropriate**: Enable RLS on tenant tables and use `FORCE ROW LEVEL SECURITY` on tables where owner bypass would undermine runtime checks.
3. **No service role in runtime blocks**: Frontend code and AI-authored block/runtime code must use user-scoped or narrowly scoped server credentials, never broad service-role keys.
4. **Gateway-only mutations**: Mutations go through the action gateway from ADR-D4. Direct operational table writes from app roles are revoked.
5. **Session context discipline**: If using transaction pooling or custom session variables, set tenant context inside each transaction and explicitly reset/avoid session variables unless the pooler behavior is proven safe.
6. **Static and migration gates**: CI checks must flag hardcoded secrets, service-role usage in runtime code, missing RLS on tenant tables, unsafe `SECURITY DEFINER` functions, and direct table mutations that bypass the gateway.

## Evidence Table

| Source | Evidence | Decision impact |
|---|---|---|
| PostgreSQL RLS docs | Superusers and roles with `BYPASSRLS` always bypass RLS; table owners normally bypass RLS unless `FORCE ROW LEVEL SECURITY` is set. | RLS is necessary but not sufficient; force and role design matter. |
| Supabase RLS docs | Service keys can bypass RLS and should not be exposed to customers or browsers. | Runtime blocks cannot carry service-role credentials. |
| Supabase API security docs | Grants and RLS work together to decide object and row access. | Use table grants, function grants, and RLS as layered controls. |
| ADR-D4 gateway design | Gateway RPCs and audit/outbox writes provide an explicit mutation chokepoint. | Tenant isolation must be enforced at the gateway and table layers. |

## Rejected Alternative

### RLS-only isolation with broad service-role backend access
RLS-only is not enough when runtime code can use `service_role`, direct SQL, or unsafe privileged functions. A single AI-authored Edge Function with broad credentials and a missing tenant predicate can leak or mutate cross-tenant data. Service-role access remains necessary for migrations and controlled admin jobs, but it must not become the normal block runtime.

## Known Contradictions
- Separate database-per-tenant or schema-per-tenant isolation is cleaner for blast-radius containment, but it increases provisioning, migration, analytics, and Supabase/PostgREST routing complexity.
- RLS adds query and policy complexity. The first build spike must include tests for query plans and tenant-leak attempts, not just happy-path UI checks.
- Session variables can be convenient for tenant context but are easy to misuse with poolers. Prefer JWT claims/policy functions first; test pooler behavior before relying on connection-local state.

## What New Evidence Would Flip This Decision
1. A tenant-leak test or pooler spike shows shared-table RLS cannot be operated safely with the chosen Supabase deployment.
2. A first customer requires contractual physical/database isolation.
3. Supabase or another adopted substrate offers low-friction database-per-tenant or schema-routing support that preserves developer velocity.

## Build Spike Requirements
1. Create a two-tenant fixture and prove cross-tenant reads/writes fail through API roles.
2. Prove direct table writes are revoked and only gateway actions mutate tenant data.
3. Test whether Supavisor transaction pooling preserves, clears, or leaks custom session settings.
4. Add migration checks for `tenant_id`, RLS enabled, required policies, and forbidden service-role usage in runtime paths.

## Primary Sources
1. [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
2. [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
3. [Supabase: Securing your API](https://supabase.com/docs/guides/api/securing-your-api)
4. [Supabase: Understanding API keys](https://supabase.com/docs/guides/getting-started/api-keys)

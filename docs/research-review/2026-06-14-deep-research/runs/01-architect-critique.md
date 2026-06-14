# Architecture Attack Memo

**Bottom line:** the direction is sensible, but the current ADRs understate the hardest problem: cross-system mutation correctness. RLS, RPCs, and an approval queue do not solve the moment a gateway must update Tekmetric, update a projection, emit an outbox event, and remain idempotent through crashes.

## 1. Strongest Objections

### Confirmed Public Evidence

1. **The gateway is right, but “database-enforced gateway” is not enough.**
   PostgREST can expose functions as RPCs, and functions can mutate state, but any exposed function executable by the active role is callable. Supabase also notes functions are executable by any role by default unless execution is revoked, and `SECURITY DEFINER` needs fixed `search_path`. This means ADR-D4 needs a default-deny function model, not just “use RPC.”
   Confidence: **High**. Evidence: Supabase function privileges and `SECURITY DEFINER` guidance; PostgREST RPC docs. ([supabase.com](https://supabase.com/docs/guides/database/functions)) ([docs.postgrest.org](https://docs.postgrest.org/en/v12/references/api/functions.html))

2. **Supabase RLS is viable, but one leaked secret key collapses the tenant model.**
   Supabase secret keys use `service_role`, have full data access, and bypass RLS. PostgreSQL also says superusers, `BYPASSRLS`, and table owners bypass RLS unless forced. ADR-D5 is directionally right, but “no service role in runtime blocks” must extend to outbox workers, n8n credentials, repair jobs, and admin scripts unless each is given a narrow custom role.
   Confidence: **High**. Evidence: Supabase API key docs; PostgreSQL RLS docs. ([supabase.com](https://supabase.com/docs/guides/getting-started/api-keys)) ([postgresql.org](https://www.postgresql.org/docs/current/ddl-rowsecurity.html))

3. **The audit log is not automatically an audit log just because it is in Postgres.**
   A custom audit table in the same database is useful, but privileged roles can still modify it. Supabase supports PGAudit for monitoring database activity, but its own docs frame configuration carefully because broad logging is noisy. ADR-D2/D4 should distinguish product audit rows, database audit evidence, retention, tamper resistance, and export/offsite archival.
   Confidence: **High**. Evidence: Supabase PGAudit docs. ([supabase.com](https://supabase.com/docs/guides/database/extensions/pgaudit))

4. **n8n is not just a licensing issue; it is also an agency surface.**
   n8n’s license restricts use to internal business purposes and disallows white-label/paid hosted access without a commercial agreement. Separately, workflow engines with broad node catalogs increase excessive-functionality risk unless workflows are allowlisted and credentials are scoped. OWASP explicitly calls out excessive functionality, permissions, autonomy, and recommends downstream authorization and human approval for high-impact actions.
   Confidence: **High**. Evidence: n8n license docs; OWASP Excessive Agency. ([docs.n8n.io](https://docs.n8n.io/sustainable-use-license/)) ([genai.owasp.org](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/))

5. **Tekmetric-first inventory adjustment may overlap the incumbent instead of creating a wedge.**
   Tekmetric publicly advertises 70+ integrations and an application path, but not public write API semantics. It also markets inventory logging, real-time stock updates, integrated ordering, multi-location inventory, and inventory feeds. The first vertical may still be right, but the first workflow risks being “a barcode UI for a problem Tekmetric already claims to solve.”
   Confidence: **Medium-High**. Evidence: Tekmetric integrations, partner, and inventory pages. ([tekmetric.com](https://www.tekmetric.com/integrations)) ([tekmetric.com](https://www.tekmetric.com/partners)) ([tekmetric.com](https://www.tekmetric.com/feature/inventory))

### Partner / Private Verification Required

6. **The SoR plan depends on Tekmetric details that are currently unknown.**
   Must verify inventory write endpoints, webhook coverage, ordering guarantees, rate limits, caching/projection rights, sandbox access, OAuth model, per-shop scoping, multi-location behavior, and whether external idempotency keys are supported. Without this, ADR-D2’s “SoR-first write” is an architectural placeholder.
   Confidence: **High**.

7. **The commercial deployment model must be decided before choosing n8n.**
   n8n may fit client-owned/internal deployments. It is unsafe as a default hidden backend for a paid multi-tenant product unless n8n confirms terms in writing.
   Confidence: **High**. Evidence: n8n docs say a separate commercial agreement is required for non-permitted product use. ([docs.n8n.io](https://docs.n8n.io/sustainable-use-license/))

### Settle By Building

8. **The external-write saga is under-specified.**
   “Write incumbent first, then update Supabase projection/audit/outbox” is not atomic. If Tekmetric succeeds and Supabase fails, the audit/projection is wrong. If Supabase records intent first and Tekmetric fails, the local state may lie. The architecture needs explicit action states: `requested`, `approved`, `external_pending`, `external_succeeded`, `projection_applied`, `outbox_emitted`, `reconciled`, `failed_compensating`.
   Confidence: **High**.

9. **Approval gates can make the first workflow unusable if too broad.**
   MCP and OWASP support confirmation for sensitive/high-impact operations, but approving every AI-authored message body or every inventory adjustment may bury staff. The first spike should prove a risk-class policy: internal templated SMS can be lower risk; customer-facing freeform AI text should require approval.
   Confidence: **Medium**. Evidence: MCP recommends human denial/confirmation for operations; OWASP recommends human approval for high-risk actions. ([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)) ([genai.owasp.org](https://genai.owasp.org/llmrisk/llm01-prompt-injection/))

10. **Supavisor/session-variable tenant context should be treated as guilty until proven safe.**
   Supabase recommends transaction pooling for serverless/edge functions, and transaction mode has behavior differences such as no prepared statements. Tenant authority should come from JWT claims and membership checks first, not connection-local state.
   Confidence: **Medium-High**. Evidence: Supabase connection/pooler docs. ([supabase.com](https://supabase.com/docs/guides/database/connecting-to-postgres))

## 2. First Build Spike Tests

1. Build `inventory.adjust_quantity` against a **mock Tekmetric adapter with failure injection** before depending on partner access.
2. Test crash points after approval, after external write, before projection update, before audit insert, before outbox enqueue, and during notification send.
3. Prove idempotency across local DB and external adapter, not just duplicate RPC calls.
4. Prove direct `INSERT/UPDATE/DELETE` fails for app, block, workflow, and worker roles.
5. Prove cross-tenant reads/writes fail for projection, audit, approval queue, and outbox.
6. Add exploit tests for `SECURITY DEFINER`, function execute grants, `search_path`, and tenant spoofing.
7. Test two concurrent approvals for the same action.
8. Test worker retries with duplicate outbox delivery and external API timeout.
9. Test approval UX latency: internal SMS, customer SMS, destructive adjustment, and AI-authored text.
10. Run a pooler/session test, but prefer no session variables for tenant authority in v1.

## 3. ADRs That Should Change

- **ADR-D1:** Keep auto-repair, but weaken Tekmetric from “first incumbent” to “first candidate.” Add a fallback incumbent/mock-adapter path and require proof the QR/bin workflow is not already solved well enough by Tekmetric.
- **ADR-D2:** Replace simple SoR-first language with an explicit saga/reconciliation model. Add delete/tombstone handling, cache rights, external idempotency, and projection drift budgets.
- **ADR-D3:** Make custom outbox worker or Trigger.dev/Temporal the default SaaS path; n8n only for client-owned/internal use or with signed commercial terms. Add workflow-node/tool allowlisting.
- **ADR-D4:** Split “database authorization gateway” from “side-effect executor.” Add default-revoke function grants, typed manifest/codegen, action state machine, and external side-effect idempotency.
- **ADR-D5:** Ban runtime `service_role` by default, including workers. Require custom least-privilege DB roles, RLS tests for every tenant table, and no session-variable tenant authority until proven.
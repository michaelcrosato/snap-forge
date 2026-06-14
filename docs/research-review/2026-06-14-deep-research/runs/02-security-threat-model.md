# Security Memo: First Build Spike

Scope: `QR/bin scan -> gateway-approved inventory adjustment -> system-of-record update -> staff/customer notification`, using Supabase/Postgres as projection/audit/outbox, incumbent shop system as SoR, and a typed action gateway as the only mutation/side-effect path.

## Confirmed Public Evidence

PostgreSQL RLS is not a complete boundary by itself: superusers, `BYPASSRLS` roles, and table owners bypass RLS unless `FORCE ROW LEVEL SECURITY` is used. RLS also does not cover whole-table operations like `TRUNCATE`. ([postgresql.org](https://www.postgresql.org/docs/current/ddl-rowsecurity.html))

Supabase confirms that grants and RLS both matter, that functions need explicit `EXECUTE` control, and that new public objects can become API-reachable if grants/RLS are mishandled. ([supabase.com](https://supabase.com/docs/guides/api/securing-your-api)) Supabase service/secret keys are elevated, use the `service_role`, and bypass RLS; they must not appear in runtime block code, browsers, logs, URLs, or source control. ([supabase.com](https://supabase.com/docs/guides/getting-started/api-keys))

`SECURITY DEFINER` is a privilege boundary. Supabase recommends `SECURITY INVOKER` by default and requires fixed `search_path` when `SECURITY DEFINER` is used. Function execution is public by default unless revoked. ([supabase.com](https://supabase.com/docs/guides/database/functions))

PostgREST exposes executable functions under `/rpc` when the active role can execute them, so RPC is a valid gateway boundary only if grants are tight. ([docs.postgrest.org](https://docs.postgrest.org/en/v12/references/api/functions.html))

MCP and OWASP LLM guidance support the repo’s stance: tool inputs must be validated, access controlled, rate limited, logged, and sensitive actions should require user confirmation. ([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)) OWASP specifically calls out prompt injection and excessive agency risks, including excessive permissions, excessive autonomy, and indirect prompt injection from external content. ([genai.owasp.org](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)) ([genai.owasp.org](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/))

Twilio requires prior consent, proof of consent, clear sender identity, and opt-out handling for SMS. ([twilio.com](https://www.twilio.com/en-us/legal/messaging-policy)) FTC CAN-SPAM rules require truthful headers/subjects, postal address, opt-out, and prompt honoring of opt-outs for commercial email. ([ftc.gov](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business))

Future regulated verticals are real gates: Supabase requires a signed BAA and HIPAA add-on for PHI. ([supabase.com](https://supabase.com/docs/guides/platform/hipaa-projects)) HIPAA security rules require access controls, audit controls, integrity controls, and transmission security for ePHI. ([ecfr.gov](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C)) PCI DSS applies to entities storing, processing, or transmitting cardholder data; Stripe’s low-risk integrations reduce PCI obligations by keeping sensitive card data off snap-forge servers. ([pcisecuritystandards.org](https://www.pcisecuritystandards.org/standards/)) ([docs.stripe.com](https://docs.stripe.com/security/guide)) Metrc API access is a state/vendor validation path with training, API agreement, sandbox assessment, and production key issuance. ([metrc.com](https://www.metrc.com/oklahoma-integration-and-api/))

## Threat Model

Primary assets: tenant inventory data, SoR credentials, Supabase elevated keys, audit log, approval records, idempotency keys, contact details, outbound message bodies, QR/bin identifiers, and future regulated data tags.

Trust boundaries: scanner PWA/browser; authenticated user session; action gateway/RPC; privileged SoR adapter; Supabase DB/RLS; outbox worker; Twilio/Resend/Stripe/Metrc-style external APIs; AI proposer if present.

Main attacker paths: forged scan payloads, cross-tenant IDs, direct table mutations, stolen service key, unsafe definer function, approval row tampering, replayed idempotency key, duplicate webhook/outbox delivery, AI-generated malicious message/action, and outbound SMS/email to unconsented recipients.

## Concrete Controls, Tests, and CI Checks

| Risk | Required controls | Test cases | CI/static checks |
|---|---|---|---|
| RLS bypass | `tenant_id` on every tenant table; `ENABLE RLS`; `FORCE RLS` on operational tables; deny direct table writes to runtime roles; no owner/runtime role overlap. | Tenant A cannot read/update Tenant B rows; runtime direct `insert/update/delete/truncate` fails; owner-bypass scenario fails under forced RLS. | SQL migration check: tenant tables must include `tenant_id`, RLS enabled, force RLS, policies present; fail on broad grants to `anon/authenticated`. |
| `service_role` misuse | No service/secret key in scanner, blocks, workers that process user-originated actions; isolate admin credentials to migrations and tightly reviewed admin jobs. | Runtime env lacks service key; block cannot initialize Supabase admin client; leaked publishable key still limited by RLS. | Secret scanning plus grep/Semgrep for `service_role`, `sb_secret_`, `SUPABASE_SERVICE`, `createClient(...service...)` outside approved paths. |
| `SECURITY DEFINER` risk | Prefer invoker. Definer only for small gateway RPCs; fixed `search_path = ''`; schema-qualified tables; explicit tenant/actor checks; revoke execute from `public`; grant only gateway role. | Malicious same-name table/function in writable schema cannot hijack; caller without tenant membership fails; unauthenticated execute fails. | SQL lint: definer functions must include `set search_path`; no unqualified table refs; no `grant execute ... to public`; require review label for definer migrations. |
| Approval-gate bypass | Action contract includes `risk_class`, `requires_approval`, `approval_id`, approver actor, expiry, and immutable approved payload hash. Gateway executes only the exact approved payload. | High-risk/customer-message action returns `PENDING_APPROVAL`; changed quantity/message after approval fails; self-approval blocked where policy says two-person approval. | Contract check: high-risk actions must declare approval policy; code search fails direct Twilio/Resend/SoR calls outside gateway/outbox worker. |
| Audit log integrity | Append-only `action_events` and `approval_events`; no update/delete grants; include actor, tenant, request hash, approved payload hash, idempotency key, SoR result, outbox IDs, timestamps. Optional hash chain per tenant/day. | Runtime cannot update/delete audit rows; every success/failure has audit event; tampered hash chain detected; failed SoR call leaves attempt record. | SQL check: audit tables deny update/delete; triggers prevent mutation; required columns present; migration tests enforce audit write in gateway transaction. |
| Idempotency | Unique `(tenant_id, action_name, idempotency_key)`; store request hash and final result; duplicate same payload returns same result; duplicate different payload rejects. Outbox has unique event key. | Double scan/click applies once; concurrent duplicate requests apply once; same idempotency key with different quantity fails; outbox retry sends once. | Test harness runs parallel duplicate RPC calls; SQL check for unique indexes on action and outbox keys. |
| Prompt injection / AI agency | Treat AI as proposer only. Model may emit typed action JSON, never direct SQL/API calls. Validate schema deterministically. No external scan/customer text in system prompts as instructions. | QR code containing prompt text cannot change action type/tenant/recipient; AI-proposed customer SMS requires approval; model output with extra fields rejected. | Allowlist tool/action registry; schema validation tests; grep for raw model output passed to DB/API; prompt-injection fixtures in eval suite. |
| SMS/email risk | Store consent/proof/source; separate staff vs customer notifications; default first spike to staff-only unless customer consent exists; opt-out suppression list; templates or approved AI-authored bodies only. | No consent means no customer SMS/email; STOP suppresses future SMS; staff notification cannot be routed to customer phone; promotional copy blocked in transactional channel. | Static rule: Twilio/Resend imports only in notification worker; require consent lookup before enqueue; test fixtures for opt-out and missing consent. |
| SoR update integrity | SoR adapter is gateway-owned; external call result recorded; projection update only after confirmed SoR success; reconciliation job detects drift. | SoR timeout does not update projection as successful; retry does not double-adjust; reconciliation flags mismatch. | Direct adapter calls outside gateway forbidden; integration tests with mock SoR for success, timeout, duplicate, stale projection. |

## Partner / Private Verification Required

Tekmetric-specific API facts remain unverified: auth model, write endpoints for inventory adjustment, webhook coverage, idempotency support, rate limits, caching/projection rights, audit fields, sandbox availability, partner fees, and approval timeline.

Twilio/Resend account configuration must be verified per customer: 10DLC/toll-free requirements, sender identity, opt-out behavior, consent evidence retention, message category, delivery-region constraints, and whether healthcare/regulated content needs extra contractual terms.

For future HIPAA/PCI/Metrc work, verify signed BAAs, vendor DPAs, card-data flow diagrams, Metrc state-specific validation requirements, retention rules, and whether logs/messages may contain regulated identifiers.

## Settle By Building

Build the spike as a hostile test harness, not a happy-path demo:

1. Two tenants, two users, one scanner client, one gateway RPC, one mock SoR adapter, one outbox worker, one staff notification channel.
2. Use a mock incumbent first if Tekmetric docs are delayed; model Tekmetric as unavailable, slow, duplicate-returning, and partially failing.
3. Add pgTAP or equivalent migration tests for grants/RLS/RPC/audit/idempotency.
4. Add Semgrep/regex CI gates for service-role use, direct table writes, direct external side effects, unsafe definer SQL, missing RLS, and missing idempotency indexes.
5. Add AI red-team fixtures: prompt text embedded in QR/bin label, malicious customer note, cross-tenant object ID, altered approval payload, duplicate scan replay, and outbound message without consent.

Bottom line: the repo’s architecture is directionally sound, but only if the database rejects bypasses by default. The first spike should pass only when direct writes fail, cross-tenant access fails, privileged credentials are absent from runtime blocks, approval records cannot be replayed or edited, and duplicate scans cannot double-apply inventory changes.

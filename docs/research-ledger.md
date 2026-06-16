# Research Ledger

This ledger tracks decision-grade claims from the snap-forge architecture research and links them to the ADRs that currently own each decision.

## Evidence Labels

- **Confirmed public evidence**: Supported by public primary sources or official project repositories/docs.
- **Partner/private verification required**: Directionally plausible, but exact details require partner docs, credentials, contracts, or build-time testing.
- **Settle by building**: The decision needs an implementation spike, benchmark, or live environment test.

## Claims and Audits

### P0 Decision Mapping

| P0 decision | Ledger claim | Owning artifact |
|---|---|---|
| D1: First vertical | [C1-VERT] | [`adr-d1-first-vertical.md`](adr-d1-first-vertical.md) |
| D2: System of record / projection | [C2-SOR] | [`adr-d2-system-of-record.md`](adr-d2-system-of-record.md) |
| D3: Workflow engine / licensing | [C3-LIC] | [`adr-d3-workflow-engine.md`](adr-d3-workflow-engine.md) |
| D4: Action gateway | [C4-GATE] | [`adr-d4-action-gateway.md`](adr-d4-action-gateway.md) |
| D5: Tenant isolation | [C5-TENANT] | [`adr-d5-multi-tenancy.md`](adr-d5-multi-tenancy.md) |

### [C1-VERT] Auto repair is the best first vertical
- **Claim**: Auto repair should be the first vertical because it has active incumbents and integration ecosystems while avoiding Metrc and HIPAA gates at the first proof point.
- **Evidence**: Tekmetric publicly advertises 70+ integrations and a partner/integration application path. Metrc state pages show vendor training, legal agreement, sandbox, capability assessment, and production key requirements. Supabase requires a BAA and HIPAA add-on for PHI.
- **Evidence label**: Confirmed public evidence, with Tekmetric API specifics requiring partner/private verification.
- **Classification**: **B (modify-or-compose)**. Build around incumbent systems instead of replacing them.
- **Verdict**: **CONFIRM** auto repair as first vertical.
- **Owned by**: [`adr-d1-first-vertical.md`](adr-d1-first-vertical.md)

### [C2-SOR] Incumbent SoR plus local operational projection
- **Claim**: Snap-forge should treat the incumbent shop system as the system of record and use Supabase as a local projection, audit log, and outbox.
- **Evidence**: Tekmetric's public site confirms an integration ecosystem, but not endpoint semantics. The transactional outbox pattern is a standard way to avoid dual-write loss between local state and asynchronous messages.
- **Evidence label**: Confirmed pattern; partner/private verification required for Tekmetric sync details.
- **Classification**: **B (modify-or-compose)**. Combine incumbent APIs, local projections, gateway audit, and outbox workers.
- **Verdict**: **MODIFY** direct-write design into SoR-first writes plus local projection/reconciliation.
- **Owned by**: [`adr-d2-system-of-record.md`](adr-d2-system-of-record.md)

### [C3-LIC] Workflow engine choice depends on deployment model
- **Claim**: n8n is a good single-tenant/internal automation tool but is not the default free substrate for a multi-tenant snap-forge SaaS. SaaS deployments should prefer permissive/code-first orchestration or a commercial agreement.
- **Evidence**: n8n's Sustainable Use License allows internal business use but restricts white-labeling/paid hosted access and some backend uses involving user credentials. Activepieces core is MIT, but enterprise folders require a commercial license. Windmill is AGPLv3/Apache-2.0 mix with enterprise/commercial offerings. Trigger.dev and Node-RED are Apache-2.0.
- **Evidence label**: Confirmed public evidence; legal review required before resale/embedding.
- **Classification**: **B (modify-or-compose)** for single-tenant n8n; **A (adopt)** for permissive runtimes where license fit is clear.
- **Verdict**: **MODIFY** orchestrator choice by deployment model.
- **Owned by**: [`adr-d3-workflow-engine.md`](adr-d3-workflow-engine.md)

### [C4-GATE] Mutations need a database-enforced action gateway
- **Claim**: AI-authored blocks and app clients must not write directly to operational tables or call high-risk side effects without a typed action, audit, idempotency, and approval decision.
- **Evidence**: Supabase/PostgREST expose tables and functions through grants; service keys can bypass RLS; PostgreSQL functions can act as RPC boundaries; MCP recommends human-deniable tool invocation; OWASP LLM guidance flags excessive agency and prompt injection risks.
- **Evidence label**: Confirmed public evidence; implementation approach must be tested.
- **Classification**: **C (adapt-old-pattern)**. Use grants, stored functions/RPC, audit tables, outbox, and approval queues.
- **Verdict**: **MODIFY** into a database-enforced gateway with careful `SECURITY DEFINER` use rather than blanket PL/pgSQL privilege.
- **Owned by**: [`adr-d4-action-gateway.md`](adr-d4-action-gateway.md)

### [C5-TENANT] Shared Postgres with RLS is viable only with layered controls
- **Claim**: A shared database can be the first tenant model if RLS is paired with direct-write revocation, service-role isolation, gateway-only mutations, migration checks, and pooler/session discipline.
- **Evidence**: PostgreSQL documents RLS bypass by superusers, `BYPASSRLS`, and table owners unless forced. Supabase documents service keys that can bypass RLS and warns not to expose them to customers or browsers.
- **Evidence label**: Confirmed public evidence; Supavisor/session behavior is settle-by-building.
- **Classification**: **B (modify-or-compose)**. RLS plus operational controls, not RLS alone.
- **Verdict**: **MODIFY** tenant isolation into layered controls.
- **Owned by**: [`adr-d5-multi-tenancy.md`](adr-d5-multi-tenancy.md)

## Parallel-Run Reconciliation

A sibling `opus` research run at `research/opus-4-8-20260614-1049` produced a full ADR set and a granular evidence ledger (not merely a memo). Its deferred P1 decisions were reconciled into this branch as below, and its load-bearing unique primary-evidence rows were salvaged into the [Salvaged primary-evidence rows](#salvaged-primary-evidence-rows-from-researchopus-4-8-20260614-1049) section (2026-06-15); the branch is now closed as superseded. Reconciliation of the deferred decisions:

| Sibling-run item | Reconciliation |
|---|---|
| P0 decisions D1-D5 are researchable, with part of D4 settle-by-building | Captured in the five ADRs above; D4 implementation ergonomics remains a build-spike blocker in [`open-questions.md`](open-questions.md). |
| D6 AI runtime boundary deferred | Added to deferred P1 decisions in [`open-questions.md`](open-questions.md). |
| D7 MCP/tooling boundary deferred | Added to deferred P1 decisions in [`open-questions.md`](open-questions.md). |
| D8 AI-authored-code governance deferred | Added to deferred P1 decisions in [`open-questions.md`](open-questions.md). |
| D9 Compliance boundary deferred | Added to deferred P1 decisions in [`open-questions.md`](open-questions.md). |
| D10 Operational burden deferred | Added to deferred P1 decisions in [`open-questions.md`](open-questions.md). |

## Solution Index

- **A (Adopt)**: Supabase as shared core; Twilio/Stripe/Resend SDKs; Trigger.dev, Temporal, or Node-RED where license/runtime fit is clear.
- **B (Modify-or-compose)**: Auto-repair incumbent integration; Supabase projection plus incumbent SoR; n8n for single-tenant/internal deployments; RLS plus gateway plus CI controls.
- **C (Adapt-old-pattern)**: Transactional outbox; stored procedure/RPC write gate; audit log and approval queue.
- **D (Novel)**: None required for the first build spike.
- **E (Refuted)**: AI as the unattended integration layer; direct database writes by AI-authored blocks; schemaless JSONB as a schema replacement; n8n-as-hidden-SaaS-backend without licensing review.

## Salvaged primary-evidence rows (from `research/opus-4-8-20260614-1049`)

Granular, per-claim evidence salvaged from the closed parallel run (2026-06-15). Stable IDs `OPUS-D{n}-{nn}`. Confidence: ✅✅ clean adversarial verification · ✅ primary-source-grounded + corroborated · ◐ single primary source. Every external fact below was independently re-verified against live sources during the 2026-06-15 foundation review (see [`foundation-review-2026-06-15.md`](foundation-review-2026-06-15.md)).

### D1 — First vertical
| ID | Claim (evidence) | Source · date | Conf | Decision impact |
|---|---|---|---|---|
| OPUS-D1-01 | Shopmonkey API is self-service: any Admin generates Public/Private keys; public REST v3 docs; no NDA/partner/revenue gate | shopmonkey.dev/overview · 2026 | ✅✅ | Makes auto-repair buildable solo; becomes the primary first integration |
| OPUS-D1-04 | Tekmetric API access is request-based, ~2–3 wk approval "at Tekmetric's discretion", not guaranteed; OAuth2 client_credentials + sandbox | beetlebugorg/tekmetric-mcp README · 2025-10 | ✅ | Demotes Tekmetric to approval-gated secondary |

### D2 — System of record
| ID | Claim (evidence) | Source · date | Conf | Decision impact |
|---|---|---|---|---|
| OPUS-D2-01 | CQRS: write model = SoR; read model = "durable, read-only cache", eventually consistent | learn.microsoft.com /azure/architecture/patterns/cqrs | ✅✅ | Incumbent-as-SoR + projection is a sound pattern |
| OPUS-D2-02 | Tekmetric: narrow webhooks; else "your account data will sync once per hour" | support.shopgenie.io tekmetric webhooks | ✅✅ | "Thin cache" framing fails → needs delta-poll |
| OPUS-D2-03 | Shopify mandates reconciliation jobs (webhook delivery not guaranteed) via updated_at | shopify.dev/docs/apps/build/webhooks | ✅✅ | Projection always needs push + delta-poll + reconcile |
| OPUS-D2-04 | SoR is per bounded context / per domain (data sovereignty per microservice) | learn.microsoft.com /dotnet/architecture/microservices | ✅ | SoR is per-domain; Supabase = SoR for originated data |
| OPUS-D2-05 | Treating a projection as both incumbent-cache and originated-store invites the dual-write problem | confluent.io/blog/dual-write-problem | ✅ | Write-backs need a transactional outbox |

### D3 — Workflow engine + license (architecture-changer)
| ID | Claim (evidence) | Source · date | Conf | Decision impact |
|---|---|---|---|---|
| OPUS-D3-01 | n8n Sustainable Use License limits use to "internal business purposes"; distribution only free-of-charge non-commercial. Fair-code, SPDX NOASSERTION | raw n8n LICENSE.md (master) · 2026 | ✅✅ | n8n not free for commercial multi-tenant resale |
| OPUS-D3-02 | n8n help center: hosting clients' workflows = paid Enterprise; embedding/exposing to clients = paid Embed/OEM | support.n8n.io + docs.n8n.io/embed | ✅✅ | snap-forge's exact pattern requires a paid n8n license |
| OPUS-D3-03 | n8n "back-end to power a feature" carve-out is void if using users' own credentials to access their data | n8n FAQ · 2026 | ✅✅ | Closes the free-backend loophole for snap-forge |
| OPUS-D3-04 | Activepieces core = MIT Expat; packages/ee (multi-tenancy, RBAC, SSO, embed, white-label, audit) = Commercial | raw Activepieces LICENSE · rel 0.85.3 2026-06-14 | ✅✅ | MIT engine usable; build own tenancy, don't enable ee/ |
| OPUS-D3-05 | Windmill = AGPLv3 + proprietary EE; network copyleft attaches when re-exposing modified Windmill | github windmill LICENSE · 2026 | ✅ | Windmill is an AGPL trap for closed-source SaaS unless isolated/licensed |
| OPUS-D3-06 | Trigger.dev = clean Apache-2.0, self-hostable, HITL waitpoints, active | api.github.com/repos/triggerdotdev/trigger.dev | ✅ | Lowest-license-risk code-first orchestrator candidate |
| OPUS-D3-07 | n8n engineering merit: ~192k★, rel 2.25.7 2026-06-10, 400+ integrations | api.github.com/repos/n8n-io/n8n | ✅✅ | Ranking sound on merit; only licensing demotes it |

### D4 — Gateway contract
| ID | Claim (evidence) | Source · date | Conf | Decision impact |
|---|---|---|---|---|
| OPUS-D4-01 | service_role has BYPASSRLS and is what Edge Functions / webhooks / orchestrator DB nodes use | supabase.com/docs/.../postgres/roles | ✅✅ | A library gateway is bypassable → pure-library invariant refuted |
| OPUS-D4-02 | BYPASSRLS bypasses **row security only**, not GRANT/REVOKE table privileges | postgresql.org/docs/current/ddl-rowsecurity.html | ✅✅ | Table-level REVOKE can still bind service_role |
| OPUS-D4-03 | service_role is NOT a superuser (only bypass-RLS) | github supabase discussions #36362 | ✅✅ | Confirms REVOKE binds it |
| OPUS-D4-04 | REVOKE EXECUTE FROM PUBLIC + selective grants + SECURITY DEFINER funcs = single controlled write path | docs.postgrest.org/.../db_authz.html | ✅✅ | The enforcement layer that makes the invariant physically true |
| OPUS-D4-05 | Real-world 42501 "permission denied" proves service_role loses table access after REVOKE | supabase troubleshooting 42501 docs | ✅ | DB-level enforcement is documented + observed |
| OPUS-D4-06 | One-action-per-block has friction: reads (CQRS), multi-action txns, bulk ops need escape hatches | enterprisecraftsmanship.com + CQRS | ✅ | Mandates read/bulk/multi-step escape hatches |

### D5 — Multi-tenancy / RLS
| ID | Claim (evidence) | Source · date | Conf | Decision impact |
|---|---|---|---|---|
| OPUS-D5-01 | "Supabase provides special Service keys, which can be used to bypass RLS" (verbatim) | supabase.com/docs/.../row-level-security | ✅✅ | RLS is not the boundary for the service_role backend tier |
| OPUS-D5-02 | CVE-2025-48757 (CVSS 9.3): missing/insufficient RLS exposed PII/API-keys/payment data across 170+ Lovable+Supabase projects | mattpalmer.io · 2025-05 | ✅✅ | "Forgot RLS = breach" is empirical on this stack |
| OPUS-D5-03 | RLS engine CVEs: 2024-10976, 2025-8713 | postgresql.org/support/security | ✅ | Shared-schema correctness contingent on staying patched (≥17.6/16.10) |
| OPUS-D5-04 | AWS SaaS Lens: tenant-boundary crossing "potentially unrecoverable"; compliance pushes to silo | docs.aws.amazon.com/.../saas-lens/tenant-isolation | ✅ | Pool/shared-schema often not acceptable for regulated tenants |
| OPUS-D5-05 | Supabase HIPAA model is project-level (BAA + add-on; not self-hosted) | supabase.com/docs/guides/platform/hipaa-projects | ✅ | Compliance unit of isolation = project, not row → silo for PHI |
| OPUS-D5-06 | RLS perf fixes: (select auth.uid()) 179→9ms; index tenant col 171→<0.1ms; TO authenticated 170→<0.1ms | supabase.com/docs/.../row-level-security | ✅ | RLS-at-scale is fine for non-regulated if discipline enforced |

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

A sibling `opus` research worktree at `research/opus-4-8-20260614-1049` produced an `open-questions.md` memo rather than a full competing ledger. Its claims were reconciled into this branch as follows:

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

# Open Questions and Build Blockers

This file tracks the questions that must be resolved before or during the first build spike.

## Partner and Commercial Blockers

### Q1: Tekmetric API access, endpoint coverage, and approval timeline
- **Question**: What are the exact partner requirements, fees, contract terms, approval timeline, endpoint coverage, authentication model, write permissions, webhook events, rate limits, and caching rules for Tekmetric API access?
- **Why it matters**: ADR-D1 and ADR-D2 choose auto repair and a Tekmetric-first evaluation path, but public pages do not prove the implementation details.
- **Next step**: Apply through Tekmetric's integration/partner flow and request developer documentation under the right business entity.
- **Owner artifact**: [`adr-d1-first-vertical.md`](adr-d1-first-vertical.md), [`adr-d2-system-of-record.md`](adr-d2-system-of-record.md)

### Q2: Workflow engine license fit by deployment model
- **Question**: For the first paid deployment, is snap-forge acting as a consultant for a client-owned internal system, or selling a multi-tenant SaaS/embedded automation product?
- **Why it matters**: n8n can fit internal/client-owned automation, but multi-tenant SaaS or embedded visual workflow functionality may require a commercial agreement or a different orchestrator.
- **Next step**: Decide deployment model before committing to n8n, Activepieces Embed, Windmill, Trigger.dev, Node-RED, or a custom outbox worker.
- **Owner artifact**: [`adr-d3-workflow-engine.md`](adr-d3-workflow-engine.md)

### Q3: Metrc validation timelines by target state
- **Question**: What is the current onboarding timeline for a third-party Metrc integrator in likely target states?
- **Why it matters**: Cannabis is deferred, but it remains a likely later vertical. State-specific timelines affect roadmap commitments.
- **Next step**: Contact Metrc/API program contacts for the target states only after a cannabis prospect exists.
- **Owner artifact**: [`adr-d1-first-vertical.md`](adr-d1-first-vertical.md)

## Build-Spike Questions

### Q4: PL/pgSQL/RPC gateway ergonomics and performance
- **Question**: Can the first action gateway be maintained safely with small Postgres RPC functions, or should TypeScript generate/coordinate part of the contract while the database enforces grants?
- **Why it matters**: ADR-D4 chooses a database-enforced gateway but does not assume PL/pgSQL should contain all business validation forever.
- **Next step**: Build `inventory.adjust_quantity` with revoked direct writes, RPC, audit log, outbox, idempotency, and approval tests. Load test with `k6`, `autocannon`, or a minimal script.
- **Owner artifact**: [`adr-d4-action-gateway.md`](adr-d4-action-gateway.md)

### Q4a: Gateway invariant under a real side-effecting write
- **Question**: Does the invariant "nothing writes or calls out except through the gateway" survive the first real block without forcing unsafe workarounds?
- **Why it matters**: Research can settle the enforcement model, but not the ergonomics of a real workflow with gateway validation, approval branching, outbox side effects, and external API calls.
- **Next step**: In the first build spike, route the full reference path through the gateway: `QR-scan -> adjust inventory -> write audit/outbox -> notify salesperson`.
- **Owner artifact**: [`adr-d4-action-gateway.md`](adr-d4-action-gateway.md)

### Q5: Supavisor/session variable safety
- **Question**: If tenant context uses custom session settings, does the chosen Supabase/Supavisor pooler mode reliably reset that state between transactions?
- **Why it matters**: Session leakage can cross tenant boundaries. The safer default is JWT/policy-based tenant resolution unless pooler behavior is proven.
- **Next step**: In a live Supabase project, set a transaction-local tenant variable for Tenant A, reuse pooled connections, and prove Tenant B cannot observe it.
- **Owner artifact**: [`adr-d5-multi-tenancy.md`](adr-d5-multi-tenancy.md)

### Q6: CI/static checks for AI-authored block safety
- **Question**: Which static checks catch direct operational table writes, runtime `service_role` usage, unsafe `SECURITY DEFINER`, missing RLS, and missing gateway/audit usage?
- **Why it matters**: The architecture assumes AI-authored blocks stay small and constrained. CI must enforce that assumption.
- **Next step**: Add a repository rule set during the build spike: secret scanning, grep/Semgrep rules for Supabase service-role usage, SQL migration checks, and direct table mutation checks.
- **Owner artifact**: [`adr-d4-action-gateway.md`](adr-d4-action-gateway.md), [`adr-d5-multi-tenancy.md`](adr-d5-multi-tenancy.md)

## Deferred Product Questions

### Q7: First block workflow scope
- **Question**: Should the first block stop at "scan -> inventory adjustment -> internal SMS" or include customer-facing messaging?
- **Why it matters**: AI-authored outbound customer messages require the approval gate from ADR-D4. Internal/staff SMS can be a lower-risk first test.
- **Next step**: Start with staff/internal notification unless a pilot customer explicitly needs customer-facing messaging.

## Deferred P1 Decisions

These were identified during the parallel `opus` research run and are intentionally deferred until after the P0 ADRs and first build spike.

### D6: AI Runtime Boundary
- **Question**: Should AI remain build-time only, act as a human-in-the-loop runtime assistant, or propose limited runtime actions behind the gateway?
- **Current posture**: Build-time and human-in-the-loop first; no unattended high-risk runtime action execution.

### D7: MCP and Tooling Boundary
- **Question**: Which MCP servers and tool catalogs are allowed at dev time, and which, if any, can become production dependencies?
- **Current posture**: MCP is acceptable as build-time/human-supervised connective tissue; production blocks should prefer direct SDKs unless a server is explicitly reviewed and scoped.

### D8: AI-Authored-Code Governance
- **Question**: What branch, test, review, static-analysis, and rollback gates are mandatory for AI-authored blocks?
- **Current posture**: Small blocks, tests, static checks for service-role/direct-write bypasses, and review gates are mandatory before production.

### D9: Compliance Boundary
- **Question**: How should PHI, PCI, Metrc compliance writes, message approval, logging, and retention be encoded per action?
- **Current posture**: High-risk actions require explicit approval, audit, and environment prerequisites before implementation.

### D10: Operational Burden
- **Question**: Which parts should be managed services versus self-hosted for small-business support economics?
- **Current posture**: Prefer managed/adopted substrate where compliance and cost allow; self-hosting requires an explicit support and security model.

# ADR-D2: System of Record and Operational Projections

- **Status**: DECISION-GRADE for boundary; SPIKE-REQUIRED for incumbent-specific sync mechanics
- **Verdict**: MODIFY `operational-projection-cache`
- **Confidence level**: High for the boundary pattern; medium for Tekmetric-specific mechanics
- **Date**: 2026-06-14

## Goal
Define where durable truth lives and how snap-forge reads, writes, and reconciles data when an incumbent product such as Tekmetric remains the client-visible system of record.

## Decision
Treat the incumbent shop-management system as the **System of Record** for domain objects it owns, and treat Supabase as an **operational projection**:

1. **Reads**: Serve snap-forge UI/search/list workflows from local Supabase projection tables where low-latency queries and joins are needed.
2. **Writes**: For records owned by the incumbent, execute the incumbent API write through the action gateway first. Only after success should snap-forge update the local projection and audit log.
3. **Outbox**: Record follow-on side effects such as SMS, email, analytics events, and reconciliation jobs in a Postgres outbox table inside the same transaction as the local projection/audit update.
4. **Sync**: Prefer incumbent webhooks if provided. If webhook coverage, ordering, or retry guarantees are incomplete, add scheduled reconciliation using the best supported partner endpoint: delta sync when available, otherwise paginated full/partial refresh.

## Evidence Table

| Source | Evidence | Decision impact |
|---|---|---|
| Tekmetric integrations page | Public evidence confirms Tekmetric has an integration ecosystem and an integration application path, but public docs do not expose endpoint coverage, rate limits, or webhook guarantees. | Do not build against assumed Tekmetric mechanics; verify through partner docs. |
| Transactional outbox pattern | The outbox pattern avoids distributed two-phase commit by storing messages/events in the same database transaction as local state changes. | Supports using Supabase as the local audit/projection/outbox boundary. |
| Supabase/Postgres | Supabase gives Postgres, functions, RLS, realtime, and edge functions in one shared core. | Fits the local projection and event-log role without inventing a database substrate. |

## Falsification Attempt

### Thesis
Skip the local projection and query the incumbent API directly on every user interaction.

### Result: REFUTED AS DEFAULT
Direct-query architecture is attractive because it avoids local drift, but it fails as the default shape:

1. **Latency**: Every screen/search/scan depends on third-party API latency and availability.
2. **Query shape**: Snap-forge workflows need cross-object queries, local assignment context, and audit joins that incumbent APIs may not expose.
3. **Rate/contract uncertainty**: Public Tekmetric pages do not disclose the limits needed to prove direct-query scalability. Until partner docs prove otherwise, design for constrained third-party APIs.
4. **Audit boundary**: The action gateway needs a local audit and event log even when the incumbent owns the domain record.

## Known Contradictions
- Local projections introduce drift risk. That is why every projected table needs `source_system`, `source_id`, `source_updated_at`, `last_synced_at`, and reconciliation metadata.
- Synchronous SoR-first writes add latency. That tradeoff is deliberate for domain data where the incumbent remains authoritative.

## What New Evidence Would Flip This Decision
1. The chosen incumbent exposes low-latency, high-rate, strongly consistent APIs with all query shapes needed by the reference workflow.
2. The chosen first block does not need local search, joins, audit, or offline-tolerant UI behavior.
3. Partner docs prohibit projection/caching of the required data.

## Build Spike Requirements
1. Acquire Tekmetric partner/API documentation.
2. Identify which objects support webhooks, delta sync, pagination, and writes.
3. Build a small reconciliation prototype for one object set, with duplicate event and missed webhook tests.
4. Measure write latency for SoR-first gateway calls.

## Primary Sources
1. [Tekmetric Integrations](https://www.tekmetric.com/integrations)
2. [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
3. [Supabase Database Functions](https://supabase.com/docs/guides/database/functions)

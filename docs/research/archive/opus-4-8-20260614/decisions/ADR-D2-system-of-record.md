# ADR-D2 — System of record

- **Verdict:** MODIFY · **Confidence:** high
- **Classification:** B (modify-compose) · **Role:** foundational data-architecture decision (governs the gateway, sync layer, audit/approval guarantees)
- **Independent verification:** supported
- **Run:** `research/opus-4-8-20260614-1049` · 2026-06-14 · ledger IDs `OPUS-D2-*`

## Decision
Replace the doc's implicit **global/binary** "incumbent = source of truth, Supabase = cache" framing with an explicit **per-domain system-of-record** model, and mandate a real sync contract (push **+ delta-poll + reconcile + idempotent upsert**) rather than a "thin cache on top of the API."

## Claim tested
> "The incumbent vertical system (e.g. Tekmetric) is the source of truth; snap-forge's Supabase is an operational projection/cache built 'on top of and between' incumbent APIs, and snap-forge should NOT try to replace the incumbent system of record."

## Load-bearing sources
1. **Azure Architecture Center — CQRS** — https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs — the write model is SoR; the read model is a "durable, read-only cache" that is eventually consistent. This is the *sound* version of the doc's design — confirming it as a pattern, not an anti-pattern.
2. **Tekmetric webhooks (Shopgenie support)** — https://support.shopgenie.io/support/setting-up-webhooks-in-tekmetric — narrow webhook event set (appointment/RO events only); verbatim: **"If you don't use webhooks, your account data will sync once per hour."** The disconfirming crux: a naive projection is hourly-stale for most entities.
3. **.NET microservices — data sovereignty per microservice** — https://learn.microsoft.com/en-us/dotnet/architecture/microservices/architect-microservice-container-applications/data-sovereignty-per-microservice — SoR is per bounded context, supporting per-domain ownership.

## Evidence for
- The incumbent-as-SoR + read-projection pattern is **canonically sound** (CQRS). Where incumbents expose proper webhooks (Shopify: HTTPS/PubSub/EventBridge with field filtering), a near-real-time external projection is genuinely feasible.

## Evidence against (why MODIFY, not CONFIRM)
- **Tekmetric has no general real-time push** — narrow webhooks + otherwise **hourly** sync. The projection needs delta-poll (`updatedDateStart`) + reconcile, not a thin cache.
- **Webhooks are best-effort even on Shopify** — Shopify mandates "reconciliation jobs to periodically fetch data" via `updated_at`; you always need push **plus** reconcile.
- **The framing is too binary.** Data snap-forge *originates* (CRM notes, tasks, scan events, audit log, approval decisions) has **no incumbent owner** — Supabase **must** be the SoR for those domains. Treating them as a cache invites the **dual-write problem** (Confluent), solvable only with a transactional outbox/CDC where Supabase is a real write-store.
- **Greenfield shops** (no incumbent) collapse the premise: Supabase is SoR for everything; the projection layer degenerates to empty. The architecture must assume this up front.
- The **Tekmetric REST API is documented as fragile** (inaccuracies, inconsistent pagination; community MCP archived 2026-02-18) — budget defensive delta-sync/backfill.

## Falsification attempt
Tried to **refute outright**: that incumbent APIs can't feed a projection at all (polling-only/hourly) **and** that the projection pattern is itself an anti-pattern. Both failed — the pattern is canonically sound and incumbents *can* feed a projection (just not naively). But the **binary/global framing** is wrong (SoR is per-domain; Supabase is unavoidably SoR for originated data and greenfield). Hence MODIFY.

## Independent verification
Verifier independently fetched and verbatim-confirmed all three pillars: Tekmetric's "sync once per hour" fallback (Shopgenie), CQRS read-model-as-durable-cache + eventual consistency (Microsoft), and Shopify's "shouldn't rely solely on webhooks → reconciliation jobs" mandate. Verdict **supported (high)**. Caveat: Tekmetric's exact webhook *event list* is secondary-sourced (official API docs are auth-gated, HTTP 401), but the load-bearing **hourly-sync** fact is verbatim-confirmed.

## What would flip this
- **Toward CONFIRM (global framing OK):** incumbents ship comprehensive, ordered, replayable CDC across all entities **and** snap-forge originates essentially no first-class data.
- **Toward REFUTE (Supabase as global SoR):** incumbent APIs prove too lossy/rate-limited to maintain even an eventually-consistent projection, **or** snap-forge's originated/audit/approval data becomes the dominant, legally load-bearing dataset (anchoring truth in a third-party system you don't control becomes the larger risk).

## Recommendation
Adopt a **per-domain SoR** model: (1) incumbent-owned domains → incumbent = SoR, Supabase = read-only CQRS projection with **webhooks + scheduled delta-poll + reconciliation + idempotent upserts keyed on incumbent IDs**; (2) snap-forge-originated domains (CRM, tasks, scan events, **audit, approvals**) → **Supabase is the SoR**, any write-back through the gateway's transactional outbox; (3) greenfield → Supabase SoR for everything; (4) treat the Tekmetric API as fragile and budget for backfill. Keep the doc's "don't replace the incumbent" instinct as the default — just make ownership explicit and per-domain.

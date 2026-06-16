# ADR-D1: First Vertical Selection

- **Status**: DECISION-GRADE, with partner-access caveats
- **Verdict**: CONFIRM `auto-repair`
- **Confidence level**: High for vertical choice; medium for Tekmetric API specifics until partner docs are available
- **Date**: 2026-06-14

## Goal
Select the first vertical to validate the snap-forge architecture while minimizing regulatory overhead, integration friction, and irreversible product bets.

## Decision
Choose **auto repair** as the first vertical. The first reference workflow should be:

`QR/bin scan -> gateway-approved inventory adjustment -> system-of-record update -> customer/staff SMS notification`

The decision is based on the public evidence that auto repair has active incumbent systems, integration ecosystems, and lower regulated-data overhead than cannabis or medical/dental. Tekmetric is the leading first incumbent to evaluate, but its exact partner API contract, endpoint coverage, rate limits, webhook semantics, fees, and approval timeline must be verified through the Tekmetric integration/partner process before build work depends on them.

## Evidence Table

| Source | Evidence | Decision impact |
|---|---|---|
| Tekmetric integrations page | Tekmetric publicly advertises 70+ integrations and has a "Learn More & Apply" integration entrypoint at `api.tekmetric.com`. | Confirms an integration ecosystem exists, but not exact API terms. |
| Tekmetric partner program | Tekmetric describes a formal partner program with benefits determined by partnership scope and joint initiatives. | Treat API access and commercial terms as a partner-gated dependency, not a public API assumption. |
| Metrc state integration pages | Multiple state pages require vendor training, a signed API agreement by an authorized officer, sandbox access, capability assessment, and production vendor key issuance before becoming a validated integrator. | Cannabis carries non-code certification and state-specific approval gates. |
| Supabase HIPAA docs/pricing | Supabase allows PHI only with a signed BAA and HIPAA add-on enabled; Team and Enterprise customers can request a BAA, and pricing lists HIPAA as a paid add-on. | Medical/dental is viable later, but PHI work needs an explicit paid compliance path before implementation. |

## Rejected Alternatives

### Cannabis first
Cannabis inventory workflows map naturally to the snap-forge thesis, but Metrc production access is a gated third-party integrator path. The steps are state-specific and include legal/administrative prerequisites before production credentials are issued. That makes cannabis a poor first validation target unless a client already brings validated integrator access.

### Medical/dental first
Medical/dental has standardized healthcare integration surfaces such as FHIR, but the moment the system stores or processes PHI, the infrastructure and operating model need a BAA, audit controls, and HIPAA-specific configuration. That is manageable, but it is not the lowest-friction proof point.

## Known Contradictions
- Auto repair incumbents already cover many shop workflows. That is not a reason to avoid the vertical; it means snap-forge should build between and around incumbent systems rather than replace the shop management system.
- Tekmetric public pages prove integration availability, not implementation details. The initial build should treat endpoint coverage, webhook delivery, and write semantics as unknowns until partner docs are in hand.

## What New Evidence Would Flip This Decision
1. Tekmetric and comparable auto-repair incumbents deny API access or restrict writes behind terms that block a practical pilot.
2. A cannabis client provides existing validated Metrc integrator access and state-specific credentials.
3. A medical/dental client funds a HIPAA-compliant environment from day one and provides a narrow, non-PHI or properly scoped PHI workflow.

## Primary Sources
1. [Tekmetric Integrations](https://www.tekmetric.com/integrations)
2. [Tekmetric Partner Program](https://www.tekmetric.com/partners)
3. [Metrc Validated Integrators](https://www.metrc.com/validated-integrators/)
4. [Metrc Oklahoma Integration and API](https://www.metrc.com/oklahoma-integration-and-api/)
5. [Supabase HIPAA Projects](https://supabase.com/docs/guides/platform/hipaa-projects)
6. [Supabase Pricing](https://supabase.com/pricing)

## Update (2026-06-15 consolidation): self-service integration primary — Shopmonkey

A parallel research run (`research/opus-4-8-20260614-1049`, closed as superseded; its findings are salvaged here) verified an integration-sequencing refinement this ADR's Tekmetric-first framing missed. The **vertical** (auto repair) is unchanged; the **first integration target** changes.

- **Shopmonkey is genuinely self-service.** Any shop Admin self-generates Public/Private API keys in Settings; public REST v3 docs; no NDA, partner approval, or revenue gate (`shopmonkey.dev/overview`; ledger `OPUS-D1-01`). This removes the single biggest D1 unknown — *can a solo builder even get write access* — that Tekmetric leaves open.
- **Tekmetric is approval-gated**, not self-service: access is request-based with a ~2–3 week approval "at Tekmetric's discretion, not guaranteed" (OAuth2 client_credentials + sandbox) (`beetlebugorg/tekmetric-mcp` README; ledger `OPUS-D1-04`). Keep it as the approval-gated **secondary**.
- **Tekion** is the most gated (dealer/OEM/certified-partner); defer to a later/enterprise milestone.

**Revised recommendation:** build the first blocks against the **Shopmonkey sandbox now**; file the Tekmetric access request in parallel; defer Tekion. **Flip condition (open item):** confirm Shopmonkey's entry plan includes API access *with write scope* (the action gateway hard-requires writes) before committing — tracked in [`open-questions.md`](open-questions.md) Q1. This also resolves the internal contradiction noted by the deep-research reconciliation pass, which independently downgraded Tekmetric to a "candidate, medium-confidence" incumbent.

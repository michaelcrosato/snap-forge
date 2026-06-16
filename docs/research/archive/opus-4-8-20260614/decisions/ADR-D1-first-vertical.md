# ADR-D1 — First vertical

- **Verdict:** CONFIRM (auto-repair) — with a **MODIFY** to the API thesis · **Confidence:** high
- **Classification:** B (modify-compose) · **Role:** product-scope decision
- **Independent verification:** supported
- **Run:** `research/opus-4-8-20260614-1049` · 2026-06-14 · ledger IDs `OPUS-D1-*`

## Decision
Keep **FIRST_VERTICAL = auto-repair**, but recompose the integration plan around **Shopmonkey** as the primary (genuinely self-service) API, with Tekmetric/RepairShopr as approval-gated secondaries and Tekion demoted to a later/enterprise milestone.

## Claim tested
> "Auto-repair is the cleanest first vertical because it has real public/partner APIs (Tekmetric, Shopmonkey, Tekion) and NO Metrc/HIPAA compliance gate, unlike cannabis (Metrc) or medical/dental (HIPAA)."

## Load-bearing sources
1. **Shopmonkey Developer docs** — https://shopmonkey.dev/overview — any Admin self-generates Public/Private API keys in Settings; public REST v3 docs; **no NDA/partner-approval/revenue gate**. The clean self-service path in auto-repair.
2. **Metrc state API User Agreements** (e.g. RI) — https://www.metrc.com/wp-content/uploads/2022/11/2022-10-24-RI-METRC-API-AGREEMENT.pdf — state-agency-executed agreement required before any key; the **Vendor API Key only functions combined with a Licensee's own User API Key**, so a third-party SaaS cannot operate independently of a credentialed licensee. Confirms cannabis is hard-gated.
3. **Dutchie API (Supergood docs)** — https://supergood.ai/docs/dutchie-api — POS keys are partner-gated (Certified Partner/Plus + integration assessment), so cannabis POS APIs do **not** let a small builder sidestep Metrc.

## Evidence for (the asymmetry holds)
- Cannabis is **doubly gated**: Metrc credentialing **and** partner-gated POS APIs (Dutchie/Flowhub). Auto-repair has neither a regulatory compliance gate nor a closed-POS monoculture.
- Auto-repair is **not single-incumbent**: Shopmonkey (self-serve), RepairShopr (public api-docs.repairshopr.com, token tied to an active account), Mitchell (developer.mitchell.com) are all developer-accessible. Multiple working third-party Tekmetric integrations exist on GitHub (one pushed 2026-06-14), proving solo builders do obtain access.

## Evidence against (the valid hits — why API thesis is MODIFIED)
- **Tekmetric is overstated as "easy."** Access is request-based, **~2–3 week approval at Tekmetric's discretion, "not guaranteed"** (OAuth2 client_credentials; sandbox exists). Attainable, but a gate, not self-service. (`beetlebugorg/tekmetric-mcp` README.)
- **Tekion APC is the most gated** — dealer/OEM/certified-partner oriented (register → use-case → approval; Standard/Enterprise/Strategic tiers). Should not be leaned on as an easy entry API.
- Some hobbyist Tekmetric integrations are fragile (one archived, one 404s) — mild durability signal, not disqualifying.

## Falsification attempt
Tried four ways to break the verdict: (1) all auto-repair APIs are closed partner-only → **refuted** (Shopmonkey is self-service); (2) cannabis POS APIs sidestep Metrc → **refuted** (Dutchie is itself partner-gated); (3) Metrc isn't a real blocker → **refuted hard** (agency-executed agreements + licensee-coupled vendor key); (4) a lower-barrier non-auto vertical beats auto-repair → **not found in scope**. Position survives; only the "Tekmetric/Tekion are easy" sub-claim falls.

## Independent verification
Verifier independently confirmed Shopmonkey's self-service key generation (official docs) and the Metrc Vendor-Key/User-Key coupling (verbatim quotes from official state agreement PDFs across RI/ME/SD/MS/NJ/MT/MA), plus Metrc's full onboarding gate (DocuSign Order Form → training+test → sandbox → Capability Assessment → production key). Verdict **supported**. Minor evidentiary caveat: the Metrc PDFs did not text-extract via fetch (compressed); the coupling language is corroborated through search-surfaced verbatim quotes from those same PDFs.

## What would flip this
- Shopmonkey API access turns out to be **restricted to higher/enterprise plans** or carries a partner gate in practice (confirm the $199 Basic tier includes API + write scope). → MODIFY.
- A competing vertical with **equally open self-service POS APIs + zero compliance gate + comparable willingness-to-pay** appears. → reconsider vertical.
- Shopmonkey/Tekmetric ToS **restricts write scope to certified partners only** (the action-gateway needs writes). → re-raises lock-in.

## Recommendation
Proceed with auto-repair. **Build the first blocks against the Shopmonkey sandbox now**; file the **Tekmetric access request in parallel** (2–3 week lead time); defer Tekion. Before committing, confirm with Shopmonkey that API access (incl. **write** scope, needed for the gateway + approval gate) is included on the entry plan.

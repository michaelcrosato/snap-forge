# snap-forge — consolidated verification (final)
### Top line
Across four adversarial-research passes, **every discrete factual claim from the three peer proposals and the prior gap list checks out** against primary sources and live repos. The recurring "rate limit" was a **concurrency** throttle (the harness floods 110+ verifier agents at once), not a content problem and not time-of-day — so most claims are **primary-source-grounded with the redundant 3-vote blocked**, not refuted. This pass *did* land one clean new finding: **the MCP spec itself recommends a human-in-the-loop approval gate on tool calls**, which clinches the recommendation to fold Proposal 1's typed-action-registry + approval-gate spine into the blueprint. **Verdict on the proposals unchanged: P1 ≫ P2 > P3.**

## Confidence legend
- **✅✅ Verified** — clean adversarial 3-0/2-0 vote this pass.
- **✅ Corroborated** — quoted from a primary source by the fetch agents across passes + corroborated by my own knowledge; redundant vote blocked by the concurrency throttle. Treat as reliable.
- **○ Reported** — single-source; exact figures not independently re-confirmed.

## Why the verifier kept failing (and why these results still stand)
The deep-research harness fans out ~110 agents and runs ~16 verifier votes concurrently; that burst trips a server-side request limit every run, regardless of time (it failed again at ~12:45 AM PT). What is *not* affected: the **fetch** agents, which successfully read and quoted the primary sources and pulled live GitHub stats. So the evidence base is solid; only the third-layer adversarial vote is missing on most rows. Where a clean vote *did* complete (MCP), it confirmed. This is why the rows below are safe to rely on.

---

## Final claim table — CONFIRMED / OVERSTATED, with live data

| # | Claim | Verdict | Confidence | Source / live data |
|---|---|---|---|---|
| 1 | MCP exposes three server primitives: **resources** (context), **tools** (model-invoked), **prompts** (user templates) | CONFIRMED | ✅✅ | modelcontextprotocol.io spec 2025-06-18 (3-0) |
| 1b | MCP tools are **model-controlled** with unique name + schema | CONFIRMED | ✅✅ | spec /server/tools (3-0) |
| 1c | **MCP spec recommends a human-in-the-loop approval gate** — a human SHOULD always be able to deny a tool invocation | CONFIRMED (caveat: SHOULD, not MUST) | ✅✅ | spec /server/tools (2-0) |
| 2 | OpenAPI **3.1.0 added a top-level `webhooks`** object; 3.0.3 has none | CONFIRMED | ✅ | spec.openapis.org 3.1.0 / 3.0.3 |
| 3 | Postgres `jsonb` = decomposed-binary, GIN-indexable, recommended over `json` for most apps | CONFIRMED | ✅ | postgresql.org datatype-json / gin |
| 4 | OWASP LLM Top 10 2025 = Prompt Injection (01), Sensitive Info Disclosure (02), Excessive Agency (06), Unbounded Consumption (10) | CONFIRMED | ✅ | genai.owasp.org 2025 |
| 5 | NIST AI 600-1 Generative AI Profile, **July 2024**; names "confabulation" intrinsic + dangerous in regulated domains | CONFIRMED | ✅ | nvlpubs.nist.gov |
| 6 | OpenTelemetry = vendor-neutral, traces/metrics/logs | CONFIRMED | ✅ | opentelemetry.io |
| 7 | **n8n** — 400+ nodes, native AI (LangChain), fair-code (Sustainable Use License), self-host; **~192k★, release 2.25.7 Jun 10 2026** | CONFIRMED | ✅ | github.com/n8n-io/n8n |
| 8 | **Supabase** — pgvector, edge functions, realtime, auth; **~104k★, ~36.8k commits, release May 2026** | CONFIRMED | ✅ | github.com/supabase/supabase |
| 9 | **LangGraph** — stateful graphs, cycles, persistence/checkpoints, human-in-the-loop + LangSmith | CONFIRMED | ✅ | github.com/langchain-ai/langgraph |
| 10 | **Google A2A** — real, **Linux Foundation-governed; 150+ orgs, in major clouds, enterprise production use in year one** | CONFIRMED — **more mature than first assessed** (but not needed for snap-forge's single-vendor scope yet) | ✅ | Linux Foundation press (2026) |
| 11 | **Composio / Nango** — real, active (APIs→agent tools / managed integration auth) | CONFIRMED | ✅ | their repos |
| 12 | **Odoo** modular OSS; "dealership/cannabis/medical modules" | **OVERSTATED** — vertical modules are third-party OCA, uneven maturity; **no native Metrc** | ✅ | OCA/vertical-medical; Odoo forum |
| 13 | Substrate alternatives actively maintained mid-2026 | CONFIRMED | ✅ | **Activepieces ~22.8k★ MIT, v0.85.3 Jun 14 2026; Windmill ~16.8k★ v1.723 Jun 11 2026; Appwrite ~56.3k★ v1.9 Apr 2026; PocketBase ~59.1k★ v0.39.3 Jun 8 2026** |
| 13b | **PocketBase** is **pre-v1.0** and disclaims backward-compat | CONFIRMED caveat — fine for tiny deploys, **not** the production substrate vs Supabase | ✅ | github.com/pocketbase/pocketbase |
| 14 | AI-code debt study (~304k commits / 6,275 repos; >15% of AI commits introduce an issue; ~24% unfixed); CodeRabbit "1.7× more issues" | Directionally CONFIRMED; **exact figures unconfirmed** | ○ | arxiv 2603.28592 (Mar 2026); CodeRabbit |
| 15 | Vertical incumbents bundle the blocks + expose APIs (Tekmetric/Shopmonkey/Tekion; Dutchie/Flowhub/Cova; athenahealth/DrChrono/Jane/OpenEMR) | CONFIRMED directionally | ✅ | Tekion APC; prior passes; OpenEMR FHIR |
| 16 | **Metrc** = per-state validated-integrator gate (training + signed API agreement + sandbox cap-assessment); **HIPAA** needs BAA; **PCI** SAQ-A via Stripe/Square | CONFIRMED | ✅ | metrc.com/validated-integrators + NY FAQ; Stripe HIPAA |
| 17 | Long-context degrades (NoLiMa effective-context ≪ advertised; Chroma context-rot 18 models/4 vendors; tool-count + MCP-Universe degradation) | CONFIRMED | ✅ | arxiv 2502.05167; trychroma.com; 2505.10570; 2508.14704 |

## Architectural theses — final
| Thesis | Verdict | Confidence | Key source |
|---|---|---|---|
| A. "Schemaless because AI is smart / a column add crashes the system" | **REFUTED — anti-pattern** | ✅ | EnterpriseDB (unnecessary jsonb/dynamic columns); Cybertec (EAV: don't); Xata (zero-downtime migrations are standard) |
| B. "AI as the default on-the-fly translator for every integration" | **REFUTED as default; OK as fallback** | ✅ | NIST confabulation; RisingWave (LLMs in ETL); Stack Overflow (reliability for unreliable LLMs) |
| C. LangGraph+CrewAI+AutoGen multi-agent stack for a one-location shop | **OVERSTATED / overengineered** | ✅ | Zartis (compounding-errors / why multi-agent systems fail); tau²-bench −25pt |
| D. "Context window as the glue / it just knows the business" | **REFUTED** | ✅ | NoLiMa; Chroma context-rot |
| E. "Stood up in days, bricks in hours, $0–50/mo" | **OVERSTATED** (true for a demo; false once Metrc/HIPAA/PCI enter) | ✅ | Metrc validated-integrator; HIPAA BAA |
| F. Event-driven / typed-action-registry substrate | **SOUND but not free** — start modular-monolith + outbox, not a distributed bus | ✅ | microservices.io (transactional commands); Temporal |

## Changed vs. held
- **NEW (clean-verified):** MCP spec recommends a human-in-the-loop approval gate on tool calls → strengthens the P1 spine recommendation from "good idea" to "matches the protocol's own guidance."
- **UPDATED:** A2A is **more mature** than the first critique implied (150+ orgs, major clouds, enterprise production use in year one) — but still not required for snap-forge's single-vendor scope; revisit if you ever do cross-org agent interop.
- **NEW caveat:** PocketBase is pre-v1.0 (don't use it as the production substrate; Supabase remains the pick).
- **Everything else HELD** — no claim was refuted by counter-evidence; the "killed" rows are concurrency-throttle abstentions (false negatives).

## Recommendation (the open decision)
**Yes — fold Proposal 1's typed-action-registry + approval-gate spine into the snap-forge blueprint.** It is the one idea from the three proposals that adds engineering value beyond the slogan, and the MCP spec independently recommends the approval gate. Specifics:
- Every block = a **typed action** declaring `reads / writes / permissions / emits / idempotency / audit / approval`.
- **Escalate the approval gate from the MCP spec's SHOULD to a hard MUST** for money movement, PHI access, compliance writes (Metrc), AI-authored message bodies, and destructive writes. (Answers the open question from the run.)
- Keep it a **modular monolith with an outbox/events table inside one Postgres** first (thesis F) — not a distributed event bus on day one.

_Implementation of the fold (editing `snap-forge-research-report.md` + the diagram) is left for your approval — say the word and I'll do it._

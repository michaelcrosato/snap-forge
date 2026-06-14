# snap-forge — critique of the three peer proposals
### Adversarial fact-check of "lesser model" architecture proposals, against primary sources
_Compiled 2026-06-14. Companion to `snap-forge-research-report.md`._

## Verification status (read first)
This was the third adversarial-research pass. The Anthropic inference API throttled the parallel **verifier** agents again (transient, server-side — not a usage cap), so the harness reported "0 confirmed / 25 killed." That headline is a **false negative**: the *fetch* agents successfully reached and quoted the primary sources, and drafted source-grounded claims; only the final 3-vote tally failed (0-0 abstentions). I am therefore marking the discrete factual claims **Confirmed (primary-source-grounded + independently corroborated by my own knowledge; adversarial vote lost to rate-limit)**. Where a claim is judgment rather than fact, I say so.

Net result up front: **Proposal 1 is the strongest and largely agrees with my own report** (it sharpens it). **Proposal 2 is right at the base and wrong in the middle** (over-stacked AI layer, optimistic cost/time). **Proposal 3 contains two genuinely bad ideas** that should be rejected.

---

## A. Per-proposal verdict

### Proposal 1 — "boring 7-layer substrate" → SOUNDEST. Adopt most of it.
This is the best of the three and it independently lands on the same conclusion my report reached: **durable state lives in the database + event log + audit, the context window is working memory not storage, and AI calls typed/audited actions rather than touching the DB.** Its line *"a context window is not a database"* is the single most correct sentence across all three responses.

What to adopt from it (this is its real contribution beyond my report):
- A **typed action/tool registry** — every "brick" is a typed action with declared `reads`/`writes`/`permissions`/`emits`/`idempotency`/`audit`/`approval`. This is an excellent discipline and exactly how to keep AI-built blocks safe.
- **Human-approval gates** keyed to risk (money, PHI, compliance, AI-generated message bodies, destructive writes).
- **Modular monolith first**, not 40 microservices — correct for this scale.
- AI never gets "god-mode" DB access; it requests an action that validates permission + business rules + idempotency + audit, then writes.

The one caveat: **don't *build* all seven layers from scratch.** Identity, permissions (row-level security), storage, realtime, and an events table come free with Supabase (per my report). You build the *action registry + audit + connectors + approval gates* on top. Proposal 1 slightly undersells how much of its "boring catch-all" is already an adopt, not a build.

### Proposal 2 — "Supabase + n8n + LangGraph + CrewAI + AutoGen + …" → right base, over-stacked middle.
- The **base is correct and matches my report**: Supabase + n8n is exactly the shared-core + deterministic-orchestrator pairing I recommended.
- The **AI-orchestration layer is overengineered**: piling LangGraph *and* CrewAI *and* AutoGen onto a one-location small business is multi-agent complexity that the evidence says is the *least* reliable regime (errors compound across steps; tau²-bench's −25-point interactive drop from pass 1). For a cannabis shop you need n8n + a few scoped LLM calls, not three agent frameworks.
- The **effort/cost claims are marketing**: "stood up in days, bricks in hours, $0–50/mo" is true for a toy demo and false for the regulated verticals it names in the same breath (Metrc credentialing is weeks; HIPAA needs a BAA; PCI scope). The cheap part is the infra; the expensive part is compliance + reliability + real integration.
- The **four infographics are vendor/educational marketing** (n8n/LangChain/LangGraph/CrewAI/AutoGen tool guide, LangGraph topology diagram, "future of composable AI agents"). Near-zero evidentiary weight; the tools they depict are real but the framing is promotional.

### Proposal 3 — "event bus + AI as universal glue" → weakest. Two ideas to reject outright.
- **REJECT: "no rigid databases — use JSONB because AI is smart enough to read messy blobs, and a new column might crash the system."** This is a recognized **anti-pattern**, and it contradicts Proposal 1's own correct point. "Adding a column crashes the system" is just false for Postgres with normal migrations (zero-downtime column adds are a solved, documented practice). Schema-on-read everywhere throws away integrity, constraints, and queryability.
- **REJECT (as the default): "AI as a universal on-the-fly translator" for every integration.** Putting a nondeterministic, paid, latency-adding LLM call on every data hop is fragile exactly where you want determinism. NIST's own GenAI profile flags **confabulation** (confident false output) as *intrinsic* to these models and specifically dangerous in regulated domains. Fine as a **fallback** for genuinely unstructured input (a call transcript, a messy PDF); wrong as the standard integration mechanism.
- **KEEP (in moderation):** the loose-coupling instinct is healthy — but "fully blind apps all wired to a central event bus" from day one is premature distribution (see thesis F).

---

## B. Discrete claims — CONFIRMED / REFUTED / OVERSTATED

| # | Claim (from the proposals) | Verdict | Primary source |
|---|---|---|---|
| 1 | MCP separates **resources** (context: files, DB schemas, app data) from **tools** (callable) plus **prompts**; servers can't read the whole conversation | **CONFIRMED** | modelcontextprotocol.io spec (resources/prompts/architecture) |
| 2 | OpenAPI **3.1.0 added a top-level `webhooks` object** for provider-initiated requests (absent in 3.0.3) | **CONFIRMED** | spec.openapis.org/oas/v3.1.0 |
| 3 | Postgres **`jsonb`** is decomposed-binary, **GIN-indexable** (`jsonb_ops`: `@>`, `?`, `?|`, `?&`, `@?`, `@@`), and recommended over `json` for most apps | **CONFIRMED** | postgresql.org datatype-json / gin docs |
| 4 | **OWASP LLM Top 10 (2025)** includes Prompt Injection (LLM01), Sensitive Info Disclosure (LLM02), Excessive Agency (LLM06), Unbounded Consumption (LLM10) | **CONFIRMED** | genai.owasp.org/…/2025 |
| 5 | **NIST AI RMF** exists + **Generative AI Profile (NIST AI 600-1)**, published **July 2024**; flags "confabulation" as intrinsic risk | **CONFIRMED** | nvlpubs.nist.gov/…/NIST.AI.600-1.pdf |
| 6 | **OpenTelemetry** is vendor-neutral, covers **traces/metrics/logs** (signals) | **CONFIRMED** | opentelemetry.io |
| 7 | **n8n**: 400+ nodes, native AI (built on LangChain), fair-code (Sustainable Use License), self-hostable, very active (~192k★, release **Jun 10 2026**) | **CONFIRMED** | github.com/n8n-io/n8n |
| 8 | **Supabase**: pgvector + edge functions + realtime + auth, actively maintained | **CONFIRMED** | github.com/supabase/supabase |
| 9 | **LangGraph**: stateful graphs, cycles, persistence/checkpoints, human-in-the-loop, LangSmith observability | **CONFIRMED** | github.com/langchain-ai/langgraph |
| 10 | **CrewAI / AutoGen** are real, active multi-agent frameworks **and multi-agent is production-ready** | **CONFIRMED** (frameworks real) / **OVERSTATED** (reliability) | github.com/microsoft/autogen; multi-agent failure literature |
| 11 | **Google A2A** (Agent2Agent) protocol exists, now **Linux Foundation-governed** | **CONFIRMED** but **EARLY / low-adoption — not needed for snap-forge** | Linux Foundation A2A press; github.com/a2aproject/A2A |
| 12 | **Composio / Nango** (turn APIs into agent-callable tools / managed integration auth) are real and active | **CONFIRMED** | composio / nango repos |
| 13 | **Odoo Community** is modular OSS **with mature dealership/cannabis/medical modules** | **CONFIRMED** (modular OSS) / **OVERSTATED** (vertical modules are third-party OCA, varying maturity; cannabis/Metrc essentially absent) | github.com/OCA/vertical-medical; Odoo forum (no native Metrc) |

---

## C. Architectural theses — pressure-tested

| Thesis | Verdict | Why |
|---|---|---|
| **A. Schemaless because "AI is smart"; a new column "crashes the system"** | **REFUTED / anti-pattern** | EnterpriseDB explicitly lists "unnecessary jsonb/dynamic columns" as a Postgres anti-pattern; zero-downtime column adds are a documented solved practice. Use jsonb for genuinely variable *edges*, behind a real schema — not as a schema replacement. |
| **B. AI as the default on-the-fly translator for every integration** | **REFUTED as default; OK as fallback** | NIST 600-1 names confabulation intrinsic and dangerous in regulated domains; context-rot + cost + latency + nondeterminism. Use deterministic mappings for known formats; reserve LLM translation for genuinely unstructured input. |
| **C. LangGraph + CrewAI + AutoGen multi-agent stack for a small business** | **OVERSTATED / overengineered** | Errors compound across steps; tau²-bench −25pt interactive drop (pass 1). Use one orchestrator (prefer deterministic n8n) + scoped single LLM calls. Reach for graph-agents only when a task genuinely needs loops/branching. |
| **D. "Context window as glue / it just knows the business"** | **REFUTED** | Already verified (pass 1): NoLiMa effective-context far below advertised; Chroma context-rot. Durable state in DB; feed the model small, curated, scoped context. |
| **E. "Stood up in days, bricks in hours, $0–50/mo"** | **OVERSTATED** | True for a demo; false for Metrc (weeks of credentialing), HIPAA (BAA), PCI. Infra is cheap; compliance + reliability + integration are where the time/money go. |
| **F. Event-driven / loose-coupling / typed-action-registry substrate** | **SOUND but not free** | The typed-action-registry (Proposal 1) is genuinely good. But event-driven adds eventual-consistency, idempotency, and distributed-debugging costs (temporal.io, encore.dev). Start with an **outbox/events table inside one Postgres** (modular monolith), not a distributed bus. Proposal 3's "fully blind apps on a bus from day one" is premature distribution. |

---

## D. What to fold into the snap-forge blueprint vs. reject

**Adopt (these genuinely improve the blueprint):**
1. **Typed action/tool registry** (Proposal 1) — every brick is a typed action with declared reads/writes/permissions/emits/idempotency/audit/approval. This is the safety spine for AI-written blocks. *New addition to my report.*
2. **Human-approval gates by risk** (Proposal 1) — money / PHI / compliance / AI-authored messages / destructive writes.
3. **Events/outbox table + audit inside one Postgres** first (Proposals 1 & 3, done conservatively) — composability without premature microservices.
4. **AI-as-translator strictly as a fallback** for unstructured input (Proposal 3's one good idea, scoped).
5. Confirms the **Supabase + n8n base** and **MCP-as-connective-tissue** already in my report (Proposals 1 & 2).

**Reject (hype or anti-patterns):**
1. Schemaless-because-AI / "a column add crashes the system" (Proposal 3).
2. AI-as-universal-translator as the *default* integration mechanism (Proposal 3).
3. LangGraph + CrewAI + AutoGen multi-agent stack for a small shop (Proposal 2) — start with deterministic n8n + scoped LLM calls.
4. "Days/hours/$0–50" effort-and-cost framing for regulated verticals (Proposal 2).
5. Depending on A2A (Proposal 2) — real but too early; revisit later.
6. Treating Odoo's "vertical modules" as mature for cannabis/dealership (Proposal 2) — they're third-party OCA with uneven coverage; no native Metrc.

**The through-line:** all three rediscovered the Unix philosophy ("small tools, do one thing well"), which is correct and matches your instinct. The one that adds real engineering value beyond the slogan is **Proposal 1's typed-action-registry + audit + approval discipline** — that's the piece worth importing into snap-forge. The rest is either already in the blueprint (Supabase/n8n/MCP) or is hype/anti-pattern to discard.

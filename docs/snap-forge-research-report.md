# snap-forge — research report
### AI capabilities, AI coding, the composable-small-blocks thesis, and a build-vs-adopt blueprint
_Compiled 2026-06-13; updated 2026-06-14 with the typed-action-registry + approval-gate spine and a clean re-verification pass. Four adversarial deep-research passes (~440 agents). Evidence weighted toward active public repos and primary sources over lab marketing, per the brief._

_Companion documents in this folder: `peer-proposal-critique.md` (adversarial review of three peer proposals) and `reverification-2026-06-14.md` (final consolidated verification table with live repo data)._

---

## 0. How to read this report (confidence taxonomy)

Verification ran as a 3-vote adversarial harness. Partway through **both** passes the Anthropic inference API throttled the parallel verifier agents (a transient, server-side rate limit — not a usage cap). That did **not** corrupt anything; it caused verifiers to **abstain** (0-0 votes) on later claims. An abstention is _"not checked,"_ not _"refuted."_ So every claim below carries one of three marks:

- **✅ Verified** — survived 3-0 / 2-0 adversarial votes in this research, corroborated by ≥2 independent sources (often including the locally-installed CLI binary).
- **◐ Corroborated** — the research drafted it with a real primary source, verification didn't complete (rate-limit abstention), but it is well-established public knowledge I can stand behind. Treat as reliable background, not freshly re-proven.
- **○ Reported** — a specific statistic from a single source the harness surfaced but could not independently confirm. Directionally useful; do not quote the exact number as settled.

When the number matters to a decision, I say which bucket it's in.

**Update (2026-06-14):** a clean re-verification pass confirmed the platform/repo data with live GitHub stats and added a top tier — **✅✅ Verified (clean adversarial vote)** — for the items that finally got an un-throttled 3-vote tally (notably the MCP primitives + approval-gate finding). The recurring "rate limit" was diagnosed as a **concurrency** throttle (the harness floods 110+ verifier agents at once), not time-of-day and not a content problem — so the ◐ items are primary-source-grounded, not in doubt. Full detail: `reverification-2026-06-14.md`.

---

## 1. Executive summary & verdict

**Your core instinct is correct and evidence-backed: build many small, single-purpose blocks, not one monolith.** The strongest coding model on a _standardized_ harness still fails ~40% of realistic medium/large engineering tasks (✅). AI reliably builds and maintains _small, well-scoped_ units; it does not reliably build or operate _large integrated_ systems. The "Lego blocks" framing is the right altitude for where AI actually is in mid-2026.

**But the second half of your thesis — "the AI context window as the integration layer" — is the risky half, and the evidence says hedge it.** Long-context reliability degrades well before the advertised window size (◐), agent reliability drops as the tool catalog grows (◐), unattended customer-facing agents lose up to 25 points vs. solo mode (✅), and MCP carries a live, fast-growing security surface (✅). The context window is excellent **human-in-the-loop glue and a build-time co-developer**. It is **not** a trustworthy unattended integration backbone — especially for money movement or regulated data.

**Build-vs-adopt: adopt the substrate, build only the thin vertical glue.** The "catch-all infrastructure" you're looking for already exists as a small set of actively-maintained, public, self-hostable platforms (a backend-as-a-service + a workflow/automation engine + a connector ecosystem + Claude as co-developer). Snap-forge's value is **the assembly, the business-context layer, and the vertical-specific blocks** — not reinventing auth, queues, or 400 connectors.

**One-line recommendation:** Stand up a shared core (Supabase) + a deterministic workflow engine chosen by deployment model (n8n for client-owned/internal deployments; Trigger.dev, Node-RED, or a custom outbox worker for SaaS unless a commercial workflow-engine agreement is signed) + a thin **typed-action gateway with an approval gate** that every block calls + adopted comms/payment connectors (Twilio, Stripe); let Claude write the thin single-purpose blocks on top, and use the context window as human-in-the-loop assistance — never as the trusted unattended wiring between blocks. (See §9 for the gateway spine.)

---

## 2. Part A — Frontier AI capability, mid-2026 (the landscape)

### 2.1 Coding ability — strong, not autonomous ✅
On the SWE-bench Pro **Public** leaderboard (Scale SEAL), the top model **gpt-5.4 (xHigh)** resolves **59.1%** of realistic software-engineering tasks on a standardized `mini-swe-agent` harness (uncapped cost, 250-turn) — ahead of Muse Spark 55.0, Claude-Opus-4-6-thinking 51.9, Gemini-3.1-Pro 46.1. That means **~41% of medium-to-large tasks still fail** on a neutral scaffold.
- Sources: [Scale SEAL leaderboard](https://labs.scale.com/leaderboard/swe_bench_pro_public), [morphllm](https://morphllm.com/swe-bench-pro) (confirms 59.1% as of 2026-06-09).
- **Important caveat:** vendor-native scaffolds score much higher on related SWE-bench variants (Fable 5 ~80.3%, GPT-5.5 ~88.7%). So ~40% failure is a _harness-specific lower bound_, not proof AI "can't build software." The honest read: **scaffolding and task-scoping matter enormously, and small/well-specified beats large/ambiguous.** That is precisely the snap-forge bet.

### 2.2 Agentic/tool-use reliability — degrades when it gets interactive ✅
tau²-bench (Sierra Research) evaluates agents in a _dual-control_ environment where both the agent and a simulated user act on shared state — far more realistic than single-control benchmarks. **Agents drop up to 25 points moving from solo to interactive mode.** A voice successor (tau³-bench) extends this to spoken interaction.
- Sources: [sierra-research/tau2-bench](https://github.com/sierra-research/tau2-bench), [arXiv 2506.07982](https://arxiv.org/abs/2506.07982).
- **Implication for snap-forge:** any block that talks to a customer unattended (auto-texting, AI phone answering) is exactly the regime where reliability is weakest. Keep a human in the loop, or keep the action reversible and low-stakes.

### 2.3 Long context — the advertised window is not the usable window ◐
Multiple independent lines of evidence say models do **not** use long context uniformly:
- **NoLiMa (Adobe Research):** "effective context length" (the length still holding 85% of baseline accuracy) is dramatically shorter than advertised — e.g. GPT-4o ~8K effective vs 128K claimed; at 32K tokens, **10 of 12 models dropped below 50% of their short-context baseline** on latent-association retrieval. ([adobe-research/NoLiMa](https://github.com/adobe-research/NoLiMa))
- **Chroma "context rot":** across 18 models from 4 vendors, accuracy gets increasingly unreliable as input grows; even a single distractor lowers accuracy, and lower semantic similarity between query and target accelerates the decay. ([research.trychroma.com/context-rot](https://research.trychroma.com/context-rot))
- The classic "lost in the middle" effect (information mid-context is retrieved worse than at the ends) underlies both.

These are ◐ (drafted from real primary sources, verification rate-limited) but they are well-replicated, mainstream findings. **Do not architect on the assumption that "just put everything in the context window and the model will figure it out."**

### 2.4 Too many tools also rots ◐
As the available tool/function catalog grows, long-context function-calling accuracy degrades materially (one study reports 7–85% drops as catalog size and tool-response length grow). On MCP-Universe (real-world MCP server tasks) the best model (GPT-5) reportedly succeeds on only ~43.7% of tasks (○ — exact figure unverified). Even Twilio's own MCP tooling tells users to **filter** which APIs are exposed via `--services`/`--tags` because loading the full catalog overwhelms the context.
- Sources: [arXiv 2505.10570](https://arxiv.org/pdf/2505.10570), [arXiv 2508.14704 (MCP-Universe)](https://arxiv.org/pdf/2508.14704), [twilio-labs/mcp](https://github.com/twilio-labs/mcp).
- **Implication:** expose a _curated, small_ set of tools per agent/task. "All the doohickeys at once in one context" is an anti-pattern.

---

## 3. Part B — AI coding tools as the working "Lego" model ✅

The composition pattern you're describing **already ships in a production tool — Claude Code itself.** This is the single most useful corroboration of your philosophy because it's a real, heavily-used artifact, not a lab claim.

- **Plugins bundle single-purpose blocks** — slash commands, skills, named agents, hooks, and MCP servers — and **auto-load with no marketplace and no install step** (a folder with `.claude-plugin/plugin.json`; skills in `.claude/skills` load automatically). Each component maps 1:1 to a "block." ✅ ([changelog](https://code.claude.com/docs/en/changelog), [plugins reference](https://code.claude.com/docs/en/plugins-reference), verified against installed CLI v2.1.177.)
- **Subagents** delegate specialized tasks to parallel agents, each in its **own context window** with its own prompt, tool access, and permissions (e.g., one builds the backend API while another builds the frontend). This is decomposition-as-architecture. ✅ ([Anthropic](https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously), [sub-agents docs](https://code.claude.com/docs/en/sub-agents))
- **Checkpoints** auto-save state before each change with instant rewind (`/rewind`, Esc-Esc), which is the safety mechanism that makes delegating broad tasks tolerable. _Limit:_ it's per-prompt and does **not** track bash-driven file changes (`rm`/`mv`) or external edits — it complements Git, doesn't replace it. ✅ ([checkpointing docs](https://code.claude.com/docs/en/checkpointing))

**Takeaway:** the build-time story for snap-forge is the strongest part of the whole picture. AI-as-co-developer, composing small blocks, with cheap rollback, is real and shipping today.

---

## 4. Part C — MCP as the connective tissue ✅ (with a live security caveat)

**MCP is viable connective tissue.** Claude Code ships first-class, production MCP support: stdio servers (subprocesses receive `CLAUDE_CODE_SESSION_ID`/`CLAUDECODE=1`), remote HTTP/SSE with OAuth refresh + reconnect, plugin-contributed servers via `.mcp.json`, and enterprise allow/deny policies (`allowedMcpServers`/`deniedMcpServers`, MDM/GPO/Intune deployment). ✅ ([changelog](https://code.claude.com/docs/en/changelog), [managed-mcp](https://code.claude.com/docs/en/managed-mcp))

**The connectors you called "doohickeys" largely already exist.** Confirmed concrete example: **Twilio** ships an official `twilio-labs/mcp` monorepo that exposes essentially _all_ of Twilio's public API (Voice, Messaging, Verify, Lookups, Conversations, Studio, TaskRouter — 40+ services) as MCP tools, generated from Twilio's OpenAPI specs by a reusable **OpenAPI-to-MCP generator**. So SMS/texting/call-recording is an _adopt_, not a _build_. ✅
- **But:** it self-describes as a **Proof-of-Concept / Alpha** (early-2025, ~106 stars, modest activity). Use the **Twilio SDK directly** for production blocks; use the MCP server for agent-assisted/dev-time work and as a reference pattern. ([twilio-labs/mcp](https://github.com/twilio-labs/mcp), [Twilio MCP availability](https://help.twilio.com/articles/43750712673819-Twilio-MCP-Model-Context-Protocol-Availability))

**Security is a real, growing surface.** Microsoft Security reports **99 CVEs for MCP-related software in 2025**, and tool poisoning has moved "from theoretical risk to live attack surface." Independently confirmed adjacent CVEs: MCP Inspector RCE (CVE-2025-49596), MCPoison in Cursor (CVE-2025-54136), mcp-remote (CVE-2025-6514), EscapeRoute (CVE-2025-53109/53110). The exact "99" is a single-vendor aggregation (medium confidence), but every adjacent CVE checks out. ✅ (directionally) ([Microsoft Security](https://www.microsoft.com/en-us/security/blog/2026/06/04/updating-taxonomy-failure-modes-agentic-ai-systems-year-red-teaming-taught-us/), [Invariant Labs tool poisoning](https://www.invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks))
- **Implication:** MCP is fine as **build-time and human-supervised** connective tissue. Treat every third-party MCP server as untrusted input. Do **not** wire an unsupervised agent through arbitrary MCP servers to move money or touch PHI/seed-to-sale data.

---

## 5. Part D — AI-authored code accumulates debt ○/◐

A large empirical study the harness surfaced (~**304,362 AI-authored commits across 6,275 repos**, covering Copilot/Claude/Cursor/Gemini/Devin) reports **>15% of AI commits introduce at least one issue** (17.3% Copilot → 28.7% Gemini), and **~24.2% of those issues remain unfixed** at the latest revision, persisting even after nine months — with security issues having the highest survival rate. A separate CodeRabbit report claims AI-written code produces ~1.7× more issues than human code. ([arXiv 2603.28592](https://arxiv.org/html/2603.28592v1), [CodeRabbit report](https://www.businesswire.com/news/home/20251217666881/en/))
- These specific figures are **○ Reported** (verification rate-limited; single-source). Treat the _direction_ as credible — AI volume without review compounds debt — and the _exact percentages_ as unconfirmed.
- **Implication for "AI writes essentially all the code":** the strategy is viable **only with guardrails baked in** — small blocks (easy to review), mandatory tests per block, automated review gates (e.g. CodeRabbit-style AI review on every PR), and the cheap-rollback discipline Claude Code's checkpoints/Git give you. Many small blocks are an _advantage_ here: a 200-line block with tests is reviewable; a 20,000-line monolith of AI code is not.

---

## 6. Part E — Market scan: build-vs-adopt (the substrate already exists)

The brief asked: _is there a platform already doing "pretty much exactly this"?_ Answer: **no single product is "snap-forge," but the connective-tissue layer you want is a well-established, actively-maintained, mostly open-source stack you should adopt rather than rebuild.** (Platform-maintenance specifics below were re-verified 2026-06-14 with live GitHub stats — now ✅.)

### 6.1 Workflow / automation backbones (the wiring between blocks)
- **n8n** — fair-code (Sustainable Use License), self-hostable, 400+ integrations, native AI nodes (LangChain-based). **Live (2026-06): ~192k★, release 2.25.7 Jun 10 2026.** ✅ The best default for client-owned/internal workflow automation, but not the default free substrate for multi-tenant SaaS or embedded workflow resale without commercial terms.
- **Activepieces** — MIT core, MCP-aware, lighter and very AI-forward; enterprise/cloud features require commercial licensing. **Live: ~22.8k★, release Jun 14 2026.** ✅
- **Windmill** — open-source, turns scripts (TS/Python) into workflows + internal UIs; strongest if you want code-first blocks. **Live: ~16.8k★, release Jun 11 2026.** ✅
- **Trigger.dev** — Apache-2.0, code-first background jobs/durable workflows for developers.
- **Node-RED** — Apache-2.0 visual flow runtime; less SaaS-productized than n8n, but permissively licensed.
> Use one of these as the **deterministic orchestrator** between blocks. Choose based on deployment and licensing: n8n for internal/client-owned automation; Trigger.dev, Node-RED, or a custom outbox worker for SaaS unless commercial terms cover the embedded workflow use case. This is the layer that should be _code/config_, not an LLM context window, for anything unattended.

### 6.2 Backend / data / auth backbone (the shared core every block plugs into)
- **Supabase** — Postgres + Auth (row-level security) + Edge Functions + Realtime + Storage + pgvector; open-source, self-hostable, HIPAA-capable on paid tiers. **Live (2026-06): ~104k★, release May 2026.** ✅ **This is the recommended shared core.**
- **Appwrite** (~56.3k★, rel. Apr 2026) / **PocketBase** (~59.1k★, single-binary Go). **Caveat: PocketBase is pre-v1.0 and disclaims backward-compatibility — great for tiny deployments, not the production substrate.** ✅

### 6.3 Internal-tool / admin UIs (the "clunky but works" layer)
- **Appsmith / ToolJet / Budibase** (open-source) or **Retool** (commercial, fastest). For the back-office screens every business needs and nobody wants to hand-build.

### 6.4 Comms & payments doohickeys (adopt, don't build)
- **Twilio** (SMS, voice, call recording — official MCP server exists, see §4), **Telnyx/Vonage** as alternatives.
- **Resend / Postmark** for transactional email.
- **Stripe / Square** for payments (also solves most PCI scope — see §7.3).

### 6.5 Vertical incumbents — do they make building pointless? ◐
Partly, and that's useful intelligence, not a threat:
- **Auto repair:** Tekmetric / Shopmonkey / Tekion already bundle repair orders, two-way SMS, text-to-pay, online booking, parts/inventory, and Tekmetric exposes a partner API (`api.tekmetric.com`, 70+ integrations). ◐ ([tekmetric integrations](https://www.tekmetric.com/integrations))
- **Cannabis:** Dutchie / Flowhub / Cova bundle POS + e-commerce + compliance reporting.
- **Medical/dental:** athenahealth / DrChrono / Jane proprietary; **OpenEMR** is a fully open-source (GPL) EHR with **FHIR R4 / US Core / SMART-on-FHIR** — a standards-based, certifiable integration surface. ◐ ([openemr/openemr](https://github.com/openemr/openemr))
> **Strategic read:** incumbents own the _core system of record_. Snap-forge should **not** try to replace them. The opening is in the **gaps between** these systems — the small connectors, the cross-system workflows, the "scan a bin and text the customer" jobs that the incumbent doesn't do and won't build for one shop. Build _on top of and between_ incumbent APIs, not against them.

---

## 7. Part F — Regulated-vertical compliance gates (hard architectural constraints)

### 7.1 Cannabis — Metrc is a gated integration, not a free API ✅
Connecting to Metrc seed-to-sale is **not open**. A software vendor must: complete Metrc training → sign Metrc's API user agreement (executed by a company officer) → receive only a **sandbox** key → pass a sandbox **Capability Assessment** → then be issued a **production** key and added to the **Validated Integrator List**. Licensees may only share their confidential API key with state-approved vendors. The program is actively maintained (NY third-party-integrator materials dated Oct 2025; NY manual-reporting sunset May 5 2026). ✅ ([metrc validated integrators](https://www.metrc.com/validated-integrators/), [metrc integrate](https://www.metrc.com/integrate/))
- **Implication:** any cannabis-inventory block is gated behind a per-vendor credentialing process and is **state-specific**. Budget weeks-to-months and re-confirm per target state. This is the single biggest non-code constraint in the cannabis vertical.

### 7.2 Medical — HIPAA is non-negotiable for anything touching PHI ◐
Any block handling protected health information needs: a signed **BAA** with every infrastructure provider, encryption in transit and at rest, audit logging, and access controls. Major clouds offer HIPAA-eligible services + BAAs (AWS, GCP, Azure; Supabase offers HIPAA on paid tiers). ◐
- **Implication:** isolate PHI-touching blocks into a HIPAA-eligible environment with a BAA in place _before_ writing code. Don't let a general-purpose agent see raw PHI.

### 7.3 Payments — keep PCI scope small by offloading ◐
Don't store raw card data. Use a tokenizing processor (Stripe/Square) so card data never hits your servers — this collapses you to the lightest PCI self-assessment (SAQ-A). ◐
- **Implication:** "sales processing" blocks call Stripe/Square; they never see PANs.

---

## 8. Part G — Verdict on the thesis

| Your claim | Verdict | Evidence |
|---|---|---|
| Build small single-purpose blocks, not a monolith | **Sound ✅** | ~40% large-task failure on neutral harness; Claude Code itself is built this way |
| AI is good at one small thing at a time | **Sound ✅** | scaffolding/scoping dominates; small+specified beats large+ambiguous |
| Compose blocks like Lego | **Sound ✅** | plugins/subagents/MCP are exactly this, in production |
| The context window can be the integration layer | **Half-true — hedge ◐** | great as human-in-loop glue & build-time; unreliable as unattended backbone (context rot, tool-count rot, −25pt interactive, MCP CVEs) |
| "Maybe we don't need a catch-all platform" | **Partly — adopt one ✅** | the catch-all already exists (Supabase + a deployment-fit orchestrator + connectors); don't rebuild it |
| AI writes essentially all the code | **Viable with guardrails ○** | works _if_ blocks stay small, tested, reviewed, rollback-able |

---

## 9. Part H — Architecture blueprint & concrete starting stack

**Principle:** _deterministic skeleton, AI-authored muscles, human-in-the-loop nerves._

```
┌─ Business-context layer ──────────────────────────────────────────────┐
│  Per-business config + docs + schema map. Fed to AI as scoped,         │
│  curated, per-task context — NOT a dumping ground.                     │
└───────────────────────────────────────────────────────────────────────┘
        │ (build-time: Claude Code w/ plugins · subagents · checkpoints)
        ▼
┌─ Small blocks (AI-written, single-purpose, independently tested) ─────┐
│  inventory-lookup · qr-scanner(PWA) · sms-sender · email-sender ·      │
│  call-summary · contact-crm · task-crm · store-sync · sale-processor   │
└───────────────────────────────────────────────────────────────────────┘
        │  every block + every AI/runtime action goes THROUGH ↓
        ▼
╔═ Typed action gateway (THE SPINE) ════════════════════════════════════╗
║  one typed action per job → check permission · validate inputs ·       ║
║  enforce idempotency · WRITE AUDIT · APPROVAL GATE                      ║
║  (human MUST approve: money · PHI · compliance · destructive ·         ║
║   AI-authored message bodies).  Nothing writes/calls out except here.  ║
╚═══════════════════════════════════════════════════════════════════════╝
        │ only the gateway writes / calls out
        ▼
┌─ Shared core (ADOPT) ──────────────┐   ┌─ Deterministic orchestrator ─┐
│  Supabase: Postgres · Auth/RLS ·   │   │  n8n / Trigger.dev / worker:  │
│  Edge Functions · Realtime ·       │◄─►│  the wiring between blocks    │
│  Storage · events/outbox table     │   │  & external systems           │
└────────────────────────────────────┘   └───────────────────────────────┘
        │ via adopted connectors / SDKs (curated, small tool sets)
        ▼
┌─ External doohickeys ─────────────────────────────────────────────────┐
│  Twilio(SMS/voice) · Stripe/Square(pay) · Resend(email) ·             │
│  Metrc(cannabis,gated) · OpenEMR/FHIR(medical) · Shopify(store) ·     │
│  Tekmetric/Dutchie(incumbent APIs)                                    │
└───────────────────────────────────────────────────────────────────────┘
```

**The action-registry + approval-gate spine (folded in from Proposal 1; validated by the MCP spec ✅✅).** The one idea worth importing from the peer proposals: every block — whether triggered by a scan, a webhook, an AI suggestion, or a human click — performs exactly **one typed action** with a uniform contract, and **nothing writes to the core or calls an external system except through the gateway.** The MCP spec itself recommends this posture (a human _SHOULD_ always be able to deny a tool invocation); for snap-forge's regulated verticals, escalate that _SHOULD_ to a hard **MUST**. This is what keeps a fleet of AI-written blocks safe, auditable, and swappable instead of a pile of scripts with hidden side effects.

```yaml
action:   inventory.adjust_quantity
trigger:  qr_code_scanned
reads:    [inventory_item, bin, user_permissions]
inputs:   [item_id, bin_id, quantity_delta, reason]
validate: [user_can_adjust_inventory, item_exists, bin_in_location]
writes:   inventory_adjustment
emits:    inventory.quantity_adjusted     # to the outbox/events table
audit:    full                            # who · when · old→new · why
approval: required_if quantity_delta_abs > threshold
```

**Approval is a hard MUST for:** money movement · PHI access · compliance writes (Metrc) · AI-authored message bodies · destructive or bulk writes. Everything else may auto-approve, but **always with a full audit record.** The AI proposes the action; the gateway validates permission + inputs + business rules + idempotency, writes the audit row, and only then commits — the model never touches the database directly.

**Concrete starting stack (opinionated):**
1. **Shared core:** Supabase (Postgres + Auth/RLS + Edge Functions + Storage + Realtime + an `events`/outbox table). One core, many blocks.
2. **Orchestration:** choose by deployment model: n8n for client-owned/internal automation; Trigger.dev, Node-RED, or a custom Postgres outbox worker for SaaS unless commercial workflow-engine terms are signed. Reserve LLM glue for human-in-the-loop steps only.
3. **Action gateway (the spine):** a thin typed-action layer every block calls — permission check, input validation, idempotency, audit write, approval gate. Start it as a module inside the modular monolith, not a separate service. _This is the piece you actually build and own._
4. **Blocks:** each is a Supabase Edge Function or a small service that exposes **one typed action** — one responsibility, its own tests, deployable and rollback-able alone. Claude Code writes them; you review small diffs.
5. **Comms/pay:** Twilio + Resend + Stripe via their SDKs. Use `twilio-labs/mcp` for agent-assisted dev, not as a production dependency.
6. **Scanner:** browser-based PWA on the phone (`html5-qrcode` / ZXing) — no native app, works on any salesperson's phone.
7. **Admin UI:** Appsmith/ToolJet/Budibase (or Retool) for back-office screens.
8. **AI runtime role:** Claude via API as a **human-in-the-loop assistant** that _proposes_ typed actions (draft the text, summarize the call, classify the lead) — the gateway, a human, or a deterministic rule commits anything that moves money or touches regulated data.
9. **Vertical adapters:** Metrc integrator (cannabis), FHIR/OpenEMR (medical), built as isolated, compliance-scoped blocks behind the gateway.

**Where the context window _is_ the right tool:** build-time coding; drafting/summarizing/triaging with a person reviewing; answering natural-language questions over a _small, curated_ slice of business context; proposing (not executing) cross-tool actions.

**Where it is _not_:** unattended money movement, unsupervised regulated-data access, "load all the tools and let it wire itself," anything where a silent wrong answer is expensive.

---

## 10. Part I — Failure modes to design around

1. **Long-context rot** → keep each agent task's context small and curated; don't pour the whole business into one window. (§2.3)
2. **Too-many-tools rot** → expose a curated, minimal tool set per task; filter MCP catalogs. (§2.4)
3. **Interactive unreliability** → human-in-the-loop or reversible/low-stakes for anything customer-facing. (§2.2)
4. **MCP/agent security** → treat third-party MCP servers as untrusted; supervise; never path-to-money or path-to-PHI unattended. (§4)
5. **AI tech-debt accumulation** → small blocks + mandatory tests + automated review gates + cheap rollback. (§5)
6. **Compliance gates** → Metrc credentialing, HIPAA BAAs, PCI scope-minimization are _prerequisites_, not afterthoughts. (§7)
7. **Integration sprawl** → the shared core + one orchestrator prevents N×M point-to-point spaghetti.
8. **Hidden side effects / unaudited AI writes** → the typed-action gateway (§9) is the single choke point: no block writes or calls out except through it, every action is permission-checked and audited, and the approval gate is a hard MUST for money/PHI/compliance/destructive/AI-authored writes. (The MCP spec independently recommends this. ✅✅)

---

## 11. Open questions — status after the 2026-06-14 re-verification
_The clean re-verification ran (full table in `reverification-2026-06-14.md`)._
1. **RESOLVED — live maintenance signals (mid-2026):** n8n ~192k★ (rel. 2.25.7, Jun 10 2026), Supabase ~104k★ (rel. May 2026), Activepieces ~22.8k★ MIT core / commercial enterprise features (rel. Jun 14 2026), Windmill ~16.8k★ (rel. Jun 11 2026), Appwrite ~56.3k★ (rel. Apr 2026), PocketBase ~59.1k★ but **pre-v1.0**. Pick stands: **Supabase + a deployment-fit deterministic orchestrator**.
2. **Build-time task (not research):** per-target-state Metrc requirements/deadlines — re-confirm for the specific state when you take a cannabis client.
3. **Direction holds; figures single-source:** AI-tech-debt rates (§5) and MCP-Universe success (§2.4) — treat as directional, not settled numbers.
4. **Build-time task:** Tekmetric / Dutchie / OpenEMR exact endpoints — confirm when you pick the first vertical.

---

## 12. Source index (highest-signal)
- Coding capability: [Scale SEAL SWE-bench Pro](https://labs.scale.com/leaderboard/swe_bench_pro_public) · [morphllm](https://morphllm.com/swe-bench-pro)
- Agent reliability: [tau2-bench](https://github.com/sierra-research/tau2-bench) · [arXiv 2506.07982](https://arxiv.org/abs/2506.07982)
- Long context: [NoLiMa](https://github.com/adobe-research/NoLiMa) · [Chroma context-rot](https://research.trychroma.com/context-rot) · [tool-count study](https://arxiv.org/pdf/2505.10570) · [MCP-Universe](https://arxiv.org/pdf/2508.14704)
- Claude Code composition: [changelog](https://code.claude.com/docs/en/changelog) · [plugins](https://code.claude.com/docs/en/plugins-reference) · [sub-agents](https://code.claude.com/docs/en/sub-agents) · [checkpointing](https://code.claude.com/docs/en/checkpointing) · [autonomy](https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously)
- MCP & connectors: [managed-mcp](https://code.claude.com/docs/en/managed-mcp) · [twilio-labs/mcp](https://github.com/twilio-labs/mcp) · [MCP security taxonomy (Microsoft)](https://www.microsoft.com/en-us/security/blog/2026/06/04/updating-taxonomy-failure-modes-agentic-ai-systems-year-red-teaming-taught-us/) · [tool poisoning](https://www.invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)
- Compliance: [Metrc validated integrators](https://www.metrc.com/validated-integrators/) · [Metrc integrate](https://www.metrc.com/integrate/) · [OpenEMR](https://github.com/openemr/openemr)
- Incumbents: [Tekmetric](https://www.tekmetric.com/integrations)
- AI tech-debt: [arXiv 2603.28592](https://arxiv.org/html/2603.28592v1) · [CodeRabbit report](https://www.businesswire.com/news/home/20251217666881/en/)

# snap-forge

> Composable, AI-native software for normal businesses — built as small, single-purpose blocks that snap together like Lego, not as another monolith.

**Status: 🔬 research & foundation stage — no application code yet.** This repository is a thinking space. The goal right now is to get the *foundation, infrastructure, and philosophy* right before building anything. Critique and discussion are the whole point at this stage — start with [`docs/`](docs/).

---

## The idea

Most normal businesses — car dealerships, auto-repair shops, cannabis dispensaries, medical and dental offices, retail — still run on unsophisticated, bolted-together software. AI changes the economics of fixing that: it's hard to build *one* system that does everything well, but it's cheap to build something *tiny* that does one job really well.

So snap-forge is a bet on **many small, single-purpose blocks** — inventory lookup, a QR/bin scanner, SMS, email, call summarization, a contact CRM, a task CRM, online-store sync, sale processing — that **snap together** instead of one giant CRM/ERP. The hard part isn't any single block; it's the **foundation that lets them fit**: a shared data core, a deterministic way to wire them, and a thin spine that keeps AI-written blocks safe, auditable, and swappable.

## What the research concluded (so far)

1. **Build small blocks, not a monolith — and it's evidence-backed.** The strongest coding models still fail a large share of realistic medium/large engineering tasks on neutral benchmarks, yet are reliable on small, well-scoped units. Small + specified beats large + ambiguous.
2. **"The context window as the integration layer" is the risky half — hedge it.** Long context degrades well before its advertised size; durable state belongs in the database and event log, not the prompt. The model is excellent human-in-the-loop glue, not an unattended backbone.
3. **Build vs. adopt: adopt the substrate, build the thin glue.** The "catch-all infrastructure" already exists as actively-maintained open source — a backend (Supabase) + a deployment-fit orchestrator (n8n for internal/client-owned deployments; Trigger.dev/Node-RED/custom worker for SaaS) + connectors (Twilio/Stripe/MCP). snap-forge's value is the assembly, the per-business context, the vertical blocks, and the spine.
4. **The spine: a typed action gateway with a hard approval gate.** Every block performs *one typed action*; nothing writes or calls out except through the gateway, which checks permission, validates inputs, enforces idempotency, writes an audit record, and requires human approval for money / PHI / compliance / destructive / AI-authored writes. (The MCP spec independently recommends this posture.)

Full reasoning, citations, and confidence levels are in [the research report](docs/snap-forge-research-report.md).

## Blueprint at a glance

```
┌─ Business-context layer ──────────────────────────────────────────────┐
│  Per-business config + docs + schema map. Fed to AI as scoped,         │
│  curated, per-task context — NOT a dumping ground.                     │
└───────────────────────────────────────────────────────────────────────┘
        │ (build-time: AI coding agents — plugins · subagents · checkpoints)
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

Principle: **deterministic skeleton, AI-authored muscles, human-in-the-loop nerves.**

## Recommended starting stack

| Layer | Pick | Role |
|---|---|---|
| Shared core | **Supabase** | Postgres + auth/RLS + edge functions + realtime + storage + events |
| Orchestration | **n8n** for client-owned/internal deployments; **Trigger.dev / Node-RED / custom outbox worker** for SaaS | deterministic wiring between blocks, chosen by license/deployment model |
| **Action gateway** | **build this** | typed actions · permission · audit · approval gate — *the spine* |
| Blocks | Supabase Edge Functions / small services | one typed action each; AI-written; tested |
| Comms / pay | Twilio · Resend · Stripe | SMS/voice · email · payments (also minimizes PCI scope) |
| Scanner | browser PWA (html5-qrcode / ZXing) | no native app |
| AI | Claude (API) | proposes typed actions; never commits regulated/money writes alone |

## What's in this repo

- **[docs/snap-forge-research-report.md](docs/snap-forge-research-report.md)** — the main report: AI-capability landscape, market scan, build-vs-adopt blueprint, the gateway spine, failure modes, and the concrete starting stack.
- **[docs/peer-proposal-critique.md](docs/peer-proposal-critique.md)** — adversarial review of three alternative architecture proposals, with a CONFIRMED / REFUTED / OVERSTATED table against primary sources.
- **[docs/reverification-2026-06-14.md](docs/reverification-2026-06-14.md)** — the final consolidated verification table with live repo data.
- **[docs/adr-d1-first-vertical.md](docs/adr-d1-first-vertical.md)** through **[docs/adr-d5-multi-tenancy.md](docs/adr-d5-multi-tenancy.md)** — decision memos for the first vertical, SoR/projection boundary, workflow-engine licensing, action gateway, and tenant isolation.
- **[docs/research-ledger.md](docs/research-ledger.md)** — claim ledger mapping evidence, classifications, and owning ADRs.
- **[docs/open-questions.md](docs/open-questions.md)** — partner, commercial, and build-spike blockers that still need proof.
- **[docs/STATUS.md](docs/STATUS.md)** — current status and the proposed next step.

## How this was researched

The conclusions come from four adversarial "deep-research" passes that fan out web searches, fetch primary sources, and verify each claim by majority vote — deliberately weighting **active, currently-maintained public repos** over vendor/lab marketing. Claims are labelled by confidence (✅✅ clean vote · ✅ corroborated · ◐ primary-source-grounded · ○ single-source). This is research, not gospel — which is exactly why it's public.

## Reviewing & contributing

This is a foundation under active review, and review is the entire point of this stage. **Open an issue or a discussion** to challenge the thesis, the build-vs-adopt call, the stack, or the gateway design. Nothing is committed in code yet, so it is the cheapest possible moment to change direction.

## License

No license yet — early stage; treat as all rights reserved for now. A permissive license (likely MIT or Apache-2.0) will be added once direction firms up. Want to build on this sooner? Open an issue.

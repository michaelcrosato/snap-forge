# ADR-D3 — Workflow engine (incl. commercial license)

- **Verdict:** MODIFY · **Confidence:** high
- **Classification:** B (modify-compose) · **Role:** orchestration-layer + licensing decision
- **Independent verification:** supported (high) — the single strongest, self-incriminating source is n8n's own help center
- **Run:** `research/opus-4-8-20260614-1049` · 2026-06-14 · ledger IDs `OPUS-D3-*`
- **⚠ This is the run's most consequential finding — a genuine architecture-changer.**

## Decision
Strip n8n of its "free default" status. For snap-forge's **commercial multi-tenant** use, default the orchestrator to **Activepieces (MIT core)** or **Trigger.dev (Apache-2.0)**. n8n remains a candidate **only with a budgeted paid license**; Windmill only with explicit AGPL handling.

## Claim tested
> "n8n is the default deterministic orchestrator; Activepieces (MIT) is the lighter alternative; Windmill is the code-first alternative." — tested on **commercial-license** grounds for a SaaS that wires automations **for client businesses**.

## Load-bearing sources
1. **n8n LICENSE.md (Sustainable Use License)** — https://raw.githubusercontent.com/n8n-io/n8n/master/LICENSE.md — use limited to "your own internal business purposes or non-commercial/personal use"; distribution to others only "free of charge for non-commercial purposes." Fair-code, **not** OSI open source (SPDX NOASSERTION).
2. **n8n Help Center — "Which license do I need"** — https://support.n8n.io/article/can-i-use-your-license-for-my-use-case — n8n's own answer: hosting/managing **clients'** workflows + credentials in your instance ⇒ **paid Enterprise**; exposing/embedding n8n to clients ⇒ **paid Embed/OEM white-label**. snap-forge's use case is explicitly not free.
3. **Activepieces LICENSE** — https://raw.githubusercontent.com/activepieces/activepieces/main/LICENSE — core is genuine **MIT Expat**; only `packages/ee` + `.../app/ee` are Commercial-licensed (multi-tenancy, RBAC, SSO, embedding, white-label, audit logs).

## Evidence for (n8n's engineering merit is real)
- n8n is the market leader on capability/community: **~192k★, latest release n8n@2.25.7 (2026-06-10)**, 400+ integrations, deterministic visual orchestrator. The doc's *ranking* of n8n as most-capable is defensible — the problem is purely licensing.
- A **path exists**: n8n explicitly permits the multi-tenant backend pattern under a **paid Enterprise** license.

## Evidence against (decisive)
- **n8n's free license forbids snap-forge's pattern.** "Internal business purposes" = *your org's own* automations, not automations sold to third parties. Independent analyses: "the moment automation becomes a value proposition for external users, the licence blocks it"; legal risk is **retroactive** (surfaces at funding/audit/acquisition/customer legal review).
- **The free-backend carve-out is voided.** n8n's FAQ permits n8n "as a back-end to power a feature in your app" *only* "as long as you're not using users' own credentials to access their data." snap-forge wires automations **using clients' own credentials/data** — so this loophole does not apply. (Surfaced by the verifier; *strengthens* the verdict.)
- **Activepieces MIT core excludes multi-tenancy.** The Platform entity / multi-tenancy / RBAC / SSO / embedding / white-label / audit logs are EE-gated (`packages/ee`). snap-forge can lawfully build its **own** tenancy layer on the MIT engine, but must **not** enable `ee/` features without a license.
- **Windmill is AGPLv3 + proprietary EE.** Network copyleft attaches when serving a modified Windmill over a network or re-exposing it in your product — a real obligation for a closed-source SaaS, not free-and-clear. SPDX NOASSERTION.
- **Trigger.dev is clean Apache-2.0** (~15.3k★, active), self-hostable, with built-in human-in-the-loop waitpoints — well-suited to the deterministic-orchestrator + approval-gate model.

## Repo + license audit
| Engine | License | Commercial multi-tenant SaaS use | Liveness |
|---|---|---|---|
| **n8n** | Sustainable Use License (fair-code, SPDX NOASSERTION) | **Paid** Enterprise (backend) or Embed/OEM (exposed) — not free | ~192k★, rel 2.25.7 2026-06-10 |
| **Activepieces** | **MIT** core; `packages/ee` Commercial | Free on MIT core (build own tenancy); ee/ features paid | ~22.7k★, rel 0.85.3 2026-06-14 |
| **Windmill** | AGPLv3 + Apache-2.0 + proprietary EE | AGPL network-copyleft trap unless isolated / commercial license | ~16.8k★ (per prior docs) |
| **Trigger.dev** | **Apache-2.0** (clean OSI) | Free, no copyleft | ~15.3k★, pushed 2026-06-14 |
| plain Postgres-queue workers | n/a | Zero license risk (the floor) | — |

## Falsification attempt
Tried to falsify the *disconfirming* view — i.e. to show n8n **is** free/safe for snap-forge (any reading of "internal business purposes" covering client businesses; backend-only needing no license). **Failed:** n8n's own help center + OEM/Embed docs route the agency/SaaS-for-clients pattern to paid tiers. Conversely, falsification **succeeded** against "Activepieces-MIT = turnkey multi-tenant": the MIT core does *not* include multi-tenancy (EE-gated).

## Independent verification
Verifier independently confirmed every load-bearing fact from primary sources (n8n raw LICENSE verbatim; GitHub fair-code/NOASSERTION; n8n help center paid-tier routing; Activepieces MIT-core boundary) and surfaced the credential-carve-out nuance that tightens the restriction further. Verdict **supported (high)**.

## What would flip this
- **Back to CONFIRM n8n:** snap-forge **budgets a paid n8n Enterprise/Embed license** (then the engineering ranking holds); **or** n8n relicenses under a true OSI license; **or** n8n GmbH gives written confirmation snap-forge's specific architecture falls under the free license.
- **Toward Activepieces/Trigger.dev as outright default:** a capability-gap analysis shows their orchestration features fully cover snap-forge's deterministic-workflow needs.

## Recommendation
Default to **Activepieces (MIT core)** or **Trigger.dev (Apache-2.0)** for the deterministic orchestrator; build snap-forge's own per-tenant isolation on the MIT/Apache engine and don't enable Activepieces `ee/`. Keep **n8n only with a budgeted paid license** if its node ecosystem proves necessary. Treat **Windmill** as code-first-with-AGPL-handling only. **plain Postgres-queue workers** remain the zero-license-risk floor.

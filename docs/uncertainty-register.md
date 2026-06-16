# Uncertainty register — what we don't know

_Last updated 2026-06-16._

**Honest framing:** snap-forge has **not built, shipped, or sold anything.** Everything in this repo is desk research and design. The research is well-sourced and internally consistent — but *being well-argued is not the same as being right.* We do **not** actually know we are on the right path. This document is the deliberate record of that uncertainty, ordered from "could invalidate the whole direction" down to "settle by building." It exists so we never mistake a confident document for a validated one.

Confidence legend: 🔴 could invalidate the thesis · 🟠 material, unproven · 🟡 known unknown, scoped.

---

## Tier 0 — Are we even on the right path? (thesis-level)

🔴 **We have no demand validation.** Not one real business has said they want this, tried it, or would pay for it. The entire thesis rests on the belief that "normal businesses run on bolted-together software and AI changes the economics of fixing that." Plausible — and completely unproven by us. The cheapest way to learn we're wrong is to put one working slice in front of one real shop, not to refine the architecture further.

🔴 **The "many small blocks, not a monolith" bet is justified by a moving target.** The foundation review found the claim "AI can't reliably build large integrated systems" is **OVERSTATED** — the capability ceiling is rising fast (METR 50%-task horizon ~14.5h and doubling every 4–7 months; long unattended Codex runs; ~89% on SWE-bench Verified with good context engineering). Small-blocks is still a defensible bet, but the *reason* shifted from "AI can't go big" to "review/audit/rollback economics favor small." If autonomous agents become reliably good at large integrated systems within a couple of model generations, the architectural premise weakens. We are betting on a derivative, not a fixed wall.

🔴 **"Adopt the substrate, build the thin glue" assumes the glue is where the value is.** We assert snap-forge's value is the assembly + per-business context + vertical blocks + the gateway spine. We have **not** validated that (a) businesses will pay for the glue, or (b) the incumbents won't simply close the gaps themselves. Incumbents own the system of record; if they ship the "scan a bin and text the customer" workflows, the opening we're aiming at closes.

🟠 **We may be confidently wrong in unison.** Two independent research runs (opus + build-spike) "converged" on the same five decisions. That reads as corroboration, but it is **correlated** — same source prompts, same model family, similar priors. Convergence here is weak evidence of correctness; it should *not* lower scrutiny on any unvalidated assumption.

---

## Tier 1 — Commercial & strategic unknowns

🟠 **No design partner.** Auto-repair (vertical) and Shopmonkey (first integration) were chosen on desk research, not because a real auto-repair shop is waiting to pilot. Without a design partner we are guessing at the actual workflow, the actual pain, and the actual willingness to pay.

🟠 **Shopmonkey write scope is unconfirmed** (open-questions Q1). The whole "build self-service first" de-risking hinges on the entry plan including API **write** access. If write is certified-partner-only, the build order is wrong.

🟠 **n8n's commercial terms are unpriced.** The free-license boundary is verified (it bars our multi-tenant SaaS pattern), but nobody has priced an n8n Enterprise/Embed agreement. "Sign a commercial deal" is an unpriced unknown if we ever want n8n's node ecosystem.

🟡 **Tekmetric partner terms are unverifiable from outside.** The API exists and is gated; exact endpoint coverage, write semantics, webhooks, rate limits, fees, and approval timeline are behind an application we haven't filed.

🟡 **Regulated verticals are gated, not impossible.** Cannabis (Metrc per-state credentialing) and medical (HIPAA BAA + project-level isolation) carry weeks-to-months of non-code prerequisites we have not started.

---

## Tier 2 — Technical unknowns (settle by building)

🟠 **The blueprint has never run against real Supabase.** Its own pgTAP tests can't pass as written — fixtures set `request.jwt.claim.sub` but `auth.uid()` reads `request.jwt.claims` JSON, so on a real project the gateway returns "Unauthenticated" (open-questions Q8). We are reasoning about a gateway we have not actually stood up.

🟠 **Two un-reconciled blueprint designs exist** (open-questions Q9): monolithic `adjust_quantity` + session-GUC RLS (shipped) vs a `request → approve → execute` split + JWT-claim RLS (the reconciliation pass's recommendation). We have not chosen. Picking late, after code exists, is a 10x-cost fork.

🟠 **`SECURITY DEFINER` write-path latency/ergonomics never measured.** The decision to route every write through a definer RPC is sound on paper; its real p99 and developer friction on a hot path are unmeasured. This is the explicit D4 "settle-by-building" unknown.

🟡 **Supavisor pooler GUC safety is documented, not proven in our setup.** Transaction-local `set_config(...,true)` is the correct pattern and the docs back it, but we have not run the two-tenant hostile test proving no cross-tenant leakage under our actual pooled connections.

🟡 **Audit immutability is asserted, not enforced.** `audit.audit_logs` is "immutable" only by REVOKE on the writer role — no trigger/constraint/hash-chain blocks tampering. For the PHI/cannabis verticals the ADRs steer toward, that's a corner we have not actually built.

---

## Evidence caveats

- **Long-context degradation numbers (NoLiMa, Chroma) are prior-generation** (GPT-4o, Claude 3.5). The directional finding holds; the exact per-model effective-length numbers are not re-measured for the mid-2026 frontier.
- A few report figures (AI-tech-debt rates, MCP-Universe success %) are **single-source** — directionally useful, not settled.
- The "99 MCP CVEs in 2025" figure is a **single-vendor aggregation** (the underlying named CVEs are all real and verified).

---

## How we'd find out we're wrong (cheapest first)

1. **Build one reference slice** end-to-end — `Shopmonkey scan → gateway-approved inventory adjustment → audit/outbox → staff SMS` — on a real Supabase project. This simultaneously settles Q8, Q9, the definer-latency unknown, and the pooler-safety unknown.
2. **Put it in front of one real auto-repair shop.** Demand validation beats any amount of further desk research. If no shop cares, the Tier-0 risks are answered and we change direction cheaply — before there's a codebase to throw away.

> Everything in `main` is the cheapest possible moment to be wrong: there is no code to rewrite yet. That is the point of staying at this altitude until the slice is built and shown to a real user. Related: [`foundation-review-2026-06-15.md`](foundation-review-2026-06-15.md) (verification), [`open-questions.md`](open-questions.md) (build blockers Q1/Q8/Q9).

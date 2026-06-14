# Project status

**Stage: research & foundation.** No application code yet — the work so far is research, critique, and a build-vs-adopt blueprint. The deliberate goal is to get the foundation right *before* building anything.

## Done
- **Landscape + market scan + build-vs-adopt blueprint** — [`snap-forge-research-report.md`](snap-forge-research-report.md). Verdict: build small single-purpose blocks; adopt the substrate (Supabase + n8n + Twilio/Stripe + MCP); treat the AI context window as human-in-the-loop glue, not the unattended integration backbone.
- **Critique of three peer architecture proposals** — [`peer-proposal-critique.md`](peer-proposal-critique.md). Verdict: the "boring substrate" proposal is soundest; its typed-action-registry + approval-gate is the one idea worth importing.
- **Clean re-verification** — [`reverification-2026-06-14.md`](reverification-2026-06-14.md). Live repo stats confirmed; MCP's own spec recommends a human-in-the-loop approval gate (now folded in).
- **Folded the typed-action-gateway + approval-gate spine into the blueprint** (report §9 + diagram), with the approval gate hardened to a **MUST** for money / PHI / compliance / destructive / AI-authored writes.

## Methodology note
Findings came from four adversarial "deep-research" passes that fan out web searches, fetch primary sources, and verify each claim by majority vote, weighting active public repos over vendor marketing. A recurring concurrency throttle blocked the redundant verification vote on some claims; those are labelled by confidence in the report (✅✅ / ✅ / ◐ / ○) and are primary-source-grounded.

## Next step (proposed — not yet started)
1. Pick the first vertical: **auto repair** is the cleanest entry (real public APIs; no Metrc/HIPAA gate).
2. Scaffold the core: **Supabase + n8n + a thin action-gateway module**.
3. Build one reference block end-to-end through the gateway: **QR-scan → adjust inventory → SMS the salesperson.**

## Open for review
Everything here is a foundation under active review. The point of this stage is to pressure-test the thesis and the architecture before writing code — issues and discussion welcome.

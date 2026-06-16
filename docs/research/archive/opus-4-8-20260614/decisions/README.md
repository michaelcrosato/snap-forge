# snap-forge — P0 decision memos (ADRs)

_Run `research/opus-4-8-20260614-1049` · MODEL_ID `opus-4-8` · MODE `research-only` · 2026-06-14._
_Method: one falsification-first primary-source research agent per P0 decision + one independent adversarial verifier per decision (10 agents). Every verdict below survived independent verification. Evidence IDs trace to [`../research-ledger.md`](../research-ledger.md); unresolved items in [`../open-questions.md`](../open-questions.md)._

These memos test the **decision-grade** questions the existing research docs left open. They do **not** re-litigate the settled thesis-level claims (small blocks > monolith; context-window-as-glue refuted; adopt-the-substrate; the gateway spine) — those hold.

## Verdict summary

| ADR | Decision | Verdict | Confidence | Verifier | One-line result |
|---|---|---|---|---|---|
| [D1](ADR-D1-first-vertical.md) | First vertical | **CONFIRM** (modify API thesis) | high | supported | Auto-repair holds; make **Shopmonkey** (self-service API) the first integration, not Tekmetric/Tekion (approval-gated) |
| [D2](ADR-D2-system-of-record.md) | System of record | **MODIFY** | high | supported | SoR is **per-domain**: incumbent owns its domain (CQRS read-projection), Supabase owns snap-forge-originated data; needs push **+ delta-poll + reconcile**, not a thin cache |
| [D3](ADR-D3-workflow-engine-license.md) | Workflow engine **+ license** | **MODIFY** | high | supported | **n8n is NOT free for snap-forge** (Sustainable Use License bars commercial multi-tenant resale). Default to **Activepieces (MIT)** / **Trigger.dev (Apache-2.0)**; n8n only if licensed; Windmill = AGPL trap |
| [D4](ADR-D4-gateway-contract.md) | Gateway contract | **MODIFY** | high | supported | Pure library chokepoint is **refuted** (service_role bypass). Fix = **library for logic + DB-level enforcement** (REVOKE + SECURITY DEFINER). Has a SETTLE-BY-BUILDING tail |
| [D5](ADR-D5-multi-tenancy.md) | Multi-tenancy / RLS | **MODIFY** | high | refuted-as-stated → MODIFY | RLS is sound **only for JWT-bearing requests**; service_role bypasses it. Add service_role discipline + CI RLS-lint + per-vertical escalation to silo for regulated data |

**Net: 1 CONFIRM, 4 MODIFY, 0 REFUTE.** The provisional architecture survives but is sharpened in four load-bearing places. The single most consequential change is **D3** (the orchestrator license), exactly the kind of architecture-changer the protocol prioritized finding.

## The cross-cutting finding (D4 ⇄ D5)

`service_role` carries the Postgres **BYPASSRLS** attribute. It is what Edge Functions, webhook handlers, and any orchestrator DB node use. This single fact:
- **Refutes D4's** "a library guarantees nothing-writes-except-through-the-gateway" (a sibling process holding the key is a second write path), and
- **Refutes D5's** "RLS is sufficient isolation" (the backend tier bypasses RLS entirely).

The **same fix resolves both**: REVOKE direct table writes from `anon`/`authenticated`/`service_role`, and force all writes through one-per-action **SECURITY DEFINER** functions running as a dedicated writer role (these write the audit row + emit the outbox event in the same transaction). Verified nuance: BYPASSRLS bypasses RLS *policies only*, **not** table-level GRANT/REVOKE, and `service_role` is **not** a superuser — so table-level REVOKE genuinely binds it. The gateway library becomes the ergonomic front door; the SECURITY DEFINER layer is the unskippable chokepoint.

---

## ⇒ Single recommendation for the next build step

**Build one reference block end-to-end and route it through the full spine: `QR-scan → inventory.adjust_quantity → SMS the salesperson`.** This one slice forces every P0 question simultaneously and *is* the D4 SETTLE-BY-BUILDING spike. Build it with:

1. **Vertical / data source (D1):** auto-repair, integrated against the **Shopmonkey sandbox** (self-service keys). File the **Tekmetric** access request in parallel (~2–3 week approval lead time) as the approval-gated secondary. Skip Tekion for now.
2. **Orchestrator (D3):** **Activepieces (MIT core)** or **Trigger.dev (Apache-2.0)** — **not** free n8n. Build snap-forge's own per-tenant layer on the MIT engine; do **not** enable Activepieces `packages/ee` features. (If n8n is wanted for capability reasons, budget a paid Enterprise/Embed license first.)
3. **Gateway (D4):** typed-action **library** for permission/validate/idempotency/audit/approval **+** a **SECURITY DEFINER** write function for `inventory.adjust_quantity` as the sole write path; REVOKE direct table writes from API/service roles. Measure the p99 of the SECURITY-DEFINER write path vs a direct write on this block before generalizing the contract.
4. **Data model (D2):** Supabase is the **SoR** for the scan event, the inventory adjustment, the audit row, and the approval decision (snap-forge-originated). If/when it mirrors Shopmonkey inventory, model that as a read-projection with delta-poll + reconcile, behind a transactional outbox for any write-back.
5. **Isolation (D5):** shared-schema RLS for the auto-repair tenant **+ service_role discipline**: the block accesses tenant data via a tenant-scoped role / `set_config` context, never an unscoped `service_role` query. Wire the Splinter RLS linter (0013) into CI from commit one.
6. **Approval gate:** make the AI-authored SMS body and any inventory delta over threshold require human approval, written as a `pending → approved → committed` transition (watch whether this needs a staging table — a known SETTLE-BY-BUILDING unknown).

Building exactly this, and nothing more, answers the three questions research could not (the SECURITY-DEFINER write-path ergonomics/latency, the action-vs-transaction grain, and whether the approval gate composes with the write path) — and produces the first real snap-forge block.

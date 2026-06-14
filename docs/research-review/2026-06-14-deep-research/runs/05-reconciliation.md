# Decision Memo: Deep Research Reconciliation

## 1. What Remains Confirmed

- **Auto repair remains the first vertical**: high confidence. It still has the best balance of willingness to pay, lower compliance friction, and visible incumbent ecosystems. **Tekmetric remains only medium confidence** as the first incumbent because public evidence does not prove write APIs, sandbox access, caching rights, or partner timeline.
- **Adopt substrate, build the spine**: high confidence. Supabase/Postgres, SDKs, and workflow runtimes should be adopted; snap-forge should build the typed action gateway, contracts, vertical blocks, and adapter glue.
- **AI must not be the unattended integration layer**: high confidence. AI can propose typed actions and help build blocks; durable state, authorization, idempotency, audit, and side effects belong in deterministic systems.
- **RLS is viable only with layered controls**: high confidence. RLS, grants, forced RLS, no runtime `service_role`, gateway-only mutations, and CI checks all remain required.
- **n8n is not the default SaaS orchestrator**: high confidence. It fits client-owned/internal pilots; SaaS should default to custom outbox worker plus Trigger.dev/Temporal-style code-first orchestration as needed.

## 2. What Should Change

- Reframe **Tekmetric** from “first incumbent” to **“first candidate incumbent.”** Do not block the first spike on Tekmetric partner docs.
- Narrow the first spike to **staff/internal notification only**. Customer-facing SMS/email should remain behind consent, opt-out, and approval policy.
- Replace simple “SoR-first write” language with an explicit **external-write saga**. Cross-system mutation correctness is the largest under-specified risk.
- Split ADR-D4 into two concepts: **database authorization gateway** and **side-effect executor/outbox worker**.
- Strengthen function posture: **revoke function execution by default**, grant only named RPCs, and treat `SECURITY DEFINER` as a reviewed exception.
- Extend the runtime `service_role` ban to **workers, n8n flows, repair jobs, and admin scripts** unless they use narrow custom roles.
- Treat product audit rows as separate from tamper-resistant/database audit evidence. Add retention/export/offsite audit questions later.

## 3. What Must Be Settled By Building

- Whether PL/pgSQL/RPC remains maintainable once approval, locking, idempotency, audit, and outbox behavior are all present. Confidence: medium.
- Whether duplicate scans, concurrent approvals, worker retries, timeouts, and crash points avoid double-applying inventory changes. Confidence: must test.
- Whether the gateway invariant survives a real side-effecting flow without unsafe shortcuts. Confidence: medium.
- Whether RLS/grants/function grants actually fail closed through PostgREST/Supabase client paths, not only SQL fixtures. Confidence: medium.
- Whether Supavisor/session variables are safe. For v1, avoid session-variable tenant authority and prefer JWT/membership checks.

## 4. What Must Be Settled By Partner/Private Docs

- Tekmetric: inventory write endpoints, auth model, sandbox, webhooks, idempotency, rate limits, projection/caching rights, fees, approval timeline, and multi-tenant SaaS terms.
- Twilio/Resend: customer-specific consent proof, 10DLC/toll-free setup, opt-out handling, retention, regulated-content constraints, and sender requirements.
- n8n/Activepieces/Windmill: written commercial terms before embedding, resale, hosted customer access, or customer-credential automation.
- Future regulated verticals: Supabase BAA/HIPAA add-on, Metrc state validation, PCI scope, DPAs, log retention, and audit requirements.

## 5. Updated First-Build-Spike Scope

Build `inventory.adjust_quantity` with **no Tekmetric dependency, no UI, no scanner app, no real SMS provider**.

Scope should be:

- Supabase local scaffold with tenants, memberships, inventory projection, gateway tables, audit log, approvals, idempotency, and outbox.
- One gateway action: `inventory.adjust_quantity`.
- Mock incumbent adapter/outbox target with failure-injection design, even if delivery is not fully implemented in spike one.
- Staff/internal notification represented as an outbox event, not Twilio delivery.
- Tests proving direct writes fail, cross-tenant access fails, approved gateway writes succeed, duplicate/concurrent idempotency does not double-apply, unsafe function grants fail, and audit/outbox rows are created atomically.

## 6. Exact Edits Recommended

- **README.md**
  - Change “Tekmetric/Dutchie(incumbent APIs)” to “Tekmetric candidate adapter / incumbent APIs, partner-doc gated.”
  - Change first workflow wording from “staff/customer notification” to “staff notification first; customer messaging deferred behind consent and approval.”
  - Add: “The first build spike uses a mock incumbent adapter; Tekmetric is a candidate, not a hard dependency.”
  - Change SaaS orchestration recommendation to “custom outbox worker first; add Trigger.dev/Temporal when needed; n8n only for client-owned/internal or commercial terms.”

- **docs/STATUS.md**
  - Change “First reference workflow” to: `QR/bin scan -> gateway-approved inventory adjustment -> mock/incumbent adapter boundary -> audit/outbox -> staff notification event`.
  - In Next Step item 1, replace “Acquire Tekmetric docs or choose mock” with “Start with mock incumbent adapter; pursue Tekmetric docs in parallel.”
  - Add build-spike acceptance criteria: crash/failure injection, concurrent idempotency, function grant tests, no runtime service-role in workers.

- **docs/open-questions.md**
  - Add Q4b: “External-write saga correctness: what action states, retries, reconciliation, and compensation are required when incumbent write and local projection cannot be atomic?”
  - Add Q4c: “Audit integrity: what is product audit vs database audit vs offsite/tamper-resistant evidence?”
  - Update Q7 answer to staff-only first; customer messaging deferred.
  - Expand Q6 to include workflow engines, workers, repair scripts, direct adapter calls, and direct Twilio/Resend imports.

- **docs/research-ledger.md**
  - Update C1 verdict: auto repair confirmed; Tekmetric is first candidate, partner-gated.
  - Update C2 claim to include saga/reconciliation states and external idempotency.
  - Update C3 solution index: custom outbox worker as first SaaS spine; Trigger.dev/Temporal as scale-up options; n8n internal only.
  - Update C4 claim: database authorization gateway plus side-effect executor, default-revoke function grants, immutable approval payload hash.
  - Update C5 claim: no runtime `service_role` includes workers and workflow runtimes; prefer JWT claims over session variables in v1.

- **ADRs**
  - **ADR-D1**: replace “Tekmetric is the leading first incumbent” with “Tekmetric is the leading first candidate incumbent”; add service trades as fallback.
  - **ADR-D2**: replace simple SoR-first write with saga states: `requested`, `approved`, `external_pending`, `external_succeeded`, `projection_applied`, `outbox_emitted`, `reconciled`, `failed_compensating`.
  - **ADR-D3**: make custom outbox worker the default SaaS first step; Trigger.dev/Temporal when durability needs grow; n8n internal/client-owned only.
  - **ADR-D4**: add default `REVOKE EXECUTE`, immutable approved payload hash, external idempotency, internal-only executor function, and side-effect executor boundary.
  - **ADR-D5**: extend `service_role` ban to workers/workflows/scripts; require least-privilege custom roles and no session-variable tenant authority until proven.

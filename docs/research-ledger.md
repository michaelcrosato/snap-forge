# snap-forge — research ledger (P0 evidence)

_Run `research/opus-4-8-20260614-1049` · MODEL_ID `opus-4-8` · 2026-06-14._
_Exact evidence, separated from interpretation (interpretation lives in [`decisions/`](decisions/)). Stable IDs are `OPUS-D{n}-{nn}`; update entries **in place**, never duplicate. For Section 8 reconciliation, merge with the `gemini` branch ledger **by ID**._

**Confidence:** ✅✅ clean independent adversarial verification this run · ✅ primary-source-grounded + corroborated · ◐ single primary source · ○ single secondary source.
**Source type:** PRIMARY-LEGAL / PRIMARY-DOC / PRIMARY-REPO / VENDOR-DOC / ADVISORY / ANALYSIS.

## D1 — First vertical (verdict: CONFIRM / modify API thesis)
| ID | Claim (evidence) | Source · date | Type · status | Conf | Decision impact |
|---|---|---|---|---|---|
| OPUS-D1-01 | Shopmonkey API is self-service: any Admin generates Public/Private keys; public REST v3 docs; no NDA/partner/revenue gate | shopmonkey.dev/overview · 2026 | PRIMARY-DOC · live | ✅✅ | Makes auto-repair buildable solo; becomes the primary first integration |
| OPUS-D1-02 | Metrc Vendor API Key only functions combined with a Licensee's own User API Key; state-agency-executed agreement precedes any key | metrc.com RI/MS/ME/etc. agreements · 2022–2026 | PRIMARY-LEGAL · live | ✅✅ | Cannabis is hard-gated; confirms it is not the first vertical |
| OPUS-D1-03 | Dutchie POS API is partner-gated (Certified Partner/Plus + integration assessment); not self-service | supergood.ai/docs/dutchie-api · 2025–2026 | PRIMARY-DOC · live | ✅ | Cannabis POS does not sidestep Metrc for a small builder |
| OPUS-D1-04 | Tekmetric API access is request-based, ~2–3 wk approval "at Tekmetric's discretion", not guaranteed; OAuth2 client_credentials + sandbox | beetlebugorg/tekmetric-mcp README · 2025-10 | PRIMARY-REPO · repo archived | ✅ | Demotes Tekmetric to approval-gated secondary |
| OPUS-D1-05 | Tekion APC is dealer/OEM/certified-partner oriented (tiered approval) | tekion.com/products/apc · 2026 | PRIMARY-DOC · live | ✅ | Demote Tekion to later/enterprise |

## D2 — System of record (verdict: MODIFY)
| ID | Claim (evidence) | Source · date | Type · status | Conf | Decision impact |
|---|---|---|---|---|---|
| OPUS-D2-01 | CQRS: write model = SoR; read model = "durable, read-only cache", eventually consistent | learn.microsoft.com /azure/architecture/patterns/cqrs | VENDOR-DOC · live | ✅✅ | Incumbent-as-SoR + projection is a sound pattern, not an anti-pattern |
| OPUS-D2-02 | Tekmetric: narrow webhooks (appointment/RO events); else "your account data will sync once per hour" | support.shopgenie.io tekmetric webhooks | VENDOR-DOC · live | ✅✅ | Projection is hourly-stale without delta-poll → "thin cache" framing fails |
| OPUS-D2-03 | Shopify mandates reconciliation jobs (webhook delivery not guaranteed) via updated_at | shopify.dev/docs/apps/build/webhooks | PRIMARY-DOC · live | ✅✅ | Projection always needs push + delta-poll + reconcile |
| OPUS-D2-04 | SoR is per bounded context / per domain (data sovereignty per microservice) | learn.microsoft.com /dotnet/architecture/microservices | VENDOR-DOC · live | ✅ | SoR is per-domain; Supabase = SoR for originated data |
| OPUS-D2-05 | Treating a projection as both incumbent-cache and originated-store invites the dual-write problem | confluent.io/blog/dual-write-problem | ANALYSIS · live | ✅ | Write-backs need a transactional outbox |

## D3 — Workflow engine + license (verdict: MODIFY) — architecture-changer
| ID | Claim (evidence) | Source · date | Type · status | Conf | Decision impact |
|---|---|---|---|---|---|
| OPUS-D3-01 | n8n Sustainable Use License limits use to "internal business purposes or non-commercial/personal"; distribution to others only free-of-charge non-commercial. Fair-code, SPDX NOASSERTION | raw n8n LICENSE.md (master) · 2026 | PRIMARY-LEGAL · live | ✅✅ | n8n not free for commercial multi-tenant resale |
| OPUS-D3-02 | n8n's own help center: hosting clients' workflows = paid Enterprise; embedding/exposing to clients = paid Embed/OEM | support.n8n.io "which license" + docs.n8n.io/embed | PRIMARY-DOC · live | ✅✅ | snap-forge's exact pattern requires a paid n8n license |
| OPUS-D3-03 | n8n free "back-end to power a feature" carve-out is void if using users' own credentials to access their data | n8n FAQ (verifier-surfaced) · 2026 | PRIMARY-DOC · live | ✅✅ | Closes the free-backend loophole for snap-forge |
| OPUS-D3-04 | Activepieces core = MIT Expat; packages/ee (multi-tenancy, RBAC, SSO, embed, white-label, audit) = Commercial | raw Activepieces LICENSE + activepieces.com/docs/about/license | PRIMARY-LEGAL · live (rel 0.85.3 2026-06-14) | ✅✅ | MIT engine usable commercially; build own tenancy, don't enable ee/ |
| OPUS-D3-05 | Windmill = AGPLv3 + Apache-2.0 + proprietary EE; network copyleft attaches when serving modified Windmill / re-exposing it | github windmill LICENSE · 2026 | PRIMARY-LEGAL · live | ✅ | Windmill is an AGPL trap for closed-source SaaS unless isolated/licensed |
| OPUS-D3-06 | Trigger.dev = clean Apache-2.0, self-hostable, HITL waitpoints, active (~15.3k★, pushed 2026-06-14) | api.github.com/repos/triggerdotdev/trigger.dev | PRIMARY-REPO · live | ✅ | Lowest-license-risk code-first orchestrator candidate |
| OPUS-D3-07 | n8n engineering merit: ~192k★, rel 2.25.7 2026-06-10, 400+ integrations | api.github.com/repos/n8n-io/n8n | PRIMARY-REPO · live | ✅✅ | Ranking is sound on merit; only licensing demotes it |

## D4 — Gateway contract (verdict: MODIFY)
| ID | Claim (evidence) | Source · date | Type · status | Conf | Decision impact |
|---|---|---|---|---|---|
| OPUS-D4-01 | service_role has BYPASSRLS and is what Edge Functions / webhooks / orchestrator DB nodes use | supabase.com/docs/.../postgres/roles | VENDOR-DOC · live | ✅✅ | A library gateway is bypassable by sibling processes → pure-library invariant refuted |
| OPUS-D4-02 | BYPASSRLS bypasses **row security only**, not GRANT/REVOKE table privileges | postgresql.org/docs/current/ddl-rowsecurity.html | PRIMARY-DOC · live | ✅✅ | Table-level REVOKE can still bind service_role |
| OPUS-D4-03 | service_role is NOT a superuser (only bypass-RLS) | github supabase discussions #36362 + roles-superuser doc | VENDOR-DOC · live | ✅✅ | Confirms REVOKE binds it (superusers would bypass GRANT/REVOKE) |
| OPUS-D4-04 | REVOKE EXECUTE FROM PUBLIC + selective grants + SECURITY DEFINER funcs = single controlled write path; DB is authoritative authz layer | docs.postgrest.org/.../db_authz.html + supabase securing-your-api | PRIMARY-DOC · live | ✅✅ | The enforcement layer that makes the invariant physically true |
| OPUS-D4-05 | Real-world 42501 "permission denied" proves service_role loses table access after REVOKE | supabase troubleshooting 42501 docs | VENDOR-DOC · live | ✅ | DB-level enforcement is documented + observed, not theoretical |
| OPUS-D4-06 | One-action-per-block has friction: reads (CQRS), multi-action transactions, bulk ops need escape hatches | enterprisecraftsmanship.com ddd-bulk-operations + CQRS | ANALYSIS · live | ✅ | Mandates read/bulk/multi-step escape hatches |

## D5 — Multi-tenancy / RLS (verdict: MODIFY; bare claim refuted)
| ID | Claim (evidence) | Source · date | Type · status | Conf | Decision impact |
|---|---|---|---|---|---|
| OPUS-D5-01 | "Supabase provides special Service keys, which can be used to bypass RLS" (verbatim) | supabase.com/docs/.../row-level-security | VENDOR-DOC · live | ✅✅ | RLS is not the boundary for the service_role backend tier |
| OPUS-D5-02 | CVE-2025-48757 (CVSS 9.3): missing/insufficient RLS exposed PII/API-keys/payment data across 170+ Lovable+Supabase projects | mattpalmer.io + securityonline.info · 2025-05 | ADVISORY · disclosed | ✅✅ | "Forgot RLS = breach" is empirical on this stack |
| OPUS-D5-03 | RLS engine CVEs: 2024-10976 (wrong policy under role/plan reuse), 2025-8713 (optimizer stats leak hidden rows) | postgresql.org/support/security | ADVISORY · patched ≥17.1/16.5 & ≥17.6/16.10 | ✅ | Shared-schema correctness contingent on staying patched |
| OPUS-D5-04 | AWS SaaS Lens: tenant-boundary crossing "potentially unrecoverable"; compliance pushes tenants to silo | docs.aws.amazon.com/wellarchitected/.../saas-lens/tenant-isolation | VENDOR-DOC · live | ✅ | Pool/shared-schema often not acceptable for regulated tenants |
| OPUS-D5-05 | Supabase HIPAA model is project-level (BAA Team/Enterprise + add-on, High-Compliance config; not self-hosted) | supabase.com/docs/guides/platform/hipaa-projects | VENDOR-DOC · live | ✅ | Compliance unit of isolation = project, not row → silo for PHI |
| OPUS-D5-06 | RLS perf fixes: (select auth.uid()) 179→9ms; index tenant col 171→<0.1ms; TO authenticated 170→<0.1ms | supabase.com/docs/.../row-level-security (perf) | VENDOR-DOC · live | ✅ | RLS-at-scale is fine for non-regulated if discipline enforced |

## Contradiction / caveat notes
- **OPUS-D2-02**: Tekmetric's exact webhook *event list* is secondary-sourced (official API docs auth-gated, HTTP 401); the load-bearing "hourly sync" fact is verbatim-confirmed.
- **OPUS-D1-02**: Metrc agreement PDFs did not text-extract via fetch (compressed); coupling language corroborated via search-surfaced verbatim quotes from the same official PDFs.
- **OPUS-D5-01 nuance**: if a user **JWT** is attached, the client adheres to that user's RLS even under a service key — but snap-forge's elevated paths are server-to-server with no JWT, so the bypass stands.
- All five verdicts passed independent adversarial verification (D5's bare "sufficient" claim was refuted-as-stated, which *is* the MODIFY).

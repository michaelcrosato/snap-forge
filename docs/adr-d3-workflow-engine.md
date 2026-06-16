# ADR-D3: Workflow Engine Selection and Licensing

- **Status**: DECISION-GRADE for near-term direction; LEGAL-REVIEW REQUIRED before resale/embedding
- **Verdict**: MODIFY `context-specific-orchestrator`
- **Confidence level**: High for public license constraints; medium for product-specific commercial terms
- **Date**: 2026-06-14

## Goal
Choose the deterministic orchestration layer for block wiring, retries, waits, scheduled work, and integration side effects without violating source/license terms when snap-forge is sold to multiple businesses.

## Decision
Use different orchestration choices by deployment model:

1. **Single-tenant, client-owned/internal deployments**: n8n is acceptable for internal business automation and consulting/support around n8n workflows, assuming the client is using it for its own internal business purposes and not reselling n8n functionality.
2. **Multi-tenant SaaS or customer-facing embedded workflow product**: do not depend on n8n's default Sustainable Use License for the orchestrator. Use a permissively licensed/code-first runtime such as Trigger.dev, Temporal, Node-RED, or a custom Postgres outbox worker unless a commercial n8n agreement is signed.
3. **Embedded visual workflow UI**: treat Activepieces, Windmill, and n8n as commercial-license decisions, not free defaults. Activepieces core is MIT, but enterprise/cloud features live under a commercial license. Windmill is AGPLv3 plus commercial/enterprise offerings. Those may still be valid choices, but they need explicit licensing review for snap-forge's distribution model.

## Evidence Table

| Source / project | Public license posture | Implication |
|---|---|---|
| n8n | Sustainable Use License allows internal business use and consulting/support, but disallows white-labeling n8n or hosting it and charging people for access; separate commercial agreement required for non-permitted use. | Strong single-tenant/internal fit; risky as default multi-tenant SaaS substrate. |
| Activepieces | Core is MIT; enterprise/cloud features under `packages/ee` and `packages/server/api/src/app/ee` require an Activepieces license. | Core can be adopted; embedding/white-label/enterprise needs commercial review. |
| Windmill | Repository is AGPLv3/Apache-2.0 mix with commercial licenses and enterprise features available. | Not "prohibited," but AGPL and enterprise-feature boundaries need legal review before SaaS embedding/resale. |
| Trigger.dev | Apache-2.0, self-hostable, code-first background jobs/workflows with queues, retries, idempotency, and human-in-the-loop waitpoints. | Best permissive default for SaaS background orchestration. |
| Node-RED | Apache-2.0. | Permissive visual-flow alternative; verify UX and security fit separately. |

## Falsification Attempt

### Thesis
Use n8n as the hidden backend for a multi-tenant snap-forge SaaS because end users will not see the n8n editor.

### Result: NOT SAFE AS A DEFAULT
n8n's own license examples distinguish internal business use from products where value derives substantially from n8n functionality or where user credentials are collected to power app features. A multi-tenant SaaS that uses customers' own credentials and sells workflow automation through a wrapper could fall outside the default license. That does not make n8n unusable; it means snap-forge needs a commercial agreement or a different orchestrator for that deployment model.

## Known Contradictions
- n8n has the best low-code workflow UX for fast pilots. Use it where the license model fits.
- Trigger.dev is more developer-oriented. It is a better legal/runtime fit for SaaS, but less friendly for non-technical workflow editing.
- Node-RED is permissively licensed and visual, but it is not as SaaS-productized as n8n or Activepieces.

## What New Evidence Would Flip This Decision
1. n8n provides written commercial terms that fit snap-forge's SaaS economics.
2. Activepieces makes required embedding/white-label features available under MIT or acceptable commercial terms.
3. The first client is definitively single-tenant and client-owned, with no customer-facing resale of workflow functionality.

## Primary Sources
1. [n8n Sustainable Use License](https://docs.n8n.io/sustainable-use-license/)
2. [Activepieces License](https://www.activepieces.com/docs/about/license)
3. [Windmill GitHub Repository](https://github.com/windmill-labs/windmill)
4. [Windmill Pricing](https://www.windmill.dev/pricing)
5. [Trigger.dev GitHub Repository](https://github.com/triggerdotdev/trigger.dev)
6. [Node-RED License](https://github.com/node-red/node-red/blob/master/LICENSE)

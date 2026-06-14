# snap-forge Vertical and Orchestrator Memo

## 1. Ranked Vertical Recommendation

| Rank | Vertical | Recommendation | Why |
|---:|---|---|---|
| 1 | **Auto repair** | **Keep as first vertical** | Best balance of WTP, low compliance friction, concrete workflow fit, and visible incumbent integration ecosystem. Tekmetric publishes $199-$439/month shop plans plus add-ons, inventory features, texting, payments, and third-party integrations. It also advertises 70+ integrations and an integration application path. [Tekmetric pricing](https://www.tekmetric.com/pricing), [integrations](https://www.tekmetric.com/integrations) |
| 2 | **Service trades** | Strong fallback | High operational pain and WTP. Jobber ranges from $49-$699/month and exposes a GraphQL API for app monetization; Housecall Pro ranges from $59-$299/month. Good workflows: lead intake, quote follow-up, scheduling, technician notifications. Risk: workflows fragment by trade, pushing snap-forge toward bespoke consulting. [Jobber pricing](https://www.getjobber.com/pricing/), [Jobber API](https://developer.getjobber.com/docs/), [Housecall Pro pricing](https://www.housecallpro.com/pricing/) |
| 3 | **General retail** | Good integration lab, weaker product wedge | Shopify and Square APIs are excellent; sales cycles can be short. But Shopify starts at $29/month and POS Pro is $89/location, with thousands of apps already competing. Strong feasibility, weaker defensibility. [Shopify pricing](https://www.shopify.com/pricing), [Shopify Admin API](https://shopify.dev/docs/api/admin-rest), [Square APIs](https://developer.squareup.com/us/en) |
| 4 | **Dental / medical offices** | Defer unless a funded HIPAA pilot exists | WTP is real and Open Dental is integration-friendly, but PHI triggers HIPAA, BAAs, access controls, audit, breach process, and longer sales/security review. Open Dental’s public docs are unusually clear: read-only DB queries are allowed, writes must go through API. [HHS HIPAA](https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html), [Open Dental pricing](https://www.opendental.com/site/order.html), [Open Dental API posture](https://opendental.com/site/programmingresources.html) |
| 5 | **Cannabis retail** | Defer unless client brings Metrc access | Workflow fit is excellent for inventory/QR/compliance, but Metrc API access is state-gated and includes training, API agreement, sandbox assessment, and production key issuance. High compliance defensibility, poor first-spike speed. [Metrc Oklahoma API steps](https://www.metrc.com/oklahoma-integration-and-api/), [validated integrators](https://www.metrc.com/validated-integrators/) |

**Conclusion:** auto repair still looks like the right first vertical. Service trades is the credible fallback if Tekmetric API access blocks the first workflow.

Confidence: **High** for auto repair over cannabis/medical/general retail; **medium-high** versus service trades.

## 2. Tekmetric Public Evidence and Unknowns

**Public evidence supporting Tekmetric-first evaluation**

- Tekmetric publicly prices core shop software at $199, $349, and $439/month, with enterprise custom pricing and paid add-ons for multi-shop, tire suite, and marketing. That proves shops already pay meaningful SaaS ARPU. [Tekmetric pricing](https://www.tekmetric.com/pricing)
- Inventory/vendor management is included in the entry plan; parts reports, integrated parts ordering, texting, dashboards, payments, and marketing appear in higher tiers/add-ons. That maps directly to the proposed scan -> inventory adjustment -> notification workflow. [Tekmetric pricing](https://www.tekmetric.com/pricing)
- Tekmetric advertises 70+ integrations and an “apply” entrypoint at `api.tekmetric.com`; integration categories include parts/inventory, payments/accounting, marketing/communications, labor guides, diagnostics, and vehicle info. [Tekmetric integrations](https://www.tekmetric.com/integrations)
- Tekmetric has a partner program with application flow, co-marketing, preferred partner visibility, and access to its shop network, but benefits depend on partnership scope. [Tekmetric partners](https://www.tekmetric.com/partners)

**Unknowns that remain build-blocking**

- Whether partners can write inventory adjustments, repair orders, customers, notes, messages, or only read/sync.
- API auth model, sandbox access, webhooks, rate limits, pagination, idempotency support, caching rules, data retention, audit obligations, and fees.
- Partner approval timeline and whether a small new vendor can get access without a signed pilot customer.
- Whether a multi-tenant snap-forge SaaS can use one approved integration, or whether each shop must authorize separately under terms that limit local projections.
- Whether Tekmetric permits the reference workflow’s “system-of-record update” semantics, or only allows projection/sync.

**Tekmetric conclusion:** keep Tekmetric as the first incumbent to evaluate, but do not let the first build spike depend on undocumented Tekmetric writes. Build the adapter boundary against a mock Tekmetric-shaped incumbent until partner docs are available.

Confidence: **Medium**.

## 3. Orchestrator Recommendation Matrix

| Option | Client-owned / internal | Consultant-managed | Multi-tenant SaaS | Embedded automation sold to customers | Licensing / commercial blocker |
|---|---|---|---|---|---|
| **n8n** | **Best fast pilot choice** | Good if clearly for client internal use | **No, unless commercial deal** | **No, unless commercial deal** | Sustainable Use License allows internal use but blocks white-label/paid hosted access and certain backend uses with users’ credentials. [n8n license](https://docs.n8n.io/sustainable-use-license/) |
| **Activepieces** | Good | Good core option | Possible with care | **Best visual embed candidate if paid edition fits** | Core is MIT, but enterprise/cloud features require license; embedding is a paid-edition feature. [license](https://www.activepieces.com/docs/about/license), [embedding](https://www.activepieces.com/docs/embedding/overview) |
| **Windmill** | Good internal developer platform | Legal review | Legal review | Legal review / commercial | CE is free internally, but managed services, resale, wrapping, and re-exposing parts to users require commercial license or AGPL compliance. [Windmill license](https://github.com/windmill-labs/windmill) |
| **Trigger.dev** | Good code-first | Good | **Best SaaS default** | Good if no visual builder needed | Apache-2.0; built for durable TypeScript tasks, queues, retries, idempotency, observability, and human-in-loop pauses. [Trigger.dev](https://github.com/triggerdotdev/trigger.dev) |
| **Node-RED** | Good lightweight/local | Good | Weak default | Possible but productization burden | Apache-2.0, but multi-tenant auth, isolation, governance, and product UX are on snap-forge. [Node-RED license](https://github.com/node-red/node-red/blob/main/LICENSE) |
| **Temporal** | Overkill unless workflows are long-running/critical | Good with strong eng ops | Strong for complex SaaS workflows | Good code engine, not visual automation | MIT; excellent durability but heavier ops and developer model. [Temporal repo](https://github.com/temporalio/temporal), [Temporal docs](https://docs.temporal.io/temporal) |
| **Custom outbox worker** | Good for first narrow workflow | Good | **Best minimal SaaS spine** | Good for fixed product workflows | No third-party license blocker, but connector/UI/retry tooling must be built. |

**Orchestrator conclusion:**
Use **n8n only for single-tenant internal/client-owned pilots**. For snap-forge SaaS, start with a **custom Postgres outbox worker plus typed gateway**, and add **Trigger.dev** when retries, schedules, long-running jobs, or human-in-loop orchestration outgrow the worker. Use **Activepieces paid embedding** only if customer-editable visual workflows become core product scope.

Confidence: **High** on n8n restriction; **medium-high** on Trigger/custom outbox SaaS recommendation.

## 4. Evidence That Would Change the Recommendation

- **Tekmetric flips stronger:** partner docs confirm inventory writes, webhooks, sandbox, reasonable fees, acceptable caching/projection, and approval in weeks not months.
- **Tekmetric flips weaker:** no write access, no practical sandbox, prohibitive partner fees, or terms blocking multi-tenant SaaS/local projection.
- **Service trades becomes #1:** a paid pilot brings Jobber/Housecall/ServiceTitan access and a repeatable workflow across multiple trades.
- **Cannabis becomes #1:** a client already has validated Metrc integrator access in target states and funds compliance work.
- **Dental/medical becomes #1:** a client funds HIPAA infrastructure, signs BAA requirements up front, and provides a narrow EHR/PMS workflow with API access.
- **General retail becomes #1:** evidence of a high-value repeated workflow not already solved by Shopify/Square apps, with acquisition channel access.
- **n8n becomes SaaS-acceptable:** written commercial terms fit snap-forge margins and allow customer-credential workflows.
- **Activepieces becomes default:** paid embed terms are affordable and tenant isolation/credential handling meet snap-forge’s gateway model.

## 5. Confidence by Conclusion

| Conclusion | Confidence |
|---|---|
| Auto repair remains the best first vertical | **High** |
| Tekmetric remains the best first incumbent to evaluate | **Medium** |
| Tekmetric must not be a hard dependency before partner docs | **High** |
| Service trades is the best fallback vertical | **Medium-high** |
| Cannabis should be deferred for first spike | **High** |
| Dental/medical should be deferred unless funded HIPAA scope exists | **High** |
| General retail is easy to integrate but weak as first product wedge | **Medium** |
| n8n fits internal/client-owned pilots, not default SaaS | **High** |
| Custom outbox + Trigger.dev is the safest SaaS path | **Medium-high** |
| Activepieces/Windmill embedding requires commercial/legal review | **High** |

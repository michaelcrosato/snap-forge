# snap-forge Deep Research Review Package

Generated: 2026-06-14

Purpose: hold research-only outputs for lead-agent review before any integration into the main project docs. This folder is intentionally separate from `docs/research/`, `docs/adr-*.md`, `docs/STATUS.md`, and `README.md`.

## Review Order

1. `runs/05-reconciliation.md` - lead decision memo and recommended edits.
2. `runs/01-architect-critique.md` - adversarial architecture review.
3. `runs/02-security-threat-model.md` - security, compliance, and CI/static-check review.
4. `runs/03-build-spike-plan.md` - concrete `inventory.adjust_quantity` build-spike shape.
5. `runs/04-market-integration-licensing.md` - vertical, Tekmetric, and workflow-engine review.
6. `prompts/*.md` - exact prompts used for each research pass.

## Files

| File | Role |
|---|---|
| `prompts/01-architect-critique.md` | Prompt for architecture attack pass |
| `prompts/02-security-threat-model.md` | Prompt for security/compliance pass |
| `prompts/03-build-spike-plan.md` | Prompt for practical build-spike pass |
| `prompts/04-market-integration-licensing.md` | Prompt for market/integration/licensing pass |
| `prompts/05-reconciliation.md` | Prompt for synthesis pass |
| `runs/00-sandbox-read-check.md` | Notes the nested Codex CLI sandbox could not read local files directly |
| `runs/01-architect-critique.md` | Repo-context-embedded architecture critique |
| `runs/02-security-threat-model.md` | Repo-context-embedded threat model |
| `runs/03-build-spike-plan.md` | Repo-context-embedded first spike plan |
| `runs/04-market-integration-licensing.md` | Repo-context-embedded market and licensing memo |
| `runs/05-reconciliation.md` | Final review-only synthesis |

## Execution Notes

- The nested Codex CLI could not launch PowerShell under its own sandbox, so each successful run used embedded repo context captured from the current worktree.
- The runs used live web search for external primary/current sources where needed.
- Existing project docs were not edited as part of this review package.
- While these runs were executing, separate untracked artifacts appeared under `docs/research/` and `tests/`. They are outside this review package and were not modified here.

## Main Synthesis

The reconciliation memo recommends keeping the high-level thesis but changing the first spike posture:

- Treat Tekmetric as the first candidate incumbent, not a hard dependency.
- Start with a mock incumbent adapter and staff/internal notification event.
- Make cross-system mutation correctness explicit through saga/reconciliation states.
- Split the gateway into a database authorization boundary and a side-effect executor/outbox worker.
- Default SaaS orchestration to a custom outbox worker first, adding Trigger.dev or Temporal only when needed; reserve n8n for client-owned/internal or commercially approved deployments.

No integration edits have been applied from this package.

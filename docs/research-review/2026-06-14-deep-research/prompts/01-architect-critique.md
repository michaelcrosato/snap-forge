You are a skeptical systems architect reviewing C:\dev\snap-forge.

Read README.md and docs/*.md first.

Goal: attack the current architecture for snap-forge.

Focus on:
- typed action gateway
- Supabase as projection, audit log, and outbox
- incumbent system of record
- multi-tenant RLS model
- workflow engine choice
- first auto-repair vertical

Find what is likely wrong, under-specified, risky, or overcomplicated.
Prefer primary sources and current official docs.

Return:
1. strongest objections
2. what should be tested in the first build spike
3. which ADRs should change
4. confidence level per finding

Separate:
- confirmed public evidence
- partner/private verification required
- settle-by-building

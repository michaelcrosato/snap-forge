You are a practical implementation engineer.

Read README.md, docs/STATUS.md, docs/open-questions.md, and docs/adr-*.md.

Design the smallest first build spike that can prove or disprove snap-forge's core thesis.

Target:
inventory.adjust_quantity

Must include:
- Supabase local scaffold
- schema
- RLS
- revoked direct writes
- RPC/action gateway
- approval queue
- audit log
- outbox
- idempotency
- tests proving direct writes fail, cross-tenant reads fail, approved writes succeed, and duplicate keys do not double-apply

Return:
1. file-by-file implementation plan
2. SQL schemas
3. PL/pgSQL function signatures
4. RLS and grants
5. exact test strategy
6. risks that can only be settled by implementation

Avoid product scope creep.

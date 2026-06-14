# First Build Spike Memo: `inventory.adjust_quantity`

**Goal:** prove or disprove the snap-forge thesis at its narrowest useful boundary: one tenant-scoped operational write that cannot happen directly, only through a typed gateway with approval, audit, outbox, and idempotency.

No UI, no Tekmetric dependency, no SMS provider, no scanner app. Use a mock incumbent boundary only as an outbox event target.

## 1. File-By-File Implementation Plan

```text
supabase/
  config.toml
  migrations/
    000001_init_extensions.sql
    000002_core_identity.sql
    000003_inventory_schema.sql
    000004_gateway_schema.sql
    000005_rls_and_grants.sql
    000006_inventory_adjust_quantity_rpc.sql
  seed.sql
tests/
  sql/
    inventory_adjust_quantity_test.sql
package.json
README.md
```

### `supabase/config.toml`

Minimal Supabase local scaffold:

- local Postgres
- local Auth available, but tests may simulate JWT claims directly
- no Edge Functions required for spike
- no external services

### `000001_init_extensions.sql`

Enable only what is needed:

```sql
create extension if not exists pgcrypto;
create extension if not exists pgtap;
```

`pgtap` is optional but useful for exact database-level assertions.

### `000002_core_identity.sql`

Create tenant and membership primitives.

Tables:

- `app.tenants`
- `app.tenant_memberships`

Purpose: prove tenant-scoped RLS with user claims.

### `000003_inventory_schema.sql`

Create operational inventory projection.

Tables:

- `inventory.items`
- `inventory.inventory_adjustments`

Direct writes to these tables must be revoked from runtime roles.

### `000004_gateway_schema.sql`

Create gateway infrastructure.

Tables:

- `gateway.action_requests`
- `gateway.approvals`
- `gateway.idempotency_keys`
- `gateway.audit_log`
- `gateway.outbox`

### `000005_rls_and_grants.sql`

Enable and force RLS, revoke direct writes, expose only approved RPCs.

Runtime roles should be able to:

- read tenant-visible inventory rows
- submit an adjustment action request
- approve a pending request if they have approver role
- read their own tenant’s action/audit/outbox metadata if needed for tests

Runtime roles should not be able to:

- insert/update/delete `inventory.items`
- insert/update/delete `inventory.inventory_adjustments`
- write audit/outbox directly
- read cross-tenant rows

### `000006_inventory_adjust_quantity_rpc.sql`

Create the action gateway functions.

Minimum functions:

```sql
gateway.request_inventory_adjust_quantity(...)
gateway.approve_action_request(...)
gateway.execute_inventory_adjust_quantity(...)
```

`execute_inventory_adjust_quantity` should not be granted to `authenticated`; only `approve_action_request` calls it internally.

### `seed.sql`

Two tenants, three users, and fixture inventory:

- tenant A
- tenant B
- actor A
- approver A
- actor B
- one item in tenant A
- one item in tenant B

### `tests/sql/inventory_adjust_quantity_test.sql`

Database integration tests proving:

1. direct writes fail
2. cross-tenant reads fail
3. approved writes succeed
4. duplicate idempotency key does not double-apply

## 2. SQL Schemas

```sql
create schema if not exists app;
create schema if not exists inventory;
create schema if not exists gateway;

create table app.tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_at timestamptz not null default now()
);

create table app.tenant_memberships (
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  user_id uuid not null,
  role text not null check (role in ('member', 'approver', 'admin')),
  created_at timestamptz not null default now(),
  primary key (tenant_id, user_id)
);

create table inventory.items (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  sku text not null,
  name text not null,
  quantity integer not null default 0,
  source_system text not null default 'local_mock',
  source_id text,
  source_updated_at timestamptz,
  last_synced_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (tenant_id, sku)
);

create table inventory.inventory_adjustments (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  item_id uuid not null references inventory.items(id),
  delta integer not null check (delta <> 0),
  previous_quantity integer not null,
  new_quantity integer not null,
  reason text not null,
  action_request_id uuid not null,
  actor_user_id uuid not null,
  approved_by_user_id uuid not null,
  created_at timestamptz not null default now()
);

create table gateway.action_requests (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  action_name text not null check (action_name = 'inventory.adjust_quantity'),
  actor_user_id uuid not null,
  idempotency_key text not null,
  risk_class text not null default 'approval_required',
  status text not null check (
    status in ('pending_approval', 'approved', 'rejected', 'executed')
  ),
  payload jsonb not null,
  result jsonb,
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  executed_at timestamptz,
  unique (tenant_id, action_name, idempotency_key)
);

create table gateway.approvals (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  action_request_id uuid not null references gateway.action_requests(id) on delete cascade,
  approved_by_user_id uuid not null,
  decision text not null check (decision in ('approved', 'rejected')),
  note text,
  created_at timestamptz not null default now(),
  unique (action_request_id)
);

create table gateway.idempotency_keys (
  tenant_id uuid not null,
  action_name text not null,
  idempotency_key text not null,
  action_request_id uuid not null references gateway.action_requests(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (tenant_id, action_name, idempotency_key)
);

create table gateway.audit_log (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  action_request_id uuid references gateway.action_requests(id),
  actor_user_id uuid,
  event_type text not null,
  action_name text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table gateway.outbox (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null references app.tenants(id) on delete cascade,
  action_request_id uuid references gateway.action_requests(id),
  topic text not null,
  payload jsonb not null,
  status text not null default 'pending' check (status in ('pending', 'processing', 'sent', 'failed')),
  attempts integer not null default 0,
  created_at timestamptz not null default now(),
  available_at timestamptz not null default now()
);
```

## 3. PL/pgSQL Function Signatures

```sql
create or replace function app.current_user_id()
returns uuid
language sql
stable
as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;

create or replace function app.is_tenant_member(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = app, public
as $$
  select exists (
    select 1
    from app.tenant_memberships m
    where m.tenant_id = p_tenant_id
      and m.user_id = app.current_user_id()
  )
$$;

create or replace function app.is_tenant_approver(p_tenant_id uuid)
returns boolean
language sql
stable
security definer
set search_path = app, public
as $$
  select exists (
    select 1
    from app.tenant_memberships m
    where m.tenant_id = p_tenant_id
      and m.user_id = app.current_user_id()
      and m.role in ('approver', 'admin')
  )
$$;
```

Gateway RPCs:

```sql
create or replace function gateway.request_inventory_adjust_quantity(
  p_tenant_id uuid,
  p_item_id uuid,
  p_delta integer,
  p_reason text,
  p_idempotency_key text
)
returns uuid;

create or replace function gateway.approve_action_request(
  p_action_request_id uuid,
  p_decision text,
  p_note text default null
)
returns jsonb;

create or replace function gateway.execute_inventory_adjust_quantity(
  p_action_request_id uuid,
  p_approved_by_user_id uuid
)
returns jsonb;
```

Recommended posture:

- `request_inventory_adjust_quantity`: `security definer`, granted to `authenticated`
- `approve_action_request`: `security definer`, granted to `authenticated`
- `execute_inventory_adjust_quantity`: `security definer`, **not granted** to runtime roles

Core behavior:

- request validates tenant membership, item tenant, nonzero delta, reason, idempotency key
- duplicate idempotency key returns the existing `action_request_id`
- request creates `pending_approval`, audit row, and idempotency row
- approve validates approver membership
- approve calls execute only once
- execute locks action request and item row with `for update`
- execute updates quantity, writes adjustment row, audit row, and outbox row in one transaction
- repeat approval/execution returns existing result without changing quantity again

## 4. RLS And Grants

```sql
alter table app.tenants enable row level security;
alter table app.tenant_memberships enable row level security;
alter table inventory.items enable row level security;
alter table inventory.inventory_adjustments enable row level security;
alter table gateway.action_requests enable row level security;
alter table gateway.approvals enable row level security;
alter table gateway.audit_log enable row level security;
alter table gateway.outbox enable row level security;

alter table inventory.items force row level security;
alter table inventory.inventory_adjustments force row level security;
alter table gateway.action_requests force row level security;
alter table gateway.approvals force row level security;
alter table gateway.audit_log force row level security;
alter table gateway.outbox force row level security;
```

Read policies:

```sql
create policy tenant_read_items
on inventory.items
for select
to authenticated
using (app.is_tenant_member(tenant_id));

create policy tenant_read_adjustments
on inventory.inventory_adjustments
for select
to authenticated
using (app.is_tenant_member(tenant_id));

create policy tenant_read_action_requests
on gateway.action_requests
for select
to authenticated
using (app.is_tenant_member(tenant_id));

create policy tenant_read_audit
on gateway.audit_log
for select
to authenticated
using (app.is_tenant_member(tenant_id));

create policy tenant_read_outbox
on gateway.outbox
for select
to authenticated
using (app.is_tenant_member(tenant_id));
```

Do **not** create runtime insert/update/delete policies on operational tables.

Grants:

```sql
revoke all on schema inventory from anon, authenticated;
revoke all on schema gateway from anon, authenticated;

grant usage on schema inventory to authenticated;
grant usage on schema gateway to authenticated;

grant select on inventory.items to authenticated;
grant select on inventory.inventory_adjustments to authenticated;
grant select on gateway.action_requests to authenticated;
grant select on gateway.audit_log to authenticated;
grant select on gateway.outbox to authenticated;

revoke insert, update, delete on inventory.items from authenticated;
revoke insert, update, delete on inventory.inventory_adjustments from authenticated;
revoke insert, update, delete on gateway.audit_log from authenticated;
revoke insert, update, delete on gateway.outbox from authenticated;

grant execute on function gateway.request_inventory_adjust_quantity(
  uuid, uuid, integer, text, text
) to authenticated;

grant execute on function gateway.approve_action_request(
  uuid, text, text
) to authenticated;

revoke all on function gateway.execute_inventory_adjust_quantity(
  uuid, uuid
) from public, anon, authenticated;
```

## 5. Exact Test Strategy

Use SQL integration tests against local Supabase Postgres. Run with either:

```bash
supabase db reset
psql "$DATABASE_URL" -f tests/sql/inventory_adjust_quantity_test.sql
```

or Supabase’s pgTAP workflow if wired into `supabase test db`.

### Test fixtures

Create:

- tenant A
- tenant B
- user A member of tenant A
- approver A approver of tenant A
- user B member of tenant B
- item A quantity `10`
- item B quantity `20`

Simulate authenticated users:

```sql
set local role authenticated;
set local request.jwt.claim.sub = '<user_uuid>';
```

### Test 1: direct writes fail

As user A:

```sql
insert into inventory.items (...) values (...);
update inventory.items set quantity = quantity + 1 where id = '<item_a>';
delete from inventory.items where id = '<item_a>';
```

Expected:

- insert/update/delete are rejected by grants/RLS
- item quantity remains unchanged

### Test 2: cross-tenant reads fail

As user A:

```sql
select count(*) from inventory.items where tenant_id = '<tenant_b>';
```

Expected:

- returns `0`
- direct lookup by tenant B item ID returns no rows

### Test 3: approved writes succeed

As user A:

```sql
select gateway.request_inventory_adjust_quantity(
  '<tenant_a>',
  '<item_a>',
  -2,
  'QR bin count correction',
  'idem-adjust-001'
);
```

Expected:

- creates one `pending_approval` request
- quantity remains `10`
- audit has `action_requested`

As approver A:

```sql
select gateway.approve_action_request(
  '<action_request_id>',
  'approved',
  'count verified'
);
```

Expected:

- item quantity becomes `8`
- one `inventory.inventory_adjustments` row exists
- action request status becomes `executed`
- audit has `action_approved` and `action_executed`
- outbox has one event, e.g. `inventory.adjusted`

### Test 4: duplicate idempotency key does not double-apply

As user A, call the same request again:

```sql
select gateway.request_inventory_adjust_quantity(
  '<tenant_a>',
  '<item_a>',
  -2,
  'QR bin count correction',
  'idem-adjust-001'
);
```

Expected:

- returns same `action_request_id`
- does not create a second request
- does not create a second approval
- does not create a second adjustment
- does not create a second outbox event
- final quantity remains `8`

Also call approval again:

```sql
select gateway.approve_action_request(
  '<action_request_id>',
  'approved',
  'duplicate approval attempt'
);
```

Expected:

- returns existing result
- final quantity remains `8`

## 6. Risks Settled Only By Implementation

1. **PL/pgSQL gateway ergonomics**
   The spike must show whether small database RPCs stay readable and reviewable once validation, locking, approval, audit, and idempotency are all present.

2. **`SECURITY DEFINER` safety**
   The design depends on tightly scoped definer functions. Implementation must prove no runtime role can call internal execution paths or bypass tenant checks.

3. **Idempotency under concurrency**
   The duplicate-key test should include concurrent calls. A simple sequential test is not enough to prove no double-apply race.

4. **RLS test realism**
   SQL tests that simulate JWT claims are useful, but the spike should later add a Supabase client/PostgREST test to prove the same behavior through the actual API surface.

5. **Outbox boundary**
   The spike can prove atomic outbox creation, not delivery semantics. Worker retry, leasing, and external side-effect idempotency remain separate follow-up work.

6. **Incumbent SoR write ordering**
   This spike should use a mock local projection. It does not settle Tekmetric write permissions, latency, webhook coverage, or whether SoR-first writes are practical.

7. **Supavisor/session behavior**
   This design should prefer JWT-derived user identity for the spike. Pooler/session variable safety remains a separate live-environment test.
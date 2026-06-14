-- =========================================================================
-- RUN CHALLENGES AND VERIFICATION
-- =========================================================================

-- Seed data
INSERT INTO public.tenants (id, name) VALUES
('00000000-0000-0000-0000-00000000000a', 'Tenant A'),
('00000000-0000-0000-0000-00000000000b', 'Tenant B');

INSERT INTO public.tenant_users (tenant_id, user_id, role) VALUES
('00000000-0000-0000-0000-00000000000a', '11111111-1111-1111-1111-111111111111', 'staff'),
('00000000-0000-0000-0000-00000000000a', '22222222-2222-2222-2222-222222222222', 'admin'),
('00000000-0000-0000-0000-00000000000b', '33333333-3333-3333-3333-333333333333', 'staff');

INSERT INTO inventory.inventory_items (id, tenant_id, sku, name, quantity) VALUES
('10000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-00000000000a', 'SKU-A1', 'Item A1', 10),
('20000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-00000000000b', 'SKU-B1', 'Item B1', 20);

-- =========================================================================
-- CHALLENGE 1: EXCEPTION HANDLER CRASH ON NULL TENANT / ACTOR
-- =========================================================================
\echo '--- Running Challenge 1: Unauthenticated request ---'
-- Set sub claim to NULL (unauthenticated)
SET request.jwt.claim.sub = '';

-- Let's try calling adjust_quantity.
-- We expect 'Unauthenticated request' to be raised.
-- But wait, because auth.uid() is null, the EXCEPTION handler will try to insert:
-- VALUES (p_idempotency_key, v_tenant_id, v_actor_id, ...) where v_tenant_id and v_actor_id are null.
-- Since actor_id and tenant_id are NOT NULL in gateway.idempotency_keys, this INSERT will fail.
-- PostgreSQL will throw a NOT NULL constraint violation error INSTEAD of returning a clean 'FAILED' action result!

SELECT * FROM inventory.adjust_quantity(
    '10000000-0000-0000-0000-000000000000',
    5,
    'Restock',
    'key-unauth'
);

-- Let's see if the exception handler also crashes when user is authenticated but user has no tenant association.
\echo '--- Running Challenge 1b: User has no tenant association ---'
SET request.jwt.claim.sub = '44444444-4444-4444-4444-444444444444'; -- No tenant map

SELECT * FROM inventory.adjust_quantity(
    '10000000-0000-0000-0000-000000000000',
    5,
    'Restock',
    'key-no-tenant'
);


-- =========================================================================
-- CHALLENGE 2: CONCURRENCY RETRY & ERROR MESSAGE OVERWRITE
-- =========================================================================
\echo '--- Running Challenge 2: Error Message Overwrite ---'
-- Let's authenticate as Tenant A user
SET request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';

-- First call: attempts to adjust quantity, but results in negative quantity (-15 delta on 10 quantity)
-- This will fail and write a FAILED status with the actual error message.
SELECT * FROM inventory.adjust_quantity(
    '10000000-0000-0000-0000-000000000000',
    -15,
    'Reduce too much',
    'key-overwrite-test'
);

-- Let's see what is stored in the database right now.
\echo '--- DB status before second concurrent-simulated call: ---'
SELECT key, status, response_body FROM gateway.idempotency_keys WHERE key = 'key-overwrite-test';

-- Now, simulate a concurrent call Tx B.
-- Since the key is already in the database with status 'FAILED', a sequential call will fall through and re-run.
-- But a concurrent call Tx B (which was blocked on INSERT) will fail with unique_violation, lock the row,
-- see 'FAILED' status, and raise an exception: "Request is already in progress or failed concurrently".
-- This exception is caught by Tx B's outer block, which runs ON CONFLICT DO UPDATE.
-- The WHERE clause: status NOT IN ('SUCCESS', 'PENDING_APPROVAL') is true (since status is FAILED).
-- So Tx B updates the row, setting the error message to its own error message.
-- Let's simulate this by running a manual update to mimic Tx B's exception block behavior,
-- or we can just trace the exact code logic:
-- "WHEN unique_violation THEN ... SELECT status ... FOR UPDATE; IF v_idemp_status = 'FAILED' THEN RAISE EXCEPTION 'Request is already in progress or failed concurrently';"
-- If we do that, we raise the exception, which goes to the outer block:
-- "ON CONFLICT DO UPDATE SET status = 'FAILED', response_body = jsonb_build_object('error', v_err_msg)"
-- Where v_err_msg is "Request is already in progress or failed concurrently".
-- Let's run a query to verify what the response_body looks like if that happens.
-- We can just execute the inner unique_violation block's logic manually to show the result.
-- Let's do that:
-- If Tx B is running, it raises "Request is already in progress or failed concurrently", which is caught by the EXCEPTION block.
-- The EXCEPTION block runs the INSERT ... ON CONFLICT DO UPDATE.
-- Let's execute that INSERT ... ON CONFLICT DO UPDATE statement directly as Tx B would, to see what happens:
BEGIN;
-- Set request sub
SET request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';
INSERT INTO gateway.idempotency_keys (key, tenant_id, actor_id, action_name, status, response_body, expires_at)
VALUES ('key-overwrite-test', '00000000-0000-0000-0000-00000000000a', '11111111-1111-1111-1111-111111111111', 'inventory.adjust_quantity', 'FAILED', jsonb_build_object('error', 'Request is already in progress or failed concurrently'), now() + INTERVAL '24 hours')
ON CONFLICT (tenant_id, key) DO UPDATE
SET status = 'FAILED',
    response_body = jsonb_build_object('error', 'Request is already in progress or failed concurrently')
WHERE gateway.idempotency_keys.status NOT IN ('SUCCESS', 'PENDING_APPROVAL');
COMMIT;

\echo '--- DB status after second call: ---'
SELECT key, status, response_body FROM gateway.idempotency_keys WHERE key = 'key-overwrite-test';


-- =========================================================================
-- CHALLENGE 3: RLS POLICY BLOCKS GLOBAL BACKGROUND WORKER
-- =========================================================================
\echo '--- Running Challenge 3: RLS blocks background worker ---'
-- Create a custom role for the background worker
DROP ROLE IF EXISTS worker_role;
CREATE ROLE worker_role WITH LOGIN PASSWORD 'worker_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON public.outbox_events TO worker_role;

-- Enable and force RLS on outbox_events
ALTER TABLE public.outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outbox_events FORCE ROW LEVEL SECURITY;

-- Let's insert a test event
INSERT INTO public.outbox_events (tenant_id, event_type, payload) VALUES
('00000000-0000-0000-0000-00000000000a', 'test_event', '{"data": "tenantA"}'),
('00000000-0000-0000-0000-00000000000b', 'test_event', '{"data": "tenantB"}');

-- Now, run as worker_role and try to SELECT all unprocessed events.
-- Because RLS is enabled on outbox_events and FORCE RLS is ON, the worker_role must pass the RLS policies.
-- Let's check the RLS policies on public.outbox_events:
-- 1. read_outbox_events FOR SELECT TO authenticated USING (tenant_id IN ...)
-- 2. gateway_all_outbox_events FOR ALL TO gateway_executor USING (tenant_id::text = current_setting('gateway.current_tenant_id', true))
-- 3. lockdown_outbox_events FOR ALL TO authenticated USING (false)
-- Since worker_role is NOT authenticated and NOT gateway_executor, there is NO policy that allows worker_role to read or write outbox_events!
-- Let's verify if worker_role can read any rows.
SET ROLE worker_role;
SELECT COUNT(*) FROM public.outbox_events WHERE processed = FALSE;

-- Even if we grant all policies, if the worker role has to use tenant-scoped policies, it cannot read across all tenants.
RESET ROLE;


-- =========================================================================
-- CHALLENGE 4: MUTABILITY OF AUDIT LOGS
-- =========================================================================
\echo '--- Running Challenge 4: Mutability of Audit Logs ---'
-- Let's insert an audit log
INSERT INTO audit.audit_logs (tenant_id, actor_id, action_name, table_name, record_id, old_state, new_state)
VALUES ('00000000-0000-0000-0000-00000000000a', '11111111-1111-1111-1111-111111111111', 'test_action', 'test_table', '30000000-0000-0000-0000-000000000000', '{}', '{}');

-- Run as gateway_executor
SET ROLE gateway_executor;
-- Set tenant ID context
SET gateway.current_tenant_id = '00000000-0000-0000-0000-00000000000a';

-- Check if gateway_executor can delete or update audit logs
UPDATE audit.audit_logs SET new_state = '{"compromised": true}' WHERE action_name = 'test_action';
\echo '--- Audit logs after gateway_executor update: ---'
SELECT * FROM audit.audit_logs;

DELETE FROM audit.audit_logs WHERE action_name = 'test_action';
\echo '--- Audit logs count after delete: ---'
SELECT COUNT(*) FROM audit.audit_logs;

RESET ROLE;

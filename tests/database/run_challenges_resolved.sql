-- =========================================================================
-- RUN CHALLENGES AND VERIFICATION (RESOLVED SCHEMA)
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
-- CHALLENGE 1: EXCEPTION HANDLER GRACEFUL FAIL ON NULL TENANT / ACTOR
-- =========================================================================
\echo '--- Running Challenge 1: Unauthenticated request ---'
-- Set sub claim to NULL (unauthenticated)
SET request.jwt.claim.sub = '';

-- Call adjust_quantity - should return FAILED status gracefully without crashing
SELECT * FROM inventory.adjust_quantity(
    '10000000-0000-0000-0000-000000000000',
    5,
    'Restock',
    'key-unauth'
);

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
\echo '--- Running Challenge 2: Error Message Overwrite / Failures ---'
-- Authenticate as Tenant A user
SET request.jwt.claim.sub = '11111111-1111-1111-1111-111111111111';

-- First call: attempts to adjust quantity, but results in negative quantity (-15 delta on 10 quantity)
-- Should return FAILED and write it.
SELECT * FROM inventory.adjust_quantity(
    '10000000-0000-0000-0000-000000000000',
    -15,
    'Reduce too much',
    'key-overwrite-test'
);

\echo '--- DB status before second call: ---'
SELECT key, status, response_body FROM gateway.idempotency_keys WHERE key = 'key-overwrite-test';

-- Second call: using the same key. In the resolved code, this goes to the unique_violation handler,
-- reads the status 'FAILED' and should return the cached failure response directly.
SELECT * FROM inventory.adjust_quantity(
    '10000000-0000-0000-0000-000000000000',
    -15,
    'Reduce too much',
    'key-overwrite-test'
);

-- Check DB status again to ensure the error was not overwritten with a concurrency error.
\echo '--- DB status after second call: ---'
SELECT key, status, response_body FROM gateway.idempotency_keys WHERE key = 'key-overwrite-test';


-- =========================================================================
-- CHALLENGE 3: BACKGROUND WORKER OUTBOX ACCESS
-- =========================================================================
\echo '--- Running Challenge 3: RLS blocks background worker ---'
-- Seed some events
INSERT INTO public.outbox_events (tenant_id, event_type, payload) VALUES
('00000000-0000-0000-0000-00000000000a', 'test_event', '{"data": "tenantA"}'),
('00000000-0000-0000-0000-00000000000b', 'test_event', '{"data": "tenantB"}');

-- Set role to outbox_processor
SET ROLE outbox_processor;

-- Read all unprocessed events. Should succeed and return 2 rows.
SELECT COUNT(*) FROM public.outbox_events WHERE processed = FALSE;

-- Reset role
RESET ROLE;


-- =========================================================================
-- CHALLENGE 4: MUTABILITY OF AUDIT LOGS
-- =========================================================================
\echo '--- Running Challenge 4: Mutability of Audit Logs ---'
-- Set to gateway_executor
SET ROLE gateway_executor;
SET gateway.current_tenant_id = '00000000-0000-0000-0000-00000000000a';

-- Try to UPDATE audit logs. Should fail with permission denied.
\echo '--- Attempting UPDATE on audit logs (expect error) ---'
UPDATE audit.audit_logs SET new_state = '{"compromised": true}' WHERE action_name = 'inventory.adjust_quantity';

-- Try to DELETE audit logs. Should fail with permission denied.
\echo '--- Attempting DELETE on audit logs (expect error) ---'
DELETE FROM audit.audit_logs WHERE action_name = 'inventory.adjust_quantity';

RESET ROLE;

# Build Spike Blueprint: Database Architecture and Action Gateway

This document outlines the database schemas, gateway functions, row-level security (RLS) configuration, and automated verification suites required to execute the first build spike for snap-forge.

---

## 1. Database Schema Design

The database objects are divided into four distinct schemas:
1.  **`public`**: Contains global systems tables such as tenants, user-to-tenant maps, and the transactional messaging outbox.
2.  **`inventory`**: Houses core operational tables for inventory tracking (items, SKU codes, quantities, and historical adjustments).
3.  **`gateway`**: Manages operational components for action execution, including idempotency state keys and approval queues.
4.  **`audit`**: Stores immutable audit logs.

### SQL Schema Code Block
```sql
-- =========================================================================
-- 1. SCHEMAS
-- =========================================================================
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS gateway;
CREATE SCHEMA IF NOT EXISTS audit;

ALTER DEFAULT PRIVILEGES IN SCHEMA public, inventory, gateway, audit REVOKE INSERT, UPDATE, DELETE ON TABLES FROM authenticated, public;
ALTER DEFAULT PRIVILEGES IN SCHEMA public, inventory, gateway, audit REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- =========================================================================
-- 2. CORE SYSTEM & TENANCY TABLES
-- =========================================================================
CREATE TABLE public.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE public.tenant_users (
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL, -- references Supabase auth.users(id)
    role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'staff')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, user_id)
);
CREATE INDEX idx_tenant_users_user_id ON public.tenant_users(user_id);

-- =========================================================================
-- 3. INVENTORY DOMAIN TABLES
-- =========================================================================
CREATE TABLE inventory.inventory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    source_system TEXT NOT NULL DEFAULT 'local', -- e.g., 'tekmetric', 'local'
    source_id TEXT, -- external system reference ID
    source_updated_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, sku)
);

CREATE TABLE inventory.inventory_adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory.inventory_items(id) ON DELETE CASCADE,
    quantity_delta INT NOT NULL CHECK (quantity_delta <> 0),
    actor_id UUID NOT NULL, -- references auth.users(id)
    reason TEXT,
    idempotency_key TEXT NOT NULL,
    approved_by UUID, -- references auth.users(id) if approved via gate
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_inventory_adj_tenant ON inventory.inventory_adjustments(tenant_id);

-- =========================================================================
-- 4. GATEWAY, IDEMPOTENCY, AND APPROVALS TABLES
-- =========================================================================
CREATE TYPE gateway.action_result AS (
    status TEXT,          -- 'SUCCESS', 'PENDING_APPROVAL', 'FAILED'
    approval_id UUID,     -- ID of the approval request if pending
    message TEXT,         -- Descriptive status/error message
    new_quantity INT      -- The updated quantity (if SUCCESS)
);

CREATE TABLE gateway.idempotency_keys (
    key TEXT NOT NULL,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    actor_id UUID NOT NULL,
    action_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'SUCCESS', 'FAILED', 'PENDING_APPROVAL')),
    response_body JSONB, -- stores cached gateway.action_result
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (tenant_id, key)
);
CREATE INDEX idx_idempotency_expiry ON gateway.idempotency_keys(expires_at);

CREATE TABLE gateway.approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    action_name TEXT NOT NULL,
    action_payload JSONB NOT NULL,
    idempotency_key TEXT NOT NULL,
    actor_id UUID NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    approver_id UUID, -- references auth.users(id)
    decision_reason TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, idempotency_key)
);
CREATE INDEX idx_approval_requests_tenant_status ON gateway.approval_requests(tenant_id, status);

-- =========================================================================
-- 5. AUDIT & MESSAGING (OUTBOX) TABLES
-- =========================================================================
CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    actor_id UUID NOT NULL,
    action_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    old_state JSONB,
    new_state JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_logs_tenant_created ON audit.audit_logs(tenant_id, created_at DESC);

CREATE TABLE public.outbox_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES public.tenants(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ
);
CREATE INDEX idx_outbox_events_unprocessed ON public.outbox_events(created_at) WHERE processed = FALSE;
CREATE INDEX idx_outbox_events_tenant ON public.outbox_events(tenant_id);
```

---

## 2. Action Gateway Signature & RPC

The gateway mutation for modifying inventory is exposed via the `inventory.adjust_quantity` function.

### Exact Validation Steps inside the RPC:
1.  **Actor Identification**: Checks `auth.uid()` to identify the calling user. Throws an exception if unauthenticated.
2.  **Tenant Membership Lookup**: Finds the tenant context (`tenant_id`) and user role by querying `public.tenant_users`.
3.  **Tenant Context Injection**: Executes `set_config('gateway.current_tenant_id', v_tenant_id, true)` to scope RLS checks to the resolved tenant.
4.  **Idempotency Validation**: Queries `gateway.idempotency_keys` with `SELECT FOR UPDATE` to lock the key. If the key exists:
    *   If status is `SUCCESS` or `PENDING_APPROVAL`, returns the cached `action_result` immediately.
    *   If status is `PENDING`, raises an exception (request in progress).
    *   If not found, inserts a row with `PENDING` status.
5.  **Threshold Checking**: Compares the adjustment delta against the manager approval threshold (default is ±50 items).
    *   If exceeded, inserts a row into `gateway.approval_requests` and caches a `PENDING_APPROVAL` response.
6.  **Transaction-Consistent Update**:
    *   Fetches the item's current quantity with `SELECT FOR UPDATE` to prevent race conditions.
    *   Computes `new_quantity` and checks that it is non-negative (`quantity >= 0` check).
    *   Updates the `inventory.inventory_items` table.
    *   Inserts the adjustment tracking row into `inventory.inventory_adjustments`.
7.  **Audit & Outbox Inserts**: Inserts an entry into `audit.audit_logs` and emits a JSON payload event to `public.outbox_events` in the same transaction.
8.  **Exception Handling**: Employs a PL/pgSQL `EXCEPTION WHEN OTHERS` subtransaction block to catch runtime errors. When an execution fails:
    *   The database rolls back mutations made inside the block.
    *   The subtransaction updates the idempotency key status to `FAILED` and records the error message, ensuring the client receives a structured failure response while preserving the idempotency key lock state.

### PL/pgSQL Action Gateway Code
```sql
DROP FUNCTION IF EXISTS inventory.adjust_quantity(UUID, INT, TEXT, TEXT, UUID);
CREATE OR REPLACE FUNCTION inventory.adjust_quantity(
    p_item_id UUID,
    p_quantity_delta INT,
    p_reason TEXT,
    p_idempotency_key TEXT,
    p_tenant_id UUID DEFAULT NULL
)
RETURNS gateway.action_result
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = inventory, public, gateway, pg_temp
AS $$
DECLARE
    v_actor_id UUID;
    v_tenant_id UUID;
    v_role TEXT;
    v_current_qty INT;
    v_new_qty INT;
    v_result gateway.action_result;
    v_idemp_status TEXT;
    v_idemp_response JSONB;
    v_approval_id UUID;
    v_approval_threshold INT := 50; -- Delta threshold requiring manager approval
    v_old_state JSONB;
    v_new_state JSONB;
    v_err_msg TEXT;
BEGIN
    -- 1. Identify Actor
    v_actor_id := auth.uid();
    IF v_actor_id IS NULL THEN
        RAISE EXCEPTION 'Unauthenticated request' USING ERRCODE = '42501';
    END IF;

    -- 2. Identify and Validate Tenancy
    IF p_tenant_id IS NOT NULL THEN
        SELECT tenant_id, role INTO v_tenant_id, v_role
        FROM public.tenant_users
        WHERE user_id = v_actor_id AND tenant_id = p_tenant_id;
    ELSE
        SELECT tenant_id, role INTO v_tenant_id, v_role
        FROM public.tenant_users
        WHERE user_id = v_actor_id
        ORDER BY created_at ASC
        LIMIT 1;
    END IF;

    IF v_tenant_id IS NULL THEN
        RAISE EXCEPTION 'User has no tenant association' USING ERRCODE = '42501';
    END IF;

    -- Set the transaction-scoped tenant context for RLS policies
    PERFORM set_config('gateway.current_tenant_id', v_tenant_id::text, true);

    -- 3. Validate Idempotency Key
    IF p_idempotency_key IS NULL OR trim(p_idempotency_key) = '' THEN
        RAISE EXCEPTION 'Idempotency key is required' USING ERRCODE = '22000';
    END IF;

    -- Wrap early insert of idempotency key in nested BEGIN ... EXCEPTION WHEN unique_violation THEN ... END;
    BEGIN
        INSERT INTO gateway.idempotency_keys (key, tenant_id, actor_id, action_name, status, expires_at)
        VALUES (p_idempotency_key, v_tenant_id, v_actor_id, 'inventory.adjust_quantity', 'PENDING', now() + INTERVAL '24 hours');
    EXCEPTION
        WHEN unique_violation THEN
            SELECT status, response_body INTO v_idemp_status, v_idemp_response
            FROM gateway.idempotency_keys
            WHERE tenant_id = v_tenant_id AND key = p_idempotency_key
            FOR UPDATE;
            
            IF NOT FOUND THEN
                INSERT INTO gateway.idempotency_keys (key, tenant_id, actor_id, action_name, status, expires_at)
                VALUES (p_idempotency_key, v_tenant_id, v_actor_id, 'inventory.adjust_quantity', 'PENDING', now() + INTERVAL '24 hours');
            ELSIF v_idemp_status = 'FAILED' THEN
                UPDATE gateway.idempotency_keys
                SET status = 'PENDING', response_body = NULL, created_at = now()
                WHERE tenant_id = v_tenant_id AND key = p_idempotency_key;
            ELSIF v_idemp_status IN ('SUCCESS', 'PENDING_APPROVAL') THEN
                v_result.status := v_idemp_response->>'status';
                v_result.approval_id := (v_idemp_response->>'approval_id')::UUID;
                v_result.message := v_idemp_response->>'message';
                v_result.new_quantity := (v_idemp_response->>'new_quantity')::INT;
                RETURN v_result;
            ELSE
                RAISE EXCEPTION 'Request is already in progress or failed concurrently' USING ERRCODE = '42000';
            END IF;
    END;

    -- 4. Validate Inventory Item belongs to the tenant
    SELECT quantity INTO v_current_qty
    FROM inventory.inventory_items
    WHERE id = p_item_id AND tenant_id = v_tenant_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Inventory item not found or tenant access denied' USING ERRCODE = 'P0002';
    END IF;

    -- Validate quantity delta
    IF p_quantity_delta = 0 THEN
        RAISE EXCEPTION 'Quantity delta cannot be zero' USING ERRCODE = '22000';
    END IF;

    -- 5. Evaluate Approval Policy
    IF abs(p_quantity_delta) > v_approval_threshold THEN
        -- Exceeds threshold: Insert approval request
        INSERT INTO gateway.approval_requests (tenant_id, action_name, action_payload, idempotency_key, actor_id, status)
        VALUES (
            v_tenant_id,
            'inventory.adjust_quantity',
            jsonb_build_object('item_id', p_item_id, 'quantity_delta', p_quantity_delta, 'reason', p_reason, 'actor_id', v_actor_id),
            p_idempotency_key,
            v_actor_id,
            'PENDING'
        )
        RETURNING id INTO v_approval_id;

        v_result := ROW(
            'PENDING_APPROVAL', 
            v_approval_id, 
            'Adjustment exceeds threshold of ' || v_approval_threshold || ' and requires manager approval.', 
            NULL
        )::gateway.action_result;

        UPDATE gateway.idempotency_keys
        SET status = 'PENDING_APPROVAL', response_body = to_jsonb(v_result)
        WHERE tenant_id = v_tenant_id AND key = p_idempotency_key;

        RETURN v_result;
    END IF;

    -- 6. Apply Adjustment Mutation
    v_new_qty := v_current_qty + p_quantity_delta;
    
    IF v_new_qty < 0 THEN
        RAISE EXCEPTION 'Adjustment would result in negative quantity (% -> %)', v_current_qty, v_new_qty USING ERRCODE = '23514';
    END IF;

    -- Update inventory
    UPDATE inventory.inventory_items
    SET quantity = v_new_qty, updated_at = now()
    WHERE id = p_item_id;

    -- Record adjustment
    INSERT INTO inventory.inventory_adjustments (tenant_id, item_id, quantity_delta, actor_id, reason, idempotency_key)
    VALUES (v_tenant_id, p_item_id, p_quantity_delta, v_actor_id, p_reason, p_idempotency_key);

    -- Write Audit Log
    v_old_state := jsonb_build_object('quantity', v_current_qty);
    v_new_state := jsonb_build_object('quantity', v_new_qty);
    
    INSERT INTO audit.audit_logs (tenant_id, actor_id, action_name, table_name, record_id, old_state, new_state)
    VALUES (v_tenant_id, v_actor_id, 'inventory.adjust_quantity', 'inventory.inventory_items', p_item_id, v_old_state, v_new_state);

    -- Emit Outbox Event
    INSERT INTO public.outbox_events (tenant_id, event_type, payload)
    VALUES (
        v_tenant_id,
        'inventory.quantity_adjusted',
        jsonb_build_object(
            'item_id', p_item_id,
            'quantity_delta', p_quantity_delta,
            'old_quantity', v_current_qty,
            'new_quantity', v_new_qty,
            'actor_id', v_actor_id,
            'reason', p_reason
        )
    );

    -- Update Idempotency status to SUCCESS
    v_result := ROW('SUCCESS', NULL, 'Quantity adjusted successfully.', v_new_qty)::gateway.action_result;

    UPDATE gateway.idempotency_keys
    SET status = 'SUCCESS', response_body = to_jsonb(v_result)
    WHERE tenant_id = v_tenant_id AND key = p_idempotency_key;

    RETURN v_result;

EXCEPTION
    WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS v_err_msg = MESSAGE_TEXT;
        
        -- Re-establish GUC tenant context
        IF v_tenant_id IS NOT NULL THEN
            PERFORM set_config('gateway.current_tenant_id', v_tenant_id::text, true);
        END IF;

        v_result := ROW('FAILED', NULL, 'Action failed: ' || v_err_msg, NULL)::gateway.action_result;
        
        -- Guard failed key logging
        IF SQLSTATE <> '42000' AND v_tenant_id IS NOT NULL AND v_actor_id IS NOT NULL AND p_idempotency_key IS NOT NULL THEN
            INSERT INTO gateway.idempotency_keys (key, tenant_id, actor_id, action_name, status, response_body, expires_at)
            VALUES (p_idempotency_key, v_tenant_id, v_actor_id, 'inventory.adjust_quantity', 'FAILED', to_jsonb(v_result), now() + INTERVAL '24 hours')
            ON CONFLICT (tenant_id, key) DO UPDATE
            SET status = 'FAILED', response_body = to_jsonb(v_result)
            WHERE gateway.idempotency_keys.status NOT IN ('SUCCESS', 'PENDING_APPROVAL');
        END IF;
        
        RETURN v_result;
END;
$$;
```

---

## 3. RLS Policies & Grants Lockdown

To block clients and AI blocks from bypassing the Action Gateway, mutations are prohibited at the schema permission level.

### Layer 1: SQL Grants Lockdown
All direct writes (`INSERT`, `UPDATE`, `DELETE`) on operational tables are revoked from client-facing roles (`authenticated`, `anon`, `public`).
```sql
-- Revoke operational write grants from general users
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA inventory FROM authenticated, public;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gateway     FROM authenticated, public;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit       FROM authenticated, public;
REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public      FROM authenticated, public;

-- Grant schema usage
GRANT USAGE ON SCHEMA inventory, gateway, audit, public TO authenticated;

-- Allow reading data via standard SELECT queries (fully filtered by RLS policies)
GRANT SELECT ON TABLE inventory.inventory_items       TO authenticated;
GRANT SELECT ON TABLE inventory.inventory_adjustments TO authenticated;
GRANT SELECT ON TABLE gateway.approval_requests       TO authenticated;
GRANT SELECT ON TABLE gateway.idempotency_keys        TO authenticated;
GRANT SELECT ON TABLE public.outbox_events            TO authenticated;
GRANT SELECT ON TABLE audit.audit_logs                TO authenticated;
GRANT SELECT ON TABLE public.tenant_users             TO authenticated;
GRANT SELECT ON TABLE public.tenants                  TO authenticated;
-- Allow execution of gateway functions
GRANT EXECUTE ON FUNCTION inventory.adjust_quantity(UUID, INT, TEXT, TEXT, UUID) TO authenticated;

-- Layer 2: RLS Policies & Least Privileged Definer Role
-- Instead of running gateway functions as the postgres superuser (which would bypass Row Level Security), snap-forge creates a dedicated non-superuser role gateway_executor to own the gateway functions. When a function executes, PostgreSQL enforces the policies assigned to the gateway_executor.

-- 1. Create a non-login executor role
CREATE ROLE gateway_executor WITH NOLOGIN;
GRANT USAGE ON SCHEMA inventory, gateway, audit, public TO gateway_executor;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA inventory, gateway TO gateway_executor;
GRANT SELECT, INSERT ON TABLE audit.audit_logs TO gateway_executor;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.outbox_events TO gateway_executor;
GRANT SELECT ON TABLE public.tenants, public.tenant_users TO gateway_executor;

REVOKE UPDATE, DELETE ON TABLE audit.audit_logs FROM public, authenticated, gateway_executor;

-- Create outbox_processor role
CREATE ROLE outbox_processor WITH NOLOGIN;
GRANT USAGE ON SCHEMA public, audit TO outbox_processor;
GRANT SELECT, UPDATE ON TABLE public.outbox_events TO outbox_processor;
GRANT SELECT ON TABLE audit.audit_logs TO outbox_processor;

-- Set gateway functions to execute under the gateway_executor role
ALTER FUNCTION inventory.adjust_quantity(UUID, INT, TEXT, TEXT, UUID) OWNER TO gateway_executor;

-- 2. Enable RLS and Force RLS on all tables
ALTER TABLE inventory.inventory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory.inventory_items FORCE ROW LEVEL SECURITY;

ALTER TABLE inventory.inventory_adjustments ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory.inventory_adjustments FORCE ROW LEVEL SECURITY;

ALTER TABLE gateway.approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE gateway.approval_requests FORCE ROW LEVEL SECURITY;

ALTER TABLE gateway.idempotency_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE gateway.idempotency_keys FORCE ROW LEVEL SECURITY;

ALTER TABLE public.outbox_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outbox_events FORCE ROW LEVEL SECURITY;

ALTER TABLE audit.audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit.audit_logs FORCE ROW LEVEL SECURITY;

ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenants FORCE ROW LEVEL SECURITY;

ALTER TABLE public.tenant_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tenant_users FORCE ROW LEVEL SECURITY;

-- 3. Define read policies for general runtime users
CREATE POLICY read_inventory_items ON inventory.inventory_items
    FOR SELECT TO authenticated
    USING (tenant_id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid()));

CREATE POLICY read_inventory_adjustments ON inventory.inventory_adjustments
    FOR SELECT TO authenticated
    USING (tenant_id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid()));

CREATE POLICY read_approval_requests ON gateway.approval_requests
    FOR SELECT TO authenticated
    USING (tenant_id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid()));

CREATE POLICY read_idempotency_keys ON gateway.idempotency_keys
    FOR SELECT TO authenticated
    USING (tenant_id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid()));

CREATE POLICY read_outbox_events ON public.outbox_events
    FOR SELECT TO authenticated
    USING (tenant_id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid() AND role IN ('admin', 'manager')));

CREATE POLICY read_audit_logs ON audit.audit_logs
    FOR SELECT TO authenticated
    USING (tenant_id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid() AND role IN ('admin', 'manager')));

CREATE POLICY read_tenants ON public.tenants
    FOR SELECT TO authenticated
    USING (id IN (SELECT tenant_id FROM public.tenant_users WHERE user_id = auth.uid()));

CREATE POLICY read_tenant_users_auth ON public.tenant_users
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY read_tenant_users_executor ON public.tenant_users
    FOR SELECT TO gateway_executor
    USING (user_id = auth.uid());

-- RLS policies for outbox_processor on public.outbox_events
CREATE POLICY outbox_processor_select_outbox ON public.outbox_events
    FOR SELECT TO outbox_processor
    USING (true);

CREATE POLICY outbox_processor_update_outbox ON public.outbox_events
    FOR UPDATE TO outbox_processor
    USING (true)
    WITH CHECK (true);

-- RLS policy for outbox_processor on audit.audit_logs
CREATE POLICY outbox_processor_select_audit ON audit.audit_logs
    FOR SELECT TO outbox_processor
    USING (true);

-- 4. Define write/all policies for the gateway executor
-- The gateway_executor is only authorized to write/modify rows that match the transaction-local tenant context
CREATE POLICY gateway_all_inventory_items ON inventory.inventory_items
    FOR ALL TO gateway_executor
    USING (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_all_inventory_adjustments ON inventory.inventory_adjustments
    FOR ALL TO gateway_executor
    USING (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_all_approval_requests ON gateway.approval_requests
    FOR ALL TO gateway_executor
    USING (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_all_idempotency_keys ON gateway.idempotency_keys
    FOR ALL TO gateway_executor
    USING (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_all_outbox_events ON public.outbox_events
    FOR ALL TO gateway_executor
    USING (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid)
    WITH CHECK (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_insert_audit_logs ON audit.audit_logs
    FOR INSERT TO gateway_executor
    WITH CHECK (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_select_tenants ON public.tenants
    FOR SELECT TO gateway_executor
    USING (id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

CREATE POLICY gateway_select_tenant_users ON public.tenant_users
    FOR SELECT TO gateway_executor
    USING (tenant_id = nullif(current_setting('gateway.current_tenant_id', true), '')::uuid);

-- 5. Explicitly lock down all direct modifications for general authenticated, anon, and PUBLIC users
CREATE POLICY lockdown_insert_inventory_items ON inventory.inventory_items AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_inventory_items ON inventory.inventory_items AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_inventory_items ON inventory.inventory_items AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_inventory_adjustments ON inventory.inventory_adjustments AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_inventory_adjustments ON inventory.inventory_adjustments AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_inventory_adjustments ON inventory.inventory_adjustments AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_approval_requests ON gateway.approval_requests AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_approval_requests ON gateway.approval_requests AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_approval_requests ON gateway.approval_requests AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_idempotency_keys ON gateway.idempotency_keys AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_idempotency_keys ON gateway.idempotency_keys AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_idempotency_keys ON gateway.idempotency_keys AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_outbox_events ON public.outbox_events AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_outbox_events ON public.outbox_events AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_outbox_events ON public.outbox_events AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_audit_logs ON audit.audit_logs AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_audit_logs ON audit.audit_logs AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_audit_logs ON audit.audit_logs AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_tenants ON public.tenants AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_tenants ON public.tenants AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_tenants ON public.tenants AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));

CREATE POLICY lockdown_insert_tenant_users ON public.tenant_users AS RESTRICTIVE FOR INSERT TO authenticated, anon, PUBLIC WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_update_tenant_users ON public.tenant_users AS RESTRICTIVE FOR UPDATE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon')) WITH CHECK (current_user NOT IN ('authenticated', 'anon'));
CREATE POLICY lockdown_delete_tenant_users ON public.tenant_users AS RESTRICTIVE FOR DELETE TO authenticated, anon, PUBLIC USING (current_user NOT IN ('authenticated', 'anon'));
```

---

## 4. Automated Tests Specification

### pgTAP Database-level Tests
Run directly within the database to test security permissions, tenancy isolation, and idempotency logic.

```sql
-- tests/database/gateway_tests.sql
BEGIN;
SELECT plan(8);

-- 1. Establish Fixture Data
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
-- TEST 1: DIRECT WRITE LOCKDOWN
-- =========================================================================
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', true);

SELECT throws_like(
    $$ INSERT INTO inventory.inventory_items (tenant_id, sku, name, quantity) VALUES ('00000000-0000-0000-0000-00000000000a', 'SKU-A2', 'Item A2', 5) $$,
    '%permission denied%',
    'Direct INSERT must be blocked for authenticated roles'
);

SELECT throws_like(
    $$ UPDATE inventory.inventory_items SET quantity = 50 WHERE id = '10000000-0000-0000-0000-000000000000' $$,
    '%permission denied%',
    'Direct UPDATE must be blocked for authenticated roles'
);

-- =========================================================================
-- TEST 2: TENANT READ ISOLATION
-- =========================================================================
SELECT results_eq(
    $$ SELECT sku FROM inventory.inventory_items $$,
    $$ VALUES ('SKU-A1') $$,
    'Tenant A user should only see Tenant A inventory items'
);

SELECT set_config('request.jwt.claim.sub', '33333333-3333-3333-3333-333333333333', true); -- Tenant B User
SELECT results_eq(
    $$ SELECT sku FROM inventory.inventory_items $$,
    $$ VALUES ('SKU-B1') $$,
    'Tenant B user should only see Tenant B inventory items'
);

-- =========================================================================
-- TEST 3: TENANT WRITE ISOLATION AT GATEWAY
-- =========================================================================
SELECT set_config('request.jwt.claim.sub', '11111111-1111-1111-1111-111111111111', true); -- Tenant A User
SELECT is(
    (SELECT status FROM inventory.adjust_quantity('20000000-0000-0000-0000-000000000000', 5, 'Restock B', 'key-1')),
    'FAILED',
    'Gateway must block adjusting inventory of another tenant'
);

-- =========================================================================
-- TEST 4: IDEMPOTENCY KEY ENFORCEMENT
-- =========================================================================
-- First call - succeeds
SELECT is(
    (SELECT status FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', 5, 'Restock A', 'key-idemp')),
    'SUCCESS',
    'Initial gateway adjustment call should succeed'
);

-- Second call - cached response
SELECT is(
    (SELECT status FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', 5, 'Restock A', 'key-idemp')),
    'SUCCESS',
    'Second call with identical idempotency key should return SUCCESS'
);

-- Verify quantity only adjusted once (10 + 5 = 15)
RESET ROLE;
SELECT is(
    (SELECT quantity FROM inventory.inventory_items WHERE id = '10000000-0000-0000-0000-000000000000'),
    15,
    'Quantity should change exactly once'
);

SELECT * FROM finish();
ROLLBACK;
```

### TypeScript Integration Tests (Vitest)
Executes HTTP API requests against the Supabase schema using tenant-scoped JWTs.

```typescript
// tests/integration/inventory.test.ts
import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { describe, it, expect, beforeAll } from 'vitest';

describe('Inventory Gateway Integration Tests', () => {
  let clientA: SupabaseClient; // Authenticated as User A (Tenant A)
  let clientB: SupabaseClient; // Authenticated as User B (Tenant B)

  beforeAll(async () => {
    // Initialize Supabase JS clients with anon key and set user sessions
    const supabaseUrl = process.env.SUPABASE_URL!;
    const supabaseAnonKey = process.env.SUPABASE_ANON_KEY!;

    clientA = createClient(supabaseUrl, supabaseAnonKey, { db: { schema: 'inventory' } });
    await clientA.auth.setSession({
      access_token: process.env.USER_A_JWT!,
      refresh_token: ''
    });

    clientB = createClient(supabaseUrl, supabaseAnonKey, { db: { schema: 'inventory' } });
    await clientB.auth.setSession({
      access_token: process.env.USER_B_JWT!,
      refresh_token: ''
    });
  });

  it('blocks direct writes to the inventory table', async () => {
    const uniqueSku = `BAD-SKU-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    const { error } = await clientA
      .from('inventory_items')
      .insert({ tenant_id: '00000000-0000-0000-0000-00000000000a', sku: uniqueSku, name: 'Item', quantity: 10 });
    
    // Expect PostgREST to return a 401/403 or permission denied error code (42501)
    expect(error?.code).toBe('42501'); 
  });

  it('isolates inventory reads between tenants', async () => {
    const { data: dataA } = await clientA.from('inventory_items').select('sku');
    const { data: dataB } = await clientB.from('inventory_items').select('sku');

    expect(dataA?.map(i => i.sku)).toContain('SKU-A1');
    expect(dataA?.map(i => i.sku)).not.toContain('SKU-B1');

    expect(dataB?.map(i => i.sku)).toContain('SKU-B1');
    expect(dataB?.map(i => i.sku)).not.toContain('SKU-A1');
  });

  it('enforces idempotency key checks', async () => {
    const uniqueIdempKey = `idemp-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`;
    const payload = {
      p_item_id: '10000000-0000-0000-0000-000000000000',
      p_quantity_delta: 5,
      p_reason: 'Integrity Test',
      p_idempotency_key: uniqueIdempKey
    };

    // Fetch initial quantity first
    const { data: initialData } = await clientA
      .from('inventory_items')
      .select('quantity')
      .eq('id', '10000000-0000-0000-0000-000000000000')
      .single();
    const initialQty = initialData?.quantity ?? 10;
    const expectedQty = initialQty + 5;

    // Execute first call
    const res1 = await clientA.rpc('adjust_quantity', payload);
    expect(res1.data.status).toBe('SUCCESS');
    expect(res1.data.new_quantity).toBe(expectedQty); 

    // Execute duplicate call
    const res2 = await clientA.rpc('adjust_quantity', payload);
    expect(res2.data.status).toBe('SUCCESS');
    expect(res2.data.new_quantity).toBe(expectedQty); // Must still return expectedQty (cached response body)
  });
});
```

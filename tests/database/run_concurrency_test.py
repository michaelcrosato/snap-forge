import subprocess
import threading
import time
import json
import sys

def run_sql(sql_code, role=None, jwt_sub=None, db="signalstack_sms", user="signalstack"):
    # Build psql command
    cmd = ["docker", "exec", "-i", "signalstack-sms-postgres-1", "psql", "-U", user, "-d", db, "-t", "-A"]
    
    # Prepend role and jwt sub settings if provided
    prepends = []
    if jwt_sub is not None:
        prepends.append(f"SET request.jwt.claim.sub = '{jwt_sub}';")
    if role is not None:
        prepends.append(f"SET ROLE {role};")
        
    full_sql = "\n".join(prepends) + "\n" + sql_code
    
    res = subprocess.run(cmd, input=full_sql, text=True, capture_output=True)
    return res.returncode, res.stdout.strip(), res.stderr.strip()

def setup_database():
    print("=== Loading Resolved Schema and Seeding Database ===")
    # Load resolved schema
    with open("tests/database/test_gateway_resolved.sql", "r") as f:
        schema_sql = f.read()
    
    code, stdout, stderr = run_sql(schema_sql)
    if "ERROR" in stderr:
        # Ignore role already exists / role cannot be dropped errors
        non_critical = True
        for line in stderr.splitlines():
            if "ERROR" in line and not ("role" in line and ("already exists" in line or "cannot be dropped" in line)):
                non_critical = False
                print(f"Critical schema load error: {line}")
        if not non_critical:
            sys.exit(1)
        
    # Seed data
    seed_sql = """
    -- Clean up previous seeds
    DELETE FROM public.tenant_users;
    DELETE FROM public.tenants;
    
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
    """
    code, stdout, stderr = run_sql(seed_sql)
    if "ERROR" in stderr:
        print(f"Error seeding database: {stderr}")
        sys.exit(1)
    print("Database schema loaded and seeded successfully.\n")

def test_concurrency_success():
    print("=== CHALLENGE 1: Concurrent Calls with Same Idempotency Key (Success Case) ===")
    
    # 1. Add delay trigger for 'key-concurrent-success'
    trigger_sql = """
    CREATE OR REPLACE FUNCTION test_delay_trigger() RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.key = 'key-concurrent-success' THEN
            PERFORM pg_sleep(3);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS test_concurrency_delay ON gateway.idempotency_keys;
    CREATE TRIGGER test_concurrency_delay
    BEFORE INSERT ON gateway.idempotency_keys
    FOR EACH ROW
    EXECUTE FUNCTION test_delay_trigger();
    """
    run_sql(trigger_sql)

    results = {}
    
    def call_gateway_1():
        sql = "SELECT * FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', 5, 'Con 1', 'key-concurrent-success', '00000000-0000-0000-0000-00000000000a');"
        code, stdout, stderr = run_sql(sql, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
        results["t1"] = (code, stdout, stderr)
        
    def call_gateway_2():
        sql = "SELECT * FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', 2, 'Con 2', 'key-concurrent-success', '00000000-0000-0000-0000-00000000000a');"
        code, stdout, stderr = run_sql(sql, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
        results["t2"] = (code, stdout, stderr)

    t1 = threading.Thread(target=call_gateway_1)
    t2 = threading.Thread(target=call_gateway_2)
    
    t1.start()
    time.sleep(0.5) # ensure t1 gets in first and triggers sleep
    t2.start()
    
    t1.join()
    t2.join()
    
    # Print results
    print(f"Thread 1 Result: Code={results['t1'][0]}, Output={results['t1'][1]}, Error={results['t1'][2]}")
    print(f"Thread 2 Result: Code={results['t2'][0]}, Output={results['t2'][1]}, Error={results['t2'][2]}")
    
    # Check final quantity
    code, stdout, stderr = run_sql("SELECT quantity FROM inventory.inventory_items WHERE id = '10000000-0000-0000-0000-000000000000';")
    qty = int(stdout.splitlines()[-1]) # get last line in case of GUC set output
    print(f"Final Quantity: {qty} (Expected: 15)")
    
    # Assertions
    passed = True
    if qty != 15:
        print("FAIL: Quantity adjusted twice or not at all!")
        passed = False
    
    # Both should have succeeded and returned the same result
    # Format of action_result: (SUCCESS,,Quantity adjusted successfully.,15)
    r1 = results['t1'][1]
    r2 = results['t2'][1]
    if "SUCCESS" not in r1 or "SUCCESS" not in r2:
        print("FAIL: One of the threads did not return SUCCESS!")
        passed = False
    if "15" not in r1 or "15" not in r2:
        print("FAIL: Thread response did not contain new quantity 15!")
        passed = False
        
    print(f"Challenge 1 Concurrency Success: {'PASSED' if passed else 'FAILED'}\n")
    return passed

def test_concurrency_failure():
    print("=== CHALLENGE 2: Concurrent Calls with Same Idempotency Key (Failure Case) ===")
    
    # We want Thread 1 to try to adjust quantity to negative (fails), while Thread 2 concurrently calls it.
    # 1. Add delay trigger for 'key-concurrent-fail'
    trigger_sql = """
    CREATE OR REPLACE FUNCTION test_delay_trigger_fail() RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.key = 'key-concurrent-fail' THEN
            PERFORM pg_sleep(3);
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS test_concurrency_delay_fail ON gateway.idempotency_keys;
    CREATE TRIGGER test_concurrency_delay_fail
    BEFORE INSERT ON gateway.idempotency_keys
    FOR EACH ROW
    EXECUTE FUNCTION test_delay_trigger_fail();
    """
    run_sql(trigger_sql)

    # Reset inventory quantity to 10
    run_sql("UPDATE inventory.inventory_items SET quantity = 10 WHERE id = '10000000-0000-0000-0000-000000000000';")

    results = {}
    
    def call_gateway_1():
        # Delta -15 on quantity 10 will fail check constraint/rule
        sql = "SELECT * FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', -15, 'Reduce too much', 'key-concurrent-fail', '00000000-0000-0000-0000-00000000000a');"
        code, stdout, stderr = run_sql(sql, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
        results["t1"] = (code, stdout, stderr)
        
    def call_gateway_2():
        sql = "SELECT * FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', -15, 'Reduce too much', 'key-concurrent-fail', '00000000-0000-0000-0000-00000000000a');"
        code, stdout, stderr = run_sql(sql, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
        results["t2"] = (code, stdout, stderr)

    t1 = threading.Thread(target=call_gateway_1)
    t2 = threading.Thread(target=call_gateway_2)
    
    t1.start()
    time.sleep(0.5) # ensure t1 gets in first and triggers sleep
    t2.start()
    
    t1.join()
    t2.join()
    
    print(f"Thread 1 Result: Code={results['t1'][0]}, Output={results['t1'][1]}, Error={results['t1'][2]}")
    print(f"Thread 2 Result: Code={results['t2'][0]}, Output={results['t2'][1]}, Error={results['t2'][2]}")
    
    # Check idempotency keys table status
    code, stdout, stderr = run_sql("SELECT status, response_body FROM gateway.idempotency_keys WHERE key = 'key-concurrent-fail';")
    print(f"Idempotency Key in DB: {stdout}")
    
    passed = True
    r1 = results['t1'][1]
    r2 = results['t2'][1]
    if "FAILED" not in r1 or "FAILED" not in r2:
        print("FAIL: One of the threads did not return FAILED status!")
        passed = False
    # Check if there is a concurrency overwrite error
    if "already in progress" in r2 or "concurrently" in r2:
        print("FAIL: Thread 2 returned a concurrency overwrite error instead of the cached failure!")
        passed = False
        
    print(f"Challenge 2 Concurrency Failure: {'PASSED' if passed else 'FAILED'}\n")
    return passed

def test_exception_handler_and_guc():
    print("=== CHALLENGE 3: Exception Handler and GUC State Recovery ===")
    
    # We call adjust_quantity with negative quantity, causing a CHECK constraint exception in PG.
    # We verify that:
    # 1. The GUC current_tenant_id is re-established in the EXCEPTION block.
    # 2. It successfully inserts a FAILED status into gateway.idempotency_keys.
    # 3. The transaction does not crash, and returns the FAILED status response.
    
    # Clean up previous keys
    run_sql("DELETE FROM gateway.idempotency_keys WHERE key = 'key-guc-test';")
    run_sql("UPDATE inventory.inventory_items SET quantity = 10 WHERE id = '10000000-0000-0000-0000-000000000000';")
    
    sql = "SELECT * FROM inventory.adjust_quantity('10000000-0000-0000-0000-000000000000', -15, 'GUC test', 'key-guc-test', '00000000-0000-0000-0000-00000000000a');"
    code, stdout, stderr = run_sql(sql, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
    
    print(f"Call Result: Code={code}, Output={stdout}, Error={stderr}")
    
    # Check if key is logged in DB
    code_db, stdout_db, stderr_db = run_sql("SELECT status, response_body FROM gateway.idempotency_keys WHERE key = 'key-guc-test';")
    print(f"Idempotency Key in DB: {stdout_db}")
    
    passed = True
    if "FAILED" not in stdout:
        print("FAIL: Function did not return FAILED result!")
        passed = False
    if "FAILED" not in stdout_db:
        print("FAIL: Idempotency key was not logged as FAILED in DB (likely due to RLS violation during exception handling)!")
        passed = False
        
    print(f"Challenge 3 Exception Handler & GUC: {'PASSED' if passed else 'FAILED'}\n")
    return passed

def test_guc_clearing_casting():
    print("=== CHALLENGE 4: GUC Setting Clearing and UUID Casting Errors ===")
    
    # We want to check if clearing or setting a non-UUID value on gateway.current_tenant_id throws casting errors in SELECTs.
    
    # 1. Clear GUC to empty string
    print("Test 4a: Setting gateway.current_tenant_id = ''")
    sql_a = """
    SET gateway.current_tenant_id = '';
    SELECT COUNT(*) FROM inventory.inventory_items;
    """
    code_a, stdout_a, stderr_a = run_sql(sql_a, role="gateway_executor")
    print(f"Result 4a: Code={code_a}, Output={stdout_a}, Error={stderr_a}")
    
    # 2. Set GUC to invalid UUID 'abc'
    print("Test 4b: Setting gateway.current_tenant_id = 'abc'")
    sql_b = """
    SET gateway.current_tenant_id = 'abc';
    SELECT COUNT(*) FROM inventory.inventory_items;
    """
    code_b, stdout_b, stderr_b = run_sql(sql_b, role="gateway_executor")
    print(f"Result 4b: Code={code_b}, Output={stdout_b}, Error={stderr_b}")
    
    passed = True
    if "ERROR" in stderr_a:
        print("FAIL: Setting GUC to empty string caused error!")
        passed = False
    if "ERROR" not in stderr_b or "invalid input syntax for type uuid" not in stderr_b:
        print("FAIL: Setting GUC to invalid UUID did NOT throw the expected uuid casting error!")
        passed = False
    else:
        print(f"Expected behavior: setting invalid GUC to non-uuid threw casting error: {stderr_b}")
        
    print(f"Challenge 4 GUC Casting: {'PASSED' if passed else 'FAILED'}\n")
    return passed

def test_rls_bypasses():
    print("=== CHALLENGE 5: RLS Policy Bypasses and Direct Writes ===")
    
    # We try to write directly to inventory.inventory_items as:
    # 1. authenticated
    # 2. anon
    # 3. PUBLIC (which is default for authenticated/anon)
    
    passed = True
    
    # 1. Direct Insert by authenticated
    sql_ins = "INSERT INTO inventory.inventory_items (tenant_id, sku, name, quantity) VALUES ('00000000-0000-0000-0000-00000000000a', 'SKU-DIRECT', 'Direct', 100);"
    code, stdout, stderr = run_sql(sql_ins, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
    print(f"Direct Insert as authenticated: Code={code}, Error={stderr}")
    if "ERROR" not in stderr or "permission denied" not in stderr:
        print("FAIL: Direct insert by authenticated user was not blocked by permission denied!")
        passed = False
        
    # 2. Direct Update by authenticated
    sql_upd = "UPDATE inventory.inventory_items SET quantity = 100 WHERE id = '10000000-0000-0000-0000-000000000000';"
    code, stdout, stderr = run_sql(sql_upd, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
    print(f"Direct Update as authenticated: Code={code}, Error={stderr}")
    if "ERROR" not in stderr or "permission denied" not in stderr:
        print("FAIL: Direct update by authenticated user was not blocked by permission denied!")
        passed = False
        
    # 3. Direct Delete by authenticated
    sql_del = "DELETE FROM inventory.inventory_items WHERE id = '10000000-0000-0000-0000-000000000000';"
    code, stdout, stderr = run_sql(sql_del, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
    print(f"Direct Delete as authenticated: Code={code}, Error={stderr}")
    if "ERROR" not in stderr or "permission denied" not in stderr:
        print("FAIL: Direct delete by authenticated user was not blocked by permission denied!")
        passed = False
        
    # 4. Direct Write by anon
    code, stdout, stderr = run_sql(sql_ins, role="anon")
    print(f"Direct Insert as anon: Code={code}, Error={stderr}")
    if "ERROR" not in stderr or ("permission denied" not in stderr and "schema inventory" not in stderr):
        print("FAIL: Direct insert by anon user was not blocked!")
        passed = False
        
    print(f"Challenge 5 RLS Bypasses: {'PASSED' if passed else 'FAILED'}\n")
    return passed

def test_tenant_selects():
    print("=== CHALLENGE 6: Authenticated User Tenant SELECT Queries ===")
    
    # Verify User A (Tenant A) can select items, but sees only Tenant A rows.
    # User A: jwt_sub = 11111111-1111-1111-1111-111111111111
    # Items: SKU-A1 (Tenant A), SKU-B1 (Tenant B)
    
    sql = "SELECT id, sku, tenant_id FROM inventory.inventory_items;"
    code, stdout, stderr = run_sql(sql, role="authenticated", jwt_sub="11111111-1111-1111-1111-111111111111")
    print(f"User A SELECT results:\n{stdout}")
    
    passed = True
    if "ERROR" in stderr:
        print(f"FAIL: SELECT query failed with error: {stderr}")
        passed = False
    else:
        # Check that SKU-A1 is present, but SKU-B1 is not
        if "SKU-A1" not in stdout:
            print("FAIL: User A cannot see their own tenant's item SKU-A1!")
            passed = False
        if "SKU-B1" in stdout:
            print("FAIL: User A can see Tenant B's item SKU-B1 (RLS leak)!")
            passed = False
            
    print(f"Challenge 6 Tenant SELECT: {'PASSED' if passed else 'FAILED'}\n")
    return passed

if __name__ == "__main__":
    setup_database()
    
    results = []
    results.append(test_concurrency_success())
    results.append(test_concurrency_failure())
    results.append(test_exception_handler_and_guc())
    results.append(test_guc_clearing_casting())
    results.append(test_rls_bypasses())
    results.append(test_tenant_selects())
    
    print("=== TEST SUMMARY ===")
    if all(results):
        print("ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED!")
        sys.exit(1)

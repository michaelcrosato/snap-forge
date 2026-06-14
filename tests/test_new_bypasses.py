import sys
import os

# Adjust path to import from tests.test_linters_adversarial
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.test_linters_adversarial import (
    strip_comments,
    run_check_3,
    run_check_4,
    run_check_5
)

def test_keyword_comment_bypass():
    print("--- Testing Keyword Comment Bypass (e.g., CREATE/*comment*/FUNCTION) ---")

    # Bypass A: CREATE/*comment*/FUNCTION
    # If the creator uses a comment between CREATE and FUNCTION, PostgreSQL compiles it fine,
    # but the linter uses a regex split on r"\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+"
    # which expects spaces. Since strip_comments removes /*comment*/ completely,
    # it becomes CREATEFUNCTION, so the linter skips it entirely!
    sql_a = """
    CREATE/*comment*/FUNCTION public.bypass_create_comment() RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        -- no search_path, no tenant check
        NULL;
    END;
    $$;
    """
    errors_a = run_check_3({"test_a.sql": sql_a})
    print(f"Bypass A (CREATE/*comment*/FUNCTION): Errors detected: {errors_a}")
    print(f"Bypass A succeeded? {len(errors_a) == 0} (Expected True if bypassed)")

    # Bypass B: SECURITY/*comment*/DEFINER
    # Even if CREATE FUNCTION is matched, using a comment between SECURITY and DEFINER
    # causes strip_comments to turn it into SECURITYDEFINER.
    # The linter regex checks for r"\bSECURITY\s+DEFINER\b", so it won't see it as SECURITY DEFINER
    # and will skip checking search_path/tenant.
    sql_b = """
    CREATE FUNCTION public.bypass_security_comment() RETURNS void
    LANGUAGE plpgsql
    SECURITY/*comment*/DEFINER
    AS $$
    BEGIN
        NULL;
    END;
    $$;
    """
    errors_b = run_check_3({"test_b.sql": sql_b})
    print(f"Bypass B (SECURITY/*comment*/DEFINER): Errors detected: {errors_b}")
    print(f"Bypass B succeeded? {len(errors_b) == 0} (Expected True if bypassed)")

def test_nested_definition_bypass():
    print("\n--- Testing Nested Definition / Split Bypass ---")

    # Bypass C: CREATE FUNCTION inside another function body
    # The linter splits on CREATE FUNCTION.
    # If a valid SECURITY DEFINER function contains the string literal 'CREATE FUNCTION',
    # the linter splits the outer function block into two parts.
    # The first part (the outer function definition up to the nested CREATE FUNCTION)
    # does not have a matching closing dollar-tag (since the closing tag is in the second part).
    # Thus, the outer function block match fails, and the outer function is completely skipped!
    sql_c = """
    CREATE OR REPLACE FUNCTION public.outer_unsafe_func() RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        -- This string literal will split the linter's split parser
        EXECUTE 'CREATE OR REPLACE FUNCTION public.inner_func() RETURNS void AS ...';
    END;
    $$;
    """
    errors_c = run_check_3({"test_c.sql": sql_c})
    print(f"Bypass C (Nested CREATE FUNCTION in string): Errors detected: {errors_c}")
    print(f"Bypass C succeeded? {len(errors_c) == 0} (Expected True if bypassed)")

def test_rls_comment_bypass():
    print("\n--- Testing RLS Comment Bypass ---")

    # Bypass D: CREATE/*comment*/TABLE
    # If the linter doesn't detect the table creation because of a comment,
    # it won't check for RLS on it.
    sql_d = """
    CREATE/*comment*/TABLE public.bypass_rls_table (id uuid);
    """
    errors_d = run_check_4({"test_d.sql": sql_d})
    print(f"Bypass D (CREATE/*comment*/TABLE): Errors detected: {errors_d}")
    print(f"Bypass D succeeded? {len(errors_d) == 0} (Expected True if bypassed)")

def test_audit_comment_bypass():
    print("\n--- Testing Audit Logging Comment Bypass ---")

    # Bypass E: INSERT/*comment*/INTO
    # If a mutation uses comments between keywords, the comment stripper merges them,
    # and the linter's mutation regex (which expects whitespace) fails to match it.
    sql_e = """
    CREATE OR REPLACE FUNCTION public.bypass_audit_comment() RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public, pg_temp
    AS $$
    BEGIN
        -- performs mutation but bypassed linter check
        INSERT/*comment*/INTO public.orders (id) VALUES (1);
        -- has tenant check to pass Check 3
        IF current_setting('app.current_tenant_id', true) IS NULL THEN
            RAISE EXCEPTION 'no tenant';
        END IF;
    END;
    $$;
    """
    errors_e = run_check_5({"test_e.sql": sql_e})
    print(f"Bypass E (INSERT/*comment*/INTO): Errors detected: {errors_e}")
    print(f"Bypass E succeeded? {len(errors_e) == 0} (Expected True if bypassed)")

def test_search_path_body_bypass():
    print("\n--- Testing Search Path Body Bypass ---")

    # Bypass F: SET search_path inside function body rather than definition options
    # The linter regex searches the entire func_block, so it matches the string inside the body
    # even though it's insecure and doesn't protect the function entry.
    sql_f = """
    CREATE OR REPLACE FUNCTION public.bypass_search_path_body() RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    AS $$
    BEGIN
        -- Insecure search path setting in body, but linter is fooled
        EXECUTE 'SET search_path = public, pg_temp';
        -- Tenant check
        IF auth.uid() IS NULL THEN
            RAISE EXCEPTION 'unauthorized';
        END IF;
    END;
    $$;
    """
    errors_f = run_check_3({"test_f.sql": sql_f})
    print(f"Bypass F (SET search_path in body): Errors detected: {errors_f}")
    print(f"Bypass F succeeded? {len(errors_f) == 0} (Expected True if bypassed)")

def test_tenant_check_string_bypass():
    print("\n--- Testing Tenant Check String Bypass ---")

    # Bypass G: Tenant check keyword inside a string literal
    # The linter regex searches the entire func_block (with strings) for tenant check keywords,
    # so a dummy string literal containing "tenant_id" satisfies the check.
    sql_g = """
    CREATE OR REPLACE FUNCTION public.bypass_tenant_string() RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public, pg_temp
    AS $$
    BEGIN
        -- Dummy string literal to bypass tenant check
        PERFORM 'tenant_id';
    END;
    $$;
    """
    errors_g = run_check_3({"test_g.sql": sql_g})
    print(f"Bypass G (tenant keyword in string): Errors detected: {errors_g}")
    print(f"Bypass G succeeded? {len(errors_g) == 0} (Expected True if bypassed)")

def test_table_hyphen_bypass():
    print("\n--- Testing Table Hyphen Bypass ---")

    # Bypass H: Double-quoted table name with a hyphen
    # The linter regex uses [\w]+ which doesn't match hyphens (valid in double-quoted SQL identifiers),
    # causing the table to be ignored during RLS verification.
    sql_h = """
    CREATE TABLE public."my-table" (id uuid);
    """
    errors_h = run_check_4({"test_h.sql": sql_h})
    print(f"Bypass H (hyphenated table name): Errors detected: {errors_h}")
    print(f"Bypass H succeeded? {len(errors_h) == 0} (Expected True if bypassed)")

def test_table_prefix_hyphen_bypass():
    print("\n--- Testing Table Prefix Hyphen Bypass ---")

    # Bypass I: Double-quoted table name with a hyphen sharing a prefix with an RLS-enabled table.
    # The linter matches the prefix "orders" for both tables. Because public.orders has RLS enabled,
    # the linter is fooled into thinking public."orders-archive" also has RLS enabled, resulting in no errors.
    sql_i = """
    CREATE TABLE public.orders (id uuid);
    ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
    CREATE TABLE public."orders-archive" (id uuid); -- No RLS enabled on this table!
    """
    errors_i = run_check_4({"test_i.sql": sql_i})
    print(f"Bypass I (prefix hyphen RLS bypass): Errors detected: {errors_i}")
    print(f"Bypass I succeeded? {len(errors_i) == 0} (Expected True if bypassed)")

def test_dynamic_mutation_bypass():
    print("\n--- Testing Dynamic Mutation Bypass ---")

    # Bypass J: String concatenation inside dynamic EXECUTE
    # The linter regex looks for literal mutation keywords (e.g. INSERT INTO),
    # but constructing it dynamically via string concatenation completely hides it.
    sql_j = """
    CREATE OR REPLACE FUNCTION public.bypass_dynamic_mutation() RETURNS void
    LANGUAGE plpgsql
    SECURITY DEFINER
    SET search_path = public, pg_temp
    AS $$
    BEGIN
        -- Obfuscated mutation
        EXECUTE 'INS' || 'ERT INTO public.orders (id) VALUES (1)';
        -- tenant check to pass Check 3
        IF auth.uid() IS NULL THEN
            RAISE EXCEPTION 'unauthorized';
        END IF;
    END;
    $$;
    """
    errors_j = run_check_5({"test_j.sql": sql_j})
    print(f"Bypass J (dynamic mutation concatenation): Errors detected: {errors_j}")
    print(f"Bypass J succeeded? {len(errors_j) == 0} (Expected True if bypassed)")

if __name__ == "__main__":
    test_keyword_comment_bypass()
    test_nested_definition_bypass()
    test_rls_comment_bypass()
    test_audit_comment_bypass()
    test_search_path_body_bypass()
    test_tenant_check_string_bypass()
    test_table_hyphen_bypass()
    test_table_prefix_hyphen_bypass()
    test_dynamic_mutation_bypass()

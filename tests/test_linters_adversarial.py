import re
import sys
import os

# --- IMPLEMENTATIONS FROM open_questions_resolution.md ---

def strip_comments(sql):
    out = []
    i = 0
    n = len(sql)
    stack = []
    
    while i < n:
        state = stack[-1] if stack else None
        
        if state is None:
            if sql[i:i+2] == '/*':
                i += 2
                while i < n and sql[i:i+2] != '*/':
                    i += 1
                i += 2
                out.append(" ")
            elif sql[i:i+2] == '--':
                i += 2
                while i < n and sql[i] != '\n':
                    i += 1
                out.append(" ")
            elif sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m:
                    tag = m.group(0)
                    preceding = "".join(out).rstrip()
                    if re.search(r'\bas$', preceding.lower()):
                        stack.append(("AS_DOLLAR", tag))
                    else:
                        stack.append(("NORMAL_DOLLAR", tag))
                    out.append(tag)
                    i += len(tag)
                else:
                    out.append(sql[i])
                    i += 1
            elif sql[i] == "'":
                preceding = "".join(out).rstrip()
                if re.search(r'\bas$', preceding.lower()):
                    stack.append(("AS_SINGLE_QUOTE", "'"))
                else:
                    stack.append(("NORMAL_SINGLE_QUOTE", "'"))
                out.append("'")
                i += 1
            else:
                out.append(sql[i])
                i += 1
                
        elif state[0] == "NORMAL_SINGLE_QUOTE":
            if sql[i:i+2] == "''":
                out.append("''")
                i += 2
            elif sql[i] == "'":
                out.append("'")
                stack.pop()
                i += 1
            else:
                out.append(sql[i])
                i += 1
                
        elif state[0] == "NORMAL_DOLLAR":
            tag = state[1]
            tag_len = len(tag)
            if sql[i:i+tag_len] == tag:
                out.append(tag)
                stack.pop()
                i += tag_len
            else:
                out.append(sql[i])
                i += 1
                
        elif state[0] == "AS_SINGLE_QUOTE":
            if sql[i:i+2] == "''":
                stack.append(("NESTED_SINGLE_QUOTE", "''"))
                out.append("''")
                i += 2
            elif sql[i] == "'":
                out.append("'")
                stack.pop()
                i += 1
            elif sql[i:i+2] == '/*':
                i += 2
                while i < n and sql[i:i+2] != '*/':
                    i += 1
                i += 2
                out.append(" ")
            elif sql[i:i+2] == '--':
                i += 2
                while i < n and sql[i] != '\n':
                    i += 1
                out.append(" ")
            elif sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m:
                    tag = m.group(0)
                    stack.append(("NESTED_DOLLAR", tag))
                    out.append(tag)
                    i += len(tag)
                else:
                    out.append(sql[i])
                    i += 1
            else:
                out.append(sql[i])
                i += 1
                
        elif state[0] == "NESTED_SINGLE_QUOTE":
            tag = state[1]
            if tag == "''":
                if sql[i:i+4] == "''''":
                    out.append("''''")
                    i += 4
                elif sql[i:i+2] == "''":
                    out.append("''")
                    stack.pop()
                    i += 2
                else:
                    out.append(sql[i])
                    i += 1
            else: # tag == "'"
                if sql[i:i+2] == "''":
                    out.append("''")
                    i += 2
                elif sql[i] == "'":
                    out.append("'")
                    stack.pop()
                    i += 1
                else:
                    out.append(sql[i])
                    i += 1
                    
        elif state[0] == "NESTED_DOLLAR":
            tag = state[1]
            tag_len = len(tag)
            if sql[i:i+tag_len] == tag:
                out.append(tag)
                stack.pop()
                i += tag_len
            else:
                out.append(sql[i])
                i += 1
                
        elif state[0] == "AS_DOLLAR":
            tag = state[1]
            tag_len = len(tag)
            if sql[i:i+tag_len] == tag:
                next_tag_idx = sql.find(tag, i + tag_len)
                if next_tag_idx != -1:
                    between_text = sql[i + tag_len : next_tag_idx]
                    if re.search(r'\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+', between_text, re.IGNORECASE):
                        stack.pop()
                        out.append(tag)
                        i += tag_len
                    else:
                        out.append(tag)
                        i += tag_len
                else:
                    stack.pop()
                    out.append(tag)
                    i += tag_len
            elif sql[i:i+2] == '/*':
                i += 2
                while i < n and sql[i:i+2] != '*/':
                    i += 1
                i += 2
                out.append(" ")
            elif sql[i:i+2] == '--':
                i += 2
                while i < n and sql[i] != '\n':
                    i += 1
                out.append(" ")
            elif sql[i] == "'":
                stack.append(("NESTED_SINGLE_QUOTE", "'"))
                out.append("'")
                i += 1
            elif sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m and m.group(0) != tag:
                    inner_tag = m.group(0)
                    stack.append(("NESTED_DOLLAR", inner_tag))
                    out.append(inner_tag)
                    i += len(inner_tag)
                else:
                    out.append(sql[i])
                    i += 1
            else:
                out.append(sql[i])
                i += 1
                
    return "".join(out)


def strip_string_literals(sql):
    out = []
    i = 0
    n = len(sql)
    in_single_quote = False
    dollar_tag = None
    
    while i < n:
        if dollar_tag is not None:
            tag_len = len(dollar_tag)
            if sql[i:i+tag_len] == dollar_tag:
                out.append(dollar_tag)
                i += tag_len
                dollar_tag = None
            else:
                i += 1
        elif in_single_quote:
            if sql[i:i+2] == "''":
                i += 2
            elif sql[i] == "'":
                out.append("'")
                in_single_quote = False
                i += 1
            else:
                i += 1
        else:
            if sql[i:i+2] == '/*':
                out.append(sql[i:i+2])
                i += 2
            elif sql[i:i+2] == '--':
                out.append(sql[i:i+2])
                i += 2
            elif sql[i] == "'":
                in_single_quote = True
                out.append("'")
                i += 1
            elif sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m:
                    dollar_tag = m.group(0)
                    out.append(dollar_tag)
                    i += len(dollar_tag)
                else:
                    out.append(sql[i])
                    i += 1
            else:
                out.append(sql[i])
                i += 1
    return "".join(out)


def split_migration_functions(sql):
    blocks = []
    i = 0
    n = len(sql)
    stack = []
    current_block_start = None
    
    while i < n:
        state = stack[-1] if stack else None
        
        if state is None:
            if sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m:
                    tag = m.group(0)
                    preceding = sql[:i].rstrip()
                    if preceding.lower().endswith('as') and (len(preceding) == 2 or not preceding[-3].isalnum()):
                        stack.append(("AS_DOLLAR", tag))
                    else:
                        stack.append(("NORMAL_DOLLAR", tag))
                    i += len(tag)
                    continue
            elif sql[i] == "'":
                preceding = sql[:i].rstrip()
                if preceding.lower().endswith('as') and (len(preceding) == 2 or not preceding[-3].isalnum()):
                    stack.append(("AS_SINGLE_QUOTE", "'"))
                else:
                    stack.append(("NORMAL_SINGLE_QUOTE", "'"))
                i += 1
                continue
            
            m_create = re.match(r'^CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+', sql[i:], re.IGNORECASE)
            if m_create and current_block_start is None:
                i += len(m_create.group(0))
                current_block_start = i
                continue
                
            if sql[i] == ';':
                if current_block_start is not None:
                    blocks.append(sql[current_block_start:i+1])
                    current_block_start = None
                i += 1
                continue
                
            i += 1
            
        elif state[0] == "NORMAL_SINGLE_QUOTE":
            if sql[i:i+2] == "''":
                i += 2
            elif sql[i] == "'":
                stack.pop()
                i += 1
            else:
                i += 1
                
        elif state[0] == "NORMAL_DOLLAR":
            tag = state[1]
            tag_len = len(tag)
            if sql[i:i+tag_len] == tag:
                stack.pop()
                i += tag_len
            else:
                i += 1
                
        elif state[0] == "AS_SINGLE_QUOTE":
            if sql[i:i+2] == "''":
                stack.append(("NESTED_SINGLE_QUOTE", "''"))
                i += 2
            elif sql[i] == "'":
                stack.pop()
                i += 1
            elif sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m:
                    tag = m.group(0)
                    stack.append(("NESTED_DOLLAR", tag))
                    i += len(tag)
                else:
                    i += 1
            else:
                i += 1
                
        elif state[0] == "NESTED_SINGLE_QUOTE":
            tag = state[1]
            if tag == "''":
                if sql[i:i+4] == "''''":
                    i += 4
                elif sql[i:i+2] == "''":
                    stack.pop()
                    i += 2
                else:
                    i += 1
            else: # tag == "'"
                if sql[i:i+2] == "''":
                    i += 2
                elif sql[i] == "'":
                    stack.pop()
                    i += 1
                else:
                    i += 1
                    
        elif state[0] == "NESTED_DOLLAR":
            tag = state[1]
            tag_len = len(tag)
            if sql[i:i+tag_len] == tag:
                stack.pop()
                i += tag_len
            else:
                i += 1
                
        elif state[0] == "AS_DOLLAR":
            tag = state[1]
            tag_len = len(tag)
            if sql[i:i+tag_len] == tag:
                next_tag_idx = sql.find(tag, i + tag_len)
                if next_tag_idx != -1:
                    between_text = sql[i + tag_len : next_tag_idx]
                    if re.search(r'\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+', between_text, re.IGNORECASE):
                        stack.pop()
                        i += tag_len
                    else:
                        i += tag_len
                else:
                    stack.pop()
                    i += tag_len
            elif sql[i] == "'":
                stack.append(("NESTED_SINGLE_QUOTE", "'"))
                i += 1
            elif sql[i] == '$':
                m = re.match(r'^\$[a-zA-Z_0-9]*\$', sql[i:])
                if m and m.group(0) != tag:
                    inner_tag = m.group(0)
                    stack.append(("NESTED_DOLLAR", inner_tag))
                    i += len(inner_tag)
                else:
                    i += 1
            else:
                i += 1

    return blocks


def run_check_3(files_dict):
    """
    Check 3: Unsafe SECURITY DEFINER Usage
    Returns: list of errors found
    """
    errors = []
    for filepath, content in files_dict.items():
        content_no_comments = strip_comments(content)
        parts = split_migration_functions(content_no_comments)
        
        for func_block in parts:
            name_match = re.match(r"^(?:\"?([\w]+)\"?\.)?\"?([\w]+)\"?", func_block)
            if not name_match:
                continue
            schema_name = name_match.group(1)
            func_name = name_match.group(2)
            full_name = f"{schema_name}.{func_name}" if schema_name else func_name
            
            if re.search(r"\bSECURITY\s+DEFINER\b", func_block, re.IGNORECASE):
                body_match = re.search(r"AS\s*(?:(\$[a-zA-Z_0-9]*\$)(.*)\1|'(.*)')", func_block, re.DOTALL | re.IGNORECASE)
                body = body_match.group(2) if body_match and body_match.group(1) is not None else (body_match.group(3) if body_match else "")
                body_no_strings = strip_string_literals(body or "")

                # 7. Check for search_path ONLY in options/definition block (outside the body)
                options_block = func_block
                if body_match:
                    options_block = func_block.replace(body_match.group(0), " ")
                
                has_search_path = re.search(
                    r"SET\s+search_path\s*(?:=|\bTO\b)\s*[^;]*\bpg_temp\b", 
                    options_block, 
                    re.IGNORECASE
                )
                if not has_search_path:
                    errors.append(f"Function '{full_name}' in {filepath} lacks search_path with pg_temp")
                    
                # 8. Check for tenant verification check ONLY in body_no_strings (stripped of string literals)
                has_tenant_check = re.search(
                    r"(auth\.uid|auth\.jwt|tenant_id|current_setting)", 
                    body_no_strings, 
                    re.IGNORECASE
                )
                if not has_tenant_check:
                    errors.append(f"Function '{full_name}' in {filepath} lacks tenant check")

                # Track parentheses in set_config on body_no_strings
                for m in re.finditer(r"\bset_config\s*\(", body_no_strings, re.IGNORECASE):
                    start_idx = m.end()
                    paren_count = 1
                    j = start_idx
                    args_str = ""
                    while j < len(body_no_strings) and paren_count > 0:
                        c = body_no_strings[j]
                        if c == '(':
                            paren_count += 1
                        elif c == ')':
                            paren_count -= 1
                        if paren_count > 0:
                            args_str += c
                        j += 1
                    
                    args = []
                    curr_arg = []
                    p_count = 0
                    for c in args_str:
                        if c == '(':
                            p_count += 1
                            curr_arg.append(c)
                        elif c == ')':
                            p_count -= 1
                            curr_arg.append(c)
                        elif c == ',' and p_count == 0:
                            args.append("".join(curr_arg).strip())
                            curr_arg = []
                        else:
                            curr_arg.append(c)
                    args.append("".join(curr_arg).strip())
                    
                    if len(args) < 3 or args[2].lower() not in ('true', "'true'"):
                        errors.append(f"Function '{full_name}' calls set_config without local=true: 'set_config({args_str})'")

                raw_set_matches = re.finditer(r"(?:\bBEGIN\b|\bTHEN\b|\bLOOP\b|\bELSE\b|;|^)\s*\bSET\s+(?:LOCAL\s+)?(?!search_path\b)([^;]+)", body_no_strings, re.IGNORECASE)
                for rsm in raw_set_matches:
                    errors.append(f"Function '{full_name}' contains raw SET statement: 'SET {rsm.group(1).strip()}'")
    return errors


def run_check_4(files_dict):
    """
    Check 4: Missing Row Level Security (RLS) on Created Tables
    Returns: list of errors found
    """
    errors = []
    all_created_tables = []
    all_cleaned_content = []
    
    for filepath, content in files_dict.items():
        content_no_comments = strip_comments(content)
        content_no_strings = strip_string_literals(content_no_comments)
        all_cleaned_content.append(content_no_strings)

        # Match CREATE TABLE statements, capturing optional schema quotes/hyphens and table quotes/hyphens
        created_tables = re.finditer(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:(\"?)([\w-]+)\1\.)?(\"?)([\w-]+)\3(?![\w-])",
            content_no_strings,
            re.IGNORECASE
        )
        for match in created_tables:
            schema = match.group(2)
            table = match.group(4)
            is_quoted = bool(match.group(3))
            all_created_tables.append((schema, table, is_quoted, filepath))

    combined_content = "\n".join(all_cleaned_content)

    for schema, table, is_quoted, filepath in all_created_tables:
        norm_create_schema = (schema or 'public').lower()
        
        # Match ALTER TABLE ENABLE ROW LEVEL SECURITY with optional ONLY
        alter_matches = re.finditer(
            r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:(\"?)([\w-]+)\1\.)?(\"?)([\w-]+)\3\s+(?:ENABLE|FORCE)\s+ROW\s+LEVEL\s+SECURITY",
            combined_content,
            re.IGNORECASE
        )
        has_rls = False
        for match in alter_matches:
            alter_schema = match.group(2)
            alter_table = match.group(4)
            norm_alter_schema = (alter_schema or 'public').lower()
            
            if norm_alter_schema == norm_create_schema:
                if is_quoted:
                    if alter_table == table:
                        has_rls = True
                        break
                else:
                    if alter_table.lower() == table.lower():
                        has_rls = True
                        break
                        
        if not has_rls:
            full_table_name = f"{schema}.{table}" if schema else table
            errors.append(f"Table '{full_table_name}' created in {filepath} does not have RLS enabled")
    return errors


def run_check_5(files_dict):
    """
    Check 5: Missing Audit Logging in Mutation Gateways
    Returns: list of errors found
    """
    errors = []
    for filepath, content in files_dict.items():
        content_no_comments = strip_comments(content)
        parts = split_migration_functions(content_no_comments)
        
        for func_block in parts:
            name_match = re.match(r"^(?:\"?([\w]+)\"?\.)?\"?([\w]+)\"?", func_block)
            if not name_match:
                continue
            schema_name = name_match.group(1)
            func_name = name_match.group(2)
            full_name = f"{schema_name}.{func_name}" if schema_name else func_name

            has_mutation = False
            body_match = re.search(r"AS\s*(?:(\$[a-zA-Z_0-9]*\$)(.*)\1|'(.*)')", func_block, re.DOTALL | re.IGNORECASE)
            if body_match:
                body = body_match.group(2) if body_match.group(1) is not None else body_match.group(3)
                if body is not None:
                    # Strip quotes from body for matching to avoid quoted schema/table mismatch
                    body_clean = body.replace('"', '')
                    if re.search(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|DELETE)\b", body_clean, re.IGNORECASE):
                        mutations = re.findall(r"\b(?:INSERT\s+INTO|UPDATE|DELETE\s+FROM|DELETE)\s+(?:ONLY\s+)?([\w.-]+)\b", body_clean, re.IGNORECASE)
                        for table in mutations:
                            table_lower = table.lower()
                            if "audit_logs" not in table_lower and "outbox_events" not in table_lower:
                                has_mutation = True
                                break

            if has_mutation:
                # Strip quotes from func_block for audit/outbox checks
                func_block_clean = func_block.replace('"', '')
                has_audit = re.search(r"\bINSERT\s+INTO\s+audit\.audit_logs\b", func_block_clean, re.IGNORECASE)
                has_outbox = re.search(r"\bINSERT\s+INTO\s+public\.outbox_events\b", func_block_clean, re.IGNORECASE)

                if not has_audit:
                    errors.append(f"Mutation function '{full_name}' in {filepath} does not log to audit.audit_logs")
                if not has_outbox:
                    errors.append(f"Mutation function '{full_name}' in {filepath} does not insert into public.outbox_events")
    return errors


# --- ADVERSARIAL TEST SUITE ---

def test_comment_stripper_bypasses():
    print("--- Running Comment Stripper Tests ---")
    
    # Test 1: PostgreSQL comments inside string literal (not AS block)
    # The linter should NOT strip comments inside normal single-quoted strings.
    sql_1 = "SELECT 'hello -- world' AS value;"
    stripped_1 = strip_comments(sql_1)
    print(f"Test 1: {sql_1!r} -> {stripped_1!r}")
    
    # Test 2: PostgreSQL comments inside a single-quoted AS body
    # Here preceding ends with 'as', so dollar_tag becomes "'".
    # Inside this block, '--' is encountered. It should get stripped.
    sql_2 = "CREATE FUNCTION f() RETURNS void AS 'SELECT 1; -- comment\nSELECT 2;' LANGUAGE sql;"
    stripped_2 = strip_comments(sql_2)
    print(f"Test 2: {sql_2!r} -> {stripped_2!r}")
    
    # Test 3: SQL comments in string literal inside dollar quotes
    sql_3 = "CREATE FUNCTION f() RETURNS void AS $$\nSELECT '/* not comment */';\n$$ LANGUAGE sql;"
    stripped_3 = strip_comments(sql_3)
    print(f"Test 3: {sql_3!r} -> {stripped_3!r}")
    
    # Test 4: Nested dollar quotes of same tag bypass
    # An inner $$ terminates the outer $$ parser in strip_comments?
    # Wait, in strip_comments, if dollar_tag is $$ and it sees $$, it terminates.
    sql_4 = "CREATE FUNCTION f() RETURNS void AS $$\nBEGIN\n  EXECUTE $$ SELECT 1; $$;\nEND;\n$$ SECURITY DEFINER;"
    stripped_4 = strip_comments(sql_4)
    print(f"Test 4: {sql_4!r} -> {stripped_4!r}")

    # Test 5: Escaped string literal with comment pattern inside AS '...'
    sql_5 = "CREATE FUNCTION f() RETURNS void AS 'SELECT ''hello -- world'';' LANGUAGE sql;"
    stripped_5 = strip_comments(sql_5)
    print(f"Test 5: {sql_5!r} -> {stripped_5!r}")

    # Test 6: Escaped block comment pattern inside AS '...'
    sql_6 = "CREATE FUNCTION f() RETURNS void AS 'SELECT ''hello /* world */'';' LANGUAGE sql;"
    stripped_6 = strip_comments(sql_6)
    print(f"Test 6: {sql_6!r} -> {stripped_6!r}")



def test_check_3_definer_bypasses():
    print("\n--- Running Check 3 (SECURITY DEFINER) Tests ---")
    
    # Bypass 3.1: Nested same-tag dollar quotes
    # The parser matches up to the first closing $$ inside the body, missing SECURITY DEFINER at the end.
    sql_b1 = """
    CREATE OR REPLACE FUNCTION public.bypass_nested() RETURNS void AS $$
    BEGIN
        EXECUTE $$
            SELECT 1;
        $$;
    END;
    $$ SECURITY DEFINER;
    """
    errors_b1 = run_check_3({"test.sql": sql_b1})
    print(f"Bypass 3.1 (Nested same-tag dollar quotes): Detected errors? {errors_b1} (Expected empty list if bypassed)")
    
    # Bypass 3.2: SQL-standard body (PostgreSQL 14+) without AS
    sql_b2 = """
    CREATE FUNCTION public.bypass_no_as() RETURNS int
    LANGUAGE sql
    SECURITY DEFINER
    RETURN 42;
    """
    errors_b2 = run_check_3({"test.sql": sql_b2})
    print(f"Bypass 3.2 (SQL-standard body without AS): Detected errors? {errors_b2} (Expected empty list if bypassed)")

    # Bypass 3.3: Case-insensitive / comment space after AS
    # E.g. AS/*comment*/'...'
    sql_b3 = """
    CREATE FUNCTION public.bypass_comment_as() RETURNS void
    AS/*comment*/'
    BEGIN
        SELECT 1;
    END;
    ' SECURITY DEFINER;
    """
    errors_b3 = run_check_3({"test.sql": sql_b3})
    print(f"Bypass 3.3 (AS with comment separator): Detected errors? {errors_b3} (Expected empty list if bypassed)")


def test_check_4_rls_bypasses():
    print("\n--- Running Check 4 (RLS) Tests ---")
    
    # Bypass 4.1: Enable RLS with ONLY keyword
    # E.g. ALTER TABLE ONLY my_table ENABLE ROW LEVEL SECURITY;
    # This is valid syntax but fails Check 4 (false positive).
    sql_b1 = """
    CREATE TABLE public.only_table (id uuid);
    ALTER TABLE ONLY public.only_table ENABLE ROW LEVEL SECURITY;
    """
    errors_b1 = run_check_4({"test.sql": sql_b1})
    print(f"Bypass 4.1 (ALTER TABLE ONLY): Detected errors? {errors_b1} (Expected error since ONLY isn't supported by linter)")

    # Bypass 4.2: Schema prefix matching issue / multiple tables
    # RLS enabled on public.orders, but not archive.orders.
    # The linter matches RLS from public.orders to archive.orders because it does a global search.
    sql_b2 = """
    CREATE TABLE public.orders (id uuid);
    CREATE TABLE archive.orders (id uuid);
    ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
    """
    errors_b2 = run_check_4({"test.sql": sql_b2})
    print(f"Bypass 4.2 (Global RLS match namespace bypass): Detected errors? {errors_b2} (Expected ['Table archive.orders ... does not have RLS enabled'], but if empty, it's bypassed)")


def test_check_5_audit_logging_bypasses():
    print("\n--- Running Check 5 (Audit Logging) Tests ---")
    
    # Bypass 5.1: Nested same-tag dollar quotes masking mutations
    # A mutation is placed inside a function but after the first $$; the linter doesn't see it.
    sql_b1 = """
    CREATE OR REPLACE FUNCTION public.bypass_audit() RETURNS void AS $$
    BEGIN
        EXECUTE $$ SELECT 1; $$;
        INSERT INTO public.orders (id) VALUES (1);
    END;
    $$ SECURITY DEFINER;
    """
    errors_b1 = run_check_5({"test.sql": sql_b1})
    print(f"Bypass 5.1 (Nested same-tag dollar quotes masking mutations): Detected errors? {errors_b1} (Expected empty if bypassed, otherwise error due to missing audit/outbox)")


if __name__ == "__main__":
    test_comment_stripper_bypasses()
    test_check_3_definer_bypasses()
    test_check_4_rls_bypasses()
    test_check_5_audit_logging_bypasses()

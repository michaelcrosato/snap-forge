# Open Questions Resolution and Security Architecture Gates

This document provides resolutions for the open questions and deferred decisions tracked in `docs/open-questions.md`, based on architectural research and compliance-gating requirements for snap-forge.

---

## 1. Resolution of Open Questions (Q1 to Q10)

### Q1: Tekmetric API Access, Endpoint Coverage, and Approval Timeline
*   **Onboarding & Partnership Requirements**: Accessing the Tekmetric API (`api.tekmetric.com`) requires registering a developer/partner profile under a registered business entity. A partnership agreement must be signed, subject to partner fees and developer verification. Sandbox access is granted in 1–2 weeks, but production key approval and directory listing can take several weeks.
*   **Authentication Model**: The API uses standard B2B OAuth2 Client Credentials Flow.
*   **Rate Limits**: The API is capped at `600 requests/minute` (10 req/sec) per shop tenant.
*   **Operational Caching & Read Projection**: To prevent rate limit exhaustion and eliminate UI latency (which ranges from 200ms to 1000ms for direct external API calls), snap-forge will use Supabase as an operational read projection (caching layer). Reads are served locally from Supabase; mutations are sent synchronously API-first to Tekmetric. The local projection is updated immediately upon API success.
*   **State Synchronization**: Real-time state sync is handled by custom webhooks registered in the Tekmetric dashboard under **Settings > Integrations > Custom Webhooks**. Tekmetric sends POST requests for Appointment and Repair Order (RO) changes. To handle webhook delivery failures or gaps, snap-forge will implement scheduled background reconciliation crons (delta syncs).

### Q2: Workflow Engine License Fit by Deployment Model
*   **Resolution**: 
    *   For **single-tenant client-owned/internal systems**, **n8n** is acceptable.
    *   For **multi-tenant SaaS** or **commercial embedded** systems, n8n and Windmill must be avoided due to SUL and AGPLv3 licensing constraints.
    *   **Trigger.dev** (Apache-2.0, code-first) is selected as the default backend workflow engine for background jobs and orchestrations.
    *   If a customer-facing visual visual editor is required, **Activepieces (MIT Core)** will be embedded, with the caveat that white-labeling and tenant management features (living under `packages/ee`) will require a commercial license.
*   **Comparison Matrix**:
    *   See [Section 2: Workflow Orchestrator Comparison](#2-workflow-orchestrator-comparison) for details.

### Q3: Metrc Validation Timelines by Target State
*   **Compliance Onboarding**: Metrc is state-regulated seed-to-sale cannabis tracking. A developer must complete mandatory vendor training, have a company officer sign the Metrc API User Agreement, obtain a Sandbox key, pass a Sandbox **Capability Assessment** (demonstrating compliant requests for mock inventory, transfers, and sales), and receive state regulatory approval.
*   **Timelines**: Transitioning from Sandbox Capability Assessment to production key approval takes **4 to 12 weeks** (1 to 3 months) due to state-specific administrative backlogs (e.g., CA/OR faster at 4-6 weeks, NY/OK slower at 8-12 weeks).
*   **Resolution**: Due to these legal and compliance delays, cannabis retail is deferred. Auto repair (Tekmetric) is the designated first vertical.

### Q4: PL/pgSQL/RPC Gateway Ergonomics and Performance
*   **Resolution**: Small, highly constrained PL/pgSQL functions are chosen for the Action Gateway because they enforce absolute transactional boundaries, low latency, and direct database-enforced grants. Business validations and authorization checks are executed atomically inside the transaction. TypeScript will act as the high-level orchestrator, coordinating the API payload and initiating the gateway RPC call, but the database remains the final arbiter of security and state constraints.

### Q4a: Gateway Invariant Under a Real Side-Effecting Write
*   **Resolution**: The invariant "nothing writes except through the gateway" is enforced by revoking direct table writes from the runtime user roles (`authenticated`, `anon`, `public`).
*   **Side Effects Decoupling**: Rather than invoking HTTP webhooks or external API calls inside the database transaction (which causes connection blocking and long-running locks), the gateway function writes to a transactionally consistent outbox (`public.outbox_events`). An external outbox worker (e.g., a Trigger.dev job or custom worker) polls or listens to this table via PostgreSQL logical replication, executing external notifications and mutations asynchronously.

### Q5: Supavisor/Session Variable Safety
*   **Resolution**: Custom session variables are highly unsafe in transaction pooling mode due to connection reuse.
*   **Recommendation**: Use native Supabase/PostgREST JWT claims (which are set via `SET LOCAL` on every transaction) or explicit transaction-local GUC settings with `is_local = true`.
*   *Detailed analysis is provided in [Section 3: Supavisor Transaction Pooling and Variable Leakage](#3-supavisor-transaction-pooling-and-variable-leakage).*

### Q6: CI/Static Checks for AI-Authored Block Safety
*   **Resolution**: Maintain a strict set of 5 core CI security checks (direct writes, service_role usage, unsafe SECURITY DEFINER, missing RLS, and missing audit logging) to prevent AI-authored code from bypassing security policies.
*   *Rules and script implementations are detailed in [Section 4: CI/Static Gates and Security Checks](#4-cistatic-gates-and-security-checks).*

### Q7: First Block Workflow Scope
*   **Resolution**: The first block workflow will focus strictly on the internal/staff path: `QR/bin scan -> gateway-approved inventory adjustment -> system-of-record update -> staff/salesperson SMS notification`. Customer-facing messaging is deferred to avoid additional approval gate overhead and Twilio A2P 10DLC registration delays.

### Q8: AI Runtime Boundary (D6)
*   **Resolution**: AI is restricted to build-time code generation and human-in-the-loop runtime assistance. Unattended runtime execution of actions by AI agents is strictly prohibited. AI blocks can propose inputs or draft workflow logic, but they must execute behind the Action Gateway, which enforces hard tenancy, validation, and manual approval thresholds.

### Q9: MCP and Tooling Boundary (D7)
*   **Resolution**: Model Context Protocol (MCP) servers are developer-time utilities only. They must not be imported, embedded, or set as dependencies in the production runtime environments. All production connectors must interact through standard SDKs or native HTTPS integrations.

### Q10: AI-Authored-Code Governance (D8)
*   **Resolution**: All AI-authored code blocks are subjected to automated CI syntax linting, static security analysis (Semgrep + SQL checkers), Vitest/pgTAP test coverage, and human peer review before merging into `main`. Direct hot-patching of code in production is blocked.

---

## 2. Workflow Orchestrator Comparison

Below is a detailed comparison of workflow orchestrators for SaaS, self-hostability, and embedding:

| Orchestrator | Primary License | Self-Hosting | SaaS / Embedding (Free) | Commercial Implications / Risks |
| :--- | :--- | :--- | :--- | :--- |
| **n8n** | Sustainable Use (SUL) | Free (internal use only) | ❌ Prohibited | If n8n is wrapped and offered as a paid service to third parties, it violates the SUL and requires commercial licensing. |
| **Activepieces** | MIT (Core) | Free | ✅ Permissive (Core) | Core features are free to wrap. However, advanced Enterprise Edition (EE) features (e.g., white-labeling, audit logs, multi-tenant UI) require a paid commercial license. |
| **Windmill** | AGPLv3 | Free | ⚠️ Copyleft Risk | Under AGPLv3, if you wrap or modify Windmill as a hosted service, you must open-source your entire proprietary SaaS wrapper unless you purchase a commercial license. |
| **Trigger.dev** | Apache-2.0 | Free | ✅ Permissive | Fully permissive. Highly recommended for code-first background tasks and orchestrations. Contains no client-facing drag-and-drop editor. |
| **Node-RED** | Apache-2.0 | Free | ✅ Permissive | Permissive, visual tool, but uses an older tech stack and is less optimized for modern cloud multi-tenancy compared to Trigger.dev. |

---

## 3. Supavisor Transaction Pooling and Variable Leakage

### The Mechanics of Transaction Pooling vs. Session State
PostgreSQL connection poolers (like Supavisor or PgBouncer) optimize database connection limits by multiplexing client connections:
*   **Session Pooling**: A client is assigned a physical database connection for their entire session. While session-local variables are safe from other users during the connection, the pooler must execute `RESET ALL` or `DISCARD ALL` upon client disconnect to clean up state before the connection is assigned to a new user.
*   **Transaction Pooling**: A client is assigned a physical database connection *only* for the duration of a single transaction. Once the transaction terminates via `COMMIT` or `ROLLBACK`, the connection is immediately returned to the pool.
*   **The Reset Dilemma**: Executing `RESET ALL` or `DISCARD ALL` after every transaction in transaction pooling adds a database round-trip, doubling the latency of short transactions. Consequently, **Supavisor and PgBouncer do not reset session variables between transactions** in transaction pooling mode.

### The Leakage Scenario (Step-by-Step)
1.  **Tenant A** starts a transaction through Supavisor.
2.  Tenant A's code sets a custom session-local variable:
    ```sql
    SET app.current_tenant_id = 'tenant-1111-uuid';
    ```
3.  PostgreSQL stores this key-value pair in the physical connection's GUC (Grand Unified Configuration) dictionary.
4.  Tenant A's transaction completes and commits. The connection is released to the pool. **The connection GUC dictionary still retains `app.current_tenant_id = 'tenant-1111-uuid'`.**
5.  **Tenant B** begins a transaction and is assigned the same physical connection.
6.  Tenant B executes a query without explicitly initializing the tenant context.
7.  The RLS policy on the target table reads the session variable:
    ```sql
    CREATE POLICY tenant_isolation ON operational_table
        AS RESTRICTIVE
        USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    ```
8.  Because the variable was not reset, `current_setting('app.current_tenant_id')` returns `'tenant-1111-uuid'`.
9.  **Tenant B reads/mutates Tenant A's private data.**

### Why `SET LOCAL` is Insufficient
Using `SET LOCAL app.current_tenant_id = '...'` (or `set_config('...', '...', true)`) ensures the setting is scoped strictly to the current transaction. PostgreSQL automatically wipes these settings upon transaction commit or abort.
However, this relies entirely on developer discipline. If a developer or AI generator omits the `LOCAL` keyword or passes `false` to `set_config()`, the variable leaks silently because PostgreSQL does not raise an error.

### Recommendations for Safe Multi-Tenancy
1.  **Prefer JWT/Policy-Based Tenant Resolution (PostgREST model)**:
    PostgREST parses the incoming JWT and automatically executes a transaction-local setting for every transaction:
    ```sql
    SET LOCAL "request.jwt.claims" = '...json_string...';
    ```
    This is guaranteed to be set or cleared at transaction boundaries, eliminating the leakage risk. Write RLS policies using:
    ```sql
    CREATE POLICY tenant_isolation ON operational_table
        FOR ALL
        USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id')::uuid);
    ```
2.  **Enforce Transaction-Local Settings via API Gateway**:
    Always enforce the `is_local = true` flag when setting GUC contexts within PL/pgSQL functions:
    ```sql
    PERFORM set_config('gateway.current_tenant_id', v_tenant_id::text, true);
    ```
3.  **Strict Database Grants**:
    Revoke direct table mutations (`INSERT`, `UPDATE`, `DELETE`) from runtime roles. Users can only select data through PostgREST (filtered by JWT-based RLS) and must perform all writes via the Action Gateway (which safely manages the transaction-local context).

---

## 4. CI/Static Gates and Security Checks

To safeguard the codebase from unsafe AI-authored blocks or developer oversights, the CI/CD pipeline enforces the following five checks:

### Check 1: Direct Operational Table Writes
*   **Threat**: Code bypassing the action gateway and writing directly to operational tables.
*   **Semgrep Rule (`supabase-direct-write.yaml`)**:
```yaml
rules:
  - id: supabase-direct-table-write
    metadata:
      category: security
      description: Detects direct writes to operational tables bypassing the action gateway.
    languages:
      - typescript
      - javascript
    patterns:
      - pattern-either:
          - pattern: $CLIENT.from(...).insert(...)
          - pattern: $CLIENT.from(...).update(...)
          - pattern: $CLIENT.from(...).delete(...)
          - pattern: $CLIENT.from(...).upsert(...)
      - pattern-not:
          - pattern: $CLIENT.from("audit_logs").insert(...)
          - pattern: $CLIENT.from("system_telemetry").insert(...)
    message: |
      CRITICAL: Direct database mutation detected. Runtime blocks and client code are restricted from direct writes.
      All mutations must go through the Action Gateway RPCs (e.g., `$CLIENT.rpc('adjust_quantity', ...)`).
    severity: ERROR
```

### Check 2: Runtime `service_role` Usage
*   **Threat**: Code instantiating a client with the superuser `service_role` key, which bypasses RLS.
*   **Semgrep Rule (`supabase-service-role-runtime.yaml`)**:
```yaml
rules:
  - id: supabase-service-role-runtime
    metadata:
      category: security
      description: Prevents runtime blocks from using the superuser service_role key.
    languages:
      - typescript
      - javascript
    patterns:
      - pattern-either:
          - pattern: process.env.SUPABASE_SERVICE_ROLE_KEY
          - pattern: Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")
          - pattern: createClient($URL, process.env.SUPABASE_SERVICE_ROLE_KEY, ...)
          - pattern: createClient($URL, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY"), ...)
          - pattern: getServiceRoleClient()
    message: |
      CRITICAL: Service role key usage detected. The service_role key bypasses RLS and must not be used in runtime blocks.
      Use user-scoped credentials or the Action Gateway.
    severity: ERROR
```

### Check 3: Unsafe `SECURITY DEFINER` Usage
*   **Threat**: `SECURITY DEFINER` functions executing with creator privileges but lacking a fixed `search_path` (making them vulnerable to hijacking) or failing to check tenant context.
*   **Python Static Checker (`check_security_definer.py`)**:
```python
import re
import sys
import glob

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

def check_sql_files():
    errors = 0
    # Scan all migration files
    for filepath in glob.glob("supabase/migrations/*.sql"):
        with open(filepath, 'r') as f:
            content = f.read()

        # Strip SQL comments ignoring comments inside string literals before parsing
        content_no_comments = strip_comments(content)

        # Split the content on CREATE FUNCTION / CREATE OR REPLACE FUNCTION blocks
        parts = split_migration_functions(content_no_comments)
        
        # The first part is the text before the first function, skip it
        for func_block in parts:
            # Handle double-quoted camelcase function names: FUNCTION\s+(?:\"?([\w]+)\"?\.)?\"?(\w+)\"?
            name_match = re.match(r"^(?:\"?([\w]+)\"?\.)?\"?([\w]+)\"?", func_block)
            if not name_match:
                continue
            schema_name = name_match.group(1)
            func_name = name_match.group(2)
            full_name = f"{schema_name}.{func_name}" if schema_name else func_name
            
            # Check if this function is defined with SECURITY DEFINER
            if re.search(r"\bSECURITY\s+DEFINER\b", func_block, re.IGNORECASE):
                body_match = re.search(r"AS\s*(?:(\$[a-zA-Z_0-9]*\$)(.*)\1|'(.*)')", func_block, re.DOTALL | re.IGNORECASE)
                body = body_match.group(2) if body_match and body_match.group(1) is not None else (body_match.group(3) if body_match else "")
                body_no_strings = strip_string_literals(body or "")

                # 1. Check for search_path ONLY in options/definition block (outside the body)
                options_block = func_block
                if body_match:
                    options_block = func_block.replace(body_match.group(0), " ")
                
                has_search_path = re.search(
                    r"SET\s+search_path\s*(?:=|\bTO\b)\s*[^;]*\bpg_temp\b", 
                    options_block, 
                    re.IGNORECASE
                )
                if not has_search_path:
                    print(f"[-] ERROR: Function '{full_name}' in {filepath} is SECURITY DEFINER but lacks 'SET search_path = public, pg_temp'.")
                    errors += 1
                    
                # 2. Check for tenant verification checks ONLY in body_no_strings
                has_tenant_check = re.search(
                    r"(auth\.uid|auth\.jwt|tenant_id|current_setting)", 
                    body_no_strings, 
                    re.IGNORECASE
                )
                if not has_tenant_check:
                    print(f"[-] WARNING: Function '{full_name}' in {filepath} is SECURITY DEFINER but no tenant check (tenant_id, auth.uid, auth.jwt) was detected in its context.")
                    errors += 1

                # 3. Validate that any set_config calls inside the function body set the third parameter to true
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
                        print(f"[-] ERROR: Function '{full_name}' in {filepath} calls set_config without explicitly setting transaction-local to true: 'set_config({args_str})'.")
                        errors += 1

                # 4. Scan for raw SET or SET LOCAL statements (excluding SET search_path)
                raw_set_matches = re.finditer(r"(?:\bBEGIN\b|\bTHEN\b|\bLOOP\b|\bELSE\b|;|^)\s*\bSET\s+(?:LOCAL\s+)?(?!search_path\b)([^;]+)", body_no_strings, re.IGNORECASE)
                for rsm in raw_set_matches:
                    print(f"[-] ERROR: Function '{full_name}' in {filepath} contains raw SET statement: 'SET {rsm.group(1).strip()}'.")
                    errors += 1

    if errors > 0:
        print(f"\n[!] Security checks failed with {errors} errors.")
        sys.exit(1)
    else:
        print("[+] All SECURITY DEFINER functions comply with search_path and tenant checks.")
        sys.exit(0)

if __name__ == "__main__":
    check_sql_files()
```

### Check 4: Missing Row Level Security (RLS) on Created Tables
*   **Threat**: Tables created without RLS enabled, exposing data to the public API by default.
*   **Python Static Checker (`check_rls.py`)**:
```python
import re
import sys
import glob

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

def check_rls_compliance():
    errors = 0
    all_created_tables = []
    all_cleaned_content = []
    
    for filepath in glob.glob("supabase/migrations/*.sql"):
        with open(filepath, 'r') as f:
            content = f.read()

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
            print(f"[-] ERROR: Table '{full_table_name}' created in {filepath} does not have ROW LEVEL SECURITY enabled.")
            errors += 1

    if errors > 0:
        print(f"\n[!] RLS checks failed with {errors} errors.")
        sys.exit(1)
    else:
        print("[+] All tables have Row Level Security enabled.")
        sys.exit(0)

if __name__ == "__main__":
    check_rls_compliance()
```

### Check 5: Missing Audit Logging in Mutation Gateways
*   **Threat**: Gateway action functions performing database mutations without logging them to `audit_logs` or writing to `outbox_events` within the same transaction.
*   **Python Static Checker (`check_audit_logging.py`)**:
```python
import re
import sys
import glob

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

def check_audit_logging():
    errors = 0
    for filepath in glob.glob("supabase/migrations/*.sql"):
        with open(filepath, 'r') as f:
            content = f.read()

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
                    print(f"[-] ERROR: Mutation function '{full_name}' in {filepath} does not log to audit.audit_logs.")
                    errors += 1
                if not has_outbox:
                    print(f"[-] ERROR: Mutation function '{full_name}' in {filepath} does not insert into public.outbox_events.")
                    errors += 1

    if errors > 0:
        print(f"\n[!] Audit logging checks failed with {errors} errors.")
        sys.exit(1)
    else:
        print("[+] All mutation functions have audit logging and outbox inserts configured.")
        sys.exit(0)

if __name__ == "__main__":
    check_audit_logging()
```


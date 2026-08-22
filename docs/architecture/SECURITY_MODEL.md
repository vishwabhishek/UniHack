# UniHack Simplifi PIM — Security & Threat Model

## 1. Ingestion Security & SSRF Defenses

Evidence ingestion handles external manufacturer links and files. To prevent Server-Side Request Forgery (SSRF) and content injection:

### SSRF Protection Policy
1. **Domain Allowlisting**: Only official manufacturer domains (e.g. `*.sharkbite.com`, `*.nibco.com`, `*.frigidaire.com`, `*.diablotools.com`, `*.electrolux.com`, `*.milwaukeetool.com`, `*.dewalt.com`) are permitted.
2. **Blocked Targets**:
   - `localhost`, `127.0.0.1`, `0.0.0.0`, `::1`
   - RFC 1918 Private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
   - Link-Local & Cloud Metadata IPs (`169.254.0.0/16`, AWS EC2 `169.254.169.254`)
   - Unique Local IPv6 (`fc00::/7`), Link-Local IPv6 (`fe80::/10`)
3. **DNS Rebinding Defense**: Hostnames are resolved before ingestion; if resolved IP belongs to any restricted range, ingestion is aborted immediately.
4. **Scheme Enforcement**: Only `http://` and `https://` are permitted. `file://`, `ftp://`, `gopher://` are rejected.
5. **Content Size & MIME Type Limits**: Maximum source file size is strictly capped at 10 MB (`MAX_SOURCE_FILE_SIZE_BYTES = 10 * 1024 * 1024`). Permitted MIME types are `text/html`, `application/pdf`, and `text/plain`.

---

## 2. Authentication & Authorization (RBAC)

### Role Permission Matrix
| Role | Capabilities | Forbidden Actions |
|---|---|---|
| `viewer` | Read-only access to catalog, inspector, export, stats, audit history | Cannot edit fields, approve products, or launch jobs |
| `specialist` | Register evidence, run batch enrichment, edit candidate fields, run benchmark | Cannot approve/promote products to `Validated` or delete data |
| `reviewer` | Full review actions: approve, reject, mark unknown, promote to `Validated` | Cannot manage users |
| `admin` | Full system control: user management, credentials, configuration | None |

### Token Security & Session Management
- **Short-Lived Access Tokens**: JWT tokens expire in 60 minutes (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60`).
- **Token Versioning & Instant Revocation**: Every user record has a `token_version` counter in the database. When a user requests session logout or security resets via `POST /api/auth/revoke-tokens`, `token_version` increments in SQLite, immediately invalidating all outstanding JWTs.
- **Production Secret Guard**: If `ENVIRONMENT=production`, the application validates that `JWT_SECRET` is not the default demo secret and has at least 32 characters of entropy. Insecure setups abort startup immediately.
- **Brute-Force Rate Limiting**: Exponential login throttling returns `429 Too Many Requests` with a standard `Retry-After` header.

---

## 3. Data Integrity & Immutable Audit Trail

- **Immutable Audit Repository**: All field-level approvals, edits, rejections, and export downloads are written to the `audit_logs` table with timestamp, `user_email`, `role`, `action`, before/after JSON diffs, and `request_id`.
- **Spreadsheet Formula Injection Defense (CWE-1236)**: Cells starting with formula characters (`=`, `+`, `-`, `@`, `\t`, `|`) are escaped with a leading single quote (`'`) upon CSV export to prevent remote code execution in spreadsheet applications.
- **SHA-256 Export Integrity**: Every downloaded CSV/Excel export generates a SHA-256 checksum stored in `export_history` and returned in the `X-Export-Checksum` header.

# UniHack Simplifi PIM — API Contract & Specification

## 1. Authentication & Headers

Every request to secured endpoints must provide:
```http
Authorization: Bearer <JWT_TOKEN>
X-Request-ID: <OPTIONAL_CLIENT_CORRELATION_ID>
```

Responses always return:
```http
X-Request-ID: req_xxxxxxxxxxxx
```

---

## 2. Standard Error Response Envelope

All API errors (4xx, 5xx) strictly follow the standardized envelope:

```json
{
  "detail": "Descriptive human-readable error or list of field errors",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED | UNAUTHORIZED | FORBIDDEN | NOT_FOUND | VALIDATION_ERROR | INTERNAL_SERVER_ERROR",
    "message": "Human-readable explanation of error",
    "request_id": "req_81918fd72134",
    "status_code": 429,
    "details": {}
  }
}
```

---

## 3. Endpoints Matrix

### System & Health Probes
| Method | Path | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/health` | Public | Liveness probe returning record tallies and health status |
| `GET` | `/api/ready` | Public | Readiness probe checking SQLite DB connectivity |
| `GET` | `/api/version` | Public | Version info, schema versions, and active model config |

### Authentication & Users
| Method | Path | Required Role | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | Public | Authenticate user credentials, returns JWT with role and user profile |
| `POST` | `/api/auth/register` | Public | Register a new user account |
| `GET` | `/api/auth/me` | Authenticated | Retrieve current user profile and role |
| `POST` | `/api/auth/revoke-tokens` | Authenticated | Increment token version, revoking all active JWT sessions for caller |

### Catalog & Search
| Method | Path | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/products` | `viewer` | Paginated product search with fuzzy filters and status filters |
| `GET` | `/api/products/{id}` | `viewer` | Retrieve single product details with 252 delivery mapping |
| `GET` | `/api/stats` | `viewer` | Aggregated catalog counts, mean confidence, and KPI totals |
| `GET` | `/api/filters` | `viewer` | Facet lists for statuses, departments, and brands |

### Persistent Asynchronous Jobs
| Method | Path | Required Role | Description |
|---|---|---|---|
| `POST` | `/api/jobs/enrichment` | `specialist` | Submit batch enrichment job with `idempotency_key` and bounded concurrency |
| `GET` | `/api/jobs/{job_id}` | `viewer` | Retrieve real-time progress counts and status of a job |
| `GET` | `/api/jobs/{job_id}/events`| `viewer` | Granular per-product lifecycle event stream |
| `POST` | `/api/jobs/{job_id}/cancel`| `specialist` | Request cancellation of an active running job |
| `GET` | `/api/jobs` | `viewer` | List historical and active batch enrichment jobs |

### Evidence & Source Registry
| Method | Path | Required Role | Description |
|---|---|---|---|
| `POST` | `/api/evidence/register` | `specialist` | Register official manufacturer source; validates SSRF and chunks text |
| `GET` | `/api/evidence/registry` | `viewer` | List all registered manufacturer sources |
| `GET` | `/api/evidence/chunks/{src_id}`| `viewer` | Retrieve structured evidence chunks for a source |
| `POST` | `/api/evidence/enrich/{mpn}` | `specialist` | Trigger on-demand evidence extraction and LOV validation for MPN |

### HITL Review & Curation
| Method | Path | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/review/queue` | `viewer` | Fetch flagged and low-confidence items requiring human review |
| `GET` | `/api/review/{id}/fields`| `viewer` | Retrieve field-level candidate facts, citations, and status |
| `POST` | `/api/review/{id}/field-action`| `specialist` (edit) / `reviewer` (approve, reject, mark_unknown) | Apply field-level curation and record immutable audit |
| `POST` | `/api/review/{id}/promote-to-validated` | `reviewer` | Promote product to `Validated`; rejects if high-risk fields unresolved |
| `POST` | `/api/review/{id}/approve` | `reviewer` | Approve product record for production delivery |
| `POST` | `/api/review/{id}/reject` | `reviewer` | Flag or reject product with feedback notes |
| `GET` | `/api/review/{id}/audit-trail` | `viewer` | Get complete immutable audit history for product |

### 252-Column Delivery Export
| Method | Path | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/export/csv` | `viewer` | Download 252-column CSV with formula injection defense & audit logging |
| `GET` | `/api/export/xlsx` | `viewer` | Download 252-column Excel (.xlsx) workbook |
| `GET` | `/api/export/columns` | `viewer` | Get all 252 column definitions, numbers, and functional groupings |

### Quality Benchmark & Evaluation
| Method | Path | Required Role | Description |
|---|---|---|---|
| `GET` | `/api/benchmark/results`| `viewer` | Fetch evaluation metrics against ground truth dataset |
| `POST` | `/api/benchmark/run` | `specialist` | Trigger full benchmark evaluation across 252 columns |

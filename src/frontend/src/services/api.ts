import {
  CatalogStats,
  FilterOptions,
  ProductListResponse,
  ProductDetail,
  TransformRequest,
  TransformResponse,
  PlaygroundPreset,
  ReviewQueueResponse,
  BenchmarkReport,
  AuthResponse,
  User
} from '../types';

const API_BASE = '/api';

// ----------------------------------------------------------------------------
// Cookie Management Helpers
// ----------------------------------------------------------------------------
export function setCookie(name: string, value: string, days: number = 7) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

export function getCookie(name: string): string | null {
  const nameEQ = encodeURIComponent(name) + '=';
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) {
      return decodeURIComponent(c.substring(nameEQ.length, c.length));
    }
  }
  return null;
}

export function deleteCookie(name: string) {
  document.cookie = `${encodeURIComponent(name)}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

// The server owns the session in an HttpOnly cookie. Do not persist JWTs in
// browser-readable storage where an XSS vulnerability could exfiltrate them.
let authToken: string | null = null;

export function setAuthToken(token: string | null, userProfile?: User | null) {
  void token; // JWT is returned only for backward-compatible API clients.
  authToken = null;
  if (userProfile) {
    sessionStorage.setItem('unilog_user_profile', JSON.stringify(userProfile));
  } else {
    sessionStorage.removeItem('unilog_user_profile');
  }
}

export function getAuthToken(): string | null {
  return authToken;
}

export function getSavedUserProfile(): User | null {
  try {
    const raw = sessionStorage.getItem('unilog_user_profile');
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Failed to parse cached user profile:', e);
  }
  return null;
}

function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  const csrfToken = getCookie('unilog_csrf_token');
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }
  return headers;
}

// ============================================================================
// Authentication & User Management Endpoints
// ============================================================================

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to login');
  }
  const data: AuthResponse = await res.json();
  setAuthToken(data.token, data.user);
  return data;
}

export async function registerUser(email: string, password: string, name: string, role: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name, role })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errorData.detail || 'Failed to register account');
  }
  const data: AuthResponse = await res.json();
  setAuthToken(data.token, data.user);
  return data;
}

export async function getCurrentUserProfile(): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch current user: ${res.statusText}`);
  return res.json();
}

export async function logoutUser(): Promise<void> {
  const res = await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to log out: ${res.statusText}`);
}

// ============================================================================
// Catalog & Stats Endpoints
// ============================================================================

export async function fetchStats(): Promise<CatalogStats> {
  const res = await fetch(`${API_BASE}/stats`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
  return res.json();
}

export async function fetchFilters(): Promise<FilterOptions> {
  const res = await fetch(`${API_BASE}/filters`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch filters: ${res.statusText}`);
  return res.json();
}

export interface ProductQueryParams {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;
  category?: string;
  brand?: string;
  min_confidence?: number;
  max_confidence?: number;
  sort_by?: string;
  sort_dir?: string;
}

export async function fetchProducts(params: ProductQueryParams = {}): Promise<ProductListResponse> {
  const query = new URLSearchParams();
  if (params.page) query.append('page', params.page.toString());
  if (params.limit) query.append('limit', params.limit.toString());
  if (params.search) query.append('search', params.search);
  if (params.status && params.status !== 'All') query.append('status', params.status);
  if (params.category && params.category !== 'All') query.append('category', params.category);
  if (params.brand && params.brand !== 'All') query.append('brand', params.brand);
  if (params.min_confidence !== undefined) query.append('min_confidence', params.min_confidence.toString());
  if (params.max_confidence !== undefined) query.append('max_confidence', params.max_confidence.toString());
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.sort_dir) query.append('sort_dir', params.sort_dir);

  const res = await fetch(`${API_BASE}/products?${query.toString()}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch products: ${res.statusText}`);
  return res.json();
}

export async function fetchProductDetail(id: string): Promise<ProductDetail> {
  const res = await fetch(`${API_BASE}/products/${encodeURIComponent(id)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch product detail: ${res.statusText}`);
  return res.json();
}

export async function fetchProductKnowledgeGraph(id: string): Promise<{
  product_id: string;
  mfg_part_number: string;
  nodes: Array<{ id: string; label: string; type: string; group: string; color: string }>;
  edges: Array<{ source: string; target: string; label: string }>;
  stats: { total_nodes: number; total_edges: number; ontology_depth: number; lov_conformance: string };
}> {
  const res = await fetch(`${API_BASE}/products/${encodeURIComponent(id)}/graph`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch knowledge graph: ${res.statusText}`);
  return res.json();
}

// ============================================================================
// LlamaIndex Neural RAG Hybrid Search Endpoints
// ============================================================================

export interface RAGSearchResult {
  product_id: string;
  row_id: number;
  mfg_part_number: string;
  sku: string;
  brand_name: string;
  manufacturer_name: string;
  classpath: string;
  unspsc: string;
  short_desc: string;
  invoice_desc: string;
  mobile_desc: string;
  confidence_score: number;
  status: string;
  hybrid_score: number;
  dense_score: number;
  bm25_score: number;
  match_reason: string;
  attributes: Array<{ label: string; value: string; uom?: string }>;
}

export interface RAGSearchResponse {
  query: string;
  total_results: number;
  latency_ms: number;
  embedding_model: string;
  retrieval_strategy: string;
  synthesis: string;
  results: RAGSearchResult[];
}

export async function fetchRAGSearch(params: {
  q: string;
  top_k?: number;
  dense_weight?: number;
  min_confidence?: number;
  category?: string;
  status?: string;
}): Promise<RAGSearchResponse> {
  const query = new URLSearchParams();
  query.append('q', params.q);
  if (params.top_k) query.append('top_k', params.top_k.toString());
  if (params.dense_weight !== undefined) query.append('dense_weight', params.dense_weight.toString());
  if (params.min_confidence !== undefined) query.append('min_confidence', params.min_confidence.toString());
  if (params.category && params.category !== 'All') query.append('category', params.category);
  if (params.status && params.status !== 'All') query.append('status', params.status);

  const res = await fetch(`${API_BASE}/rag/search?${query.toString()}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to execute LlamaIndex RAG search: ${res.statusText}`);
  return res.json();
}

export async function fetchRAGInfo(): Promise<{
  status: string;
  embedding_model: string;
  vector_dimensions: number;
  total_documents_indexed: number;
  retrievers: string[];
  hybrid_fusion: string;
}> {
  const res = await fetch(`${API_BASE}/rag/info`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch RAG metadata: ${res.statusText}`);
  return res.json();
}



// ============================================================================
// Playground & Transformation Endpoints
// ============================================================================

export async function transformProduct(payload: TransformRequest): Promise<TransformResponse> {
  const res = await fetch(`${API_BASE}/playground/transform`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to transform product: ${res.statusText}`);
  return res.json();
}

export async function fetchPlaygroundPresets(): Promise<PlaygroundPreset[]> {
  const res = await fetch(`${API_BASE}/playground/presets`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch playground presets: ${res.statusText}`);
  return res.json();
}

// ============================================================================
// Review & HITL Quality Board Endpoints
// ============================================================================

export async function fetchReviewQueue(page = 1, limit = 20, minConfidence?: number): Promise<ReviewQueueResponse> {
  const query = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (minConfidence !== undefined) query.append('min_confidence', minConfidence.toString());

  const res = await fetch(`${API_BASE}/review/queue?${query.toString()}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.statusText}`);
  return res.json();
}

export async function approveProduct(id: string, notes?: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ approved: true, notes })
  });
  if (!res.ok) throw new Error(`Failed to approve product: ${res.statusText}`);
  return res.json();
}

export async function rejectProduct(id: string, reason: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/reject`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ approved: false, notes: reason })
  });
  if (!res.ok) throw new Error(`Failed to reject product: ${res.statusText}`);
  return res.json();
}

export async function updateProduct(id: string, payload: Partial<ProductDetail>): Promise<ProductDetail> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to update product: ${res.statusText}`);
  return res.json();
}

export async function fetchProductFieldReview(id: string): Promise<import('../types').ProductFieldReview> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/fields`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch field review: ${res.statusText}`);
  return res.json();
}

export async function submitFieldAction(
  id: string,
  payload: import('../types').FieldActionPayload
): Promise<import('../types').ProductFieldReview> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/field-action`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Field action failed: ${res.statusText}`);
  }
  return res.json();
}

export async function promoteProductValidated(
  id: string,
  notes?: string
): Promise<import('../types').PromoteValidatedResponse> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/promote-validated`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ approved: true, notes })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Validation promotion failed: ${res.statusText}`);
  }
  return res.json();
}

// ============================================================================
// Benchmark & Export Endpoints
// ============================================================================

export async function fetchBenchmarkResults(): Promise<BenchmarkReport> {
  const res = await fetch(`${API_BASE}/benchmark/results`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch benchmark results: ${res.statusText}`);
  return res.json();
}

export async function runBenchmark(): Promise<{ status: string; message: string; report: BenchmarkReport }> {
  const res = await fetch(`${API_BASE}/benchmark/run`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ force_recompute: true })
  });
  if (!res.ok) throw new Error(`Failed to run benchmark: ${res.statusText}`);
  return res.json();
}

export async function fetchExportColumns(): Promise<{ total_columns: number; headers: string[]; groups: Record<string, string[]> }> {
  const res = await fetch(`${API_BASE}/export/columns`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch export columns: ${res.statusText}`);
  return res.json();
}

export function getExportCsvUrl(status?: string, search?: string): string {
  const query = new URLSearchParams();
  if (status && status !== 'All') query.append('status', status);
  if (search) query.append('search', search);
  return `${API_BASE}/export/csv?${query.toString()}`;
}

export function getExportXlsxUrl(status?: string, search?: string): string {
  const query = new URLSearchParams();
  if (status && status !== 'All') query.append('status', status);
  if (search) query.append('search', search);
  return `${API_BASE}/export/xlsx?${query.toString()}`;
}

// ============================================================================
// Official Manufacturer Evidence Registry Endpoints
// ============================================================================

export async function fetchSourceRegistry(): Promise<import('../types').SourceRegistryEntry[]> {
  const res = await fetch(`${API_BASE}/evidence/registry`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch source registry: ${res.statusText}`);
  return res.json();
}

export async function registerEvidenceSource(
  payload: import('../types').SourceRegistrationRequest
): Promise<import('../types').SourceRegistrationResponse> {
  const res = await fetch(`${API_BASE}/evidence/register`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Source registration failed: ${res.statusText}`);
  }
  return res.json();
}

export async function queryEvidence(params: {
  mpn?: string;
  keyword?: string;
}): Promise<{ mpn: string; total_chunks: number; chunks: import('../types').EvidenceChunk[]; candidates: import('../types').ExtractedCandidate[] }> {
  const query = new URLSearchParams();
  if (params.mpn) query.append('mpn', params.mpn);
  if (params.keyword) query.append('keyword', params.keyword);

  const res = await fetch(`${API_BASE}/evidence/query?${query.toString()}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to query evidence: ${res.statusText}`);
  return res.json();
}

// ============================================================================
// Batch Evidence Enrichment & Cache Management Endpoints
// ============================================================================

export async function startBatchEnrichment(
  payload: import('../types').BatchStartRequest = {}
): Promise<import('../types').BatchReport> {
  const res = await fetch(`${API_BASE}/evidence/batch/start`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to start batch enrichment: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchLatestBatchJob(): Promise<import('../types').BatchReport | null> {
  const res = await fetch(`${API_BASE}/evidence/batch/latest`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch latest batch job: ${res.statusText}`);
  return res.json();
}

export async function fetchBatchJobStatus(jobId: string): Promise<import('../types').BatchReport> {
  const res = await fetch(`${API_BASE}/evidence/batch/status/${encodeURIComponent(jobId)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch batch status: ${res.statusText}`);
  return res.json();
}

export async function cancelBatchJob(jobId: string): Promise<{ message: string; job_id: string }> {
  const res = await fetch(`${API_BASE}/evidence/batch/cancel/${encodeURIComponent(jobId)}`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to cancel batch job: ${res.statusText}`);
  return res.json();
}

export async function fetchCacheStats(): Promise<import('../types').CacheStats> {
  const res = await fetch(`${API_BASE}/evidence/cache/stats`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch cache stats: ${res.statusText}`);
  return res.json();
}

export async function clearExtractionCache(): Promise<{ message: string; stats: import('../types').CacheStats }> {
  const res = await fetch(`${API_BASE}/evidence/cache/clear`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to clear cache: ${res.statusText}`);
  return res.json();
}

// ============================================================================
// User Management Endpoints (Admin RBAC)
// ============================================================================

export async function fetchUsers(): Promise<User[]> {
  const res = await fetch(`${API_BASE}/auth/users`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch users: ${res.statusText}`);
  return res.json();
}

export async function updateUserRole(userId: string, role: string): Promise<{ status: string; message: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/users/${encodeURIComponent(userId)}/role`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify({ role })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to update user role: ${res.statusText}`);
  }
  return res.json();
}

// ============================================================================
// Product Timeline & Export History Endpoints
// ============================================================================

export async function fetchProductTimeline(productId: string): Promise<import('../types').ProductTimelineResponse> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(productId)}/timeline`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch timeline: ${res.statusText}`);
  return res.json();
}

export async function fetchExportHistory(limit: number = 25): Promise<import('../types').ExportHistoryResponse> {
  const res = await fetch(`${API_BASE}/export/history?limit=${limit}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch export history: ${res.statusText}`);
  return res.json();
}

export async function fetchSystemHealth(): Promise<import('../types').SystemHealthData> {
  const res = await fetch(`${API_BASE}/system/health`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch system health: ${res.statusText}`);
  return res.json();
}

// ============================================================================
// Source Lifecycle Management Endpoints
// ============================================================================

export async function markSourceStale(sourceId: string, reason?: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/evidence/source/${encodeURIComponent(sourceId)}/mark-stale`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ reason: reason || 'Marked stale by specialist' })
  });
  if (!res.ok) throw new Error(`Failed to mark source stale: ${res.statusText}`);
  return res.json();
}

export async function supersedeSource(sourceId: string, newSourceId: string, reason?: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/evidence/source/${encodeURIComponent(sourceId)}/supersede`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ new_source_id: newSourceId, reason: reason || 'Superseded by newer source' })
  });
  if (!res.ok) throw new Error(`Failed to supersede source: ${res.statusText}`);
  return res.json();
}

export async function rejectSource(sourceId: string, reason: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/evidence/source/${encodeURIComponent(sourceId)}/reject`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ reason })
  });
  if (!res.ok) throw new Error(`Failed to reject source: ${res.statusText}`);
  return res.json();
}

export async function reingestSource(sourceId: string): Promise<import('../types').SourceRegistrationResponse> {
  const res = await fetch(`${API_BASE}/evidence/source/${encodeURIComponent(sourceId)}/re-ingest`, {
    method: 'POST',
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Failed to re-ingest source: ${res.statusText}`);
  }
  return res.json();
}

export async function fetchSourceHistory(sourceId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/evidence/source/${encodeURIComponent(sourceId)}/history`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch source history: ${res.statusText}`);
  return res.json();
}


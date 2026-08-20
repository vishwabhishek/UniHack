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

// In-Memory Token Manager with localStorage sync
let authToken: string | null = localStorage.getItem('unilog_auth_token');

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem('unilog_auth_token', token);
  } else {
    localStorage.removeItem('unilog_auth_token');
  }
}

export function getAuthToken(): string | null {
  return authToken || localStorage.getItem('unilog_auth_token');
}

function getAuthHeaders(): Record<string, string> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
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
  setAuthToken(data.token);
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
  setAuthToken(data.token);
  return data;
}

export async function getCurrentUserProfile(): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) throw new Error(`Failed to fetch current user: ${res.statusText}`);
  return res.json();
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

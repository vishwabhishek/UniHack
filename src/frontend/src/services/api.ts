import {
  CatalogStats,
  FilterOptions,
  ProductListResponse,
  ProductDetail,
  TransformRequest,
  TransformResponse,
  PlaygroundPreset,
  ReviewQueueResponse,
  BenchmarkReport
} from '../types';

const API_BASE = '/api';

export async function fetchStats(): Promise<CatalogStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
  return res.json();
}

export async function fetchFilters(): Promise<FilterOptions> {
  const res = await fetch(`${API_BASE}/filters`);
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

  const res = await fetch(`${API_BASE}/products?${query.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch products: ${res.statusText}`);
  return res.json();
}

export async function fetchProductDetail(id: string): Promise<ProductDetail> {
  const res = await fetch(`${API_BASE}/products/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Failed to fetch product detail: ${res.statusText}`);
  return res.json();
}

export async function transformProduct(payload: TransformRequest): Promise<TransformResponse> {
  const res = await fetch(`${API_BASE}/playground/transform`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Transformation failed: ${res.statusText}`);
  return res.json();
}

export async function fetchPlaygroundPresets(): Promise<PlaygroundPreset[]> {
  const res = await fetch(`${API_BASE}/playground/presets`);
  if (!res.ok) throw new Error(`Failed to fetch presets: ${res.statusText}`);
  return res.json();
}

export async function fetchReviewQueue(): Promise<ReviewQueueResponse> {
  const res = await fetch(`${API_BASE}/review/queue`);
  if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.statusText}`);
  return res.json();
}

export async function approveProduct(id: string, notes: string = ''): Promise<{ success: boolean; status: string; id: string }> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved: true, notes })
  });
  if (!res.ok) throw new Error(`Failed to approve product: ${res.statusText}`);
  return res.json();
}

export async function rejectProduct(id: string, reason: string = ''): Promise<{ success: boolean; status: string; id: string }> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved: false, notes: reason })
  });
  if (!res.ok) throw new Error(`Failed to reject product: ${res.statusText}`);
  return res.json();
}

export async function updateProduct(id: string, payload: Partial<ProductDetail>): Promise<ProductDetail> {
  const res = await fetch(`${API_BASE}/review/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to update product: ${res.statusText}`);
  return res.json();
}

export async function fetchBenchmarkResults(): Promise<BenchmarkReport> {
  const res = await fetch(`${API_BASE}/benchmark/results`);
  if (!res.ok) throw new Error(`Failed to fetch benchmark results: ${res.statusText}`);
  return res.json();
}

export async function runBenchmark(): Promise<{ status: string; message: string; report: BenchmarkReport }> {
  const res = await fetch(`${API_BASE}/benchmark/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force_recompute: true })
  });
  if (!res.ok) throw new Error(`Failed to run benchmark: ${res.statusText}`);
  return res.json();
}

export async function fetchExportColumns(): Promise<{ total_columns: number; headers: string[]; groups: Record<string, string[]> }> {
  const res = await fetch(`${API_BASE}/export/columns`);
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

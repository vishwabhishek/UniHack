import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  Eye,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  ArrowUpDown,
  RefreshCw,
  Edit3
} from 'lucide-react';
import { ProductListItem, FilterOptions } from '../types';
import { fetchProducts, fetchFilters } from '../services/api';

interface CatalogExplorerProps {
  onInspectProduct: (productId: string) => void;
  onEditProduct: (productId: string) => void;
  initialStatus?: string;
}

export const CatalogExplorer: React.FC<CatalogExplorerProps> = ({
  onInspectProduct,
  onEditProduct,
  initialStatus = 'All'
}) => {
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(20);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [search, setSearch] = useState<string>('');
  const [status, setStatus] = useState<string>(initialStatus);
  const [category, setCategory] = useState<string>('All');
  const [brand, setBrand] = useState<string>('All');
  const [minConfidence, setMinConfidence] = useState<number>(0.0);
  const [sortBy, setSortBy] = useState<string>('row_id');
  const [sortDir, setSortDir] = useState<string>('asc');

  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null);

  useEffect(() => {
    loadFilters();
  }, []);

  useEffect(() => {
    loadProducts();
  }, [page, limit, search, status, category, brand, minConfidence, sortBy, sortDir]);

  const loadFilters = async () => {
    try {
      const data = await fetchFilters();
      setFilterOptions(data);
    } catch (e) {
      console.error('Failed to load filter options:', e);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const data = await fetchProducts({
        page,
        limit,
        search: search.trim() || undefined,
        status: status !== 'All' ? status : undefined,
        category: category !== 'All' ? category : undefined,
        brand: brand !== 'All' ? brand : undefined,
        min_confidence: minConfidence > 0 ? minConfidence : undefined,
        sort_by: sortBy,
        sort_dir: sortDir
      });
      setProducts(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (e) {
      console.error('Failed to load products:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleResetFilters = () => {
    setSearch('');
    setStatus('All');
    setCategory('All');
    setBrand('All');
    setMinConfidence(0.0);
    setSortBy('row_id');
    setSortDir('asc');
    setPage(1);
  };

  return (
    <div className="space-y-4">
      {/* Control Bar & Filter Facets */}
      <div className="bg-slate-900/80 rounded-xl border border-slate-800 p-4 backdrop-blur-sm space-y-3">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          {/* Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search across 1,000 items by MPN, Brand, Title, or Classpath..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-slate-950/70 border border-slate-700/80 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
            />
          </div>

          {/* Action Tools */}
          <div className="flex items-center space-x-2 w-full md:w-auto justify-end">
            <button
              onClick={loadProducts}
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-all"
              title="Refresh results"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={handleResetFilters}
              className="px-3 py-2 bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg text-xs font-medium border border-slate-700/60 transition-all"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Filter Dropdowns & Range Sliders */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2.5 pt-2 border-t border-slate-800/80 text-xs">
          {/* Status Filter */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Status</label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-700 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="All">All Statuses</option>
              <option value="Validated">Validated</option>
              <option value="Enriched">Enriched</option>
              <option value="Flagged">Needs Human Review</option>
            </select>
          </div>

          {/* Department / Category Filter */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Department</label>
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-700 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="All">All Departments</option>
              {filterOptions?.departments.map((dept) => (
                <option key={dept.value} value={dept.value}>
                  {dept.label} ({dept.count})
                </option>
              ))}
            </select>
          </div>

          {/* Brand Filter */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Brand</label>
            <select
              value={brand}
              onChange={(e) => {
                setBrand(e.target.value);
                setPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-700 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="All">All Brands</option>
              {filterOptions?.brands.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label} ({b.count})
                </option>
              ))}
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label className="block text-[11px] font-medium text-slate-400 mb-1">Sort By</label>
            <select
              value={`${sortBy}-${sortDir}`}
              onChange={(e) => {
                const [sb, sd] = e.target.value.split('-');
                setSortBy(sb);
                setSortDir(sd);
              }}
              className="w-full bg-slate-950 border border-slate-700 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-sky-500"
            >
              <option value="row_id-asc">Row ID (1 → 1000)</option>
              <option value="confidence-desc">Highest Confidence</option>
              <option value="confidence-asc">Lowest Confidence (Review)</option>
              <option value="brand-asc">Brand (A → Z)</option>
              <option value="mfg_part_num-asc">MPN (A → Z)</option>
            </select>
          </div>

          {/* Min Confidence Threshold */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[11px] font-medium text-slate-400">Min Confidence</label>
              <span className="text-[10px] font-mono text-sky-400 font-semibold">
                {(minConfidence * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={minConfidence}
              onChange={(e) => {
                setMinConfidence(parseFloat(e.target.value));
                setPage(1);
              }}
              className="w-full accent-sky-500 bg-slate-800 rounded-lg h-1.5 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Catalog Data Table */}
      <div className="bg-slate-900/90 rounded-xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-950/90 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                <th className="py-3.5 px-3 w-14 min-w-[56px] text-center">#</th>
                <th className="py-3.5 px-4 min-w-[160px]">MPN & Identifiers</th>
                <th className="py-3.5 px-4 min-w-[170px]">Brand & Manufacturer</th>
                <th className="py-3.5 px-4 min-w-[200px]">Classpath & Fine Category</th>
                <th className="py-3.5 px-4 min-w-[250px]">INVOICE_DESC (≤ 40 CAPS)</th>
                <th className="py-3.5 px-4 min-w-[270px]">MOBILE_DESC (60–80 Chars)</th>
                <th className="py-3.5 px-3 w-28 text-center">Confidence</th>
                <th className="py-3.5 px-3 w-28 text-center">Status</th>
                <th className="py-3.5 px-3 w-24 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <RefreshCw className="w-6 h-6 animate-spin text-sky-400" />
                      <span className="font-sans text-xs">Loading catalog products...</span>
                    </div>
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-400 font-sans">
                    No catalog records match your query. Try broadening your filters.
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const isInvCompliant = p.invoice_desc_len <= 40 && p.invoice_desc === p.invoice_desc.toUpperCase();
                  const isMobCompliant = p.mobile_desc_len >= 60 && p.mobile_desc_len <= 80;

                  return (
                    <tr
                      key={p.id}
                      className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                      onClick={() => onInspectProduct(p.id)}
                    >
                      {/* Row ID */}
                      <td className="py-3 px-4 text-center text-slate-400 font-bold">
                        {p.row_id}
                      </td>

                      {/* MPN & SKU */}
                      <td className="py-3 px-4">
                        <div className="font-bold text-slate-100 text-xs">
                          {p.mfg_part_number}
                        </div>
                        <div className="text-[10px] text-slate-400 font-sans">
                          SKU: <span className="font-mono text-slate-300">{p.sku}</span>
                        </div>
                      </td>

                      {/* Brand & Manufacturer */}
                      <td className="py-3 px-4 font-sans">
                        <div className="font-semibold text-sky-300 flex items-center space-x-1">
                          <span>{p.brand_name}</span>
                        </div>
                        <div className="text-[11px] text-slate-400 line-clamp-1">
                          {p.manufacturer_name}
                        </div>
                      </td>

                      {/* Classpath */}
                      <td className="py-3 px-4 font-sans">
                        <div className="text-[11px] text-slate-200 font-medium line-clamp-1">
                          {p.product_name || p.dept}
                        </div>
                        <div className="text-[10px] text-slate-400 line-clamp-1 font-mono">
                          {p.classpath}
                        </div>
                      </td>

                      {/* INVOICE_DESC */}
                      <td className="py-3 px-4">
                        <div className="text-[11px] text-emerald-300 bg-slate-950/80 px-2 py-1 rounded border border-slate-800/80 line-clamp-1">
                          {p.invoice_desc}
                        </div>
                        <div className="flex items-center justify-between text-[10px] mt-1 text-slate-400 font-sans">
                          <span
                            className={`px-1.5 py-0.2 rounded font-mono ${
                              isInvCompliant
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                            }`}
                          >
                            {p.invoice_desc_len}/40 chars
                          </span>
                          <span className="text-[9px] text-slate-400">100% CAPS</span>
                        </div>
                      </td>

                      {/* MOBILE_DESC */}
                      <td className="py-3 px-4 font-sans">
                        <div className="text-[11px] text-slate-200 line-clamp-1">
                          {p.mobile_desc}
                        </div>
                        <div className="flex items-center justify-between text-[10px] mt-1 text-slate-400">
                          <span
                            className={`px-1.5 py-0.2 rounded font-mono ${
                              isMobCompliant
                                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            }`}
                          >
                            {p.mobile_desc_len}/80 chars
                          </span>
                          <span className="text-[9px] text-slate-400">60–80 Range</span>
                        </div>
                      </td>

                      {/* Confidence Score */}
                      <td className="py-3 px-4 text-center">
                        <div className="inline-flex flex-col items-center">
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-bold font-mono border ${
                              p.confidence_score >= 0.95
                                ? 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
                                : p.confidence_score >= 0.85
                                ? 'bg-sky-500/15 text-sky-300 border-sky-500/30'
                                : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                            }`}
                          >
                            {(p.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 text-center font-sans">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border inline-flex items-center space-x-1 ${
                            p.status === 'Validated'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                              : p.status === 'Enriched'
                              ? 'bg-sky-500/10 text-sky-400 border-sky-500/30'
                              : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          }`}
                        >
                          {p.status === 'Validated' ? (
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          ) : p.status === 'Flagged' ? (
                            <AlertTriangle className="w-3 h-3 text-amber-400" />
                          ) : null}
                          <span>{p.status}</span>
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center space-x-1">
                          <button
                            onClick={() => onInspectProduct(p.id)}
                            className="p-1.5 bg-slate-800 hover:bg-sky-600 text-slate-300 hover:text-white rounded-md transition-colors"
                            title="Side-by-Side Diff Inspector"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => onEditProduct(p.id)}
                            className="p-1.5 bg-slate-800 hover:bg-amber-600 text-slate-300 hover:text-white rounded-md transition-colors"
                            title="Review & Edit Record"
                          >
                            <Edit3 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="bg-slate-950 px-4 py-3 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center space-x-2">
            <span>Showing</span>
            <span className="font-mono text-slate-200 font-bold">
              {total > 0 ? (page - 1) * limit + 1 : 0}
            </span>
            <span>to</span>
            <span className="font-mono text-slate-200 font-bold">
              {Math.min(page * limit, total)}
            </span>
            <span>of</span>
            <span className="font-mono text-slate-200 font-bold">{total}</span>
            <span>items</span>

            <span className="mx-2 text-slate-600">|</span>

            <span>Per page:</span>
            <select
              value={limit}
              onChange={(e) => {
                setLimit(parseInt(e.target.value));
                setPage(1);
              }}
              className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 focus:outline-none"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 rounded border border-slate-700 flex items-center space-x-1 transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Prev</span>
            </button>

            <span className="px-3 py-1 bg-slate-900/60 rounded border border-slate-800 font-mono text-slate-300">
              Page <span className="font-bold text-sky-400">{page}</span> of {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="px-2.5 py-1.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 rounded border border-slate-700 flex items-center space-x-1 transition-all"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

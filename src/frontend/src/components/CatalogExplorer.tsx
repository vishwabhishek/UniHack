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
  Edit3,
  Copy,
  Check
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
  const [copiedId, setCopiedId] = useState<string | null>(null);

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

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-3">
      {/* Control & Facet Filter Bar */}
      <div className="bg-pim-panel border border-pim-border rounded p-3.5 space-y-3 shadow-sm">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          {/* Search Box */}
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-pim-textMuted" />
            <input
              type="text"
              placeholder="Search across 1,000 SKUs by MPN, Brand, Taxonomy, or Title (e.g. PDSH4816AF, Trex, Sanding)..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-4 py-2 bg-pim-surface border border-pim-border rounded text-xs text-white placeholder-pim-textMuted focus:border-pim-accent focus:ring-1 focus:ring-pim-accent font-sans"
            />
          </div>

          {/* Action Toolbar */}
          <div className="flex items-center space-x-2 w-full md:w-auto justify-end">
            <button
              onClick={loadProducts}
              className="flex items-center space-x-1.5 px-3 py-2 bg-pim-surface hover:bg-slate-800 text-slate-300 rounded text-xs font-medium border border-pim-border transition-colors font-mono"
              title="Refresh dataset"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>SYNC</span>
            </button>
            <button
              onClick={handleResetFilters}
              className="px-3 py-2 bg-pim-surface/60 hover:bg-pim-surface text-pim-textMuted hover:text-slate-200 rounded text-xs font-medium border border-pim-border transition-colors font-mono"
            >
              RESET
            </button>
          </div>
        </div>

        {/* Facet Dropdowns */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2.5 pt-2 border-t border-pim-border/80 text-xs">
          {/* Status Facet */}
          <div>
            <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
              STATUS
            </label>
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              className="w-full bg-pim-surface border border-pim-border rounded px-2 py-1.5 text-slate-200 focus:border-pim-accent text-xs font-sans"
            >
              <option value="All">All Statuses</option>
              <option value="Validated">Validated (Clean)</option>
              <option value="Enriched">Enriched (Ready)</option>
              <option value="Flagged">Flagged (Needs Review)</option>
            </select>
          </div>

          {/* Department Facet */}
          <div>
            <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
              DEPARTMENT
            </label>
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
              className="w-full bg-pim-surface border border-pim-border rounded px-2 py-1.5 text-slate-200 focus:border-pim-accent text-xs font-sans"
            >
              <option value="All">All Departments</option>
              {filterOptions?.departments.map((dept) => (
                <option key={dept.value} value={dept.value}>
                  {dept.label} ({dept.count})
                </option>
              ))}
            </select>
          </div>

          {/* Canonical Brand Facet */}
          <div>
            <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
              CANONICAL BRAND
            </label>
            <select
              value={brand}
              onChange={(e) => {
                setBrand(e.target.value);
                setPage(1);
              }}
              className="w-full bg-pim-surface border border-pim-border rounded px-2 py-1.5 text-slate-200 focus:border-pim-accent text-xs font-sans"
            >
              <option value="All">All Brands (76 MFRs)</option>
              {filterOptions?.brands.map((b) => (
                <option key={b.value} value={b.value}>
                  {b.label} ({b.count})
                </option>
              ))}
            </select>
          </div>

          {/* Sort Facet */}
          <div>
            <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
              SORT ORDER
            </label>
            <select
              value={`${sortBy}-${sortDir}`}
              onChange={(e) => {
                const [sb, sd] = e.target.value.split('-');
                setSortBy(sb);
                setSortDir(sd);
              }}
              className="w-full bg-pim-surface border border-pim-border rounded px-2 py-1.5 text-slate-200 focus:border-pim-accent text-xs font-sans"
            >
              <option value="row_id-asc">Row ID (1 → 1000)</option>
              <option value="confidence-desc">Confidence (Highest First)</option>
              <option value="confidence-asc">Confidence (Lowest / Review First)</option>
              <option value="brand-asc">Brand (A → Z)</option>
              <option value="mfg_part_num-asc">Part Number (A → Z)</option>
            </select>
          </div>

          {/* Min Confidence Range */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="text-[10px] font-mono uppercase font-semibold text-pim-textMuted">
                CONFIDENCE THRESHOLD
              </label>
              <span className="text-[10px] font-mono text-blue-400 font-bold">
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
              className="w-full accent-blue-600 bg-pim-surface rounded h-1.5 cursor-pointer mt-1"
            />
          </div>
        </div>
      </div>

      {/* High-Density Master Data Grid */}
      <div className="bg-pim-panel border border-pim-border rounded overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-pim-darkest border-b border-pim-border text-pim-textMuted font-mono uppercase tracking-wider text-[10px]">
                <th className="py-3 px-3 w-12 text-center">ID</th>
                <th className="py-3 px-3 min-w-[150px]">MPN / SKU</th>
                <th className="py-3 px-3 min-w-[170px]">Brand & Manufacturer</th>
                <th className="py-3 px-3 min-w-[200px]">Taxonomy Classpath</th>
                <th className="py-3 px-3 min-w-[260px]">INVOICE_DESC (≤40 UPPERCASE)</th>
                <th className="py-3 px-3 min-w-[270px]">MOBILE_DESC (60–80 Chars)</th>
                <th className="py-3 px-3 w-28 text-center">Score</th>
                <th className="py-3 px-3 w-28 text-center">Governance</th>
                <th className="py-3 px-3 w-24 text-center">Workbench</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pim-border/60 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-16 text-center text-pim-textMuted">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
                      <span className="font-mono text-xs">Querying Master Data Records...</span>
                    </div>
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-16 text-center text-pim-textMuted font-sans">
                    No catalog records match the active criteria. Try broadening your filter parameters.
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const isInvCompliant = p.invoice_desc_len <= 40 && p.invoice_desc === p.invoice_desc.toUpperCase();
                  const isMobCompliant = p.mobile_desc_len >= 60 && p.mobile_desc_len <= 80;

                  return (
                    <tr
                      key={p.id}
                      className="hover:bg-pim-surface/80 transition-colors group cursor-pointer"
                      onClick={() => onInspectProduct(p.id)}
                    >
                      {/* Row ID */}
                      <td className="py-2.5 px-3 text-center text-pim-textMuted font-mono font-bold text-[11px]">
                        {p.row_id}
                      </td>

                      {/* MPN & SKU */}
                      <td className="py-2.5 px-3">
                        <div className="font-mono font-bold text-white text-xs">
                          {p.mfg_part_number}
                        </div>
                        <div className="text-[10px] text-pim-textMuted font-mono">
                          SKU: <span className="text-slate-300">{p.sku}</span>
                        </div>
                      </td>

                      {/* Brand & MFR */}
                      <td className="py-2.5 px-3">
                        <div className="font-semibold text-blue-400 text-xs">
                          {p.brand_name}
                        </div>
                        <div className="text-[10px] text-pim-textSecondary line-clamp-1">
                          {p.manufacturer_name}
                        </div>
                      </td>

                      {/* Classpath */}
                      <td className="py-2.5 px-3">
                        <div className="text-xs text-slate-200 font-medium line-clamp-1">
                          {p.product_name || p.dept}
                        </div>
                        <div className="text-[10px] text-pim-textMuted line-clamp-1 font-mono">
                          {p.classpath}
                        </div>
                      </td>

                      {/* INVOICE_DESC */}
                      <td className="py-2.5 px-3">
                        <div className="text-[11px] font-mono text-emerald-300 bg-pim-surface px-2 py-0.5 rounded border border-pim-border line-clamp-1">
                          {p.invoice_desc}
                        </div>
                        <div className="flex items-center justify-between text-[10px] mt-1 font-mono">
                          <span
                            className={`px-1 rounded ${
                              isInvCompliant
                                ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                                : 'bg-rose-950/60 text-rose-400 border border-rose-800/40'
                            }`}
                          >
                            {p.invoice_desc_len}/40 chars
                          </span>
                          <span className="text-[9px] text-pim-textMuted">ALL CAPS</span>
                        </div>
                      </td>

                      {/* MOBILE_DESC */}
                      <td className="py-2.5 px-3">
                        <div className="text-[11px] text-slate-200 line-clamp-1">
                          {p.mobile_desc}
                        </div>
                        <div className="flex items-center justify-between text-[10px] mt-1 font-mono">
                          <span
                            className={`px-1 rounded ${
                              isMobCompliant
                                ? 'bg-blue-950/60 text-blue-400 border border-blue-800/40'
                                : 'bg-amber-950/60 text-amber-400 border border-amber-800/40'
                            }`}
                          >
                            {p.mobile_desc_len}/80 chars
                          </span>
                          <span className="text-[9px] text-pim-textMuted">60-80 spec</span>
                        </div>
                      </td>

                      {/* Confidence Score */}
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold font-mono border ${
                            p.confidence_score >= 0.95
                              ? 'bg-emerald-950/80 text-emerald-400 border-emerald-800/50'
                              : p.confidence_score >= 0.85
                              ? 'bg-blue-950/80 text-blue-400 border-blue-800/50'
                              : 'bg-amber-950/80 text-amber-400 border-amber-800/50'
                          }`}
                        >
                          {(p.confidence_score * 100).toFixed(0)}%
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase border inline-flex items-center space-x-1 ${
                            p.status === 'Validated'
                              ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/50'
                              : p.status === 'Enriched'
                              ? 'bg-blue-950/60 text-blue-400 border-blue-800/50'
                              : 'bg-amber-950/60 text-amber-400 border-amber-800/50'
                          }`}
                        >
                          {p.status === 'Validated' ? (
                            <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400" />
                          ) : p.status === 'Flagged' ? (
                            <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                          ) : null}
                          <span>{p.status}</span>
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-2.5 px-3 text-center" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center space-x-1">
                          <button
                            onClick={() => onInspectProduct(p.id)}
                            className="p-1 bg-pim-surface hover:bg-blue-600 text-pim-textSecondary hover:text-white rounded border border-pim-border transition-colors"
                            title="Dual-Pane Transformation Workbench"
                          >
                            <Eye className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => copyToClipboard(p.invoice_desc, p.id)}
                            className="p-1 bg-pim-surface hover:bg-slate-700 text-pim-textSecondary hover:text-white rounded border border-pim-border transition-colors"
                            title="Copy Invoice Desc"
                          >
                            {copiedId === p.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          </button>
                          <button
                            onClick={() => onEditProduct(p.id)}
                            className="p-1 bg-pim-surface hover:bg-amber-600 text-pim-textSecondary hover:text-white rounded border border-pim-border transition-colors"
                            title="Triage & Edit Record"
                          >
                            <Edit3 className="w-3 h-3" />
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

        {/* Data Grid Pagination */}
        <div className="bg-pim-darkest px-4 py-2.5 border-t border-pim-border flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-pim-textMuted font-mono">
          <div className="flex items-center space-x-2">
            <span>RECORDS:</span>
            <span className="text-white font-bold">
              {total > 0 ? (page - 1) * limit + 1 : 0}–{Math.min(page * limit, total)}
            </span>
            <span>OF</span>
            <span className="text-white font-bold">{total.toLocaleString()}</span>

            <span className="mx-2 text-slate-700">|</span>

            <span>PAGE SIZE:</span>
            <select
              value={limit}
              onChange={(e) => {
                setLimit(parseInt(e.target.value));
                setPage(1);
              }}
              className="bg-pim-surface border border-pim-border rounded px-2 py-0.5 text-white text-xs font-mono"
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
              className="px-2.5 py-1 bg-pim-surface hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded border border-pim-border flex items-center space-x-1 transition-colors"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>PREV</span>
            </button>

            <span className="px-2.5 py-1 bg-pim-surface rounded border border-pim-border text-slate-300 font-bold">
              {page} / {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="px-2.5 py-1 bg-pim-surface hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded border border-pim-border flex items-center space-x-1 transition-colors"
            >
              <span>NEXT</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

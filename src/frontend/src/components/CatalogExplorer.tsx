import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  Layers,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Edit3,
  Copy,
  Check,
  Tag,
  Sparkles,
  Zap,
  ArrowUpDown
} from 'lucide-react';
import { ProductListItem, FilterOptions, FilterOptionItem } from '../types';
import { fetchProducts, fetchFilters } from '../services/api';
import { useToast } from './Toast';

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
  const { showToast } = useToast();
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [departments, setDepartments] = useState<FilterOptionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(20);
  const [search, setSearch] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>(initialStatus);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    setSelectedStatus(initialStatus);
  }, [initialStatus]);

  useEffect(() => {
    loadFilters();
  }, []);

  useEffect(() => {
    loadData();
  }, [page, limit, search, selectedCategory, selectedStatus]);

  const loadFilters = async () => {
    try {
      const data = await fetchFilters();
      if (data && data.departments) {
        setDepartments(data.departments);
      }
    } catch (e) {
      console.error('Failed to load filter options:', e);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await fetchProducts({
        page,
        limit,
        search: search.trim() || undefined,
        category: selectedCategory || undefined,
        status: selectedStatus !== 'All' ? selectedStatus : undefined
      });
      setProducts(data.items);
      setTotalCount(data.total);
    } catch (e) {
      console.error('Failed to load products:', e);
      showToast('Error', 'Failed to fetch catalog items', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, id: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    showToast('Copied', `${label}: ${text}`, 'success');
    setTimeout(() => setCopiedId(null), 2000);
  };

  const totalPages = Math.ceil(totalCount / limit) || 1;

  return (
    <div className="space-y-4">
      {/* Search & Control Command Bar */}
      <div className="glass-panel p-4 rounded-2xl space-y-3.5 border border-white/[0.08]">
        <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-cyan-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by MPN, Brand, Raw Description, Invoice Description, or Keywords..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 bg-slate-950/70 border border-white/[0.08] rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all font-sans"
            />
          </div>

          {/* Department / Category Dropdown */}
          <div className="w-full lg:w-72">
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by Category"
              className="w-full px-3 py-2 bg-slate-950/70 border border-white/[0.08] rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-400 font-sans"
            >
              <option value="">All Departments ({departments.length})</option>
              {departments.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label} ({d.count})
                </option>
              ))}
            </select>
          </div>

          {/* Page Limit Selector */}
          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono flex-shrink-0">
            <span>SHOW:</span>
            {[20, 50, 100].map((lim) => (
              <button
                key={lim}
                onClick={() => {
                  setLimit(lim);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded-lg border transition-all ${
                  limit === lim
                    ? 'bg-blue-600/20 text-cyan-300 border-cyan-500/50 font-bold shadow-glow-cyan'
                    : 'bg-slate-950/60 text-slate-400 border-white/[0.06] hover:text-white'
                }`}
              >
                {lim}
              </button>
            ))}
          </div>
        </div>

        {/* Status Filter Badges */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/[0.04]">
          <div className="flex flex-wrap items-center gap-1.5 font-mono text-xs">
            <span className="text-[10px] text-slate-400 uppercase font-bold mr-1 flex items-center space-x-1">
              <Filter className="w-3 h-3 text-cyan-400" />
              <span>STATUS FILTER:</span>
            </span>
            {['All', 'Validated', 'Enriched', 'Flagged'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setSelectedStatus(st);
                  setPage(1);
                }}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all border ${
                  selectedStatus === st
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-glow-blue border-blue-400/40'
                    : 'bg-slate-950/60 hover:bg-slate-900 text-slate-400 border-white/[0.06] hover:text-white'
                }`}
              >
                {st === 'All' ? 'All (1,000)' : st.toUpperCase()}
              </button>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 font-mono">
            SHOWING <strong className="text-white font-bold tnum">{products.length}</strong> OF <strong className="text-white font-bold tnum">{totalCount}</strong> MASTER RECORDS
          </div>
        </div>
      </div>

      {/* High-Density Modern Master Data Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-white/[0.08] shadow-glass">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-gradient-to-r from-[#0C1220] via-[#0F172A] to-[#0C1220] border-b border-white/[0.08] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                <th className="py-3 px-3.5 w-14 text-center">ROW#</th>
                <th className="py-3 px-3.5 w-36">MPN</th>
                <th className="py-3 px-3.5 w-44">BRAND & MFG</th>
                <th className="py-3 px-3.5 w-56">INVOICE_DESC (≤ 40)</th>
                <th className="py-3 px-3.5">PRODUCT TITLE / SHORT_DESC</th>
                <th className="py-3 px-3.5 w-24 text-center">CONFIDENCE</th>
                <th className="py-3 px-3.5 w-28 text-center">STATUS</th>
                <th className="py-3 px-3.5 w-28 text-center">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-24 text-center text-slate-400 font-mono">
                    <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-3 shadow-glow-cyan" />
                    <p className="text-xs">LOADING MASTER PRODUCT RECORDS...</p>
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-20 text-center text-slate-400 font-mono">
                    NO MASTER DATA RECORDS MATCHED YOUR SEARCH QUERY OR FILTER.
                  </td>
                </tr>
              ) : (
                products.map((p) => {
                  const isCopied = copiedId === p.id;
                  return (
                    <tr
                      key={p.id}
                      className="hover:bg-slate-800/40 transition-colors group cursor-pointer"
                      onClick={() => onInspectProduct(p.id)}
                    >
                      {/* Row Index */}
                      <td className="py-3 px-3.5 text-center text-slate-400 font-mono text-[11px] tnum">
                        {p.row_id}
                      </td>

                      {/* MPN with quick copy trigger */}
                      <td className="py-3 px-3.5 font-mono">
                        <div className="flex items-center space-x-1.5">
                          <span className="font-bold text-white group-hover:text-cyan-300 transition-colors">
                            {p.mfg_part_number}
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCopy(p.mfg_part_number, p.id, 'MPN');
                            }}
                            title="Copy MPN"
                            className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/[0.08] transition-colors"
                          >
                            {isCopied ? (
                              <Check className="w-3 h-3 text-emerald-400" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </td>

                      {/* Brand & Manufacturer */}
                      <td className="py-3 px-3.5">
                        <div className="font-bold text-cyan-400 text-xs font-sans">
                          {p.brand_name}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate max-w-[170px] font-sans" title={p.manufacturer_name}>
                          {p.manufacturer_name}
                        </div>
                      </td>

                      {/* INVOICE_DESC (≤ 40 chars, ALL CAPS) */}
                      <td className="py-3 px-3.5 font-mono">
                        <div className="p-1.5 rounded-lg bg-slate-950/80 border border-white/[0.06] text-emerald-300 font-bold text-[11px] break-words">
                          {p.invoice_desc}
                        </div>
                        <span className="text-[9px] text-slate-400 mt-0.5 block tnum">
                          {p.invoice_desc.length}/40 chars
                        </span>
                      </td>

                      {/* Short Description */}
                      <td className="py-3 px-3.5 font-sans">
                        <div className="text-slate-200 text-xs font-medium line-clamp-1 group-hover:text-white transition-colors" title={p.short_desc}>
                          {p.short_desc}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5 line-clamp-1" title={p.classpath}>
                          {p.classpath}
                        </div>
                      </td>

                      {/* Confidence Meter */}
                      <td className="py-3 px-3.5 text-center font-mono">
                        <span className="font-bold text-white text-xs tnum">
                          {(p.confidence_score * 100).toFixed(0)}%
                        </span>
                        <div className="w-16 bg-slate-900 rounded-full h-1.5 mx-auto mt-1 overflow-hidden border border-white/[0.08]">
                          <div
                            className={`h-1.5 rounded-full ${
                              p.confidence_score >= 0.85
                                ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                                : 'bg-gradient-to-r from-amber-500 to-orange-400'
                            }`}
                            style={{ width: `${Math.min(p.confidence_score * 100, 100)}%` }}
                          />
                        </div>
                      </td>

                      {/* Status Tag */}
                      <td className="py-3 px-3.5 text-center font-mono">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold inline-flex items-center space-x-1 ${
                            p.status === 'Validated'
                              ? 'glow-badge-emerald'
                              : p.status === 'Flagged'
                              ? 'glow-badge-amber'
                              : 'glow-badge-cyan'
                          }`}
                        >
                          <span>{p.status.toUpperCase()}</span>
                        </span>
                      </td>

                      {/* Action Triggers */}
                      <td className="py-3 px-3.5 text-center">
                        <div className="flex items-center justify-center space-x-1" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => onInspectProduct(p.id)}
                            className="px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 text-cyan-300 border border-blue-500/30 text-[11px] font-semibold transition-all hover:scale-105"
                          >
                            Inspect
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

        {/* Pagination Navigation Footer */}
        <div className="px-4 py-3.5 bg-gradient-to-r from-[#0C1220] via-[#0F172A] to-[#0C1220] border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400 font-mono">
          <div>
            PAGE <strong className="text-white tnum">{page}</strong> OF <strong className="text-white tnum">{totalPages}</strong> ({totalCount} ITEMS)
          </div>

          <div className="flex items-center space-x-1.5">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page === 1}
              className="p-2 rounded-lg bg-slate-900 border border-white/[0.08] text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {/* Page number buttons */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum = page - 2 + i;
              if (pageNum < 1) pageNum = i + 1;
              if (pageNum > totalPages) pageNum = totalPages - 4 + i;
              if (pageNum < 1 || pageNum > totalPages) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={`w-8 h-8 rounded-lg text-xs font-bold transition-all border ${
                    page === pageNum
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-glow-blue border-blue-400/40'
                      : 'bg-slate-900 border-white/[0.08] text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page === totalPages}
              className="p-2 rounded-lg bg-slate-900 border border-white/[0.08] text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

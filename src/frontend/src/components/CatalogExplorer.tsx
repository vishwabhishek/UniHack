import React, { useState, useEffect } from 'react';
import { ProductListItem, FilterOptionItem, CatalogStats } from '../types';
import { fetchProducts, fetchFilters, fetchRAGSearch, fetchStats, RAGSearchResult } from '../services/api';
import { useToast } from './Toast';
import { MetricsBanner } from './MetricsBanner';
import { StatusBadge } from './common/StatusBadge';
import {
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Search,
  X,
  Sparkles,
  Sliders,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  HelpCircle,
  CheckCircle2,
  Info
} from 'lucide-react';

interface CatalogExplorerProps {
  onInspectProduct: (productId: string) => void;
  onEditProduct: (productId: string) => void;
  initialStatus?: string;
  globalSearch?: string;
  onSearchChange?: (q: string) => void;
}

export const CatalogExplorer: React.FC<CatalogExplorerProps> = ({
  onInspectProduct,
  onEditProduct,
  initialStatus = 'All',
  globalSearch = '',
  onSearchChange
}) => {
  const { showToast } = useToast();
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [departments, setDepartments] = useState<FilterOptionItem[]>([]);
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(20);
  const [searchTerm, setSearchTerm] = useState<string>(globalSearch);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>(initialStatus);

  // Search Engine Mode: Keyword (Exact/Lexical) vs Semantic (Hybrid Neural)
  const [searchMode, setSearchMode] = useState<'keyword' | 'semantic'>('keyword');
  const [ragResults, setRagResults] = useState<RAGSearchResult[]>([]);
  const [ragSynthesis, setRagSynthesis] = useState<string>('');
  const [ragLatency, setRagLatency] = useState<number>(0);
  const [denseWeight, setDenseWeight] = useState<number>(0.65);
  const [showSemanticInfo, setShowSemanticInfo] = useState<boolean>(false);

  useEffect(() => {
    setSelectedStatus(initialStatus);
    setPage(1);
  }, [initialStatus]);

  useEffect(() => {
    setSearchTerm(globalSearch);
    setPage(1);
  }, [globalSearch]);

  useEffect(() => {
    loadFiltersAndStats();
  }, []);

  useEffect(() => {
    if (searchMode === 'semantic' && searchTerm.trim()) {
      executeSemanticSearch();
    } else {
      loadData();
    }
  }, [page, limit, searchTerm, selectedCategory, selectedStatus, searchMode, denseWeight]);

  const loadFiltersAndStats = async () => {
    try {
      const filterData = await fetchFilters();
      setDepartments(filterData.departments || []);
      const statsData = await fetchStats();
      setStats(statsData);
    } catch (e) {
      console.error('Failed to load filter options or stats:', e);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchProducts({
        page,
        limit,
        search: searchTerm.trim() ? searchTerm.trim() : undefined,
        category: selectedCategory || undefined,
        status: selectedStatus !== 'All' ? selectedStatus : undefined
      });
      setProducts(res.items || []);
      setTotalCount(res.total || 0);
    } catch (e) {
      console.error('Failed to fetch catalog products:', e);
      showToast('Error', 'Failed to fetch catalog items', 'error');
    } finally {
      setLoading(false);
    }
  };

  const executeSemanticSearch = async () => {
    if (!searchTerm.trim()) {
      loadData();
      return;
    }
    setLoading(true);
    try {
      const res = await fetchRAGSearch({
        q: searchTerm.trim(),
        top_k: 25,
        dense_weight: denseWeight,
        category: selectedCategory || undefined,
        status: selectedStatus !== 'All' ? selectedStatus : undefined
      });
      setRagResults(res.results || []);
      setRagSynthesis(res.synthesis || '');
      setRagLatency(res.latency_ms || 0);
      setTotalCount(res.total_results || 0);
    } catch (e) {
      console.error('Failed to execute semantic search:', e);
      showToast('Search', 'Falling back to keyword search', 'warning');
      setSearchMode('keyword');
      loadData();
    } finally {
      setLoading(false);
    }
  };

  const handleSearchInputChange = (val: string) => {
    setSearchTerm(val);
    setPage(1);
    if (onSearchChange) {
      onSearchChange(val);
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setRagResults([]);
    setRagSynthesis('');
    setPage(1);
    if (onSearchChange) {
      onSearchChange('');
    }
  };

  const handleClearAllFilters = () => {
    setSearchTerm('');
    setSelectedStatus('All');
    setSelectedCategory('');
    setRagResults([]);
    setRagSynthesis('');
    setPage(1);
    if (onSearchChange) {
      onSearchChange('');
    }
  };

  const renderMiniGauge = (score: number) => {
    const active = Math.round(score * 10);
    return (
      <div className="flex items-center gap-1.5">
        <div className="mini-gauge">
          {Array.from({ length: 10 }).map((_, i) => (
            <span
              key={i}
              className={
                i < active
                  ? score >= 0.85
                    ? 'on green'
                    : 'on amber'
                  : ''
              }
            />
          ))}
        </div>
        <span className="font-mono text-xs text-[var(--text-secondary)]">{score.toFixed(2)}</span>
      </div>
    );
  };

  const renderEvidenceStatus = (item: ProductListItem) => {
    if (item.status === 'Validated') {
      return <StatusBadge status="verified" />;
    }
    if (item.validation_flags && item.validation_flags.length > 0) {
      const hasConflict = item.validation_flags.some((f) => f.toLowerCase().includes('conflict'));
      if (hasConflict) {
        return <StatusBadge status="conflict" />;
      }
      return <StatusBadge status="flagged" />;
    }
    if (item.confidence_score < 0.85) {
      return <StatusBadge status="candidate" />;
    }
    return <StatusBadge status="candidate" />;
  };

  const renderStatusChip = (st: string) => {
    return <StatusBadge status={st} />;
  };

  const totalPages = Math.ceil(totalCount / limit) || 1;

  return (
    <div className="space-y-4 font-sans">
      
      {/* Scoped Operational Summary */}
      <MetricsBanner
        stats={stats}
        onFilterStatus={(st) => {
          setSelectedStatus(st);
          setPage(1);
        }}
      />

      {/* Main Table Panel */}
      <div className="panel bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] overflow-hidden">
        
        {/* Panel Controls */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center p-4 border-b border-[var(--border)] gap-3 bg-[var(--surface-1)]">
          
          <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
            {/* Search Mode Switcher */}
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-mono text-[var(--text-muted)] uppercase hidden sm:inline">
                Mode:
              </span>
              <div className="flex items-center bg-[var(--surface-2)] p-0.5 rounded-md border border-[var(--border-strong)] font-mono text-xs">
                <button
                  onClick={() => {
                    setSearchMode('keyword');
                    setPage(1);
                  }}
                  className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                    searchMode === 'keyword'
                      ? 'bg-[var(--surface-1)] text-[var(--text-primary)] font-semibold shadow-xs'
                      : 'text-[var(--text-muted)] hover:text-white'
                  }`}
                >
                  Keyword
                </button>
                <button
                  onClick={() => {
                    setSearchMode('semantic');
                    setPage(1);
                  }}
                  className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all cursor-pointer ${
                    searchMode === 'semantic'
                      ? 'bg-[var(--cyan-bg)] text-[var(--cyan)] font-semibold shadow-xs border border-[var(--cyan)]'
                      : 'text-[var(--text-muted)] hover:text-[var(--cyan)]'
                  }`}
                >
                  <Sparkles className="w-3 h-3 text-[var(--cyan)]" />
                  <span>Semantic</span>
                </button>
              </div>

              <button
                onClick={() => setShowSemanticInfo(!showSemanticInfo)}
                title="About search modes"
                className="p-1 text-[var(--text-muted)] hover:text-white cursor-pointer"
              >
                <Info className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Search Bar */}
            <div className="relative w-full sm:w-72">
              <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => handleSearchInputChange(e.target.value)}
                placeholder={searchMode === 'semantic' ? 'Describe item or specs...' : 'Search MPN, brand, classpath...'}
                className="w-full bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-md pl-9 pr-7 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] font-mono focus:outline-none focus:border-[var(--cyan)]"
              />
              {searchTerm && (
                <button
                  onClick={handleClearSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-white p-0.5 cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto font-mono text-xs">
            {['All', 'Validated', 'Enriched', 'Flagged'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setSelectedStatus(st);
                  setPage(1);
                }}
                className={`chip-filter cursor-pointer transition-colors ${
                  selectedStatus === st
                    ? 'border-[var(--cyan)] text-[var(--cyan)] bg-[var(--cyan-bg)] font-bold'
                    : 'hover:text-[var(--text-primary)]'
                }`}
              >
                {st}
              </button>
            ))}

            {/* Department Dropdown */}
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="chip-filter bg-[var(--surface-2)] text-[var(--text-primary)] border border-[var(--border-strong)] rounded-md px-2.5 py-1 focus:outline-none focus:border-[var(--cyan)] cursor-pointer"
            >
              <option value="" className="bg-[#12161D] text-[#E7EAF0]">All Categories ({totalCount})</option>
              {departments.map((d) => (
                <option key={d.value} value={d.value} className="bg-[#12161D] text-[#E7EAF0]">
                  {d.label}
                </option>
              ))}
            </select>

          </div>
        </div>

        {/* Semantic Search Context Disclosure */}
        {showSemanticInfo && (
          <div className="p-3 bg-[var(--surface-2)] border-b border-[var(--border)] text-xs text-[var(--text-muted)] flex items-start gap-2">
            <Info className="w-4 h-4 text-[var(--cyan)] flex-shrink-0 mt-0.5" />
            <p>
              <b className="text-[var(--text-primary)]">Keyword mode:</b> Exact token and prefix filter over MPN, Brand, and Classpath.
              <br />
              <b className="text-[var(--cyan)]">Semantic mode:</b> Hybrid neural retrieval combining dense text embeddings and lexical BM25 matching.
            </p>
          </div>
        )}

        {/* Catalog Table */}
        <div className="overflow-x-auto">
          <table className="w-full border-collapse font-sans text-xs">
            <thead>
              <tr className="bg-[var(--surface-1)] border-b border-[var(--border)] text-[var(--text-muted)] font-mono text-[11px]">
                <th className="py-3 px-4 text-left font-semibold uppercase">MPN / SKU</th>
                <th className="py-3 px-4 text-left font-semibold uppercase">Product Title / Brand</th>
                <th className="py-3 px-4 text-left font-semibold uppercase">Classpath</th>
                <th className="py-3 px-4 text-left font-semibold uppercase">Evidence Status</th>
                <th className="py-3 px-4 text-left font-semibold uppercase">Confidence</th>
                <th className="py-3 px-4 text-left font-semibold uppercase">Review State</th>
                <th className="py-3 px-4 text-right font-semibold uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={7} className="py-4 px-4">
                      <div className="h-4 bg-[var(--surface-1)] rounded w-full" />
                    </td>
                  </tr>
                ))
              ) : (searchMode === 'semantic' ? ragResults.length === 0 : products.length === 0) ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-[var(--text-muted)] font-mono text-xs space-y-3">
                    <p>No catalog records matching active query &ldquo;{searchTerm}&rdquo; or filter criteria.</p>
                    {(searchTerm || selectedStatus !== 'All' || selectedCategory) && (
                      <button
                        onClick={handleClearAllFilters}
                        className="px-3 py-1.5 rounded-md bg-[var(--surface-1)] border border-[var(--border-strong)] text-[var(--cyan)] hover:underline cursor-pointer"
                      >
                        Reset all filters
                      </button>
                    )}
                  </td>
                </tr>
              ) : searchMode === 'semantic' ? (
                ragResults.map((item) => (
                  <tr
                    key={item.product_id}
                    onClick={() => onInspectProduct(item.product_id)}
                    className="cursor-pointer hover:bg-[var(--surface-1)] transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-[var(--cyan)]">
                      {item.mfg_part_number || item.sku || `SKU-${item.row_id}`}
                    </td>
                    <td className="py-3 px-4 max-w-[260px]">
                      <div className="font-semibold text-[var(--text-primary)] truncate">
                        {item.brand_name}
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)] truncate">
                        {item.match_reason}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-[var(--text-secondary)] font-mono text-[11px] truncate max-w-[200px]" title={item.classpath}>
                      {item.classpath}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                        Hybrid Match ({(item.hybrid_score * 100).toFixed(0)}%)
                      </span>
                    </td>
                    <td className="py-3 px-4">{renderMiniGauge(item.confidence_score)}</td>
                    <td className="py-3 px-4">{renderStatusChip(item.status)}</td>
                    <td className="py-3 px-4 text-right font-mono">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectProduct(item.product_id);
                        }}
                        className="text-xs text-[var(--cyan)] hover:underline inline-flex items-center gap-1 cursor-pointer"
                      >
                        <span>Inspect</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                products.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => onInspectProduct(item.id)}
                    className="cursor-pointer hover:bg-[var(--surface-1)] transition-colors"
                  >
                    <td className="py-3 px-4 font-mono font-bold text-[var(--text-primary)]">
                      {item.mfg_part_number || item.sku || `SKU-${item.row_id}`}
                    </td>
                    <td className="py-3 px-4 max-w-[280px]">
                      <div className="font-semibold text-[var(--text-primary)] truncate" title={item.short_desc || item.product_name}>
                        {item.short_desc || item.product_name || item.brand_name}
                      </div>
                      <div className="text-[11px] text-[var(--cyan)] font-mono">
                        {item.brand_name} · <span className="text-[var(--text-muted)]">{item.manufacturer_name}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-[var(--text-secondary)] font-mono text-[11px] truncate max-w-[220px]" title={item.classpath}>
                      {item.classpath || 'Industrial Component'}
                    </td>
                    <td className="py-3 px-4">{renderEvidenceStatus(item)}</td>
                    <td className="py-3 px-4">{renderMiniGauge(item.confidence_score)}</td>
                    <td className="py-3 px-4">{renderStatusChip(item.status)}</td>
                    <td className="py-3 px-4 text-right font-mono">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectProduct(item.id);
                        }}
                        className="text-xs text-[var(--cyan)] hover:underline inline-flex items-center gap-1 cursor-pointer"
                      >
                        <span>Inspect</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-3 bg-[var(--surface-1)] border-t border-[var(--border)] flex items-center justify-between font-mono text-xs text-[var(--text-muted)]">
          <div>
            Showing <span className="text-[var(--text-primary)] font-bold">{products.length}</span> of{' '}
            <span className="text-[var(--text-primary)] font-bold">{totalCount}</span> items
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="p-1 rounded bg-[var(--surface-2)] border border-[var(--border)] disabled:opacity-40 hover:text-white cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="p-1 rounded bg-[var(--surface-2)] border border-[var(--border)] disabled:opacity-40 hover:text-white cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
};

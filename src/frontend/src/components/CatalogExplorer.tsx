import React, { useState, useEffect, useRef } from 'react';
import { ProductListItem, FilterOptionItem } from '../types';
import { fetchProducts, fetchFilters, fetchRAGSearch, RAGSearchResult } from '../services/api';
import { useToast } from './Toast';
import { ChevronLeft, ChevronRight, ExternalLink, Search, X, Sparkles, Sliders, Zap } from 'lucide-react';

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
  const [loading, setLoading] = useState<boolean>(true);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(20);
  const [searchTerm, setSearchTerm] = useState<string>(globalSearch);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>(initialStatus);

  // Search Engine Mode: Standard Exact/Token vs LlamaIndex Neural RAG
  const [searchMode, setSearchMode] = useState<'standard' | 'rag'>('standard');
  const [ragResults, setRagResults] = useState<RAGSearchResult[]>([]);
  const [ragSynthesis, setRagSynthesis] = useState<string>('');
  const [ragLatency, setRagLatency] = useState<number>(0);
  const [denseWeight, setDenseWeight] = useState<number>(0.65);

  useEffect(() => {
    setSelectedStatus(initialStatus);
    setPage(1);
  }, [initialStatus]);

  useEffect(() => {
    setSearchTerm(globalSearch);
    setPage(1);
  }, [globalSearch]);

  useEffect(() => {
    loadFilters();
  }, []);

  useEffect(() => {
    if (searchMode === 'rag' && searchTerm.trim()) {
      executeRAGSearch();
    } else {
      loadData();
    }
  }, [page, limit, searchTerm, selectedCategory, selectedStatus, searchMode, denseWeight]);

  const loadFilters = async () => {
    try {
      const filterData = await fetchFilters();
      setDepartments(filterData.departments || []);
    } catch (e) {
      console.error('Failed to load filter options:', e);
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

  const executeRAGSearch = async () => {
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
      console.error('Failed to execute LlamaIndex RAG search:', e);
      showToast('RAG Search', 'Falling back to standard search', 'error');
      setSearchMode('standard');
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
      <div className="flex items-center">
        <div className="mini-gauge">
          {Array.from({ length: 10 }).map((_, i) => (
            <span
              key={i}
              className={
                i < active
                  ? score >= 0.85
                    ? 'on'
                    : 'on amber'
                  : ''
              }
            />
          ))}
        </div>
        <span className="conf-val">{score.toFixed(2)}</span>
      </div>
    );
  };

  const renderStatusChip = (st: string) => {
    const clean = st.toLowerCase();
    if (clean === 'validated') {
      return <span className="chip validated">validated</span>;
    } else if (clean === 'flagged' || clean === 'needs human review') {
      return <span className="chip flagged">flagged</span>;
    } else if (clean === 'draft') {
      return <span className="chip draft">draft</span>;
    } else {
      return <span className="chip enriched">enriched</span>;
    }
  };

  const totalPages = Math.ceil(totalCount / limit) || 1;

  const RAG_PRESETS = [
    'quiet dishwasher 120V stainless steel',
    'heavy duty diablo sanding disc for wood',
    'milwaukee saw blade 18 TPI',
    '3M abrasive wheel'
  ];

  return (
    <div className="panel bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] overflow-hidden font-sans">
      
      {/* Panel Head */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center p-[16px_18px] border-b border-[var(--border)] gap-3">
        
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto">
          <h3 className="text-[13px] font-semibold text-[var(--text-primary)] whitespace-nowrap">
            Catalog explorer
          </h3>

          {/* Mode Switcher */}
          <div className="flex items-center bg-[var(--surface-1)] p-0.5 rounded-lg border border-[var(--border-strong)] font-mono text-[11px]">
            <button
              onClick={() => {
                setSearchMode('standard');
                setPage(1);
              }}
              className={`px-2.5 py-1 rounded transition-all cursor-pointer ${
                searchMode === 'standard'
                  ? 'bg-[var(--surface-2)] text-[var(--text-primary)] font-semibold shadow-sm'
                  : 'text-[var(--text-muted)] hover:text-white'
              }`}
            >
              Exact Filter
            </button>
            <button
              onClick={() => {
                setSearchMode('rag');
                setPage(1);
              }}
              className={`px-2.5 py-1 rounded flex items-center gap-1.5 transition-all cursor-pointer ${
                searchMode === 'rag'
                  ? 'bg-[var(--cyan-bg)] text-[var(--cyan)] font-semibold shadow-sm border border-[var(--cyan)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--cyan)]'
              }`}
            >
              <Sparkles className="w-3 h-3 text-[var(--cyan)]" />
              <span>LlamaIndex RAG</span>
            </button>
          </div>

          {/* Search Input Bar */}
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => handleSearchInputChange(e.target.value)}
              placeholder={searchMode === 'rag' ? "Ask natural language question..." : "search SKU, MPN, brand, UNSPSC…"}
              className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md pl-9 pr-7 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] font-mono focus:outline-none focus:border-[var(--cyan)]"
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

        {/* Filter Chips & Dropdowns */}
        <div className="flex flex-wrap items-center gap-2 w-full lg:w-auto">
          {/* Status Quick Filters */}
          {['All', 'Validated', 'Enriched', 'Flagged'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setSelectedStatus(st);
                setPage(1);
              }}
              className={`chip-filter cursor-pointer transition-colors ${
                selectedStatus === st
                  ? 'border-[var(--cyan)] text-[var(--cyan)] bg-[var(--cyan-bg)]'
                  : 'hover:text-[var(--text-primary)]'
              }`}
            >
              status: {st.toLowerCase()}
            </button>
          ))}

          {/* Department Selector */}
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
            className="chip-filter bg-[var(--surface-1)] text-[var(--text-secondary)] focus:outline-none cursor-pointer"
          >
            <option value="">all categories ({totalCount})</option>
            {departments.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* RAG Synthesis & Prompt Suggestions (When in RAG Mode) */}
      {searchMode === 'rag' && (
        <div className="p-[12px_18px] bg-[var(--bg)] border-b border-[var(--border)] font-mono text-xs space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-[11px]">
              <span className="text-[var(--cyan)] flex items-center gap-1 font-semibold">
                <Sparkles className="w-3.5 h-3.5" />
                <span>LLAMAININDEX HYBRID RETRIEVAL:</span>
              </span>
              <span className="text-[var(--text-muted)]">
                FastEmbed BAAI/bge-small-en-v1.5 + BM25 Lexical Fusion
              </span>
            </div>

            {ragLatency > 0 && (
              <div className="flex items-center gap-2 text-[11px] text-[var(--green)]">
                <Zap className="w-3 h-3" />
                <span>{ragLatency.toFixed(1)} ms latency</span>
              </div>
            )}
          </div>

          {ragSynthesis && (
            <div className="p-2.5 bg-[var(--surface-1)] rounded border border-[var(--cyan)]/30 text-[11px] text-[var(--text-primary)]">
              {ragSynthesis}
            </div>
          )}

          {/* Quick RAG Sample Prompts */}
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[10px] text-[var(--text-muted)]">TRY PROMPTS:</span>
            {RAG_PRESETS.map((p) => (
              <button
                key={p}
                onClick={() => handleSearchInputChange(p)}
                className="px-2 py-0.5 rounded bg-[var(--surface-1)] border border-[var(--border-strong)] text-[10px] text-[var(--text-secondary)] hover:text-[var(--cyan)] hover:border-[var(--cyan)] cursor-pointer"
              >
                &ldquo;{p}&rdquo;
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <colgroup>
            <col style={{ width: '18%' }} />
            <col style={{ width: '15%' }} />
            <col style={{ width: searchMode === 'rag' ? '22%' : '28%' }} />
            {searchMode === 'rag' && <col style={{ width: '15%' }} />}
            <col style={{ width: '14%' }} />
            <col style={{ width: '8%' }} />
            <col style={{ width: '8%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>SKU / MPN</th>
              <th>Brand</th>
              <th>{searchMode === 'rag' ? 'Classpath / Reason' : 'Classpath'}</th>
              {searchMode === 'rag' && <th>Hybrid Match Score</th>}
              <th>Confidence</th>
              <th>Status</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={searchMode === 'rag' ? 7 : 6} className="py-4 px-[18px]">
                    <div className="h-4 bg-[var(--surface-1)] rounded w-full" />
                  </td>
                </tr>
              ))
            ) : (searchMode === 'rag' ? ragResults.length === 0 : products.length === 0) ? (
              <tr>
                <td colSpan={searchMode === 'rag' ? 7 : 6} className="py-12 text-center text-[var(--text-muted)] font-mono text-xs space-y-3">
                  <p>No catalog records matching active query &quot;{searchTerm}&quot; or filter criteria.</p>
                  {(searchTerm || selectedStatus !== 'All' || selectedCategory) && (
                    <button
                      onClick={handleClearAllFilters}
                      className="px-3 py-1.5 rounded-md bg-[var(--surface-1)] border border-[var(--border-strong)] text-[var(--cyan)] hover:underline cursor-pointer"
                    >
                      Clear search &amp; reset all filters
                    </button>
                  )}
                </td>
              </tr>
            ) : searchMode === 'rag' ? (
              ragResults.map((item) => (
                <tr
                  key={item.product_id}
                  onClick={() => onInspectProduct(item.product_id)}
                  className="cursor-pointer hover:bg-[rgba(255,255,255,0.015)] transition-colors"
                >
                  <td className="mono cell-primary">
                    {item.mfg_part_number || item.sku || `SKU-${item.row_id}`}
                  </td>
                  <td className="cell-secondary">{item.brand_name || '— unresolved —'}</td>
                  <td className="cell-secondary">
                    <div className="truncate max-w-[240px]" title={item.classpath}>
                      {item.classpath}
                    </div>
                    <div className="text-[10px] text-[var(--cyan)] truncate max-w-[240px]">
                      {item.match_reason}
                    </div>
                  </td>
                  <td>
                    <div className="font-mono text-xs flex items-center gap-1.5">
                      <span className="font-semibold text-[var(--green)]">{(item.hybrid_score * 100).toFixed(1)}%</span>
                      <span className="text-[9px] text-[var(--text-muted)]">(D: {item.dense_score.toFixed(2)} | B: {item.bm25_score.toFixed(2)})</span>
                    </div>
                  </td>
                  <td>{renderMiniGauge(item.confidence_score)}</td>
                  <td>{renderStatusChip(item.status)}</td>
                  <td className="text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectProduct(item.product_id);
                      }}
                      className="text-[11px] font-mono text-[var(--cyan)] hover:underline inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>inspect</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              products.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => onInspectProduct(item.id)}
                  className="cursor-pointer hover:bg-[rgba(255,255,255,0.015)] transition-colors"
                >
                  <td className="mono cell-primary">
                    {item.mfg_part_number || item.sku || `SKU-${item.row_id}`}
                  </td>
                  <td className="cell-secondary">{item.brand_name || '— unresolved —'}</td>
                  <td className="cell-secondary truncate max-w-[280px]" title={item.classpath}>
                    {item.classpath || 'Industrial Component'}
                  </td>
                  <td>{renderMiniGauge(item.confidence_score)}</td>
                  <td>{renderStatusChip(item.status)}</td>
                  <td className="text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onInspectProduct(item.id);
                      }}
                      className="text-[11px] font-mono text-[var(--cyan)] hover:underline inline-flex items-center gap-1 cursor-pointer"
                    >
                      <span>inspect</span>
                      <ExternalLink className="w-2.5 h-2.5" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Bar */}
      <div className="flex items-center justify-between p-[12px_18px] border-t border-[var(--border)] font-mono text-xs text-[var(--text-muted)]">
        <div>
          Showing <span className="text-[var(--text-primary)]">{searchMode === 'rag' ? ragResults.length : products.length}</span> of{' '}
          <span className="text-[var(--text-primary)]">{totalCount}</span> SKUs
          {searchTerm && (
            <span className="text-[var(--cyan)] ml-2">
              ({searchMode === 'rag' ? 'semantic neural RAG query' : 'matching'} &quot;{searchTerm}&quot;)
            </span>
          )}
        </div>

        {searchMode !== 'rag' && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1 rounded bg-[var(--surface-1)] border border-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white disabled:opacity-30 cursor-pointer"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span>
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="p-1 rounded bg-[var(--surface-1)] border border-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white disabled:opacity-30 cursor-pointer"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>

    </div>
  );
};

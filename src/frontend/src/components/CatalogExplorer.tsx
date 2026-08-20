import React, { useState, useEffect, useRef } from 'react';
import { ProductListItem, FilterOptionItem } from '../types';
import { fetchProducts, fetchFilters } from '../services/api';
import { useToast } from './Toast';
import { ChevronLeft, ChevronRight, ExternalLink, Search, X } from 'lucide-react';

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

  const debounceTimerRef = useRef<any>(null);

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
    loadData();
  }, [page, limit, searchTerm, selectedCategory, selectedStatus]);

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

  const handleSearchInputChange = (val: string) => {
    setSearchTerm(val);
    setPage(1);
    if (onSearchChange) {
      onSearchChange(val);
    }
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setPage(1);
    if (onSearchChange) {
      onSearchChange('');
    }
  };

  const handleClearAllFilters = () => {
    setSearchTerm('');
    setSelectedStatus('All');
    setSelectedCategory('');
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

  return (
    <div className="panel bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] overflow-hidden font-sans">
      
      {/* Panel Head */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center p-[16px_18px] border-b border-[var(--border)] gap-3">
        
        <div className="flex items-center gap-3 w-full lg:w-auto justify-between lg:justify-start">
          <h3 className="text-[13px] font-semibold text-[var(--text-primary)] whitespace-nowrap">
            Catalog explorer
          </h3>

          {/* In-Panel Search Bar */}
          <div className="relative w-full sm:w-72">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => handleSearchInputChange(e.target.value)}
              placeholder="search SKU, MPN, brand, UNSPSC…"
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

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <colgroup>
            <col style={{ width: '18%' }} />
            <col style={{ width: '15%' }} />
            <col style={{ width: '28%' }} />
            <col style={{ width: '16%' }} />
            <col style={{ width: '11%' }} />
            <col style={{ width: '12%' }} />
          </colgroup>
          <thead>
            <tr>
              <th>SKU / MPN</th>
              <th>Brand</th>
              <th>Classpath</th>
              <th>Confidence</th>
              <th>Status</th>
              <th className="text-right">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={6} className="py-4 px-[18px]">
                    <div className="h-4 bg-[var(--surface-1)] rounded w-full" />
                  </td>
                </tr>
              ))
            ) : products.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-[var(--text-muted)] font-mono text-xs space-y-3">
                  <p>No catalog records matching active search query &quot;{searchTerm}&quot; or filter criteria.</p>
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
          Showing <span className="text-[var(--text-primary)]">{products.length}</span> of{' '}
          <span className="text-[var(--text-primary)]">{totalCount}</span> SKUs
          {searchTerm && (
            <span className="text-[var(--cyan)] ml-2">
              (matching &quot;{searchTerm}&quot;)
            </span>
          )}
        </div>

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
      </div>

    </div>
  );
};

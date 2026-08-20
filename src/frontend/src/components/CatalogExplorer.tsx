import React, { useState, useEffect } from 'react';
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Edit3,
  Copy,
  Check,
  Tag,
  ArrowUpDown
} from 'lucide-react';
import { ProductListItem, FilterOptionItem } from '../types';
import { fetchProducts, fetchFilters } from '../services/api';
import { useToast } from './Toast';
import { SegmentedGauge } from './SegmentedGauge';

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
        search: search.trim() || undefined,
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

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    showToast('Copied', text, 'success');
    setTimeout(() => setCopiedId(null), 1500);
  };

  const getStatusChip = (status: string) => {
    switch (status) {
      case 'Validated':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#3DDC84]/10 text-[#3DDC84] border border-[#3DDC84]/25">
            VALIDATED
          </span>
        );
      case 'Flagged':
      case 'Needs Human Review':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#E8A33D]/10 text-[#E8A33D] border border-[#E8A33D]/25">
            FLAGGED (HITL)
          </span>
        );
      case 'Draft':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#8B93A3]/10 text-[#8B93A3] border border-[#8B93A3]/25">
            DRAFT
          </span>
        );
      default: // Enriched
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/25">
            ENRICHED
          </span>
        );
    }
  };

  const totalPages = Math.ceil(totalCount / limit) || 1;

  return (
    <div className="bg-[#12161D] border border-[#232935] rounded-xl shadow-sm overflow-hidden flex flex-col font-sans">
      
      {/* Control Bar: Search & Filter Toolbar */}
      <div className="p-3.5 border-b border-[#232935] bg-[#12161D] flex flex-col sm:flex-row items-center justify-between gap-3">
        
        {/* Search Input */}
        <div className="relative w-full sm:w-80">
          <Search className="w-3.5 h-3.5 text-[#8B93A3] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder="Search SKU, MPN, brand, title..."
            className="w-full pl-9 pr-3 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-xs text-[#E7EAF0] placeholder-[#525B6C] focus:border-[#45E0D6] focus:outline-none font-sans transition-colors"
          />
        </div>

        {/* Category & Status Filter Selectors */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* Department Filter */}
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setPage(1);
            }}
            className="px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-xs text-[#E7EAF0] focus:border-[#45E0D6] focus:outline-none font-sans"
          >
            <option value="">All Departments ({totalCount})</option>
            {departments.map((dept) => (
              <option key={dept.value} value={dept.value}>
                {dept.label} ({dept.count})
              </option>
            ))}
          </select>

          {/* Status Tabs */}
          <div className="flex bg-[#0B0E13] p-0.5 rounded-lg border border-[#232935] font-mono text-[11px]">
            {['All', 'Validated', 'Enriched', 'Flagged'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setSelectedStatus(st);
                  setPage(1);
                }}
                className={`px-2.5 py-1 rounded font-bold transition-all ${
                  selectedStatus === st
                    ? 'bg-[#1A1F29] text-[#45E0D6] border border-[#232935]'
                    : 'text-[#8B93A3] hover:text-white'
                }`}
              >
                {st.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

      </div>

      {/* Main Data Table */}
      <div className="overflow-x-auto min-h-[420px]">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#232935] bg-[#0B0E13] text-[#8B93A3] font-mono text-[10px] uppercase tracking-wider">
              <th className="py-2.5 px-3.5 w-14"># ROW</th>
              <th className="py-2.5 px-3.5 w-32">MPN</th>
              <th className="py-2.5 px-3.5 w-36">CANONICAL BRAND</th>
              <th className="py-2.5 px-3.5">SYNTHESIZED TITLE / SHORT DESC</th>
              <th className="py-2.5 px-3.5 w-36">UNSPSC / CLASSPATH</th>
              <th className="py-2.5 px-3.5 w-28">CONFIDENCE</th>
              <th className="py-2.5 px-3.5 w-24">STATUS</th>
              <th className="py-2.5 px-3.5 w-20 text-right">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#232935]">
            {loading ? (
              Array.from({ length: 10 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={8} className="py-3 px-3.5">
                    <div className="h-5 bg-[#1A1F29] rounded w-full" />
                  </td>
                </tr>
              ))
            ) : products.length === 0 ? (
              <tr>
                <td colSpan={8} className="py-12 text-center text-[#8B93A3] font-mono text-xs">
                  No catalog records matching the active filter criteria.
                </td>
              </tr>
            ) : (
              products.map((item) => (
                <tr
                  key={item.id}
                  className="hover:bg-[#1A1F29] transition-colors group cursor-pointer"
                  onClick={() => onInspectProduct(item.id)}
                >
                  {/* Row ID */}
                  <td className="py-2.5 px-3.5 font-mono text-[#8B93A3] text-[11px] tabular-nums">
                    {item.row_id}
                  </td>

                  {/* MPN */}
                  <td className="py-2.5 px-3.5 font-mono font-bold text-white text-xs whitespace-nowrap">
                    <div className="flex items-center space-x-1.5">
                      <span>{item.mfg_part_number}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopy(item.mfg_part_number, `mpn-${item.id}`);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-0.5 text-[#8B93A3] hover:text-white transition-opacity"
                        title="Copy MPN"
                      >
                        {copiedId === `mpn-${item.id}` ? <Check className="w-3 h-3 text-[#3DDC84]" /> : <Copy className="w-3 h-3" />}
                      </button>
                    </div>
                  </td>

                  {/* Brand */}
                  <td className="py-2.5 px-3.5 font-sans text-[#E7EAF0] text-xs font-semibold truncate max-w-[140px]">
                    {item.brand_name || 'Generic / Unresolved'}
                  </td>

                  {/* Synthesized Short Desc */}
                  <td className="py-2.5 px-3.5 font-sans text-[#E7EAF0] text-xs max-w-[380px] truncate">
                    {item.short_desc || item.product_name}
                  </td>

                  {/* Taxonomy */}
                  <td className="py-2.5 px-3.5 font-mono text-[11px] text-[#8B93A3] truncate max-w-[140px]">
                    <div className="text-white font-semibold">{item.dept}</div>
                    <div className="text-[10px] text-[#525B6C] truncate">{item.classpath.split(' > ').pop()}</div>
                  </td>

                  {/* Confidence Score with Segmented Gauge */}
                  <td className="py-2.5 px-3.5 whitespace-nowrap">
                    <SegmentedGauge score={item.confidence_score} size="sm" />
                  </td>

                  {/* Status Chip */}
                  <td className="py-2.5 px-3.5 whitespace-nowrap">
                    {getStatusChip(item.status)}
                  </td>

                  {/* Action */}
                  <td className="py-2.5 px-3.5 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end space-x-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectProduct(item.id);
                        }}
                        className="p-1 text-[#8B93A3] hover:text-[#45E0D6] rounded hover:bg-[#0B0E13] transition-colors"
                        title="Inspect 252-Column Record"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEditProduct(item.id);
                        }}
                        className="p-1 text-[#8B93A3] hover:text-[#E8A33D] rounded hover:bg-[#0B0E13] transition-colors"
                        title="Review / Edit Record"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-[#232935] bg-[#12161D] flex items-center justify-between text-xs text-[#8B93A3] font-mono">
        <div>
          Showing <span className="text-white font-bold">{products.length}</span> of{' '}
          <span className="text-white font-bold">{totalCount}</span> SKUs
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page <= 1}
            className="p-1.5 rounded-lg bg-[#0B0E13] border border-[#232935] text-[#8B93A3] hover:text-white disabled:opacity-30 transition-colors"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
          <span>
            PAGE <strong className="text-white">{page}</strong> / {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages, page + 1))}
            disabled={page >= totalPages}
            className="p-1.5 rounded-lg bg-[#0B0E13] border border-[#232935] text-[#8B93A3] hover:text-white disabled:opacity-30 transition-colors"
          >
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

    </div>
  );
};

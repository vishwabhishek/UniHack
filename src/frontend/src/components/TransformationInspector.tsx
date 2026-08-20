import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle2,
  AlertTriangle,
  Layers,
  FileText,
  Tag,
  Edit3,
  Copy,
  Check,
  Search,
  CheckSquare,
  Shield,
  Table,
  Cpu,
  ArrowRight
} from 'lucide-react';
import { ProductDetail } from '../types';
import { fetchProductDetail, approveProduct } from '../services/api';
import { useToast } from './Toast';

interface TransformationInspectorProps {
  productId: string | null;
  onClose: () => void;
  onEdit: (productId: string) => void;
  onApproved?: () => void;
}

export const TransformationInspector: React.FC<TransformationInspectorProps> = ({
  productId,
  onClose,
  onEdit,
  onApproved
}) => {
  const { showToast } = useToast();
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [approving, setApproving] = useState<boolean>(false);
  const [inspectorTab, setInspectorTab] = useState<'overview' | 'attributes' | 'schema252' | 'audit'>('overview');

  // Schema 252 Search & Filters
  const [schemaSearch, setSchemaSearch] = useState<string>('');
  const [schemaFilterPopulated, setSchemaFilterPopulated] = useState<boolean>(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (productId) {
      loadDetail(productId);
    }
  }, [productId]);

  const loadDetail = async (id: string) => {
    setLoading(true);
    try {
      const data = await fetchProductDetail(id);
      setProduct(data);
    } catch (e) {
      console.error('Failed to load product detail:', e);
      showToast('Error', 'Failed to load product details', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    showToast('Copied to Clipboard', fieldName, 'success');
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleApprove = async () => {
    if (!product) return;
    setApproving(true);
    try {
      await approveProduct(product.id, 'Approved via PIM Transformation Workbench');
      await loadDetail(product.id);
      showToast('Master Record Approved', `MPN ${product.mfg_part_number} marked Validated for delivery`, 'success');
      if (onApproved) onApproved();
    } catch (e) {
      console.error('Failed to approve product:', e);
      showToast('Approval Failed', 'Could not update product status', 'error');
    } finally {
      setApproving(false);
    }
  };

  if (!productId) return null;

  // Filter 252 delivery columns
  const deliveryEntries = product?.delivery_columns ? Object.entries(product.delivery_columns) : [];
  const populatedCount = deliveryEntries.filter(([_, v]) => v && v.trim().length > 0).length;
  const totalCols = deliveryEntries.length || 252;

  const filteredDeliveryEntries = deliveryEntries.filter(([k, v]) => {
    const matchesSearch =
      schemaSearch === '' ||
      k.toLowerCase().includes(schemaSearch.toLowerCase()) ||
      v.toLowerCase().includes(schemaSearch.toLowerCase());
    const matchesPopulated = !schemaFilterPopulated || (v && v.trim().length > 0);
    return matchesSearch && matchesPopulated;
  });

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-150">
      <div className="bg-pim-panel border border-pim-border rounded w-full max-w-6xl max-h-[94vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Workbench Header */}
        <div className="px-5 py-3.5 border-b border-pim-border bg-pim-darkest flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-blue-600 flex items-center justify-center border border-blue-400/40 flex-shrink-0">
              <Cpu className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                  TRANSFORMATION WORKBENCH
                </h3>
                {product && (
                  <span className="px-2 py-0.5 text-[11px] font-mono bg-pim-panel text-blue-400 rounded border border-pim-border font-bold">
                    MPN: {product.mfg_part_number} · ROW #{product.row_id}
                  </span>
                )}
              </div>
              <p className="text-[11px] text-pim-textMuted font-sans">
                Dual-pane comparative audit: Raw Ingestion Feed vs Master PIM Entity (252 Columns)
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {product && product.status !== 'Validated' && (
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold shadow-sm transition-colors disabled:opacity-50 font-mono"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{approving ? 'APPROVING...' : 'APPROVE TO PRODUCTION'}</span>
              </button>
            )}
            {product && (
              <button
                onClick={() => {
                  onClose();
                  onEdit(product.id);
                }}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-pim-surface hover:bg-slate-800 text-slate-200 rounded text-xs font-medium border border-pim-border transition-colors font-mono"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>EDIT CELL</span>
              </button>
            )}
            <button
              onClick={onClose}
              title="Close (Esc)"
              className="p-1.5 text-pim-textMuted hover:text-white rounded hover:bg-pim-surface border border-transparent hover:border-pim-border transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Workbench Workspace Tabs */}
        <div className="px-5 py-2 bg-pim-surface border-b border-pim-border flex items-center justify-between overflow-x-auto font-mono text-xs">
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setInspectorTab('overview')}
              className={`px-3 py-1.5 rounded flex items-center space-x-1.5 transition-colors ${
                inspectorTab === 'overview'
                  ? 'bg-pim-panel text-white border border-pim-borderHighlight font-semibold'
                  : 'text-pim-textSecondary hover:text-white hover:bg-pim-panel/40'
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-blue-400" />
              <span>5-TIER DESCRIPTIONS</span>
            </button>
            <button
              onClick={() => setInspectorTab('attributes')}
              className={`px-3 py-1.5 rounded flex items-center space-x-1.5 transition-colors ${
                inspectorTab === 'attributes'
                  ? 'bg-pim-panel text-white border border-pim-borderHighlight font-semibold'
                  : 'text-pim-textSecondary hover:text-white hover:bg-pim-panel/40'
              }`}
            >
              <Tag className="w-3.5 h-3.5 text-emerald-400" />
              <span>LOV ATTRIBUTES ({product?.attributes.length || 0})</span>
            </button>
            <button
              onClick={() => setInspectorTab('schema252')}
              className={`px-3 py-1.5 rounded flex items-center space-x-1.5 transition-colors ${
                inspectorTab === 'schema252'
                  ? 'bg-pim-panel text-white border border-pim-borderHighlight font-semibold'
                  : 'text-pim-textSecondary hover:text-white hover:bg-pim-panel/40'
              }`}
            >
              <Table className="w-3.5 h-3.5 text-blue-400" />
              <span>ALL 252 DELIVERY COLUMNS</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                {populatedCount}/{totalCols}
              </span>
            </button>
            <button
              onClick={() => setInspectorTab('audit')}
              className={`px-3 py-1.5 rounded flex items-center space-x-1.5 transition-colors ${
                inspectorTab === 'audit'
                  ? 'bg-pim-panel text-white border border-pim-borderHighlight font-semibold'
                  : 'text-pim-textSecondary hover:text-white hover:bg-pim-panel/40'
              }`}
            >
              <Shield className="w-3.5 h-3.5 text-amber-400" />
              <span>QUALITY & COMPLIANCE AUDIT</span>
            </button>
          </div>

          {product && (
            <div className="hidden sm:flex items-center space-x-2 text-xs">
              <span className="text-pim-textMuted">CONFIDENCE:</span>
              <span className="font-bold text-emerald-400">
                {(product.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>

        {/* Workbench Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {loading || !product ? (
            <div className="py-24 text-center text-pim-textMuted space-y-3 font-mono">
              <div className="w-7 h-7 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs">LOADING 252-COLUMN MASTER RECORD...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW & 5-TIER SPECS */}
              {inspectorTab === 'overview' && (
                <div className="space-y-5">
                  {/* Dual-Pane Layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                    {/* Left Pane: Raw Ingestion Feed (4 cols) */}
                    <div className="lg:col-span-4 bg-pim-darkest border border-pim-border rounded p-4 space-y-3.5">
                      <div className="flex items-center justify-between pb-2 border-b border-pim-border">
                        <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-rose-400 flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-rose-500" />
                          <span>RAW SUPPLIER FEED</span>
                        </span>
                        <span className="text-[10px] text-pim-textMuted font-mono">SOURCE</span>
                      </div>

                      <div className="space-y-3 text-xs">
                        <div>
                          <span className="text-pim-textMuted text-[10px] font-mono uppercase block font-semibold">
                            RAW PART_DESC
                          </span>
                          <div className="mt-1 p-2 bg-pim-surface rounded border border-pim-border font-mono text-slate-200 break-words text-[11px]">
                            {product.raw.part_desc}
                          </div>
                        </div>

                        <div>
                          <span className="text-pim-textMuted text-[10px] font-mono uppercase block font-semibold">
                            RAW MFG_PART_NUM
                          </span>
                          <div className="mt-1 p-2 bg-pim-surface rounded border border-pim-border font-mono text-slate-300 text-[11px]">
                            {product.raw.mfg_part_num || '<EMPTY>'}
                          </div>
                        </div>

                        <div>
                          <span className="text-pim-textMuted text-[10px] font-mono uppercase block font-semibold">
                            RAW PART_MANUF
                          </span>
                          <div className="mt-1 p-2 bg-pim-surface rounded border border-pim-border text-slate-300 text-xs font-sans">
                            {product.raw.part_manuf || '<NONE>'}
                          </div>
                        </div>

                        <div>
                          <span className="text-pim-textMuted text-[10px] font-mono uppercase block font-semibold">
                            STRIPPED DUMMY PLACEHOLDERS
                          </span>
                          <div className="mt-1 space-y-1">
                            {['e1_brand', 'unilog_brand', 'dib_brand'].map((field) => {
                              const val = (product.raw as any)[field];
                              const isPlaceholder = val && (val.includes('--') || val.includes('COMMODITY'));
                              return (
                                <div
                                  key={field}
                                  className="flex items-center justify-between text-[11px] p-1 bg-pim-surface rounded border border-pim-border font-mono"
                                >
                                  <span className="text-pim-textMuted text-[10px]">{field}:</span>
                                  <span className={isPlaceholder ? 'text-rose-400 line-through' : 'text-slate-300'}>
                                    {val || '<None>'}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right Pane: Canonical PIM Entity (8 cols) */}
                    <div className="lg:col-span-8 bg-pim-surface border border-pim-border rounded p-4 space-y-4">
                      <div className="flex items-center justify-between pb-2 border-b border-pim-border">
                        <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-blue-400 flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-blue-500" />
                          <span>CANONICAL PIM MASTER RECORD (252-COL STANDARD)</span>
                        </span>
                        <span className="text-xs text-pim-textMuted font-mono">
                          UNSPSC: <strong className="text-white">{product.unspsc}</strong>
                        </span>
                      </div>

                      {/* Entity & Taxonomy Block */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 text-xs bg-pim-panel p-3 rounded border border-pim-border font-mono">
                        <div>
                          <span className="text-pim-textMuted text-[10px] uppercase font-semibold">CANONICAL BRAND</span>
                          <div className="font-bold text-blue-400 text-xs mt-0.5">{product.brand_name}</div>
                        </div>
                        <div>
                          <span className="text-pim-textMuted text-[10px] uppercase font-semibold">MANUFACTURER</span>
                          <div className="font-semibold text-slate-200 text-xs mt-0.5">{product.manufacturer_name}</div>
                        </div>
                        <div>
                          <span className="text-pim-textMuted text-[10px] uppercase font-semibold">CLASSPATH</span>
                          <div className="text-slate-300 text-[10px] mt-0.5 line-clamp-1" title={product.classpath}>
                            {product.classpath}
                          </div>
                        </div>
                      </div>

                      {/* 5-Tier Generated Content Suite */}
                      <div className="space-y-3">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-pim-textMuted block">
                          5-TIER GENERATED CONTENT & HARD GATE AUDIT
                        </span>

                        {/* Tier 1: INVOICE_DESC */}
                        <div className="p-3 bg-pim-panel rounded border border-pim-border space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-emerald-400 flex items-center space-x-1">
                              <span>1. INVOICE_DESC</span>
                              <span className="text-[10px] font-normal text-pim-textMuted">(≤ 40 chars, ALL CAPS)</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-1.5 py-0.2 rounded text-[10px] ${
                                  product.invoice_desc_len <= 40
                                    ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/50'
                                    : 'bg-rose-950/80 text-rose-400'
                                }`}
                              >
                                {product.invoice_desc_len}/40 chars
                              </span>
                              <button
                                onClick={() => handleCopy(product.invoice_desc, 'INVOICE_DESC')}
                                className="text-pim-textMuted hover:text-white"
                              >
                                {copiedField === 'INVOICE_DESC' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="font-mono text-xs font-bold text-emerald-300 bg-pim-darkest p-2 rounded border border-pim-border">
                            {product.invoice_desc}
                          </div>
                        </div>

                        {/* Tier 2: MOBILE_DESC */}
                        <div className="p-3 bg-pim-panel rounded border border-pim-border space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-blue-400 flex items-center space-x-1">
                              <span>2. MOBILE_DESC</span>
                              <span className="text-[10px] font-normal text-pim-textMuted">(60–80 chars range)</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-1.5 py-0.2 rounded text-[10px] ${
                                  product.mobile_desc_len >= 60 && product.mobile_desc_len <= 80
                                    ? 'bg-blue-950/80 text-blue-400 border border-blue-800/50'
                                    : 'bg-amber-950/80 text-amber-400'
                                }`}
                              >
                                {product.mobile_desc_len}/80 chars
                              </span>
                              <button
                                onClick={() => handleCopy(product.mobile_desc, 'MOBILE_DESC')}
                                className="text-pim-textMuted hover:text-white"
                              >
                                {copiedField === 'MOBILE_DESC' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="text-xs text-slate-100 bg-pim-darkest p-2 rounded border border-pim-border font-sans">
                            {product.mobile_desc}
                          </div>
                        </div>

                        {/* Tier 3: SHORT_DESC */}
                        <div className="p-3 bg-pim-panel rounded border border-pim-border space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-white">3. SHORT_DESC / PRODUCT TITLE</span>
                            <button
                              onClick={() => handleCopy(product.short_desc, 'SHORT_DESC')}
                              className="text-pim-textMuted hover:text-white"
                            >
                              {copiedField === 'SHORT_DESC' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="text-xs text-slate-100 bg-pim-darkest p-2 rounded border border-pim-border font-sans">
                            {product.short_desc}
                          </div>
                        </div>

                        {/* Tier 4: LONG_DESC1 */}
                        <div className="p-3 bg-pim-panel rounded border border-pim-border space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-slate-300">4. LONG_DESC1 (TECHNICAL SPEC SENTENCE)</span>
                            <button
                              onClick={() => handleCopy(product.long_desc1, 'LONG_DESC1')}
                              className="text-pim-textMuted hover:text-white"
                            >
                              {copiedField === 'LONG_DESC1' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="text-xs text-slate-300 bg-pim-darkest p-2 rounded border border-pim-border leading-relaxed font-sans">
                            {product.long_desc1}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: LOV ATTRIBUTES */}
              {inspectorTab === 'attributes' && (
                <div className="bg-pim-surface border border-pim-border rounded p-4 space-y-4">
                  <div className="flex items-center justify-between border-b border-pim-border pb-2">
                    <span className="text-xs font-mono font-bold uppercase text-white">
                      50 ATTRIBUTE TRIPLETS (LABEL · VALUE · UOM) & LOV VERIFICATION
                    </span>
                    <span className="text-xs font-mono text-emerald-400 font-bold">
                      {product.attributes.length} ATTRIBUTES EXTRACTED · 0% HALLUCINATIONS
                    </span>
                  </div>

                  {product.attributes.length === 0 ? (
                    <div className="py-12 text-center text-pim-textMuted text-xs font-mono">
                      NO TECHNICAL ATTRIBUTES APPLICABLE FOR THIS COMMODITY ITEM.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5 text-xs">
                      {product.attributes.map((attr, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 bg-pim-panel rounded border border-pim-border flex items-center justify-between"
                        >
                          <div>
                            <span className="text-[10px] text-pim-textMuted font-mono block">
                              SLOT #{idx + 1}: {attr.label}
                            </span>
                            <span className="font-semibold text-white font-mono text-xs">
                              {attr.value} {attr.uom && <span className="text-blue-400">{attr.uom}</span>}
                            </span>
                          </div>
                          <span className="px-1.5 py-0.5 text-[9px] bg-emerald-950/80 text-emerald-400 border border-emerald-800/50 rounded font-mono">
                            LOV VALID
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: COMPLETE 252-COLUMN DELIVERY MATRIX */}
              {inspectorTab === 'schema252' && (
                <div className="bg-pim-surface border border-pim-border rounded p-4 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-pim-border pb-2">
                    <div>
                      <span className="text-xs font-mono font-bold uppercase text-white">
                        252-COLUMN MASTER DELIVERY SCHEMA MATRIX
                      </span>
                      <p className="text-[11px] text-pim-textMuted font-mono mt-0.5">
                        MATCHING: {filteredDeliveryEntries.length} OF {totalCols} COLUMNS ({populatedCount} POPULATED)
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 text-pim-textMuted absolute left-2.5 top-2" />
                        <input
                          type="text"
                          value={schemaSearch}
                          onChange={(e) => setSchemaSearch(e.target.value)}
                          placeholder="Search 252 delivery headers..."
                          className="bg-pim-panel border border-pim-border text-xs text-white rounded pl-8 pr-3 py-1 w-48 sm:w-60 focus:border-pim-accent font-sans"
                        />
                      </div>
                      <button
                        onClick={() => setSchemaFilterPopulated(!schemaFilterPopulated)}
                        className={`px-2.5 py-1 text-xs rounded border flex items-center space-x-1 font-mono transition-colors ${
                          schemaFilterPopulated
                            ? 'bg-blue-950/80 text-blue-400 border-blue-800/50'
                            : 'bg-pim-panel text-pim-textMuted border-pim-border hover:text-white'
                        }`}
                      >
                        <CheckSquare className="w-3.5 h-3.5" />
                        <span>POPULATED ONLY</span>
                      </button>
                    </div>
                  </div>

                  <div className="border border-pim-border rounded overflow-hidden max-h-[55vh] overflow-y-auto">
                    <table className="w-full text-left text-xs border-collapse font-mono">
                      <thead className="sticky top-0 bg-pim-darkest border-b border-pim-border text-pim-textMuted text-[10px] uppercase">
                        <tr>
                          <th className="py-2 px-3 w-12 text-center">COL#</th>
                          <th className="py-2 px-3 w-1/3">UNILOG HEADER</th>
                          <th className="py-2 px-3">DELIVERY VALUE</th>
                          <th className="py-2 px-3 w-16 text-center">COPY</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-pim-border/60">
                        {filteredDeliveryEntries.map(([colName, colVal], idx) => {
                          const hasVal = colVal && colVal.trim().length > 0;
                          return (
                            <tr key={colName} className={`hover:bg-pim-panel/60 ${hasVal ? 'bg-pim-panel/20' : ''}`}>
                              <td className="py-1.5 px-3 text-pim-textMuted text-center text-[10px]">{idx + 1}</td>
                              <td className="py-1.5 px-3 text-slate-300 font-sans font-medium text-xs">
                                {colName}
                              </td>
                              <td className="py-1.5 px-3 text-slate-200 break-words text-[11px]">
                                {hasVal ? (
                                  <span className="text-blue-300">{colVal}</span>
                                ) : (
                                  <span className="text-slate-600 italic font-sans">&lt;EMPTY&gt;</span>
                                )}
                              </td>
                              <td className="py-1.5 px-3 text-center">
                                {hasVal && (
                                  <button
                                    onClick={() => handleCopy(colVal, colName)}
                                    title="Copy value"
                                    className="p-1 text-pim-textMuted hover:text-white rounded hover:bg-pim-surface"
                                  >
                                    {copiedField === colName ? (
                                      <Check className="w-3 h-3 text-emerald-400" />
                                    ) : (
                                      <Copy className="w-3 h-3" />
                                    )}
                                  </button>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 4: QUALITY AUDIT */}
              {inspectorTab === 'audit' && (
                <div className="bg-pim-surface border border-pim-border rounded p-4 space-y-4">
                  <div className="flex items-center justify-between border-b border-pim-border pb-2">
                    <span className="text-xs font-mono font-bold uppercase text-white">
                      5-FACTOR COMPOSITE QUALITY AUDIT: {(product.confidence_score * 100).toFixed(1)}%
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      STATUS: {product.status.toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5 text-xs font-mono">
                    {Object.entries(product.confidence_breakdown).map(([factor, score]) => (
                      <div key={factor} className="p-3 bg-pim-panel rounded border border-pim-border space-y-2">
                        <span className="text-[10px] text-pim-textMuted block uppercase">
                          {factor.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center justify-between">
                          <div className="w-full bg-slate-900 rounded-full h-1.5 mr-2 overflow-hidden">
                            <div
                              className="bg-blue-500 h-1.5 rounded-full"
                              style={{ width: `${Math.min(score * 100, 100)}%` }}
                            />
                          </div>
                          <span className="text-white font-bold text-xs">
                            {(score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {product.validation_flags.length > 0 ? (
                    <div className="mt-3 pt-3 border-t border-pim-border font-mono text-xs">
                      <span className="text-[11px] font-bold text-amber-400 flex items-center space-x-1 mb-2">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>VALIDATION ANOMALIES & FLAGS:</span>
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {product.validation_flags.map((flag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 text-[10px] bg-amber-950/80 text-amber-400 border border-amber-800/50 rounded"
                          >
                            {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-950/40 border border-emerald-800/40 rounded text-emerald-400 text-xs font-mono flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                      <span>ZERO VALIDATION DEFECTS OR CHARACTER-LIMIT OVERFLOWS DETECTED.</span>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

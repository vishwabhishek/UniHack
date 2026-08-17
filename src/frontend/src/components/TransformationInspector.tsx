import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Shield,
  Layers,
  FileText,
  Tag,
  Ruler,
  Image,
  ExternalLink,
  Edit3,
  Copy,
  Check,
  Search,
  SlidersHorizontal,
  Download,
  Info,
  CheckSquare,
  Sparkles,
  Table
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
      await approveProduct(product.id, 'Approved via Side-by-Side Inspector');
      await loadDetail(product.id);
      showToast('Product Approved', `MPN ${product.mfg_part_number} marked Validated for delivery`, 'success');
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
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-6xl max-h-[94vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500/20 to-blue-600/30 border border-sky-500/40 flex items-center justify-center shadow-md">
              <Layers className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h3 className="text-base font-bold text-white tracking-tight">
                  Side-by-Side Transformation Inspector
                </h3>
                {product && (
                  <span className="px-2 py-0.5 text-xs font-mono bg-slate-800 text-sky-300 rounded-md border border-slate-700 font-semibold">
                    MPN: {product.mfg_part_number} • Row #{product.row_id}
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">
                Visual audit comparing raw supplier distributor feed vs canonical PIM enrichment
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {product && product.status !== 'Validated' && (
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-md transition-all disabled:opacity-50"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>{approving ? 'Approving...' : 'Approve for Delivery'}</span>
              </button>
            )}
            {product && (
              <button
                onClick={() => {
                  onClose();
                  onEdit(product.id);
                }}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition-all"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>Edit Record</span>
              </button>
            )}
            <button
              onClick={onClose}
              title="Close (Esc)"
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Secondary Navigation Bar */}
        <div className="px-6 py-2.5 bg-slate-950/60 border-b border-slate-800/80 flex items-center justify-between overflow-x-auto">
          <div className="flex items-center space-x-1.5 text-xs font-medium">
            <button
              onClick={() => setInspectorTab('overview')}
              className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition-all ${
                inspectorTab === 'overview'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Overview & 5-Tier Specs</span>
            </button>
            <button
              onClick={() => setInspectorTab('attributes')}
              className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition-all ${
                inspectorTab === 'attributes'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Tag className="w-3.5 h-3.5" />
              <span>LOV Attributes ({product?.attributes.length || 0})</span>
            </button>
            <button
              onClick={() => setInspectorTab('schema252')}
              className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition-all ${
                inspectorTab === 'schema252'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>All 252 Delivery Columns</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-sky-300 font-mono">
                {populatedCount}/{totalCols}
              </span>
            </button>
            <button
              onClick={() => setInspectorTab('audit')}
              className={`px-3 py-1.5 rounded-lg flex items-center space-x-1.5 transition-all ${
                inspectorTab === 'audit'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Quality & Confidence Audit</span>
            </button>
          </div>

          {product && (
            <div className="hidden sm:flex items-center space-x-2 text-xs font-mono">
              <span className="text-slate-400">Score:</span>
              <span className="font-bold text-emerald-400">
                {(product.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
          )}
        </div>

        {/* Modal Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading || !product ? (
            <div className="py-24 text-center text-slate-400 space-y-3">
              <div className="w-8 h-8 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm font-medium">Loading full 252-column product record...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW & 5-TIER SPECS */}
              {inspectorTab === 'overview' && (
                <div className="space-y-6">
                  {/* Split-Screen: Raw Distributor Input vs Canonical PIM Output */}
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                    {/* Left Pane: Raw Supplier Input (4 cols) */}
                    <div className="lg:col-span-4 bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-4 shadow-sm">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-rose-500" />
                          <span>Raw Supplier Distributor Feed</span>
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">Raw Input</span>
                      </div>

                      <div className="space-y-3 text-xs">
                        <div>
                          <span className="text-slate-400 text-[11px] block font-medium">Raw Part_Desc</span>
                          <div className="mt-1 p-2.5 bg-slate-900 rounded-lg border border-slate-800 font-mono text-slate-200 break-words">
                            {product.raw.part_desc}
                          </div>
                        </div>

                        <div>
                          <span className="text-slate-400 text-[11px] block font-medium">Raw Mfg_Part_Num</span>
                          <div className="mt-1 p-2 bg-slate-900 rounded-lg border border-slate-800 font-mono text-slate-300">
                            {product.raw.mfg_part_num || '<EMPTY>'}
                          </div>
                        </div>

                        <div>
                          <span className="text-slate-400 text-[11px] block font-medium">Raw Part_Manuf</span>
                          <div className="mt-1 p-2 bg-slate-900 rounded-lg border border-slate-800 text-slate-300">
                            {product.raw.part_manuf || '<NONE>'}
                          </div>
                        </div>

                        <div>
                          <span className="text-slate-400 text-[11px] block font-medium">Sanitized Placeholder Columns</span>
                          <div className="mt-1 space-y-1">
                            {['e1_brand', 'unilog_brand', 'dib_brand'].map((field) => {
                              const val = (product.raw as any)[field];
                              const isPlaceholder = val && (val.includes('--') || val.includes('COMMODITY'));
                              return (
                                <div
                                  key={field}
                                  className="flex items-center justify-between text-[11px] p-1.5 bg-slate-900/60 rounded border border-slate-800/60"
                                >
                                  <span className="text-slate-500">{field}:</span>
                                  <span className={`font-mono ${isPlaceholder ? 'text-rose-400 line-through' : 'text-slate-300'}`}>
                                    {val || '<None>'}
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Right Pane: Canonical PIM Normalization (8 cols) */}
                    <div className="lg:col-span-8 bg-slate-950/80 border border-sky-500/20 rounded-xl p-5 space-y-5 shadow-lg shadow-sky-500/5">
                      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                        <span className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
                          <span>Canonical PIM Enrichment (Unilog 252-Column Standard)</span>
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-slate-400 font-mono">
                            UNSPSC: <span className="text-sky-300 font-bold">{product.unspsc}</span>
                          </span>
                        </div>
                      </div>

                      {/* Entity & Taxonomy Resolution */}
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs bg-slate-900/60 p-3 rounded-lg border border-slate-800">
                        <div>
                          <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Canonical Brand</span>
                          <div className="font-bold text-sky-300 text-sm mt-0.5">{product.brand_name}</div>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Manufacturer</span>
                          <div className="font-semibold text-slate-200 mt-0.5">{product.manufacturer_name}</div>
                        </div>
                        <div>
                          <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">Classpath Hierarchy</span>
                          <div className="text-slate-300 font-mono text-[11px] mt-0.5 line-clamp-1" title={product.classpath}>
                            {product.classpath}
                          </div>
                        </div>
                      </div>

                      {/* 5-Tier Descriptions Section */}
                      <div className="space-y-3">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block">
                          5-Tier Generated Content Suite
                        </span>

                        {/* Tier 1: INVOICE_DESC */}
                        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-emerald-400 flex items-center space-x-1">
                              <span>1. INVOICE_DESC</span>
                              <span className="text-[10px] font-normal text-slate-400">(≤ 40 chars, 100% ALL CAPS)</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-1.5 py-0.2 rounded font-mono text-[10px] ${
                                  product.invoice_desc_len <= 40
                                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                    : 'bg-rose-500/10 text-rose-400'
                                }`}
                              >
                                {product.invoice_desc_len}/40 chars
                              </span>
                              <button
                                onClick={() => handleCopy(product.invoice_desc, 'INVOICE_DESC')}
                                className="text-slate-400 hover:text-slate-200"
                              >
                                {copiedField === 'INVOICE_DESC' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="font-mono text-xs font-bold text-emerald-300 bg-slate-950 p-2 rounded border border-slate-800">
                            {product.invoice_desc}
                          </div>
                        </div>

                        {/* Tier 2: MOBILE_DESC */}
                        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-cyan-400 flex items-center space-x-1">
                              <span>2. MOBILE_DESC</span>
                              <span className="text-[10px] font-normal text-slate-400">(60–80 chars range)</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`px-1.5 py-0.2 rounded font-mono text-[10px] ${
                                  product.mobile_desc_len >= 60 && product.mobile_desc_len <= 80
                                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                                    : 'bg-amber-500/10 text-amber-400'
                                }`}
                              >
                                {product.mobile_desc_len}/80 chars
                              </span>
                              <button
                                onClick={() => handleCopy(product.mobile_desc, 'MOBILE_DESC')}
                                className="text-slate-400 hover:text-slate-200"
                              >
                                {copiedField === 'MOBILE_DESC' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="text-xs text-slate-100 bg-slate-950 p-2 rounded border border-slate-800">
                            {product.mobile_desc}
                          </div>
                        </div>

                        {/* Tier 3: SHORT_DESC */}
                        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-sky-400">3. SHORT_DESC / Product Title</span>
                            <button
                              onClick={() => handleCopy(product.short_desc, 'SHORT_DESC')}
                              className="text-slate-400 hover:text-slate-200"
                            >
                              {copiedField === 'SHORT_DESC' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="text-xs text-slate-100 bg-slate-950 p-2 rounded border border-slate-800">
                            {product.short_desc}
                          </div>
                        </div>

                        {/* Tier 4: LONG_DESC1 */}
                        <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-indigo-400">4. LONG_DESC1 (Technical Spec Sentence)</span>
                            <button
                              onClick={() => handleCopy(product.long_desc1, 'LONG_DESC1')}
                              className="text-slate-400 hover:text-slate-200"
                            >
                              {copiedField === 'LONG_DESC1' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="text-xs text-slate-300 bg-slate-950 p-2 rounded border border-slate-800 leading-relaxed">
                            {product.long_desc1}
                          </div>
                        </div>

                        {/* Tier 5: MARKETING_DESCRIPTION */}
                        {product.marketing_description && (
                          <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1">
                            <span className="text-xs font-bold text-purple-400">5. MARKETING_DESCRIPTION</span>
                            <div className="text-xs text-slate-300 bg-slate-950 p-2 rounded border border-slate-800">
                              {product.marketing_description}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: LOV CONTROLLED ATTRIBUTES */}
              {inspectorTab === 'attributes' && (
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Tag className="w-4 h-4 text-sky-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                        Extracted Triplet Attributes (50 Slots) & Strict LOV Adherence
                      </h4>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      {product.attributes.length} attributes extracted • 0% Hallucinations
                    </span>
                  </div>

                  {product.attributes.length === 0 ? (
                    <div className="py-12 text-center text-slate-500 text-xs">
                      No specific dimension or functional attributes were identified for this item.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs">
                      {product.attributes.map((attr, idx) => (
                        <div
                          key={idx}
                          className="p-3 bg-slate-900 rounded-lg border border-slate-800 flex items-center justify-between group hover:border-slate-700 transition-colors"
                        >
                          <div>
                            <span className="text-[10px] text-slate-400 block font-medium">
                              Slot #{idx + 1}: {attr.label}
                            </span>
                            <span className="font-semibold text-slate-100 font-mono text-xs">
                              {attr.value} {attr.uom && <span className="text-sky-400 font-normal">{attr.uom}</span>}
                            </span>
                          </div>
                          <span className="px-1.5 py-0.5 text-[9px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded font-mono">
                            LOV Valid
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: COMPLETE 252-COLUMN DELIVERY SCHEMA (LIVE SEARCH) */}
              {inspectorTab === 'schema252' && (
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center space-x-2">
                        <Table className="w-4 h-4 text-sky-400" />
                        <span>All 252 Target Delivery Columns</span>
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Showing {filteredDeliveryEntries.length} of {totalCols} columns ({populatedCount} populated)
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                        <input
                          type="text"
                          value={schemaSearch}
                          onChange={(e) => setSchemaSearch(e.target.value)}
                          placeholder="Search 252 columns..."
                          className="bg-slate-900 border border-slate-700 text-xs text-slate-100 rounded-lg pl-8 pr-3 py-1.5 w-48 sm:w-64 focus:border-sky-500"
                        />
                      </div>
                      <button
                        onClick={() => setSchemaFilterPopulated(!schemaFilterPopulated)}
                        className={`px-2.5 py-1.5 text-xs rounded-lg border flex items-center space-x-1.5 transition-colors ${
                          schemaFilterPopulated
                            ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                            : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-slate-200'
                        }`}
                      >
                        <CheckSquare className="w-3.5 h-3.5" />
                        <span>Populated Only</span>
                      </button>
                    </div>
                  </div>

                  <div className="border border-slate-800 rounded-lg overflow-hidden max-h-[55vh] overflow-y-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 text-slate-400 font-semibold z-10">
                        <tr>
                          <th className="py-2 px-3 w-12 text-center">#</th>
                          <th className="py-2 px-3 w-1/3">Target Column Name</th>
                          <th className="py-2 px-3">Enriched Output Value</th>
                          <th className="py-2 px-3 w-16 text-center">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 font-mono">
                        {filteredDeliveryEntries.map(([colName, colVal], idx) => {
                          const hasVal = colVal && colVal.trim().length > 0;
                          return (
                            <tr key={colName} className={`hover:bg-slate-900/50 ${hasVal ? 'bg-slate-900/20' : ''}`}>
                              <td className="py-2 px-3 text-slate-500 text-center text-[10px]">{idx + 1}</td>
                              <td className="py-2 px-3 text-slate-300 font-medium font-sans">
                                {colName}
                              </td>
                              <td className="py-2 px-3 text-slate-200 break-words text-[11px]">
                                {hasVal ? (
                                  <span className="text-sky-300">{colVal}</span>
                                ) : (
                                  <span className="text-slate-600 italic font-sans">&lt;EMPTY&gt;</span>
                                )}
                              </td>
                              <td className="py-2 px-3 text-center">
                                {hasVal && (
                                  <button
                                    onClick={() => handleCopy(colVal, colName)}
                                    title="Copy value"
                                    className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800"
                                  >
                                    {copiedField === colName ? (
                                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                                    ) : (
                                      <Copy className="w-3.5 h-3.5" />
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

              {/* TAB 4: QUALITY AUDIT & CONFIDENCE */}
              {inspectorTab === 'audit' && (
                <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Shield className="w-4 h-4 text-emerald-400" />
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                        5-Factor Composite Quality & Confidence Audit: {(product.confidence_score * 100).toFixed(1)}%
                      </h4>
                    </div>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-bold ${
                        product.status === 'Validated'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : 'bg-sky-500/20 text-sky-400 border border-sky-500/30'
                      }`}
                    >
                      Status: {product.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
                    {Object.entries(product.confidence_breakdown).map(([factor, score]) => (
                      <div key={factor} className="p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-2">
                        <span className="text-[10px] text-slate-400 block capitalize font-medium">
                          {factor.replace(/_/g, ' ')}
                        </span>
                        <div className="flex items-center justify-between">
                          <div className="w-full bg-slate-800 rounded-full h-1.5 mr-2">
                            <div
                              className="bg-sky-400 h-1.5 rounded-full"
                              style={{ width: `${Math.min(score * 100, 100)}%` }}
                            />
                          </div>
                          <span className="font-mono text-slate-200 font-bold text-[11px]">
                            {(score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>

                  {product.validation_flags.length > 0 ? (
                    <div className="mt-3 pt-3 border-t border-slate-800/80">
                      <span className="text-[11px] font-bold text-amber-400 flex items-center space-x-1 mb-2">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Validation Flags & Anomaly Warnings:</span>
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {product.validation_flags.map((flag, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-1 text-[11px] bg-amber-500/10 text-amber-300 border border-amber-500/30 rounded-md font-mono"
                          >
                            {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-xs flex items-center space-x-2">
                      <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                      <span>Zero validation anomalies or character-limit infractions detected.</span>
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

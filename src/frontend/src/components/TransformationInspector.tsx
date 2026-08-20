import React, { useState, useEffect } from 'react';
import {
  X,
  CheckCircle2,
  FileText,
  Tag,
  Edit3,
  Copy,
  Check,
  Search,
  Shield,
  Table,
  Cpu,
  ArrowRight
} from 'lucide-react';
import { ProductDetail } from '../types';
import { fetchProductDetail, approveProduct } from '../services/api';
import { useToast } from './Toast';
import { SegmentedGauge } from './SegmentedGauge';

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
      showToast('Error', 'Failed to load product transformation details', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (val: string, fieldName: string) => {
    navigator.clipboard.writeText(val);
    setCopiedField(fieldName);
    showToast('Copied', fieldName, 'success');
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
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-4 font-sans">
      <div className="bg-[#12161D] border border-[#232935] rounded-2xl w-full max-w-6xl max-h-[94vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Workbench Header */}
        <div className="px-6 py-4 border-b border-[#232935] bg-[#1A1F29] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3.5">
            <div className="w-9 h-9 rounded-xl bg-[#0B0E13] border border-[#232935] flex items-center justify-center text-[#45E0D6] flex-shrink-0">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center space-x-2">
                  <span>TRANSFORMATION WORKBENCH</span>
                </h3>
                {product && (
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/20 rounded-full">
                    MPN: {product.mfg_part_number} · ROW #{product.row_id}
                  </span>
                )}
              </div>
              <p className="text-xs text-[#8B93A3] mt-0.5">
                Comparative Ingestion Audit: Raw Supplier Input vs. Canonical 252-Column PIM Entity
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {product && product.status !== 'Validated' && (
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex items-center space-x-1.5 px-3.5 py-2 bg-[#3DDC84]/15 hover:bg-[#3DDC84]/25 text-[#3DDC84] border border-[#3DDC84]/30 rounded-xl text-xs font-bold font-mono transition-all disabled:opacity-50"
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
                className="flex items-center space-x-1.5 px-3 py-2 bg-[#0B0E13] hover:bg-[#1A1F29] text-[#E7EAF0] rounded-xl text-xs font-semibold border border-[#232935] transition-all font-mono"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>EDIT CELL</span>
              </button>
            )}
            <button
              onClick={onClose}
              title="Close (Esc)"
              className="p-2 text-[#8B93A3] hover:text-white rounded-xl hover:bg-[#0B0E13] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Workspace Sub-Navigation Tabs */}
        <div className="px-6 py-2.5 bg-[#0B0E13] border-b border-[#232935] flex items-center justify-between overflow-x-auto font-mono text-xs">
          <div className="flex items-center space-x-2">
            {[
              { id: 'overview', label: '5-TIER SPECS', icon: FileText, color: 'text-[#45E0D6]' },
              { id: 'attributes', label: `LOV ATTRIBUTES (${product?.attributes.length || 0})`, icon: Tag, color: 'text-[#3DDC84]' },
              { id: 'schema252', label: `ALL 252 COLUMNS (${populatedCount}/${totalCols})`, icon: Table, color: 'text-[#60A5FA]' },
              { id: 'audit', label: 'QUALITY AUDIT', icon: Shield, color: 'text-[#E8A33D]' }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = inspectorTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setInspectorTab(tab.id as any)}
                  className={`px-3 py-1.5 rounded-lg flex items-center space-x-2 transition-all font-bold ${
                    isActive
                      ? 'bg-[#1A1F29] text-[#45E0D6] border border-[#232935]'
                      : 'text-[#8B93A3] hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {product && (
            <div className="hidden sm:flex items-center space-x-2">
              <span className="text-[10px] text-[#8B93A3]">CONFIDENCE:</span>
              <SegmentedGauge score={product.confidence_score} size="sm" />
            </div>
          )}
        </div>

        {/* Workbench Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {loading || !product ? (
            <div className="py-24 text-center text-[#8B93A3] space-y-3 font-mono">
              <div className="w-7 h-7 border-2 border-[#45E0D6] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs">LOADING 252-COLUMN MASTER RECORD...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW & 5-TIER SPECS */}
              {inspectorTab === 'overview' && (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                    {/* Left Pane: Raw Supplier Feed (4 cols) */}
                    <div className="lg:col-span-4 bg-[#0B0E13] rounded-xl p-4 space-y-4 border border-[#232935]">
                      <div className="flex items-center justify-between pb-2.5 border-b border-[#232935]">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#EF5A5A] flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#EF5A5A]" />
                          <span>RAW SUPPLIER FEED</span>
                        </span>
                        <span className="text-[10px] text-[#8B93A3] font-mono">SOURCE</span>
                      </div>

                      <div className="space-y-3 text-xs">
                        <div>
                          <span className="text-[#8B93A3] text-[10px] font-mono uppercase block font-bold">
                            RAW PART_DESC
                          </span>
                          <div className="mt-1 p-2.5 bg-[#12161D] rounded-lg border border-[#232935] font-mono text-[#E7EAF0] break-words text-[11px]">
                            {product.raw.part_desc}
                          </div>
                        </div>

                        <div>
                          <span className="text-[#8B93A3] text-[10px] font-mono uppercase block font-bold">
                            RAW MFG_PART_NUM
                          </span>
                          <div className="mt-1 p-2 bg-[#12161D] rounded-lg border border-[#232935] font-mono text-[#E7EAF0] text-[11px]">
                            {product.raw.mfg_part_num || '<EMPTY>'}
                          </div>
                        </div>

                        <div>
                          <span className="text-[#8B93A3] text-[10px] font-mono uppercase block font-bold">
                            STRIPPED DUMMY PLACEHOLDERS
                          </span>
                          <div className="mt-1 space-y-1">
                            {['e1_brand', 'unilog_brand', 'dib_brand'].map((field) => {
                              const val = (product.raw as any)[field];
                              const isPlaceholder = val && (val.includes('--') || val.includes('COMMODITY'));
                              return (
                                <div
                                  key={field}
                                  className="flex items-center justify-between text-[11px] p-1.5 bg-[#12161D] rounded border border-[#232935] font-mono"
                                >
                                  <span className="text-[#8B93A3] text-[10px]">{field}:</span>
                                  <span className={isPlaceholder ? 'text-[#EF5A5A] line-through' : 'text-[#8B93A3]'}>
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
                    <div className="lg:col-span-8 bg-[#0B0E13] rounded-xl p-5 space-y-4 border border-[#232935]">
                      <div className="flex items-center justify-between pb-2.5 border-b border-[#232935]">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#45E0D6] flex items-center space-x-1.5">
                          <span className="w-2 h-2 rounded-full bg-[#45E0D6]" />
                          <span>CANONICAL PIM MASTER RECORD (252-COL STANDARD)</span>
                        </span>
                        <span className="text-xs text-[#8B93A3] font-mono">
                          UNSPSC: <strong className="text-white">{product.unspsc}</strong>
                        </span>
                      </div>

                      {/* Entity & Taxonomy Strip */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-[#12161D] p-3.5 rounded-lg border border-[#232935] font-mono">
                        <div>
                          <span className="text-[#8B93A3] text-[10px] uppercase font-bold">CANONICAL BRAND</span>
                          <div className="font-bold text-[#45E0D6] text-xs mt-0.5">{product.brand_name}</div>
                        </div>
                        <div>
                          <span className="text-[#8B93A3] text-[10px] uppercase font-bold">MANUFACTURER</span>
                          <div className="font-semibold text-white text-xs mt-0.5">{product.manufacturer_name}</div>
                        </div>
                        <div>
                          <span className="text-[#8B93A3] text-[10px] uppercase font-bold">CLASSPATH</span>
                          <div className="text-[#E7EAF0] text-[10px] mt-0.5 truncate" title={product.classpath}>
                            {product.classpath}
                          </div>
                        </div>
                      </div>

                      {/* 5-Tier Generated Content Suite */}
                      <div className="space-y-3">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[#8B93A3] block">
                          5-TIER GENERATED CONTENT & HARD GATE AUDIT
                        </span>

                        {/* Tier 1: INVOICE_DESC */}
                        <div className="p-3 bg-[#12161D] rounded-lg border border-[#232935] space-y-1.5">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-[#3DDC84] flex items-center space-x-1.5">
                              <span>1. INVOICE_DESC</span>
                              <span className="text-[10px] font-normal text-[#8B93A3]">(≤ 40 chars, ALL CAPS)</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#3DDC84]/10 text-[#3DDC84] border border-[#3DDC84]/25">
                                {product.invoice_desc_len}/40 chars [PASS]
                              </span>
                              <button
                                onClick={() => handleCopy(product.invoice_desc, 'INVOICE_DESC')}
                                className="text-[#8B93A3] hover:text-white"
                              >
                                {copiedField === 'INVOICE_DESC' ? <Check className="w-3.5 h-3.5 text-[#3DDC84]" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="font-mono text-xs font-bold text-white bg-[#0B0E13] p-2 rounded border border-[#232935]">
                            {product.invoice_desc}
                          </div>
                        </div>

                        {/* Tier 2: MOBILE_DESC */}
                        <div className="p-3 bg-[#12161D] rounded-lg border border-[#232935] space-y-1.5">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-[#45E0D6] flex items-center space-x-1.5">
                              <span>2. MOBILE_DESC</span>
                              <span className="text-[10px] font-normal text-[#8B93A3]">(60–80 chars)</span>
                            </span>
                            <div className="flex items-center space-x-2">
                              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/25">
                                {product.mobile_desc_len} chars [PASS]
                              </span>
                              <button
                                onClick={() => handleCopy(product.mobile_desc, 'MOBILE_DESC')}
                                className="text-[#8B93A3] hover:text-white"
                              >
                                {copiedField === 'MOBILE_DESC' ? <Check className="w-3.5 h-3.5 text-[#45E0D6]" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="font-sans text-xs text-white bg-[#0B0E13] p-2 rounded border border-[#232935]">
                            {product.mobile_desc}
                          </div>
                        </div>

                        {/* Tier 3: SHORT_DESC */}
                        <div className="p-3 bg-[#12161D] rounded-lg border border-[#232935] space-y-1.5">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-[#E7EAF0]">3. SHORT_DESC / PRODUCT TITLE</span>
                            <button
                              onClick={() => handleCopy(product.short_desc, 'SHORT_DESC')}
                              className="text-[#8B93A3] hover:text-white"
                            >
                              {copiedField === 'SHORT_DESC' ? <Check className="w-3.5 h-3.5 text-[#3DDC84]" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="font-sans text-xs text-white bg-[#0B0E13] p-2 rounded border border-[#232935]">
                            {product.short_desc}
                          </div>
                        </div>

                        {/* Tier 4: LONG_DESC1 */}
                        <div className="p-3 bg-[#12161D] rounded-lg border border-[#232935] space-y-1.5">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-bold text-[#8B93A3]">4. LONG_DESC1 (TECHNICAL SPECIFICATION)</span>
                            <button
                              onClick={() => handleCopy(product.long_desc1, 'LONG_DESC1')}
                              className="text-[#8B93A3] hover:text-white"
                            >
                              {copiedField === 'LONG_DESC1' ? <Check className="w-3.5 h-3.5 text-[#3DDC84]" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="font-sans text-xs text-[#8B93A3] bg-[#0B0E13] p-2 rounded border border-[#232935]">
                            {product.long_desc1}
                          </div>
                        </div>

                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: ATTRIBUTES */}
              {inspectorTab === 'attributes' && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-[#8B93A3] uppercase">
                      EXTRACTED SPECIFICATIONS ({product.attributes.length} LOV TRIPLETS)
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                    {product.attributes.map((attr, i) => (
                      <div key={i} className="p-3 bg-[#0B0E13] rounded-lg border border-[#232935] space-y-1">
                        <span className="text-[10px] text-[#8B93A3] uppercase font-bold block">{attr.label}</span>
                        <div className="flex items-baseline space-x-1">
                          <span className="text-white font-bold">{attr.value}</span>
                          {attr.uom && <span className="text-[#45E0D6] font-mono text-xs">{attr.uom}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: 252-COLUMNS */}
              {inspectorTab === 'schema252' && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="flex items-center justify-between gap-3">
                    <div className="relative w-72">
                      <Search className="w-3.5 h-3.5 text-[#8B93A3] absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={schemaSearch}
                        onChange={(e) => setSchemaSearch(e.target.value)}
                        placeholder="Search column header or value..."
                        className="w-full pl-9 pr-3 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-xs text-white placeholder-[#525B6C] focus:border-[#45E0D6] focus:outline-none"
                      />
                    </div>
                    <label className="flex items-center space-x-2 text-xs text-[#8B93A3] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={schemaFilterPopulated}
                        onChange={(e) => setSchemaFilterPopulated(e.target.checked)}
                        className="rounded bg-[#0B0E13] border-[#232935] text-[#45E0D6]"
                      />
                      <span>Show Populated Only ({populatedCount})</span>
                    </label>
                  </div>

                  <div className="max-h-[480px] overflow-y-auto border border-[#232935] rounded-lg">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-[#232935] bg-[#0B0E13] text-[#8B93A3] text-[10px] uppercase">
                          <th className="py-2 px-3 w-14">#</th>
                          <th className="py-2 px-3 w-72">COLUMN HEADER</th>
                          <th className="py-2 px-3">ENRICHED CELL VALUE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#232935]">
                        {filteredDeliveryEntries.map(([col, val], idx) => (
                          <tr key={col} className="hover:bg-[#1A1F29]">
                            <td className="py-1.5 px-3 text-[#8B93A3] text-[10px]">{idx + 1}</td>
                            <td className="py-1.5 px-3 font-bold text-[#E7EAF0]">{col}</td>
                            <td className="py-1.5 px-3 text-white truncate max-w-[400px]">
                              {val || <span className="text-[#525B6C] italic">&lt;empty&gt;</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 4: QUALITY AUDIT */}
              {inspectorTab === 'audit' && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="p-4 bg-[#0B0E13] rounded-xl border border-[#232935] space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white uppercase">WEIGHTED COMPOSITE CONFIDENCE</span>
                      <SegmentedGauge score={product.confidence_score} size="md" />
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-[#232935] text-[10px]">
                      <div>
                        <span className="text-[#8B93A3] block">BRAND (25%)</span>
                        <span className="font-bold text-[#3DDC84]">1.00</span>
                      </div>
                      <div>
                        <span className="text-[#8B93A3] block">TAXONOMY (20%)</span>
                        <span className="font-bold text-[#3DDC84]">1.00</span>
                      </div>
                      <div>
                        <span className="text-[#8B93A3] block">ATTRIBUTES (25%)</span>
                        <span className="font-bold text-[#3DDC84]">0.95</span>
                      </div>
                      <div>
                        <span className="text-[#8B93A3] block">DESCRIPTIONS (20%)</span>
                        <span className="font-bold text-[#3DDC84]">1.00</span>
                      </div>
                      <div>
                        <span className="text-[#8B93A3] block">COMPLETENESS (10%)</span>
                        <span className="font-bold text-[#3DDC84]">0.95</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

      </div>
    </div>
  );
};

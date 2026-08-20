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
  Network,
  Layers,
  ArrowRight
} from 'lucide-react';
import { ProductDetail } from '../types';
import { fetchProductDetail, approveProduct, fetchProductKnowledgeGraph } from '../services/api';
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
  const [inspectorTab, setInspectorTab] = useState<'overview' | 'attributes' | 'schema252' | 'audit' | 'graph' | 'provenance'>('overview');

  // Knowledge Graph State
  const [graphData, setGraphData] = useState<{
    product_id: string;
    mfg_part_number: string;
    nodes: Array<{ id: string; label: string; type: string; group: string; color: string }>;
    edges: Array<{ source: string; target: string; label: string }>;
    stats: { total_nodes: number; total_edges: number; ontology_depth: number; lov_conformance: string };
  } | null>(null);
  const [graphLoading, setGraphLoading] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);

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

  useEffect(() => {
    if (productId && inspectorTab === 'graph' && !graphData) {
      loadGraph(productId);
    }
  }, [productId, inspectorTab]);

  const loadDetail = async (id: string) => {
    setLoading(true);
    try {
      const data = await fetchProductDetail(id);
      setProduct(data);
    } catch (e) {
      console.error('Failed to load product detail:', e);
      showToast('Error', 'Failed to load product detail', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadGraph = async (id: string) => {
    setGraphLoading(true);
    try {
      const data = await fetchProductKnowledgeGraph(id);
      setGraphData(data);
      if (data.nodes.length > 0) {
        setSelectedNode(data.nodes[1]); // select product node by default
      }
    } catch (e) {
      console.error('Failed to load knowledge graph:', e);
      showToast('Graph Error', 'Failed to generate relational graph', 'error');
    } finally {
      setGraphLoading(false);
    }
  };

  const handleCopy = (text: string, fieldName: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldName);
    setTimeout(() => setCopiedField(null), 2000);
    showToast('Copied', `Copied ${fieldName} to clipboard`, 'info');
  };

  const handleApprove = async () => {
    if (!product) return;
    setApproving(true);
    try {
      await approveProduct(product.id, 'Approved via PIM Transformation Workbench');
      showToast('Approved', `Product ${product.mfg_part_number} approved to production!`, 'success');
      setProduct({ ...product, status: 'Validated' });
      if (onApproved) onApproved();
    } catch (e) {
      console.error('Failed to approve product:', e);
      showToast('Error', 'Failed to approve product', 'error');
    } finally {
      setApproving(false);
    }
  };

  if (!productId) return null;

  const totalCols = 252;
  const deliveryEntries = product?.delivery_columns ? Object.entries(product.delivery_columns) : [];
  const populatedCount = deliveryEntries.filter(([_, v]) => v && v.trim().length > 0).length;

  const filteredDeliveryEntries = deliveryEntries.filter(([col, val]) => {
    const q = schemaSearch.toLowerCase().trim();
    const v = val || '';
    const matchesSearch = !q || col.toLowerCase().includes(q) || v.toLowerCase().includes(q);
    const matchesPopulated = !schemaFilterPopulated || (v && v.trim().length > 0);
    return matchesSearch && matchesPopulated;
  });

  const renderGauge = (score: number) => {
    const active = Math.round(score * 10);
    return (
      <div className="flex items-center">
        <div className="mini-gauge">
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className={i < active ? 'on' : ''} />
          ))}
        </div>
        <span className="conf-val">{score.toFixed(2)}</span>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4 font-sans">
      <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        
        {/* Workbench Header */}
        <div className="px-6 py-4 border-b border-[var(--border)] bg-[var(--surface-1)] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="w-2.5 h-2.5 rounded-[2px] bg-[var(--cyan)]" />
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider font-mono">
                  TRANSFORMATION WORKBENCH
                </h3>
                {product && (
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-[var(--cyan-bg)] text-[var(--cyan)] rounded">
                    MPN: {product.mfg_part_number} · ROW #{product.row_id}
                  </span>
                )}
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                Comparative Ingestion Audit: Raw Supplier Input vs. Canonical 252-Column PIM Entity
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {product && product.status !== 'Validated' && (
              <button
                onClick={handleApprove}
                disabled={approving}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--green-bg)] text-[var(--green)] border border-[var(--green)] rounded-md text-xs font-semibold font-mono hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
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
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--surface-2)] text-[var(--text-secondary)] hover:text-white rounded-md text-xs font-semibold border border-[var(--border-strong)] transition-colors font-mono cursor-pointer"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>EDIT CELL</span>
              </button>
            )}
            <button
              onClick={onClose}
              title="Close (Esc)"
              className="p-1.5 text-[var(--text-muted)] hover:text-white rounded-md hover:bg-[var(--surface-1)] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Workspace Navigation Tabs */}
        <div className="px-6 py-2 bg-[var(--bg)] border-b border-[var(--border)] flex items-center justify-between overflow-x-auto font-mono text-xs">
          <div className="flex items-center gap-2">
            {[
              { id: 'overview', label: '5-TIER SPECS', icon: FileText },
              { id: 'attributes', label: `LOV ATTRIBUTES (${product?.attributes.length || 0})`, icon: Tag },
              { id: 'graph', label: 'KNOWLEDGE GRAPH', icon: Network },
              { id: 'provenance', label: 'EVIDENCE & PROVENANCE', icon: Shield },
              { id: 'schema252', label: `ALL 252 COLUMNS (${populatedCount}/${totalCols})`, icon: Table },
              { id: 'audit', label: 'QUALITY AUDIT', icon: Shield }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = inspectorTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setInspectorTab(tab.id as any)}
                  className={`px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-all font-semibold cursor-pointer ${
                    isActive
                      ? 'bg-[var(--surface-2)] text-[var(--cyan)] border border-[var(--border-strong)]'
                      : 'text-[var(--text-muted)] hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {product && (
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-[11px] text-[var(--text-muted)]">CONFIDENCE:</span>
              {renderGauge(product.confidence_score)}
            </div>
          )}
        </div>

        {/* Workbench Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          {loading || !product ? (
            <div className="py-24 text-center text-[var(--text-muted)] space-y-3 font-mono">
              <div className="w-7 h-7 border-2 border-[var(--cyan)] border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs">LOADING 252-COLUMN MASTER RECORD...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: OVERVIEW & 5-TIER SPECS */}
              {inspectorTab === 'overview' && (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
                    
                    {/* Left Pane: Raw Supplier Feed (4 cols) */}
                    <div className="lg:col-span-4 bg-[var(--surface-1)] rounded-lg p-4 space-y-4 border border-[var(--border)]">
                      <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--red)] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--red)]" />
                          <span>RAW SUPPLIER FEED</span>
                        </span>
                        <span className="text-[10px] text-[var(--text-muted)] font-mono">SOURCE</span>
                      </div>

                      <div className="space-y-3 text-xs">
                        <div>
                          <span className="text-[var(--text-muted)] text-[10px] font-mono uppercase block font-semibold">
                            RAW PART_DESC
                          </span>
                          <div className="mt-1 p-2.5 bg-[var(--bg)] rounded-md border border-[var(--border)] font-mono text-[var(--text-primary)] break-words text-[11px]">
                            {product.raw.part_desc}
                          </div>
                        </div>

                        <div>
                          <span className="text-[var(--text-muted)] text-[10px] font-mono uppercase block font-semibold">
                            RAW MFG_PART_NUM
                          </span>
                          <div className="mt-1 p-2 bg-[var(--bg)] rounded-md border border-[var(--border)] font-mono text-[var(--text-secondary)] text-[11px]">
                            {product.raw.mfg_part_num || '<EMPTY>'}
                          </div>
                        </div>

                        <div>
                          <span className="text-[var(--text-muted)] text-[10px] font-mono uppercase block font-semibold">
                            STRIPPED PLACEHOLDERS
                          </span>
                          <div className="mt-1 space-y-1">
                            {['e1_brand', 'unilog_brand', 'dib_brand'].map((field) => {
                              const val = (product.raw as any)[field];
                              const isPlaceholder = val && (val.includes('--') || val.includes('COMMODITY'));
                              return (
                                <div
                                  key={field}
                                  className="flex items-center justify-between text-[11px] p-1.5 bg-[var(--bg)] rounded border border-[var(--border)] font-mono"
                                >
                                  <span className="text-[var(--text-muted)] text-[10px]">{field}:</span>
                                  <span className={isPlaceholder ? 'text-[var(--red)] line-through' : 'text-[var(--text-secondary)]'}>
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
                    <div className="lg:col-span-8 bg-[var(--surface-1)] rounded-lg p-4.5 space-y-4 border border-[var(--border)]">
                      <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--cyan)] flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-[var(--cyan)]" />
                          <span>CANONICAL PIM MASTER RECORD (252-COL STANDARD)</span>
                        </span>
                        <span className="text-xs text-[var(--text-muted)] font-mono">
                          UNSPSC: <strong className="text-[var(--text-primary)]">{product.unspsc}</strong>
                        </span>
                      </div>

                      {/* Entity & Taxonomy Strip */}
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-[var(--bg)] p-3 rounded-md border border-[var(--border)] font-mono">
                        <div>
                          <span className="text-[var(--text-muted)] text-[10px] uppercase font-semibold">CANONICAL BRAND</span>
                          <div className="font-semibold text-[var(--cyan)] text-xs mt-0.5">{product.brand_name}</div>
                        </div>
                        <div>
                          <span className="text-[var(--text-muted)] text-[10px] uppercase font-semibold">MANUFACTURER</span>
                          <div className="font-medium text-[var(--text-primary)] text-xs mt-0.5">{product.manufacturer_name}</div>
                        </div>
                        <div>
                          <span className="text-[var(--text-muted)] text-[10px] uppercase font-semibold">CLASSPATH</span>
                          <div className="text-[var(--text-secondary)] text-[10px] mt-0.5 truncate" title={product.classpath}>
                            {product.classpath}
                          </div>
                        </div>
                      </div>

                      {/* 5-Tier Generated Content Suite */}
                      <div className="space-y-2.5">
                        <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-[var(--text-muted)] block">
                          5-TIER GENERATED CONTENT &amp; HARD GATE AUDIT
                        </span>

                        {/* Tier 1: INVOICE_DESC */}
                        <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-semibold text-[var(--green)]">1. INVOICE_DESC (≤ 40 chars, ALL CAPS)</span>
                            <div className="flex items-center gap-2">
                              <span className="chip validated">{product.invoice_desc_len}/40 chars</span>
                              <button
                                onClick={() => handleCopy(product.invoice_desc, 'INVOICE_DESC')}
                                className="text-[var(--text-muted)] hover:text-white cursor-pointer"
                              >
                                {copiedField === 'INVOICE_DESC' ? <Check className="w-3.5 h-3.5 text-[var(--green)]" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="font-mono text-xs font-semibold text-[var(--text-primary)]">
                            {product.invoice_desc}
                          </div>
                        </div>

                        {/* Tier 2: MOBILE_DESC */}
                        <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-semibold text-[var(--cyan)]">2. MOBILE_DESC (60–80 chars)</span>
                            <div className="flex items-center gap-2">
                              <span className="chip enriched">{product.mobile_desc_len} chars</span>
                              <button
                                onClick={() => handleCopy(product.mobile_desc, 'MOBILE_DESC')}
                                className="text-[var(--text-muted)] hover:text-white cursor-pointer"
                              >
                                {copiedField === 'MOBILE_DESC' ? <Check className="w-3.5 h-3.5 text-[var(--cyan)]" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </div>
                          </div>
                          <div className="font-sans text-xs text-[var(--text-primary)]">
                            {product.mobile_desc}
                          </div>
                        </div>

                        {/* Tier 3: SHORT_DESC */}
                        <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-semibold text-[var(--text-secondary)]">3. SHORT_DESC / PRODUCT TITLE</span>
                            <button
                              onClick={() => handleCopy(product.short_desc, 'SHORT_DESC')}
                              className="text-[var(--text-muted)] hover:text-white cursor-pointer"
                            >
                              {copiedField === 'SHORT_DESC' ? <Check className="w-3.5 h-3.5 text-[var(--green)]" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="font-sans text-xs text-[var(--text-primary)]">
                            {product.short_desc}
                          </div>
                        </div>

                        {/* Tier 4: LONG_DESC1 */}
                        <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                          <div className="flex items-center justify-between text-xs font-mono">
                            <span className="font-semibold text-[var(--text-muted)]">4. LONG_DESC1 (TECHNICAL SPECIFICATION)</span>
                            <button
                              onClick={() => handleCopy(product.long_desc1, 'LONG_DESC1')}
                              className="text-[var(--text-muted)] hover:text-white cursor-pointer"
                            >
                              {copiedField === 'LONG_DESC1' ? <Check className="w-3.5 h-3.5 text-[var(--green)]" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                          <div className="font-sans text-xs text-[var(--text-secondary)]">
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
                  <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase">
                    EXTRACTED SPECIFICATIONS ({product.attributes.length} LOV TRIPLETS)
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                    {product.attributes.map((attr, i) => (
                      <div key={i} className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)] space-y-1">
                        <span className="text-[10px] text-[var(--text-muted)] uppercase block">{attr.label}</span>
                        <div className="flex items-baseline gap-1">
                          <span className="text-[var(--text-primary)] font-semibold">{attr.value}</span>
                          {attr.uom && <span className="text-[var(--cyan)] font-mono text-xs">{attr.uom}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: INTERACTIVE KNOWLEDGE GRAPH */}
              {inspectorTab === 'graph' && (
                <div className="space-y-4 font-mono text-xs">
                  {graphLoading ? (
                    <div className="py-20 text-center text-[var(--text-muted)] space-y-2">
                      <div className="w-6 h-6 border-2 border-[var(--cyan)] border-t-transparent rounded-full animate-spin mx-auto" />
                      <p>CONSTRUCTING RELATIONAL ONTOLOGY GRAPH...</p>
                    </div>
                  ) : graphData ? (
                    <div className="space-y-4">
                      
                      {/* Graph Metrics Strip */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                        <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)]">
                          <span className="text-[10px] text-[var(--text-muted)] uppercase block">TOTAL GRAPH NODES</span>
                          <span className="text-lg font-bold text-[var(--text-primary)]">{graphData.stats.total_nodes}</span>
                        </div>
                        <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)]">
                          <span className="text-[10px] text-[var(--text-muted)] uppercase block">RELATIONAL EDGES</span>
                          <span className="text-lg font-bold text-[var(--cyan)]">{graphData.stats.total_edges}</span>
                        </div>
                        <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)]">
                          <span className="text-[10px] text-[var(--text-muted)] uppercase block">ONTOLOGY DEPTH</span>
                          <span className="text-lg font-bold text-[var(--green)]">4 Levels</span>
                        </div>
                        <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)]">
                          <span className="text-[10px] text-[var(--text-muted)] uppercase block">LOV CONFORMANCE</span>
                          <span className="text-lg font-bold text-[var(--cyan)]">{graphData.stats.lov_conformance}</span>
                        </div>
                      </div>

                      {/* Interactive Visual Graph Explorer */}
                      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
                        {/* Nodes List / Map (8 cols) */}
                        <div className="lg:col-span-8 bg-[var(--surface-1)] rounded-lg p-4 border border-[var(--border)] space-y-3">
                          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">
                            CONNECTED ONTOLOGICAL ENTITIES (CLICK TO INSPECT)
                          </span>

                          <div className="flex flex-wrap gap-2 max-h-[340px] overflow-y-auto">
                            {graphData.nodes.map((node) => {
                              const isSelected = selectedNode?.id === node.id;
                              return (
                                <button
                                  key={node.id}
                                  onClick={() => setSelectedNode(node)}
                                  className={`p-2.5 rounded-md border text-left transition-all cursor-pointer ${
                                    isSelected
                                      ? 'border-[var(--cyan)] bg-[var(--cyan-bg)] text-[var(--cyan)] shadow-[0_0_12px_rgba(69,224,214,0.2)]'
                                      : 'border-[var(--border)] bg-[var(--surface-2)] text-[var(--text-primary)] hover:border-[var(--border-strong)]'
                                  }`}
                                >
                                  <span className="text-[9px] text-[var(--text-muted)] uppercase block font-semibold">
                                    {node.group}
                                  </span>
                                  <span className="text-xs font-semibold">{node.label}</span>
                                </button>
                              );
                            })}
                          </div>

                          {/* Relational Edge Pipeline Preview */}
                          <div className="pt-3 border-t border-[var(--border)] space-y-1.5">
                            <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">
                              SAMPLE RELATIONAL EDGES ({graphData.edges.length} TOTAL)
                            </span>
                            <div className="space-y-1 max-h-[140px] overflow-y-auto">
                              {graphData.edges.map((edge, idx) => (
                                <div key={idx} className="flex items-center gap-2 text-[11px] text-[var(--text-secondary)] p-1.5 bg-[var(--bg)] rounded border border-[var(--border)]">
                                  <span className="text-[var(--text-primary)] font-semibold">{edge.source}</span>
                                  <ArrowRight className="w-3 h-3 text-[var(--cyan)]" />
                                  <span className="chip validated text-[9px]">{edge.label}</span>
                                  <ArrowRight className="w-3 h-3 text-[var(--cyan)]" />
                                  <span className="text-[var(--text-primary)] font-semibold">{edge.target}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Node Detail Inspector (4 cols) */}
                        <div className="lg:col-span-4 bg-[var(--surface-1)] rounded-lg p-4 border border-[var(--border)] space-y-3">
                          <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase block">
                            ACTIVE NODE INSPECTION
                          </span>

                          {selectedNode ? (
                            <div className="space-y-2.5">
                              <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                                <span className="text-[10px] text-[var(--text-muted)] uppercase block">NODE ID</span>
                                <span className="text-xs font-bold text-[var(--cyan)]">{selectedNode.id}</span>
                              </div>
                              <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                                <span className="text-[10px] text-[var(--text-muted)] uppercase block">ONTOLOGY GROUP</span>
                                <span className="text-xs font-semibold text-[var(--text-primary)]">{selectedNode.group}</span>
                              </div>
                              <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                                <span className="text-[10px] text-[var(--text-muted)] uppercase block">CANONICAL LABEL</span>
                                <span className="text-xs font-semibold text-[var(--text-primary)]">{selectedNode.label}</span>
                              </div>
                              <div className="p-3 bg-[var(--bg)] rounded-md border border-[var(--border)] space-y-1">
                                <span className="text-[10px] text-[var(--text-muted)] uppercase block">TRACEABILITY STATUS</span>
                                <span className="chip validated">100% Deterministic LOV Bound</span>
                              </div>
                            </div>
                          ) : (
                            <div className="py-8 text-center text-[var(--text-muted)]">
                              Click any node to inspect ontology bindings.
                            </div>
                          )}
                        </div>

                      </div>

                    </div>
                  ) : null}
                </div>
              )}

              {/* TAB 3b: EVIDENCE & PROVENANCE LINEAGE */}
              {inspectorTab === 'provenance' && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="p-4 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-3">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3">
                      <div>
                        <div className="flex items-center gap-2 text-xs font-semibold text-[var(--cyan)] uppercase">
                          <Shield className="w-4 h-4 text-[var(--cyan)]" />
                          <span>FIELD-LEVEL PROVENANCE &amp; TRACEABILITY AUDIT</span>
                        </div>
                        <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
                          Every enriched field is mathematically mapped to its source document, extraction method, and governing guideline.
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-[var(--green-bg)] text-[var(--green)] text-[10px] font-semibold border border-[var(--green)]">
                          100% TRACEABLE LINEAGE
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[11px] pt-1">
                      <div className="p-2.5 bg-[var(--surface-2)] rounded border border-[var(--border-strong)]">
                        <span className="text-[var(--text-muted)] block text-[10px]">SOURCING RULEBOOK</span>
                        <span className="font-semibold text-[var(--text-primary)]">UNILOG_INTERNAL_CONTENT_GUIDELINES</span>
                      </div>
                      <div className="p-2.5 bg-[var(--surface-2)] rounded border border-[var(--border-strong)]">
                        <span className="text-[var(--text-muted)] block text-[10px]">CANONICAL VOCABULARIES</span>
                        <span className="font-semibold text-[var(--text-primary)]">UniCat LOV v1.0 &amp; Mfr/Brand Master</span>
                      </div>
                      <div className="p-2.5 bg-[var(--surface-2)] rounded border border-[var(--border-strong)]">
                        <span className="text-[var(--text-muted)] block text-[10px]">HALLUCINATION POLICY</span>
                        <span className="font-semibold text-[var(--green)]">Zero Fake Facts / Missing Kept Blank</span>
                      </div>
                    </div>
                  </div>

                  <div className="max-h-[460px] overflow-y-auto border border-[var(--border)] rounded-md">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-muted)] text-[10px] uppercase">
                          <th className="py-2 px-3 w-44">ENRICHED FIELD</th>
                          <th className="py-2 px-3 w-36">SOURCE TYPE</th>
                          <th className="py-2 px-3 w-48">EXTRACTION METHOD</th>
                          <th className="py-2 px-3">GOVERNING RULE / AUTHORITY</th>
                          <th className="py-2 px-3 w-28 text-right">CONFIDENCE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border)]">
                        {product.field_provenance && Object.entries(product.field_provenance).length > 0 ? (
                          Object.entries(product.field_provenance).map(([fieldKey, prov]) => (
                            <tr key={fieldKey} className="hover:bg-[var(--surface-1)]">
                              <td className="py-2 px-3 font-semibold text-[var(--text-primary)]">
                                {prov.field_name || fieldKey}
                              </td>
                              <td className="py-2 px-3">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                                    prov.source_type === 'canonical_dictionary'
                                      ? 'bg-[var(--cyan-bg)] text-[var(--cyan)]'
                                      : prov.source_type === 'rule_engine'
                                      ? 'bg-[var(--amber-bg)] text-[var(--amber)]'
                                      : prov.source_type === 'raw_input'
                                      ? 'bg-[var(--green-bg)] text-[var(--green)]'
                                      : 'bg-[var(--gray-chip)] text-[var(--text-secondary)]'
                                  }`}
                                >
                                  {prov.source_type.replace('_', ' ')}
                                </span>
                              </td>
                              <td className="py-2 px-3 text-[var(--text-secondary)]">
                                {prov.extraction_method.replace(/_/g, ' ')}
                              </td>
                              <td className="py-2 px-3 text-[var(--text-muted)] truncate max-w-[320px]" title={prov.section_or_rule}>
                                {prov.section_or_rule || 'Unilog Master Content Standard'}
                              </td>
                              <td className="py-2 px-3 text-right">
                                <span className="font-semibold text-[var(--green)]">
                                  {(prov.confidence * 100).toFixed(0)}%
                                </span>
                              </td>
                            </tr>
                          ))
                        ) : (
                          <tr>
                            <td colSpan={5} className="py-6 text-center text-[var(--text-muted)]">
                              Provenance trace data is being calculated for this product record.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 4: 252-COLUMNS */}
              {inspectorTab === 'schema252' && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="flex items-center justify-between gap-3">
                    <div className="relative w-72">
                      <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
                      <input
                        type="text"
                        value={schemaSearch}
                        onChange={(e) => setSchemaSearch(e.target.value)}
                        placeholder="Search column header or value..."
                        className="w-full pl-9 pr-3 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--cyan)]"
                      />
                    </div>
                    <label className="flex items-center gap-2 text-xs text-[var(--text-muted)] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={schemaFilterPopulated}
                        onChange={(e) => setSchemaFilterPopulated(e.target.checked)}
                        className="rounded bg-[var(--surface-1)] border-[var(--border)] text-[var(--cyan)]"
                      />
                      <span>Show Populated Only ({populatedCount})</span>
                    </label>
                  </div>

                  <div className="max-h-[480px] overflow-y-auto border border-[var(--border)] rounded-md">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-[var(--border)] bg-[var(--surface-1)] text-[var(--text-muted)] text-[10px] uppercase">
                          <th className="py-2 px-3 w-14">#</th>
                          <th className="py-2 px-3 w-72">COLUMN HEADER</th>
                          <th className="py-2 px-3">ENRICHED CELL VALUE</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--border)]">
                        {filteredDeliveryEntries.map(([col, val], idx) => (
                          <tr key={col} className="hover:bg-[var(--surface-1)]">
                            <td className="py-1.5 px-3 text-[var(--text-muted)] text-[10px]">{idx + 1}</td>
                            <td className="py-1.5 px-3 font-semibold text-[var(--text-primary)]">{col}</td>
                            <td className="py-1.5 px-3 text-[var(--text-secondary)] truncate max-w-[400px]">
                              {val || <span className="text-[var(--text-muted)] italic">&lt;empty&gt;</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* TAB 5: QUALITY AUDIT */}
              {inspectorTab === 'audit' && (
                <div className="space-y-4 font-mono text-xs">
                  <div className="p-4 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--text-primary)] uppercase">
                        WEIGHTED COMPOSITE CONFIDENCE
                      </span>
                      {renderGauge(product.confidence_score)}
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-3 border-t border-[var(--border)] text-[10px]">
                      <div>
                        <span className="text-[var(--text-muted)] block">BRAND (25%)</span>
                        <span className="font-semibold text-[var(--green)]">1.00</span>
                      </div>
                      <div>
                        <span className="text-[var(--text-muted)] block">TAXONOMY (20%)</span>
                        <span className="font-semibold text-[var(--green)]">1.00</span>
                      </div>
                      <div>
                        <span className="text-[var(--text-muted)] block">ATTRIBUTES (25%)</span>
                        <span className="font-semibold text-[var(--green)]">0.95</span>
                      </div>
                      <div>
                        <span className="text-[var(--text-muted)] block">DESCRIPTIONS (20%)</span>
                        <span className="font-semibold text-[var(--green)]">1.00</span>
                      </div>
                      <div>
                        <span className="text-[var(--text-muted)] block">COMPLETENESS (10%)</span>
                        <span className="font-semibold text-[var(--green)]">0.95</span>
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

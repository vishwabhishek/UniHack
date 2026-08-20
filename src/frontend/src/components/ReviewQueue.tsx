import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Edit3,
  CheckCircle2,
  AlertTriangle,
  Plus,
  Trash2,
  Save,
  X,
  ExternalLink
} from 'lucide-react';
import { ReviewItem, ProductDetail, AttributeTriple } from '../types';
import { fetchReviewQueue, approveProduct, fetchProductDetail, updateProduct } from '../services/api';
import { useToast } from './Toast';

interface ReviewQueueProps {
  onInspectProduct: (productId: string) => void;
  onRefreshCatalog?: () => void;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ onInspectProduct, onRefreshCatalog }) => {
  const { showToast } = useToast();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editProduct, setEditProduct] = useState<ProductDetail | null>(null);
  const [saving, setSaving] = useState<boolean>(false);

  // Editable Form State
  const [editBrand, setEditBrand] = useState<string>('');
  const [editManuf, setEditManuf] = useState<string>('');
  const [editInvoiceDesc, setEditInvoiceDesc] = useState<string>('');
  const [editMobileDesc, setEditMobileDesc] = useState<string>('');
  const [editShortDesc, setEditShortDesc] = useState<string>('');
  const [editLongDesc, setEditLongDesc] = useState<string>('');
  const [editAttributes, setEditAttributes] = useState<AttributeTriple[]>([]);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = async () => {
    setLoading(true);
    try {
      const data = await fetchReviewQueue();
      setItems(data.items);
    } catch (e) {
      console.error('Failed to load review queue:', e);
      showToast('Error', 'Failed to load exception queue', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickApprove = async (id: string) => {
    try {
      await approveProduct(id, 'Approved via HITL triage board');
      showToast('Approved', `Product #${id} marked Validated`, 'success');
      setItems((prev) => prev.filter((item) => item.id !== id));
      if (onRefreshCatalog) onRefreshCatalog();
    } catch (e) {
      console.error('Failed to approve product:', e);
      showToast('Error', 'Approval failed', 'error');
    }
  };

  const handleOpenEdit = async (id: string) => {
    try {
      const detail = await fetchProductDetail(id);
      setEditingId(id);
      setEditProduct(detail);
      setEditBrand(detail.brand_name || '');
      setEditManuf(detail.manufacturer_name || '');
      setEditInvoiceDesc(detail.invoice_desc || '');
      setEditMobileDesc(detail.mobile_desc || '');
      setEditShortDesc(detail.short_desc || '');
      setEditLongDesc(detail.long_desc1 || '');
      setEditAttributes(detail.attributes || []);
    } catch (e) {
      console.error('Failed to load product detail for edit:', e);
      showToast('Error', 'Failed to load record details', 'error');
    }
  };

  const handleSaveEdit = async () => {
    if (!editingId) return;
    setSaving(true);
    try {
      await updateProduct(editingId, {
        brand_name: editBrand,
        manufacturer_name: editManuf,
        invoice_desc: editInvoiceDesc,
        mobile_desc: editMobileDesc,
        short_desc: editShortDesc,
        long_desc1: editLongDesc,
        attributes: editAttributes,
        status: 'Validated'
      });
      setEditingId(null);
      setEditProduct(null);
      showToast('Record Saved', 'Updated specifications and marked Validated', 'success');
      await loadQueue();
      if (onRefreshCatalog) onRefreshCatalog();
    } catch (e) {
      console.error('Failed to save update:', e);
      showToast('Error', 'Failed to save record updates', 'error');
    } finally {
      setSaving(false);
    }
  };

  const addAttributeSlot = () => {
    setEditAttributes((prev) => [...prev, { label: '', value: '', uom: '' }]);
  };

  const removeAttributeSlot = (index: number) => {
    setEditAttributes((prev) => prev.filter((_, i) => i !== index));
  };

  const updateAttributeSlot = (index: number, field: keyof AttributeTriple, val: string) => {
    setEditAttributes((prev) => {
      const copy = [...prev];
      copy[index] = { ...copy[index], [field]: val };
      return copy;
    });
  };

  const renderMiniGauge = (score: number) => {
    const active = Math.round(score * 10);
    return (
      <div className="flex items-center">
        <div className="mini-gauge">
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className={i < active ? 'on amber' : ''} />
          ))}
        </div>
        <span className="conf-val text-[var(--amber)]">{score.toFixed(2)}</span>
      </div>
    );
  };

  return (
    <div className="space-y-4 font-sans">
      
      {/* Header Banner */}
      <div className="p-[16px_18px] rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-mono font-semibold text-[var(--text-primary)] uppercase tracking-wider">
              HUMAN-IN-THE-LOOP EXCEPTION TRIAGE BOARD
            </h2>
            <span className="chip flagged font-bold">
              {items.length} ANOMALIES
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Records with confidence &lt; 0.85 or data conflicts routed for specialist sign-off before delivery
          </p>
        </div>

        <button
          onClick={loadQueue}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white rounded-md text-xs font-mono border border-[var(--border)] transition-colors cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[var(--cyan)]' : ''}`} />
          <span>SYNC QUEUE</span>
        </button>
      </div>

      {/* Grid of Exception Cards */}
      {loading ? (
        <div className="py-20 text-center text-[var(--text-muted)] space-y-3 font-mono">
          <div className="w-7 h-7 border-2 border-[var(--amber)] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs">LOADING EXCEPTION TRIAGE RECORDS...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] text-center space-y-2 font-mono">
          <div className="w-8 h-8 rounded-full bg-[var(--green-bg)] text-[var(--green)] flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
            ALL CATALOG ITEMS VALIDATED
          </h3>
          <p className="text-xs text-[var(--text-muted)] font-sans max-w-md mx-auto">
            Zero records currently triggered anomaly flags. 100% of items meet master delivery criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-[var(--surface-2)] border border-[var(--border)] hover:border-[var(--border-strong)] rounded-[10px] p-4 space-y-3 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-semibold text-[var(--text-primary)] text-xs">
                      {item.mfg_part_num || item.part_number}
                    </span>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">ROW #{item.row_id}</span>
                  </div>
                  <div className="text-xs text-[var(--cyan)] font-medium mt-0.5">
                    {item.brand_name} · <span className="text-[var(--text-muted)]">{item.manufacturer_name}</span>
                  </div>
                </div>

                {renderMiniGauge(item.confidence_score)}
              </div>

              {/* Anomaly Badges */}
              <div className="flex flex-wrap gap-1.5">
                {(item.anomaly_flags || []).map((r: string, i: number) => (
                  <span key={i} className="chip flagged flex items-center gap-1">
                    <AlertTriangle className="w-2.5 h-2.5" />
                    <span>{r}</span>
                  </span>
                ))}
              </div>

              {/* Raw vs Enriched Diff Preview */}
              <div className="bg-[var(--surface-1)] p-3 rounded-md border border-[var(--border)] space-y-1.5 text-[11px] font-mono">
                <div>
                  <span className="text-[var(--red)] font-semibold block text-[10px]">RAW SUPPLIER INPUT:</span>
                  <span className="text-[var(--text-muted)] truncate block">{item.raw_part_desc || 'No raw description provided'}</span>
                </div>
                <div>
                  <span className="text-[var(--green)] font-semibold block text-[10px]">PROPOSED ENRICHED TITLE:</span>
                  <span className="text-[var(--text-primary)] truncate block">{item.short_desc || 'Pending spec curation'}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2 pt-1 border-t border-[var(--border)] font-mono text-xs">
                <button
                  onClick={() => onInspectProduct(item.id)}
                  className="px-2.5 py-1.5 rounded-md bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white border border-[var(--border)] transition-colors flex items-center gap-1 cursor-pointer"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>INSPECT</span>
                </button>
                <button
                  onClick={() => handleOpenEdit(item.id)}
                  className="px-2.5 py-1.5 rounded-md bg-[var(--amber-bg)] hover:opacity-90 text-[var(--amber)] border border-[var(--amber)] transition-opacity flex items-center gap-1 font-semibold cursor-pointer"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>CURATE SPEC</span>
                </button>
                <button
                  onClick={() => handleQuickApprove(item.id)}
                  className="px-3 py-1.5 rounded-md bg-[var(--green-bg)] hover:opacity-90 text-[var(--green)] border border-[var(--green)] transition-opacity flex items-center gap-1 font-semibold cursor-pointer"
                >
                  <CheckCircle2 className="w-3 h-3" />
                  <span>APPROVE</span>
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Specialist Edit Modal Drawer */}
      {editingId && editProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-sans">
            
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface-1)]">
              <div className="flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-[2px] bg-[var(--amber)]" />
                <h3 className="text-xs font-mono font-semibold text-[var(--text-primary)] uppercase">
                  CURATE MASTER SPECIFICATION — ROW #{editProduct.raw.row_id} ({editProduct.mfg_part_number})
                </h3>
              </div>
              <button
                onClick={() => setEditingId(null)}
                className="p-1 rounded-md text-[var(--text-muted)] hover:text-white hover:bg-[var(--surface-2)] cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body Form */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">CANONICAL BRAND</label>
                  <input
                    type="text"
                    value={editBrand}
                    onChange={(e) => setEditBrand(e.target.value)}
                    className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">MANUFACTURER NAME</label>
                  <input
                    type="text"
                    value={editManuf}
                    onChange={(e) => setEditManuf(e.target.value)}
                    className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">
                  INVOICE_DESC (ERP Hard Gate: ≤40 Chars, ALL CAPS)
                </label>
                <input
                  type="text"
                  maxLength={40}
                  value={editInvoiceDesc}
                  onChange={(e) => setEditInvoiceDesc(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--green)] font-semibold tracking-wide focus:border-[var(--cyan)] focus:outline-none"
                />
                <div className="text-[10px] text-right mt-0.5 text-[var(--text-muted)]">
                  {editInvoiceDesc.length}/40 characters
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">
                  MOBILE_DESC (Mobile Gate: 60–80 Chars)
                </label>
                <input
                  type="text"
                  value={editMobileDesc}
                  onChange={(e) => setEditMobileDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none font-sans"
                />
                <div className="text-[10px] text-right mt-0.5 text-[var(--text-muted)]">
                  {editMobileDesc.length} characters (Target: 60-80)
                </div>
              </div>

              {/* Extracted Specification Triplets */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-[10px] font-bold text-[var(--text-muted)] uppercase">
                    STRUCTURED ATTRIBUTES (LOV CONTROLLED)
                  </label>
                  <button
                    type="button"
                    onClick={addAttributeSlot}
                    className="text-[10px] text-[var(--cyan)] hover:underline flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3 h-3" />
                    <span>ADD ATTRIBUTE</span>
                  </button>
                </div>

                <div className="space-y-2">
                  {editAttributes.map((attr, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input
                        type="text"
                        placeholder="Label"
                        value={attr.label}
                        onChange={(e) => updateAttributeSlot(idx, 'label', e.target.value)}
                        className="flex-1 px-2.5 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)]"
                      />
                      <input
                        type="text"
                        placeholder="Value"
                        value={attr.value}
                        onChange={(e) => updateAttributeSlot(idx, 'value', e.target.value)}
                        className="flex-1 px-2.5 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)]"
                      />
                      <input
                        type="text"
                        placeholder="UOM"
                        value={attr.uom || ''}
                        onChange={(e) => updateAttributeSlot(idx, 'uom', e.target.value)}
                        className="w-20 px-2.5 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)]"
                      />
                      <button
                        type="button"
                        onClick={() => removeAttributeSlot(idx)}
                        className="p-1.5 text-[var(--text-muted)] hover:text-[var(--red)] cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-[var(--border)] bg-[var(--surface-1)] flex items-center justify-end gap-2 font-mono text-xs">
              <button
                type="button"
                onClick={() => setEditingId(null)}
                className="px-3.5 py-2 rounded-md bg-[var(--surface-2)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] border border-[var(--border)] cursor-pointer"
              >
                CANCEL
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={handleSaveEdit}
                className="px-4 py-2 rounded-md bg-[var(--cyan)] text-[#06201D] font-semibold flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'SAVING...' : 'SAVE & MARK VALIDATED'}</span>
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};

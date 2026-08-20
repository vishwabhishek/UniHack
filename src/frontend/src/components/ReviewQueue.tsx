import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  CheckCircle2,
  AlertTriangle,
  Edit3,
  RefreshCw,
  Tag,
  Plus,
  Trash2,
  Save,
  X,
  Sparkles,
  Zap
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
    } finally {
      setLoading(false);
    }
  };

  const handleQuickApprove = async (id: string) => {
    try {
      await approveProduct(id, 'Quick approved from triage board');
      showToast('Approved', 'Master record validated for delivery', 'success');
      await loadQueue();
      if (onRefreshCatalog) onRefreshCatalog();
    } catch (e) {
      console.error('Failed to approve item:', e);
    }
  };

  const openEditor = async (id: string) => {
    setEditingId(id);
    try {
      const detail = await fetchProductDetail(id);
      setEditProduct(detail);
      setEditBrand(detail.brand_name);
      setEditManuf(detail.manufacturer_name);
      setEditInvoiceDesc(detail.invoice_desc);
      setEditMobileDesc(detail.mobile_desc);
      setEditShortDesc(detail.short_desc);
      setEditLongDesc(detail.long_desc1);
      setEditAttributes(detail.attributes || []);
    } catch (e) {
      console.error('Failed to load product detail for edit:', e);
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
      showToast('Record Saved', 'Updated attributes and marked Validated', 'success');
      await loadQueue();
      if (onRefreshCatalog) onRefreshCatalog();
    } catch (e) {
      console.error('Failed to save update:', e);
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

  return (
    <div className="space-y-4">
      {/* Header Summary */}
      <div className="glass-panel p-5 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border border-amber-500/20 shadow-glass font-mono">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-glow-amber">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xs font-extrabold text-white uppercase tracking-wider">
                DATA QUALITY EXCEPTION BOARD (HITL TRIAGE)
              </h2>
              <span className="glow-badge-amber text-[10px] px-2 py-0.5 rounded-full font-bold">
                {items.length} ANOMALIES FLAGGED
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-sans mt-0.5">
              Low-confidence records (&lt;0.85) requiring catalog specialist sign-off before delivery packaging
            </p>
          </div>
        </div>

        <button
          onClick={loadQueue}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-slate-200 rounded-xl text-xs font-bold border border-white/[0.08] transition-all font-mono hover:scale-105"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>SYNC QUEUE</span>
        </button>
      </div>

      {/* Triage Cards Grid */}
      {loading ? (
        <div className="py-24 text-center text-slate-400 space-y-3 font-mono">
          <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto shadow-glow-amber" />
          <p className="text-xs">RETRIEVING EXCEPTION QUEUE...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl text-center space-y-3 shadow-glass font-mono border border-emerald-500/20">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mx-auto text-white shadow-glow-emerald">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-extrabold text-white uppercase tracking-wider">ALL CATALOG RECORDS 100% VALIDATED</h3>
          <p className="text-xs text-slate-400 font-sans max-w-md mx-auto">
            Zero records currently triggered anomaly flags or confidence scores under 0.85. 100% of items meet delivery criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 font-mono">
          {items.map((item) => (
            <div
              key={item.id}
              className="glass-card rounded-2xl p-4.5 space-y-3 transition-all border border-white/[0.08] hover:border-amber-500/40 hover:shadow-glow-amber"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-extrabold text-white text-xs">{item.mfg_part_num}</span>
                    <span className="text-[10px] text-slate-400 font-mono">ROW #{item.row_id}</span>
                  </div>
                  <div className="text-xs text-cyan-300 font-bold mt-0.5 font-sans">
                    {item.brand_name} · <span className="text-slate-300 font-normal">{item.manufacturer_name}</span>
                  </div>
                </div>

                <span
                  className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                    item.confidence_score >= 0.85 ? 'glow-badge-cyan' : 'glow-badge-amber'
                  }`}
                >
                  {(item.confidence_score * 100).toFixed(0)}% CONF
                </span>
              </div>

              {/* Raw Input vs Generated Invoice */}
              <div className="space-y-1.5 text-xs">
                <div className="p-2.5 bg-slate-950/80 rounded-xl border border-white/[0.06] text-slate-400 text-[10px] line-clamp-2">
                  <span className="text-slate-500 block text-[9px] uppercase font-bold">SOURCE FEED:</span>
                  {item.raw_part_desc}
                </div>
                <div className="p-2.5 bg-slate-950/80 rounded-xl border border-white/[0.06] text-emerald-300 text-[10px]">
                  <span className="text-slate-500 block text-[9px] uppercase font-bold">SYNTHESIZED INVOICE:</span>
                  {item.invoice_desc}
                </div>
              </div>

              {/* Anomaly Badges */}
              {item.anomaly_flags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {item.anomaly_flags.map((flag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-[9px] glow-badge-amber rounded-full flex items-center space-x-1"
                    >
                      <AlertTriangle className="w-2.5 h-2.5" />
                      <span>{flag}</span>
                    </span>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-2.5 border-t border-white/[0.06]">
                <button
                  onClick={() => onInspectProduct(item.id)}
                  className="px-3 py-1.5 bg-slate-950 hover:bg-slate-900 text-slate-300 rounded-xl text-[11px] font-mono border border-white/[0.08] transition-colors"
                >
                  DUAL-PANE DIFF
                </button>
                <button
                  onClick={() => openEditor(item.id)}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-cyan-300 rounded-xl text-[11px] font-mono border border-cyan-500/40 transition-colors"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>EDIT</span>
                </button>
                <button
                  onClick={() => handleQuickApprove(item.id)}
                  className="flex items-center space-x-1.5 px-4 py-1.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white rounded-xl text-[11px] font-mono font-bold shadow-glow-emerald transition-all hover:scale-105"
                >
                  <CheckCircle2 className="w-3 h-3" />
                  <span>APPROVE</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Inline Editor Modal */}
      {editingId && editProduct && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="glass-panel border border-white/[0.12] rounded-3xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden font-sans">
            <div className="px-6 py-4 border-b border-white/[0.08] bg-gradient-to-r from-[#0B101D] via-[#0F1626] to-[#0B101D] flex items-center justify-between font-mono">
              <div className="flex items-center space-x-2.5">
                <Edit3 className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  CORRECT & VALIDATE MASTER RECORD (MPN: {editProduct.mfg_part_number})
                </h3>
              </div>
              <button
                onClick={() => setEditingId(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/[0.08]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
              {/* Brand & Manufacturer Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                <div>
                  <label className="block text-slate-400 font-mono text-[10px] uppercase font-bold mb-1">
                    CANONICAL BRAND NAME (WITH ®, ™)
                  </label>
                  <input
                    type="text"
                    value={editBrand}
                    onChange={(e) => setEditBrand(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-white font-semibold focus:border-cyan-400 font-sans"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-mono text-[10px] uppercase font-bold mb-1">
                    MANUFACTURER CORPORATE ENTITY
                  </label>
                  <input
                    type="text"
                    value={editManuf}
                    onChange={(e) => setEditManuf(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-white focus:border-cyan-400 font-sans"
                  />
                </div>
              </div>

              {/* INVOICE_DESC */}
              <div>
                <div className="flex justify-between items-center mb-1 font-mono">
                  <label className="text-white text-[10px] uppercase font-bold">
                    INVOICE_DESC (MUST BE ≤ 40 CHARS & ALL CAPS)
                  </label>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                      editInvoiceDesc.length <= 40 ? 'glow-badge-emerald' : 'glow-badge-amber'
                    }`}
                  >
                    {editInvoiceDesc.length}/40 chars
                  </span>
                </div>
                <input
                  type="text"
                  maxLength={40}
                  value={editInvoiceDesc}
                  onChange={(e) => setEditInvoiceDesc(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl font-mono text-emerald-300 font-bold focus:border-cyan-400"
                />
              </div>

              {/* MOBILE_DESC */}
              <div>
                <div className="flex justify-between items-center mb-1 font-mono">
                  <label className="text-white text-[10px] uppercase font-bold">
                    MOBILE_DESC (60–80 CHARS SPEC RANGE)
                  </label>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                      editMobileDesc.length >= 60 && editMobileDesc.length <= 80
                        ? 'glow-badge-cyan'
                        : 'glow-badge-amber'
                    }`}
                  >
                    {editMobileDesc.length}/80 chars
                  </span>
                </div>
                <input
                  type="text"
                  value={editMobileDesc}
                  onChange={(e) => setEditMobileDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-white focus:border-cyan-400 font-sans"
                />
              </div>

              {/* SHORT_DESC */}
              <div>
                <label className="block text-white font-mono text-[10px] uppercase font-bold mb-1">
                  SHORT_DESC (STRUCTURED TITLE)
                </label>
                <input
                  type="text"
                  value={editShortDesc}
                  onChange={(e) => setEditShortDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-white focus:border-cyan-400 font-sans"
                />
              </div>

              {/* LONG_DESC1 */}
              <div>
                <label className="block text-white font-mono text-[10px] uppercase font-bold mb-1">
                  LONG_DESC1 (TECHNICAL SPEC SENTENCE)
                </label>
                <textarea
                  rows={2}
                  value={editLongDesc}
                  onChange={(e) => setEditLongDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-slate-200 focus:border-cyan-400 font-sans"
                />
              </div>

              {/* Dynamic Triplet Attributes */}
              <div className="pt-3 border-t border-white/[0.06] space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-white text-[10px] uppercase">
                    50 TECHNICAL TRIPLET ATTRIBUTES (LABEL · VALUE · UOM)
                  </span>
                  <button
                    onClick={addAttributeSlot}
                    className="flex items-center space-x-1.5 px-3 py-1 bg-slate-900 hover:bg-slate-800 text-cyan-300 rounded-lg text-xs font-mono border border-cyan-500/30"
                  >
                    <Plus className="w-3 h-3" />
                    <span>ADD ATTRIBUTE SLOT</span>
                  </button>
                </div>

                <div className="space-y-2 max-h-44 overflow-y-auto pr-1 font-mono">
                  {editAttributes.map((attr, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Label"
                        value={attr.label}
                        onChange={(e) => updateAttributeSlot(idx, 'label', e.target.value)}
                        className="flex-1 px-3 py-1.5 bg-slate-950/80 border border-white/[0.08] rounded-lg text-xs text-white focus:border-cyan-400"
                      />
                      <input
                        type="text"
                        placeholder="Value"
                        value={attr.value}
                        onChange={(e) => updateAttributeSlot(idx, 'value', e.target.value)}
                        className="flex-1 px-3 py-1.5 bg-slate-950/80 border border-white/[0.08] rounded-lg text-xs text-white focus:border-cyan-400"
                      />
                      <input
                        type="text"
                        placeholder="UOM"
                        value={attr.uom || ''}
                        onChange={(e) => updateAttributeSlot(idx, 'uom', e.target.value)}
                        className="w-24 px-3 py-1.5 bg-slate-950/80 border border-white/[0.08] rounded-lg text-xs text-cyan-300 focus:border-cyan-400"
                      />
                      <button
                        onClick={() => removeAttributeSlot(idx)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-white/[0.08]"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="px-6 py-4 border-t border-white/[0.08] bg-[#090D17] flex items-center justify-end space-x-3 font-mono">
              <button
                onClick={() => setEditingId(null)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-slate-300 rounded-xl text-xs font-semibold border border-white/[0.08]"
              >
                CANCEL
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={saving}
                className="flex items-center space-x-2 px-5 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white rounded-xl text-xs font-bold shadow-glow-emerald transition-all disabled:opacity-50"
              >
                <Save className="w-3.5 h-3.5" />
                <span>{saving ? 'SAVING...' : 'SAVE & APPROVE FOR PRODUCTION'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

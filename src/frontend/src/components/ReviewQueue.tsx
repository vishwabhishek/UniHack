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
  ExternalLink
} from 'lucide-react';
import { ReviewItem, ProductDetail, AttributeTriple } from '../types';
import { fetchReviewQueue, approveProduct, rejectProduct, fetchProductDetail, updateProduct } from '../services/api';

interface ReviewQueueProps {
  onInspectProduct: (productId: string) => void;
  onRefreshCatalog?: () => void;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ onInspectProduct, onRefreshCatalog }) => {
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
      await approveProduct(id, 'Quick approved from review queue');
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
    <div className="space-y-6">
      {/* Header Summary */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xl">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center">
            <ShieldAlert className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-base font-bold text-white">
                Human-In-The-Loop (HITL) Quality Triage Queue
              </h2>
              <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                {items.length} Records Pending Review
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Low-confidence items (&lt; 0.85) or anomaly-flagged records requiring content specialist sign-off
            </p>
          </div>
        </div>

        <button
          onClick={loadQueue}
          className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Review Cards Grid */}
      {loading ? (
        <div className="py-20 text-center text-slate-400 space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-sky-400 mx-auto" />
          <p className="text-xs font-sans">Loading review queue items...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center space-y-3 shadow-xl">
          <div className="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-bold text-white">All Catalog Records Clear & Validated!</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Zero records currently triggered anomaly flags or confidence scores under 0.85. 100% of items meet delivery criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-slate-900/90 border border-slate-800 hover:border-amber-500/40 rounded-xl p-4 space-y-3 backdrop-blur-sm transition-all shadow-lg"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white text-sm">{item.mfg_part_num}</span>
                    <span className="text-xs text-slate-400 font-mono">Row #{item.row_id}</span>
                  </div>
                  <div className="text-xs text-sky-400 font-semibold mt-0.5">
                    {item.brand_name} • <span className="text-slate-300 font-normal">{item.manufacturer_name}</span>
                  </div>
                </div>

                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-bold font-mono border ${
                    item.confidence_score >= 0.85
                      ? 'bg-sky-500/20 text-sky-300 border-sky-500/40'
                      : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                  }`}
                >
                  {(item.confidence_score * 100).toFixed(0)}% Conf
                </span>
              </div>

              {/* Raw Input vs Generated Invoice */}
              <div className="space-y-1 text-xs">
                <div className="p-2 bg-slate-950 rounded border border-slate-800 font-mono text-slate-400 text-[11px] line-clamp-2">
                  <span className="text-slate-500 block text-[9px] uppercase font-bold">Raw Input:</span>
                  {item.raw_part_desc}
                </div>
                <div className="p-2 bg-slate-950 rounded border border-slate-800 font-mono text-emerald-300 text-[11px]">
                  <span className="text-slate-500 block text-[9px] uppercase font-bold">Generated Invoice Desc:</span>
                  {item.invoice_desc}
                </div>
              </div>

              {/* Anomaly Badges */}
              {item.anomaly_flags.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-1">
                  {item.anomaly_flags.map((flag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-[10px] bg-amber-500/10 text-amber-300 border border-amber-500/30 rounded flex items-center space-x-1"
                    >
                      <AlertTriangle className="w-2.5 h-2.5" />
                      <span>{flag}</span>
                    </span>
                  ))}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800/80">
                <button
                  onClick={() => onInspectProduct(item.id)}
                  className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs font-medium transition-colors"
                >
                  Side-by-Side Diff
                </button>
                <button
                  onClick={() => openEditor(item.id)}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-medium transition-colors shadow-sm"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>Inline Edit</span>
                </button>
                <button
                  onClick={() => handleQuickApprove(item.id)}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold transition-colors shadow-sm"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Approve</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Inline Editor Modal */}
      {editingId && editProduct && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-950 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Edit3 className="w-5 h-5 text-sky-400" />
                <h3 className="text-sm font-bold text-white">
                  Correct & Validate Record (MPN: {editProduct.mfg_part_number})
                </h3>
              </div>
              <button
                onClick={() => setEditingId(null)}
                className="text-slate-400 hover:text-white p-1 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
              {/* Brand & Manufacturer Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Canonical Brand Name (with ®, ™)</label>
                  <input
                    type="text"
                    value={editBrand}
                    onChange={(e) => setEditBrand(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 font-semibold"
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-medium mb-1">Manufacturer Name</label>
                  <input
                    type="text"
                    value={editManuf}
                    onChange={(e) => setEditManuf(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100"
                  />
                </div>
              </div>

              {/* INVOICE_DESC */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-slate-300 font-semibold">INVOICE_DESC (Must be ≤ 40 chars & ALL CAPS)</label>
                  <span
                    className={`font-mono text-[10px] px-1.5 py-0.2 rounded ${
                      editInvoiceDesc.length <= 40 ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
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
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg font-mono text-emerald-300 font-bold"
                />
              </div>

              {/* MOBILE_DESC */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-slate-300 font-semibold">MOBILE_DESC (60–80 chars range)</label>
                  <span
                    className={`font-mono text-[10px] px-1.5 py-0.2 rounded ${
                      editMobileDesc.length >= 60 && editMobileDesc.length <= 80
                        ? 'text-cyan-400 bg-cyan-500/10'
                        : 'text-amber-400 bg-amber-500/10'
                    }`}
                  >
                    {editMobileDesc.length}/80 chars
                  </span>
                </div>
                <input
                  type="text"
                  value={editMobileDesc}
                  onChange={(e) => setEditMobileDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100"
                />
              </div>

              {/* SHORT_DESC */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1">SHORT_DESC (Facet Title)</label>
                <input
                  type="text"
                  value={editShortDesc}
                  onChange={(e) => setEditShortDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100"
                />
              </div>

              {/* LONG_DESC1 */}
              <div>
                <label className="block text-slate-300 font-semibold mb-1">LONG_DESC1 (Technical Spec Sentence)</label>
                <textarea
                  rows={2}
                  value={editLongDesc}
                  onChange={(e) => setEditLongDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100"
                />
              </div>

              {/* Dynamic Triplet Attributes */}
              <div className="pt-2 border-t border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-300">Technical Triplet Attributes</span>
                  <button
                    onClick={addAttributeSlot}
                    className="flex items-center space-x-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-sky-400 rounded text-xs"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Attribute Slot</span>
                  </button>
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {editAttributes.map((attr, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Label"
                        value={attr.label}
                        onChange={(e) => updateAttributeSlot(idx, 'label', e.target.value)}
                        className="flex-1 px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded text-xs text-slate-100"
                      />
                      <input
                        type="text"
                        placeholder="Value"
                        value={attr.value}
                        onChange={(e) => updateAttributeSlot(idx, 'value', e.target.value)}
                        className="flex-1 px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded text-xs text-slate-100"
                      />
                      <input
                        type="text"
                        placeholder="UOM"
                        value={attr.uom || ''}
                        onChange={(e) => updateAttributeSlot(idx, 'uom', e.target.value)}
                        className="w-20 px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded text-xs text-slate-100 font-mono"
                      />
                      <button
                        onClick={() => removeAttributeSlot(idx)}
                        className="p-1.5 text-slate-500 hover:text-rose-400 rounded hover:bg-slate-800"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer Actions */}
            <div className="px-6 py-4 border-t border-slate-800 bg-slate-950 flex items-center justify-end space-x-2">
              <button
                onClick={() => setEditingId(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={saving}
                className="flex items-center space-x-1.5 px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold shadow-lg shadow-emerald-500/20 disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Saving...' : 'Save & Approve for Production'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

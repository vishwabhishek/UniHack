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
import { fetchReviewQueue, approveProduct, fetchProductDetail, updateProduct } from '../services/api';
import { useToast } from './Toast';
import { SegmentedGauge } from './SegmentedGauge';

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

  return (
    <div className="space-y-4 font-sans">
      
      {/* Header Summary Banner */}
      <div className="p-4 rounded-xl bg-[#12161D] border border-[#232935] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-[#1A1F29] border border-[#232935] flex items-center justify-center text-[#E8A33D]">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                HUMAN-IN-THE-LOOP EXCEPTION TRIAGE BOARD
              </h2>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#E8A33D]/10 text-[#E8A33D] border border-[#E8A33D]/25">
                {items.length} ANOMALIES
              </span>
            </div>
            <p className="text-xs text-[#8B93A3] mt-0.5">
              Records with confidence &lt; 0.85 or data conflicts routed for specialist sign-off before delivery
            </p>
          </div>
        </div>

        <button
          onClick={loadQueue}
          className="flex items-center space-x-2 px-3 py-1.5 bg-[#0B0E13] hover:bg-[#1A1F29] text-[#E7EAF0] rounded-lg text-xs font-bold font-mono border border-[#232935] transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#45E0D6]' : ''}`} />
          <span>SYNC QUEUE</span>
        </button>
      </div>

      {/* Grid of Exception Cards */}
      {loading ? (
        <div className="py-20 text-center text-[#8B93A3] space-y-3 font-mono">
          <div className="w-7 h-7 border-2 border-[#E8A33D] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs">LOADING EXCEPTION TRIAGE RECORDS...</p>
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 rounded-xl bg-[#12161D] border border-[#232935] text-center space-y-3 font-mono">
          <div className="w-10 h-10 rounded-xl bg-[#1A1F29] border border-[#232935] flex items-center justify-center mx-auto text-[#3DDC84]">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">ALL CATALOG ITEMS VALIDATED</h3>
          <p className="text-xs text-[#8B93A3] font-sans max-w-md mx-auto">
            Zero records currently triggered anomaly flags. 100% of items meet master delivery criteria.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {items.map((item) => (
            <div
              key={item.id}
              className="bg-[#12161D] border border-[#232935] hover:border-[#E8A33D]/40 rounded-xl p-4 space-y-3 transition-all"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-white text-xs">{item.mfg_part_num}</span>
                    <span className="text-[10px] text-[#8B93A3] font-mono">ROW #{item.row_id}</span>
                  </div>
                  <div className="text-xs text-[#45E0D6] font-semibold mt-0.5">
                    {item.brand_name} · <span className="text-[#8B93A3] font-normal">{item.manufacturer_name}</span>
                  </div>
                </div>

                <SegmentedGauge score={item.confidence_score} size="sm" />
              </div>

              {/* Anomaly Badges */}
              <div className="flex flex-wrap gap-1.5">
                {(item.anomaly_flags || []).map((r: string, i: number) => (
                  <span
                    key={i}
                    className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#E8A33D]/10 text-[#E8A33D] border border-[#E8A33D]/25"
                  >
                    <AlertTriangle className="w-2.5 h-2.5" />
                    <span>{r}</span>
                  </span>
                ))}
              </div>

              {/* Raw vs Enriched Diff Preview */}
              <div className="bg-[#0B0E13] p-3 rounded-lg border border-[#232935] space-y-2 text-[11px] font-mono">
                <div>
                  <span className="text-[#EF5A5A] font-bold block text-[10px]">RAW SUPPLIER INPUT:</span>
                  <span className="text-[#8B93A3] truncate block">{item.raw_part_desc || 'No raw description provided'}</span>
                </div>
                <div>
                  <span className="text-[#3DDC84] font-bold block text-[10px]">PROPOSED ENRICHED TITLE:</span>
                  <span className="text-[#E7EAF0] truncate block">{item.short_desc || 'Pending spec curation'}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-2 pt-1 border-t border-[#232935] font-mono text-xs">
                <button
                  onClick={() => onInspectProduct(item.id)}
                  className="px-2.5 py-1.5 rounded-lg bg-[#0B0E13] hover:bg-[#1A1F29] text-[#8B93A3] hover:text-white border border-[#232935] transition-colors flex items-center space-x-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>INSPECT</span>
                </button>
                <button
                  onClick={() => handleOpenEdit(item.id)}
                  className="px-2.5 py-1.5 rounded-lg bg-[#1A1F29] hover:bg-[#232935] text-[#E8A33D] border border-[#232935] transition-colors flex items-center space-x-1 font-bold"
                >
                  <Edit3 className="w-3 h-3" />
                  <span>CURATE SPEC</span>
                </button>
                <button
                  onClick={() => handleQuickApprove(item.id)}
                  className="px-3 py-1.5 rounded-lg bg-[#3DDC84]/10 hover:bg-[#3DDC84]/20 text-[#3DDC84] border border-[#3DDC84]/30 transition-colors flex items-center space-x-1 font-bold"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-[#12161D] border border-[#232935] rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-sans">
            
            {/* Modal Header */}
            <div className="p-4 border-b border-[#232935] flex items-center justify-between bg-[#1A1F29]">
              <div className="flex items-center space-x-2.5">
                <div className="w-7 h-7 rounded-lg bg-[#0B0E13] border border-[#232935] flex items-center justify-center text-[#E8A33D]">
                  <Edit3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-mono font-bold text-white uppercase">
                    CURATE MASTER SPECIFICATION — ROW #{editProduct.raw.row_id} ({editProduct.mfg_part_number})
                  </h3>
                </div>
              </div>
              <button
                onClick={() => setEditingId(null)}
                className="p-1 rounded-lg text-[#8B93A3] hover:text-white hover:bg-[#0B0E13]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body Form */}
            <div className="p-5 overflow-y-auto space-y-4 text-xs font-mono">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">CANONICAL BRAND</label>
                  <input
                    type="text"
                    value={editBrand}
                    onChange={(e) => setEditBrand(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0B0E13] border border-[#232935] rounded-lg text-white focus:border-[#45E0D6] focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">MANUFACTURER NAME</label>
                  <input
                    type="text"
                    value={editManuf}
                    onChange={(e) => setEditManuf(e.target.value)}
                    className="w-full px-3 py-2 bg-[#0B0E13] border border-[#232935] rounded-lg text-white focus:border-[#45E0D6] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">
                  INVOICE_DESC (ERP Hard Gate: ≤40 Chars, ALL CAPS)
                </label>
                <input
                  type="text"
                  maxLength={40}
                  value={editInvoiceDesc}
                  onChange={(e) => setEditInvoiceDesc(e.target.value.toUpperCase())}
                  className="w-full px-3 py-2 bg-[#0B0E13] border border-[#232935] rounded-lg text-white font-bold tracking-wide focus:border-[#45E0D6] focus:outline-none"
                />
                <div className="text-[10px] text-right mt-0.5 text-[#8B93A3]">
                  {editInvoiceDesc.length}/40 characters
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">
                  MOBILE_DESC (Mobile Gate: 60–80 Chars)
                </label>
                <input
                  type="text"
                  value={editMobileDesc}
                  onChange={(e) => setEditMobileDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-[#0B0E13] border border-[#232935] rounded-lg text-white focus:border-[#45E0D6] focus:outline-none font-sans"
                />
                <div className="text-[10px] text-right mt-0.5 text-[#8B93A3]">
                  {editMobileDesc.length} characters (Target: 60-80)
                </div>
              </div>

              {/* Extracted Specification Triplets */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-[10px] font-bold text-[#8B93A3] uppercase">
                    STRUCTURED ATTRIBUTE TRIPLETS (LOV CONTROLLED)
                  </label>
                  <button
                    type="button"
                    onClick={addAttributeSlot}
                    className="text-[10px] font-bold text-[#45E0D6] hover:underline flex items-center space-x-1"
                  >
                    <Plus className="w-3 h-3" />
                    <span>ADD ATTRIBUTE</span>
                  </button>
                </div>

                <div className="space-y-2">
                  {editAttributes.map((attr, idx) => (
                    <div key={idx} className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="Label (e.g. Voltage)"
                        value={attr.label}
                        onChange={(e) => updateAttributeSlot(idx, 'label', e.target.value)}
                        className="flex-1 px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-white"
                      />
                      <input
                        type="text"
                        placeholder="Value (e.g. 120)"
                        value={attr.value}
                        onChange={(e) => updateAttributeSlot(idx, 'value', e.target.value)}
                        className="flex-1 px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-white"
                      />
                      <input
                        type="text"
                        placeholder="UOM (e.g. V)"
                        value={attr.uom || ''}
                        onChange={(e) => updateAttributeSlot(idx, 'uom', e.target.value)}
                        className="w-20 px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-white"
                      />
                      <button
                        type="button"
                        onClick={() => removeAttributeSlot(idx)}
                        className="p-1.5 text-[#8B93A3] hover:text-[#EF5A5A] rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-[#232935] bg-[#1A1F29] flex items-center justify-end space-x-2 font-mono text-xs">
              <button
                type="button"
                onClick={() => setEditingId(null)}
                className="px-3.5 py-2 rounded-lg bg-[#0B0E13] hover:bg-[#12161D] text-[#8B93A3] border border-[#232935]"
              >
                CANCEL
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={handleSaveEdit}
                className="px-4 py-2 rounded-lg bg-[#45E0D6] text-[#0B0E13] font-bold flex items-center space-x-1.5 disabled:opacity-50"
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

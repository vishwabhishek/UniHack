import React, { useState, useEffect } from 'react';
import {
  RefreshCw,
  Edit3,
  CheckCircle2,
  AlertTriangle,
  X,
  ExternalLink,
  ShieldAlert,
  ShieldCheck,
  FileText,
  History,
  XCircle,
  HelpCircle,
  Check
} from 'lucide-react';
import {
  ReviewItem,
  ProductFieldReview,
  FieldReviewItem,
  AuditRecord
} from '../types';
import {
  fetchReviewQueue,
  fetchProductFieldReview,
  submitFieldAction,
  promoteProductValidated
} from '../services/api';
import { useToast } from './Toast';
import { useAuth } from '../context/AuthContext';
import { PageHeader } from './common/PageHeader';
import { StatusBadge } from './common/StatusBadge';
import { EmptyState } from './common/EmptyState';

interface ReviewQueueProps {
  onInspectProduct: (productId: string) => void;
  onRefreshCatalog?: () => void;
}

export const ReviewQueue: React.FC<ReviewQueueProps> = ({ onInspectProduct, onRefreshCatalog }) => {
  const { showToast } = useToast();
  const { user, canApprove } = useAuth();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Field-level review drawer state
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [fieldReviewData, setFieldReviewData] = useState<ProductFieldReview | null>(null);
  const [loadingFields, setLoadingFields] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'fields' | 'audit'>('fields');
  const [fieldFilter, setFieldFilter] = useState<'all' | 'high_risk' | 'unresolved'>('all');

  // Action dialog state
  const [activeFieldAction, setActiveFieldAction] = useState<{
    fieldName: string;
    displayLabel: string;
    action: 'approve' | 'edit' | 'reject' | 'mark_unknown';
    currentValue: string;
  } | null>(null);
  const [actionNewValue, setActionNewValue] = useState<string>('');
  const [actionReason, setActionReason] = useState<string>('');
  const [submittingAction, setSubmittingAction] = useState<boolean>(false);
  const [promoting, setPromoting] = useState<boolean>(false);

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

  const handleOpenFieldReview = async (productId: string) => {
    setSelectedProductId(productId);
    setLoadingFields(true);
    try {
      const data = await fetchProductFieldReview(productId);
      setFieldReviewData(data);
      setActiveTab('fields');
    } catch (e) {
      console.error('Failed to load field review data:', e);
      showToast('Error', 'Failed to load field-level evidence', 'error');
      setSelectedProductId(null);
    } finally {
      setLoadingFields(false);
    }
  };

  const handleTriggerAction = (
    field: FieldReviewItem,
    action: 'approve' | 'edit' | 'reject' | 'mark_unknown'
  ) => {
    setActiveFieldAction({
      fieldName: field.field_name,
      displayLabel: field.display_label,
      action,
      currentValue: field.normalized_value || field.candidate_value || ''
    });
    setActionNewValue(field.normalized_value || field.candidate_value || '');
    if (action === 'approve') {
      setActionReason('Verified against official manufacturer source evidence');
    } else if (action === 'reject') {
      setActionReason('Unsupported or contradictory to official reference data');
    } else if (action === 'mark_unknown') {
      setActionReason('Field not supported by evidence; marked unknown to remain blank in export');
    } else {
      setActionReason('');
    }
  };

  const handleExecuteAction = async () => {
    if (!selectedProductId || !activeFieldAction) return;
    if (!actionReason.trim()) {
      showToast('Reason Required', 'Please enter a reason for this audit record', 'warning');
      return;
    }

    setSubmittingAction(true);
    try {
      const updated = await submitFieldAction(selectedProductId, {
        field_name: activeFieldAction.fieldName,
        action: activeFieldAction.action,
        new_value: activeFieldAction.action === 'edit' ? actionNewValue : undefined,
        reason: actionReason.trim()
      });
      setFieldReviewData(updated);
      showToast(
        'Action Applied',
        `Field '${activeFieldAction.displayLabel}' updated (${activeFieldAction.action})`,
        'success'
      );
      setActiveFieldAction(null);
      setActionReason('');
      setActionNewValue('');
      // Reload parent queue in background
      const q = await fetchReviewQueue();
      setItems(q.items);
      if (onRefreshCatalog) onRefreshCatalog();
    } catch (e: any) {
      console.error('Failed to submit field action:', e);
      showToast('Error', e.message || 'Failed to update field', 'error');
    } finally {
      setSubmittingAction(false);
    }
  };

  const handlePromoteProduct = async () => {
    if (!selectedProductId) return;
    setPromoting(true);
    try {
      const res = await promoteProductValidated(
        selectedProductId,
        'All high-risk and core fields verified by specialist'
      );
      showToast('Product Validated', res.message, 'success');
      setSelectedProductId(null);
      setFieldReviewData(null);
      await loadQueue();
      if (onRefreshCatalog) onRefreshCatalog();
    } catch (e: any) {
      console.error('Failed to promote product to validated:', e);
      showToast('Validation Blocked', e.message || 'High-risk fields unresolved', 'error');
    } finally {
      setPromoting(false);
    }
  };

  const renderStatusBadge = (status: string) => {
    return <StatusBadge status={status} />;
  };

  return (
    <div className="space-y-4 font-sans">
      
      {/* Standard Page Header */}
      <PageHeader
        title="Field-Level Evidence Review & HITL Triage"
        description="Audit raw distributor inputs against registered manufacturer evidence. Only verified fields reach Validated status."
        badge={<span className="chip flagged font-bold">{items.length} PRODUCTS FLAGGED</span>}
        actions={
          <button
            onClick={loadQueue}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white rounded-md text-xs font-mono border border-[var(--border)] transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[var(--cyan)]' : ''}`} />
            <span>SYNC QUEUE</span>
          </button>
        }
      />

      {/* Grid of Flagged Items */}
      {loading ? (
        <div className="py-20 text-center text-[var(--text-muted)] space-y-3 font-mono">
          <div className="w-7 h-7 border-2 border-[var(--amber)] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs">LOADING EXCEPTION TRIAGE RECORDS...</p>
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={CheckCircle2}
          title="All Catalog Items Fully Verified & Validated"
          description="Zero products currently contain unverified high-risk fields or anomaly flags. All candidate records are compliant with 252-column master delivery format."
        />
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

                <div className="text-right">
                  <span className="font-mono text-xs text-[var(--amber)] font-bold">
                    {(item.confidence_score * 100).toFixed(1)}% Conf
                  </span>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    {item.status}
                  </div>
                </div>
              </div>

              {/* Anomaly Flags */}
              <div className="flex flex-wrap gap-1.5">
                {(item.anomaly_flags || []).map((r: string, i: number) => (
                  <span key={i} className="chip flagged flex items-center gap-1 text-[10px]">
                    <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                    <span>{r}</span>
                  </span>
                ))}
              </div>

              {/* Supplier Input Preview */}
              <div className="bg-[var(--surface-1)] p-2.5 rounded border border-[var(--border)] space-y-1 text-[11px] font-mono">
                <div className="text-[10px] text-[var(--text-muted)]">RAW SUPPLIER INPUT:</div>
                <div className="text-[var(--text-primary)] truncate">{item.raw_part_desc || 'No raw description provided'}</div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-2 border-t border-[var(--border)] font-mono text-xs">
                <button
                  onClick={() => onInspectProduct(item.id)}
                  className="px-2.5 py-1.5 rounded bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white border border-[var(--border)] transition-colors flex items-center gap-1 cursor-pointer text-xs"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>INSPECT</span>
                </button>
                <button
                  onClick={() => handleOpenFieldReview(item.id)}
                  className="px-3.5 py-1.5 rounded bg-[var(--cyan-bg)] hover:opacity-90 text-[var(--cyan)] border border-[var(--cyan)] font-semibold transition-opacity flex items-center gap-1.5 cursor-pointer text-xs"
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>FIELD EVIDENCE REVIEW</span>
                </button>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Field-Level Evidence Review Modal */}
      {selectedProductId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
          <div className="bg-[var(--surface-2)] border border-[var(--border-strong)] rounded-xl w-full max-w-5xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden font-sans">
            
            {/* Modal Header */}
            <div className="p-4 border-b border-[var(--border)] flex items-center justify-between bg-[var(--surface-1)]">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-[2px] bg-[var(--cyan)]" />
                <div>
                  <h3 className="text-xs font-mono font-bold text-[var(--text-primary)] uppercase flex items-center gap-2">
                    <span>EVIDENCE REVIEW — {fieldReviewData?.mfg_part_number || 'PRODUCT'}</span>
                    <span className="text-[var(--text-muted)] font-normal">(ROW #{fieldReviewData?.row_id})</span>
                  </h3>
                  <div className="text-[11px] text-[var(--text-muted)] mt-0.5">
                    {fieldReviewData?.brand_name} · {fieldReviewData?.manufacturer_name}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {fieldReviewData && (
                  <div className="flex items-center gap-2">
                    {fieldReviewData.high_risk_unresolved_count > 0 ? (
                      <span className="px-2.5 py-1 rounded bg-rose-500/10 text-rose-400 border border-rose-500/30 text-[11px] font-mono font-semibold flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3" />
                        {fieldReviewData.high_risk_unresolved_count} HIGH-RISK UNRESOLVED
                      </span>
                    ) : (
                      <span className="px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[11px] font-mono font-semibold flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" />
                        ALL HIGH-RISK FIELDS RESOLVED
                      </span>
                    )}

                    <button
                      onClick={handlePromoteProduct}
                      disabled={!fieldReviewData.can_promote_to_validated || !canApprove || promoting}
                      className={`px-3 py-1 rounded font-mono text-xs font-bold border transition-all flex items-center gap-1.5 ${
                        fieldReviewData.can_promote_to_validated && canApprove
                          ? 'bg-emerald-600 hover:bg-emerald-500 text-white border-emerald-400 cursor-pointer shadow-sm'
                          : 'bg-zinc-800 text-zinc-500 border-zinc-700 cursor-not-allowed'
                      }`}
                      title={
                        !canApprove
                          ? `Promotion requires Reviewer or Admin role (current role: ${user?.role || 'viewer'})`
                          : fieldReviewData.can_promote_to_validated
                          ? 'Promote this product to Validated status'
                          : 'Resolve all high-risk fields first'
                      }
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>{promoting ? 'VALIDATING...' : 'PROMOTE TO VALIDATED'}</span>
                    </button>
                  </div>
                )}

                <button
                  onClick={() => {
                    setSelectedProductId(null);
                    setFieldReviewData(null);
                  }}
                  className="p-1 rounded-md text-[var(--text-muted)] hover:text-white hover:bg-[var(--surface-2)] cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Subheader Tabs & Filter Strip */}
            <div className="px-4 py-2 border-b border-[var(--border)] bg-[var(--surface-2)] flex flex-wrap items-center justify-between gap-2 text-xs font-mono">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveTab('fields')}
                  className={`px-3 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
                    activeTab === 'fields'
                      ? 'bg-[var(--surface-1)] text-[var(--cyan)] border-[var(--cyan)] font-bold'
                      : 'text-[var(--text-muted)] border-transparent hover:text-white'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>FIELD EVIDENCE ({fieldReviewData?.fields?.length || 0})</span>
                </button>
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-3 py-1 rounded border transition-colors flex items-center gap-1.5 cursor-pointer ${
                    activeTab === 'audit'
                      ? 'bg-[var(--surface-1)] text-[var(--cyan)] border-[var(--cyan)] font-bold'
                      : 'text-[var(--text-muted)] border-transparent hover:text-white'
                  }`}
                >
                  <History className="w-3.5 h-3.5" />
                  <span>AUDIT TRAIL ({fieldReviewData?.audit_trail?.length || 0})</span>
                </button>
              </div>

              {activeTab === 'fields' && (
                <div className="flex items-center gap-1 bg-[var(--surface-1)] p-0.5 rounded border border-[var(--border)]">
                  {(['all', 'high_risk', 'unresolved'] as const).map((filterMode) => (
                    <button
                      key={filterMode}
                      onClick={() => setFieldFilter(filterMode)}
                      className={`px-2 py-0.5 rounded text-[10px] uppercase transition-colors cursor-pointer ${
                        fieldFilter === filterMode
                          ? 'bg-[var(--cyan-bg)] text-[var(--cyan)] font-bold'
                          : 'text-[var(--text-muted)] hover:text-white'
                      }`}
                    >
                      {filterMode === 'all' ? 'All' : filterMode === 'high_risk' ? 'High-Risk Only' : 'Unresolved'}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Body */}
            <div className="p-4 overflow-y-auto flex-1 space-y-3 bg-[var(--surface-1)]">
              {loadingFields ? (
                <div className="py-20 text-center text-[var(--text-muted)] space-y-3 font-mono">
                  <div className="w-6 h-6 border-2 border-[var(--cyan)] border-t-transparent rounded-full animate-spin mx-auto" />
                  <p className="text-xs">LOADING FIELD LINEAGE & CITATIONS...</p>
                </div>
              ) : activeTab === 'audit' ? (
                /* Audit Trail Table */
                <div className="space-y-3 font-mono text-xs">
                  {fieldReviewData?.audit_trail?.length === 0 ? (
                    <div className="p-8 text-center text-[var(--text-muted)] bg-[var(--surface-2)] rounded-lg border border-[var(--border)]">
                      No manual audit records logged yet for this product.
                    </div>
                  ) : (
                    <div className="border border-[var(--border)] rounded-lg overflow-hidden bg-[var(--surface-2)]">
                      <table className="w-full text-left text-[11px]">
                        <thead className="bg-[var(--surface-1)] border-b border-[var(--border)] text-[var(--text-muted)]">
                          <tr>
                            <th className="p-2.5">TIMESTAMP</th>
                            <th className="p-2.5">REVIEWER</th>
                            <th className="p-2.5">FIELD</th>
                            <th className="p-2.5">ACTION</th>
                            <th className="p-2.5">PREVIOUS &rarr; NEW</th>
                            <th className="p-2.5">REASON</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border)]">
                          {fieldReviewData?.audit_trail?.map((a) => (
                            <tr key={a.id} className="hover:bg-[var(--surface-1)]">
                              <td className="p-2.5 text-[var(--text-muted)]">{a.timestamp.replace('T', ' ').slice(0, 19)}</td>
                              <td className="p-2.5 text-[var(--cyan)] font-bold">{a.reviewer}</td>
                              <td className="p-2.5 font-bold text-[var(--text-primary)]">{a.field_name}</td>
                              <td className="p-2.5">
                                <span className="px-1.5 py-0.5 rounded bg-[var(--surface-1)] border border-[var(--border)] uppercase font-bold text-[10px]">
                                  {a.action}
                                </span>
                              </td>
                              <td className="p-2.5">
                                <span className="line-through text-rose-400 mr-1.5">{a.previous_value || 'None'}</span>
                                &rarr; <span className="text-emerald-400 font-bold ml-1.5">{a.new_value || 'None'}</span>
                              </td>
                              <td className="p-2.5 text-[var(--text-secondary)]">{a.reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ) : (
                /* Field Evidence Cards */
                <div className="space-y-3">
                  {(fieldReviewData?.fields || [])
                    .filter((f) => {
                      if (fieldFilter === 'high_risk') return f.is_high_risk;
                      if (fieldFilter === 'unresolved') return f.verification_status !== 'verified' && f.verification_status !== 'unknown';
                      return true;
                    })
                    .map((f) => (
                    <div
                      key={f.field_name}
                      className={`p-3.5 rounded-lg border transition-all ${
                        f.is_high_risk
                          ? 'bg-[var(--surface-2)] border-[var(--border-strong)]'
                          : 'bg-[var(--surface-2)] border-[var(--border)] opacity-95'
                      }`}
                    >
                      {/* Field Header */}
                      <div className="flex items-center justify-between gap-2 mb-2 pb-2 border-b border-[var(--border)]">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-[var(--text-primary)]">
                            {f.display_label}
                          </span>
                          {f.is_high_risk && (
                            <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                              HIGH-RISK
                            </span>
                          )}
                          <span className="text-[10px] font-mono text-[var(--text-muted)]">
                            ({f.field_name})
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          {renderStatusBadge(f.verification_status)}
                          <span className="text-[11px] font-mono text-[var(--text-muted)]">
                            Conf: {(f.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      {/* 3-Column Value Grid: Raw vs Candidate vs Normalized */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5 text-[11px] font-mono mb-2.5">
                        <div className="p-2 rounded bg-[var(--surface-1)] border border-[var(--border)]">
                          <span className="text-[10px] text-[var(--text-muted)] block font-bold">RAW SUPPLIER INPUT</span>
                          <span className="text-zinc-300 break-words">{f.raw_supplier_input || '—'}</span>
                        </div>
                        <div className="p-2 rounded bg-[var(--surface-1)] border border-[var(--border)]">
                          <span className="text-[10px] text-amber-400/80 block font-bold">CURRENT CANDIDATE</span>
                          <span className="text-amber-200 break-words">{f.candidate_value || '—'}</span>
                        </div>
                        <div className="p-2 rounded bg-[var(--surface-1)] border border-[var(--border)]">
                          <span className="text-[10px] text-emerald-400/80 block font-bold">NORMALIZED STANDARD</span>
                          <span className="text-emerald-300 font-bold break-words">{f.normalized_value || '—'}</span>
                        </div>
                      </div>

                      {/* Evidence Lineage & Citation */}
                      <div className="p-2 rounded bg-[var(--surface-1)] border border-[var(--border)] text-[11px] font-mono flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                        <div className="space-y-0.5 max-w-2xl">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-[var(--cyan)] font-bold uppercase">CITATION:</span>
                            <span className="text-zinc-300">{f.source_citation || 'Supplier Input'}</span>
                            {f.source_url && (
                              <a
                                href={f.source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[var(--cyan)] hover:underline flex items-center gap-0.5 text-[10px]"
                              >
                                <ExternalLink className="w-2.5 h-2.5" />
                                <span>Source Link</span>
                              </a>
                            )}
                          </div>
                          {f.source_excerpt && (
                            <div className="text-[10px] text-[var(--text-muted)] italic truncate">
                              &ldquo;{f.source_excerpt}&rdquo;
                            </div>
                          )}
                        </div>

                        {/* Action Buttons for this Field */}
                        <div className="flex items-center gap-1.5 self-end sm:self-auto">
                          <button
                            onClick={() => handleTriggerAction(f, 'approve')}
                            className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-colors cursor-pointer flex items-center gap-1"
                            title="Approve and verify field"
                          >
                            <Check className="w-2.5 h-2.5" /> APPROVE
                          </button>
                          <button
                            onClick={() => handleTriggerAction(f, 'edit')}
                            className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 transition-colors cursor-pointer flex items-center gap-1"
                            title="Edit value with audit reason"
                          >
                            <Edit3 className="w-2.5 h-2.5" /> EDIT
                          </button>
                          <button
                            onClick={() => handleTriggerAction(f, 'reject')}
                            className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors cursor-pointer flex items-center gap-1"
                            title="Reject unsupported value"
                          >
                            <XCircle className="w-2.5 h-2.5" /> REJECT
                          </button>
                          <button
                            onClick={() => handleTriggerAction(f, 'mark_unknown')}
                            className="px-2 py-1 rounded text-[10px] font-mono font-bold bg-zinc-500/10 hover:bg-zinc-500/20 text-zinc-400 border border-zinc-500/30 transition-colors cursor-pointer flex items-center gap-1"
                            title="Mark unknown to leave blank in final delivery export"
                          >
                            <HelpCircle className="w-2.5 h-2.5" /> UNKNOWN
                          </button>
                        </div>
                      </div>

                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Action Prompt Sub-Modal */}
            {activeFieldAction && (
              <div className="p-4 border-t border-[var(--border)] bg-[var(--surface-2)] space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[var(--cyan)] uppercase">
                      APPLY ACTION: {activeFieldAction.action.toUpperCase()}
                    </span>
                    <span className="text-[var(--text-muted)]">
                      on field &lsquo;{activeFieldAction.displayLabel}&rsquo;
                    </span>
                  </div>
                  <button
                    onClick={() => setActiveFieldAction(null)}
                    className="text-[var(--text-muted)] hover:text-white cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {activeFieldAction.action === 'edit' && (
                  <div>
                    <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">
                      NEW NORMALIZED VALUE
                    </label>
                    <input
                      type="text"
                      value={actionNewValue}
                      onChange={(e) => setActionNewValue(e.target.value)}
                      placeholder="Enter verified new value..."
                      className="w-full px-3 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">
                    AUDIT REASON (Required by Compliance Policy)
                  </label>
                  <input
                    type="text"
                    value={actionReason}
                    onChange={(e) => setActionReason(e.target.value)}
                    placeholder="Provide specific justification or reference document..."
                    className="w-full px-3 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-1">
                  <button
                    onClick={() => setActiveFieldAction(null)}
                    className="px-3 py-1 rounded bg-[var(--surface-1)] hover:bg-[var(--border)] text-[var(--text-secondary)] border border-[var(--border)] cursor-pointer"
                  >
                    CANCEL
                  </button>
                  <button
                    onClick={handleExecuteAction}
                    disabled={submittingAction}
                    className="px-4 py-1 rounded bg-[var(--cyan-bg)] hover:opacity-90 text-[var(--cyan)] border border-[var(--cyan)] font-bold cursor-pointer"
                  >
                    {submittingAction ? 'RECORDING AUDIT...' : 'CONFIRM & PERSIST AUDIT'}
                  </button>
                </div>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
};

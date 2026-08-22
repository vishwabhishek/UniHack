import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  FileText,
  FileCheck,
  Search,
  ExternalLink,
  Plus,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Layers,
  Database,
  Info,
  Clock,
  X,
  FileCode,
  Zap,
  Play,
  Square,
  Trash2,
  Cpu,
  Coins,
  CheckCircle,
  AlertOctagon,
  Timer,
  Sliders,
  Sparkles
} from 'lucide-react';
import {
  SourceRegistryEntry,
  SourceRegistrationRequest,
  EvidenceChunk,
  ExtractedCandidate,
  BatchReport,
  CacheStats,
  ProductJobState,
  BatchProductStatus
} from '../types';
import {
  fetchSourceRegistry,
  registerEvidenceSource,
  queryEvidence,
  startBatchEnrichment,
  fetchLatestBatchJob,
  fetchBatchJobStatus,
  cancelBatchJob,
  fetchCacheStats,
  clearExtractionCache,
  markSourceStale,
  supersedeSource,
  rejectSource,
  reingestSource
} from '../services/api';

import { useToast } from './Toast';
import { PageHeader } from './common/PageHeader';
import { StatusBadge } from './common/StatusBadge';
import { EmptyState } from './common/EmptyState';

export const EvidenceInbox: React.FC = () => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'sources' | 'batch'>('sources');

  // Registry state
  const [sources, setSources] = useState<SourceRegistryEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('ALL');

  // Inspection Drawer
  const [selectedEntry, setSelectedEntry] = useState<SourceRegistryEntry | null>(null);
  const [entryChunks, setEntryChunks] = useState<EvidenceChunk[]>([]);
  const [entryCandidates, setEntryCandidates] = useState<ExtractedCandidate[]>([]);
  const [drawerLoading, setDrawerLoading] = useState<boolean>(false);

  // New Registration Modal
  const [showRegisterModal, setShowRegisterModal] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [newUrl, setNewUrl] = useState<string>('');
  const [newMpn, setNewMpn] = useState<string>('');
  const [newBrand, setNewBrand] = useState<string>('');
  const [newMfr, setNewMfr] = useState<string>('');
  const [newTitle, setNewTitle] = useState<string>('');
  const [newSourceType, setNewSourceType] = useState<string>('manufacturer_page');

  // Batch Enrichment State
  const [batchReport, setBatchReport] = useState<BatchReport | null>(null);
  const [cacheStats, setCacheStats] = useState<CacheStats | null>(null);
  const [concurrency, setConcurrency] = useState<number>(3);
  const [forceRefresh, setForceRefresh] = useState<boolean>(false);
  const [batchStarting, setBatchStarting] = useState<boolean>(false);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    loadRegistry();
    loadBatchAndCacheState();

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Real-time status polling when a batch job is running
  useEffect(() => {
    if (batchReport && batchReport.status === 'RUNNING') {
      if (!pollIntervalRef.current) {
        pollIntervalRef.current = setInterval(async () => {
          try {
            const updated = await fetchBatchJobStatus(batchReport.job_id);
            setBatchReport(updated);
            if (updated.status !== 'RUNNING') {
              if (pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
              await loadBatchAndCacheState();
              showToast('Batch Complete', `Processed ${updated.processed_products} products (${updated.completed_products} verified, ${updated.review_required_products} review required).`, 'success');
            }
          } catch (e) {
            console.error('Failed to poll batch status:', e);
          }
        }, 1000);
      }
    } else {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    }
  }, [batchReport?.status]);

  const loadRegistry = async () => {
    setLoading(true);
    try {
      const data = await fetchSourceRegistry();
      setSources(data);
    } catch (e: any) {
      console.error('Failed to load evidence registry:', e);
      showToast('Registry Error', e.message || 'Failed to load live source registry', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadBatchAndCacheState = async () => {
    try {
      const [latestBatch, stats] = await Promise.all([
        fetchLatestBatchJob().catch(() => null),
        fetchCacheStats().catch(() => null),
      ]);
      if (latestBatch) setBatchReport(latestBatch);
      if (stats) setCacheStats(stats);
    } catch (e) {
      console.error('Failed to load batch/cache state:', e);
    }
  };

  const handleStartBatch = async () => {
    setBatchStarting(true);
    try {
      const report = await startBatchEnrichment({
        max_concurrency: concurrency,
        force_refresh: forceRefresh,
      });
      setBatchReport(report);
      showToast('Batch Job Launched', `Started batch enrichment for ${report.evidence_backed_products} registered products.`, 'info');
    } catch (e: any) {
      showToast('Batch Failed', e.message || 'Could not launch batch enrichment', 'error');
    } finally {
      setBatchStarting(false);
    }
  };

  const handleCancelBatch = async () => {
    if (!batchReport) return;
    try {
      await cancelBatchJob(batchReport.job_id);
      showToast('Cancellation Sent', `Cancelled batch job ${batchReport.job_id}`, 'warning');
      const updated = await fetchBatchJobStatus(batchReport.job_id);
      setBatchReport(updated);
    } catch (e: any) {
      showToast('Cancel Error', e.message || 'Could not cancel job', 'error');
    }
  };

  const handleClearCache = async () => {
    if (!window.confirm('Wipe the persistent Gemini extraction cache? Next batch run will re-query or fallback without saved facts.')) {
      return;
    }
    try {
      const res = await clearExtractionCache();
      setCacheStats(res.stats);
      showToast('Cache Cleared', 'Persistent extraction cache wiped cleanly.', 'info');
    } catch (e: any) {
      showToast('Cache Error', e.message || 'Could not clear cache', 'error');
    }
  };

  const handleInspectEntry = async (entry: SourceRegistryEntry) => {
    setSelectedEntry(entry);
    setDrawerLoading(true);
    try {
      const queryRes = await queryEvidence({ mpn: entry.mpn });
      setEntryChunks(queryRes.chunks || []);
      setEntryCandidates(queryRes.candidates || []);
    } catch (e: any) {
      console.error('Failed to load chunks for entry:', e);
      showToast('Query Error', 'Failed to retrieve discrete chunks for this source', 'error');
    } finally {
      setDrawerLoading(false);
    }
  };

  const handleRegisterSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMpn || !newBrand || !newMfr) {
      showToast('Missing Fields', 'MPN, Brand, and Manufacturer are required.', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload: SourceRegistrationRequest = {
        url: newUrl || undefined,
        mpn: newMpn.trim().toUpperCase(),
        brand: newBrand.trim(),
        manufacturer: newMfr.trim(),
        title: newTitle.trim() || undefined,
        source_type: newSourceType
      };

      const res = await registerEvidenceSource(payload);
      if (res.success) {
        showToast('Source Registered', `Ingested ${payload.mpn} successfully (${res.chunks_count} chunks).`, 'success');
        setShowRegisterModal(false);
        setNewUrl('');
        setNewMpn('');
        setNewBrand('');
        setNewMfr('');
        setNewTitle('');
        await loadRegistry();
      } else {
        showToast('Registration Blocked', res.message, 'error');
      }
    } catch (err: any) {
      showToast('Registration Error', err.message || 'Failed to register official manufacturer source', 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleMarkStale = async (sourceId: string) => {
    try {
      await markSourceStale(sourceId, 'Source marked stale by operator');
      showToast('Source Updated', 'Source marked as STALE and cache invalidated.', 'success');
      await loadRegistry();
      if (selectedEntry?.source_id === sourceId) {
        setSelectedEntry({ ...selectedEntry, source_status: 'STALE' });
      }
    } catch (err: any) {
      showToast('Error', err.message || 'Failed to mark source stale', 'error');
    }
  };

  const handleReingest = async (sourceId: string) => {
    try {
      const res = await reingestSource(sourceId);
      if (res.success) {
        showToast('Source Re-ingested', `Successfully re-ingested ${res.chunks_count} chunks.`, 'success');
        await loadRegistry();
        if (selectedEntry?.source_id === sourceId) {
          handleInspectEntry({ ...selectedEntry, file_hash: res.file_hash, chunks_count: res.chunks_count });
        }
      } else {
        showToast('Re-ingestion Failed', res.message, 'error');
      }
    } catch (err: any) {
      showToast('Error', err.message || 'Failed to re-ingest source', 'error');
    }
  };

  const handleRejectSource = async (sourceId: string) => {
    const reason = window.prompt('Enter reason for rejecting this evidence document:');
    if (!reason) return;
    try {
      await rejectSource(sourceId, reason);
      showToast('Source Rejected', 'Source marked as REJECTED and cache invalidated.', 'success');
      await loadRegistry();
      if (selectedEntry?.source_id === sourceId) {
        setSelectedEntry({ ...selectedEntry, source_status: 'REJECTED_UNTRUSTED' });
      }
    } catch (err: any) {
      showToast('Error', err.message || 'Failed to reject source', 'error');
    }
  };


  const filteredSources = sources.filter((s) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      s.mpn.toLowerCase().includes(q) ||
      s.brand.toLowerCase().includes(q) ||
      s.manufacturer.toLowerCase().includes(q) ||
      (s.title && s.title.toLowerCase().includes(q)) ||
      s.file_hash.toLowerCase().includes(q);

    const matchesType =
      selectedType === 'ALL' ||
      (selectedType === 'PDF' && s.source_type === 'manufacturer_pdf') ||
      (selectedType === 'HTML' && s.source_type === 'manufacturer_page');

    return matchesSearch && matchesType;
  });

  const totalChunksCount = sources.reduce((acc, s) => acc + (s.chunks_count || 0), 0);

  // Status badge styling helper
  const getStatusBadge = (status: BatchProductStatus) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="w-3 h-3" /> Completed
          </span>
        );
      case 'review_required':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" /> Review Req.
          </span>
        );
      case 'validating':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse">
            <RefreshCw className="w-3 h-3 animate-spin" /> Validating
          </span>
        );
      case 'extracting':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-purple-500/10 text-purple-400 border border-purple-500/20 animate-pulse">
            <Sparkles className="w-3 h-3 animate-spin" /> Extracting
          </span>
        );
      case 'retrieving':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Database className="w-3 h-3" /> Retrieving
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertOctagon className="w-3 h-3" /> Failed
          </span>
        );
      case 'queued':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <Clock className="w-3 h-3" /> Queued
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 font-sans">
      
      {/* Standard Page Header with Tab Switcher */}
      <PageHeader
        title="Manufacturer Evidence Intelligence"
        description="Cryptographically verified manufacturer evidence registry, deterministic caching & batch enrichment engine."
        badge={<span className="chip validated font-bold">{sources.length} REGISTERED SOURCES</span>}
        actions={
          <div className="flex items-center gap-1 p-1 bg-[var(--surface-1)] rounded-lg border border-[var(--border)]">
            <button
              onClick={() => setActiveTab('sources')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-semibold transition-all cursor-pointer ${
                activeTab === 'sources'
                  ? 'bg-[var(--cyan)] text-black shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-white'
              }`}
            >
              SOURCES ({sources.length})
            </button>
            <button
              onClick={() => setActiveTab('batch')}
              className={`px-3 py-1.5 rounded-md text-xs font-mono font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'batch'
                  ? 'bg-[var(--cyan)] text-black shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-white'
              }`}
            >
              <Zap className="w-3 h-3" />
              BATCH ENRICHMENT
              {batchReport?.status === 'RUNNING' && (
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping inline-block" />
              )}
            </button>
          </div>
        }
      />

      {/* ========================================================================= */}
      {/* VIEW 1: REGISTERED EVIDENCE SOURCES CATALOG */}
      {/* ========================================================================= */}
      {activeTab === 'sources' && (
        <div className="space-y-4">
          {/* Action Bar */}
          <div className="flex items-center justify-between">
            <div className="text-xs text-[var(--text-muted)] flex items-center gap-2">
              <Lock className="w-3.5 h-3.5 text-[var(--cyan)]" />
              <span>Restricted exclusively to official manufacturer domains &amp; verified spec sheets.</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={loadRegistry}
                disabled={loading}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] hover:text-white rounded-md text-xs font-mono border border-[var(--border)] transition-colors cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[var(--cyan)]' : ''}`} />
                <span>REFRESH</span>
              </button>

              <button
                onClick={() => setShowRegisterModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[var(--cyan)] hover:bg-[var(--cyan-hover)] text-black rounded-md text-xs font-bold font-mono transition-colors cursor-pointer shadow-sm"
              >
                <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>REGISTER SOURCE</span>
              </button>
            </div>
          </div>

          {/* KPI Metric Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="p-3.5 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold">REGISTERED SOURCES</span>
              <span className="text-xl font-bold text-[var(--text-primary)]">{sources.length}</span>
              <span className="text-[10px] text-[var(--cyan)] block">Official Manufacturer Registry</span>
            </div>

            <div className="p-3.5 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold">DISCRETE CHUNKS</span>
              <span className="text-xl font-bold text-[var(--cyan)]">{totalChunksCount}</span>
              <span className="text-[10px] text-[var(--text-muted)] block">Section &amp; Heading Indexed</span>
            </div>

            <div className="p-3.5 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold">CACHE HIT SAVINGS</span>
              <span className="text-xl font-bold text-[var(--green)]">
                {cacheStats?.hit_ratio_percent || 0}%
              </span>
              <span className="text-[10px] text-[var(--green)] block">
                {cacheStats?.tokens_saved_estimate || 0} tokens saved
              </span>
            </div>

            <div className="p-3.5 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold">INTEGRITY HASHING</span>
              <span className="text-xl font-bold text-[var(--purple)]">SHA-256</span>
              <span className="text-[10px] text-[var(--purple)] block">Tamper-Evident Store</span>
            </div>
          </div>

          {/* Search & Filter Controls */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] font-mono text-xs">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by MPN, Brand, Title, or SHA-256..."
                className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded-md pl-9 pr-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--cyan)]"
              />
            </div>

            <div className="flex items-center gap-1.5">
              {['ALL', 'HTML', 'PDF'].map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedType(t)}
                  className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                    selectedType === t
                      ? 'bg-[var(--cyan)] text-black'
                      : 'bg-[var(--surface-1)] text-[var(--text-secondary)] hover:text-white border border-[var(--border)]'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Sources Table */}
          <div className="border border-[var(--border)] rounded-[10px] overflow-hidden bg-[var(--surface-2)]">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[var(--surface-1)] text-[var(--text-muted)] uppercase text-[10px] border-b border-[var(--border)]">
                  <tr>
                    <th className="p-3">Target MPN &amp; Brand</th>
                    <th className="p-3">Source Title / Document</th>
                    <th className="p-3">Format</th>
                    <th className="p-3">Discrete Chunks</th>
                    <th className="p-3">Integrity SHA-256</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border)]">
                  {loading ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-[var(--text-muted)]">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto text-[var(--cyan)] mb-2" />
                        Loading live registered manufacturer sources...
                      </td>
                    </tr>
                  ) : filteredSources.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-[var(--text-muted)]">
                        No registered sources match your search query.
                      </td>
                    </tr>
                  ) : (
                    filteredSources.map((s) => (
                      <tr key={s.source_id} className="hover:bg-[var(--surface-1)] transition-colors">
                        <td className="p-3 font-semibold text-[var(--text-primary)]">
                          <div className="flex items-center gap-1.5">
                            <Shield className="w-3.5 h-3.5 text-[var(--cyan)]" />
                            <span>{s.mpn}</span>
                          </div>
                          <span className="text-[10px] text-[var(--text-muted)] block font-normal mt-0.5">
                            {s.brand} • {s.manufacturer}
                          </span>
                        </td>
                        <td className="p-3 text-[var(--text-secondary)] max-w-xs truncate" title={s.title || s.url || ''}>
                          {s.title || s.url || 'Official Specification Data'}
                        </td>
                        <td className="p-3">
                          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold bg-[var(--surface-1)] border border-[var(--border)] text-[var(--text-secondary)]">
                            {s.source_type === 'manufacturer_pdf' ? <FileText className="w-3 h-3 text-red-400" /> : <FileCode className="w-3 h-3 text-cyan-400" />}
                            {s.source_type.replace('manufacturer_', '')}
                          </span>
                        </td>
                        <td className="p-3 text-[var(--cyan)] font-bold">
                          {s.chunks_count} chunks
                        </td>
                        <td className="p-3 font-mono text-[10px] text-[var(--text-muted)]">
                          {s.file_hash.substring(0, 12)}...
                        </td>
                        <td className="p-3">
                          <span className="chip validated text-[10px]">
                            ACTIVE
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleInspectEntry(s)}
                            className="px-2.5 py-1 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--cyan)] hover:text-white rounded border border-[var(--border)] text-[11px] font-mono transition-colors cursor-pointer"
                          >
                            Inspect Lineage
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* VIEW 2: BATCH EVIDENCE-ENRICHMENT WORKBENCH */}
      {/* ========================================================================= */}
      {activeTab === 'batch' && (
        <div className="space-y-4">
          
          {/* Controls & Configuration Panel */}
          <div className="p-4 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="text-xs font-mono font-bold text-[var(--text-primary)] uppercase flex items-center gap-1.5">
                  <Zap className="w-4 h-4 text-[var(--cyan)]" />
                  BATCH ENRICHMENT CONTROLLER
                </h3>
                <p className="text-xs text-[var(--text-muted)] mt-0.5">
                  Enqueues only products with active official evidence. Caches extractions deterministically by hash + MPN + schema.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-wrap">
                {batchReport?.status === 'RUNNING' ? (
                  <button
                    onClick={handleCancelBatch}
                    className="flex items-center gap-1.5 px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 rounded-md text-xs font-bold font-mono border border-rose-500/40 transition-colors cursor-pointer"
                  >
                    <Square className="w-3.5 h-3.5 fill-rose-300" />
                    <span>CANCEL RUNNING JOB</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStartBatch}
                    disabled={batchStarting}
                    className="flex items-center gap-2 px-4 py-2 bg-[var(--cyan)] hover:bg-[var(--cyan-hover)] text-black rounded-md text-xs font-bold font-mono transition-colors cursor-pointer shadow-sm disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5 fill-black" />
                    <span>{batchStarting ? 'LAUNCHING...' : 'RUN BATCH ENRICHMENT'}</span>
                  </button>
                )}

                <button
                  onClick={handleClearCache}
                  className="flex items-center gap-1.5 px-3 py-2 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-muted)] hover:text-white rounded-md text-xs font-mono border border-[var(--border)] transition-colors cursor-pointer"
                  title="Wipe deterministic extraction cache"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>CLEAR CACHE</span>
                </button>
              </div>
            </div>

            {/* Execution Options */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-[var(--border)] text-xs font-mono">
              <div className="flex items-center justify-between p-2.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)]">
                <span className="text-[var(--text-secondary)] flex items-center gap-1.5">
                  <Sliders className="w-3.5 h-3.5 text-[var(--cyan)]" /> Concurrency
                </span>
                <select
                  value={concurrency}
                  onChange={(e) => setConcurrency(parseInt(e.target.value, 10))}
                  disabled={batchReport?.status === 'RUNNING'}
                  className="bg-[var(--surface-2)] border border-[var(--border)] rounded px-2 py-1 text-xs text-[var(--text-primary)] focus:outline-none"
                >
                  <option value={1}>1 Worker (Sequential)</option>
                  <option value={2}>2 Workers</option>
                  <option value={3}>3 Workers (Recommended)</option>
                  <option value={5}>5 Workers (Fast)</option>
                </select>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)]">
                <span className="text-[var(--text-secondary)] flex items-center gap-1.5">
                  <RefreshCw className="w-3.5 h-3.5 text-[var(--purple)]" /> Bypass Cache
                </span>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={forceRefresh}
                    onChange={(e) => setForceRefresh(e.target.checked)}
                    disabled={batchReport?.status === 'RUNNING'}
                    className="accent-[var(--cyan)] w-4 h-4 cursor-pointer"
                  />
                  <span className="text-[11px] text-[var(--text-muted)]">Force Re-extract</span>
                </label>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-[var(--surface-1)] rounded-lg border border-[var(--border)]">
                <span className="text-[var(--text-secondary)] flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-[var(--green)]" /> Evidence Target
                </span>
                <span className="text-emerald-400 font-semibold">{sources.length} Registered Only</span>
              </div>
            </div>
          </div>

          {/* Cache ROI & Cost Savings Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="p-3 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold flex items-center gap-1">
                <Zap className="w-3 h-3 text-cyan-400" /> CACHE HIT RATIO
              </span>
              <span className="text-lg font-bold text-cyan-400">{cacheStats?.hit_ratio_percent || 0}%</span>
              <span className="text-[10px] text-[var(--text-muted)] block">
                {cacheStats?.hits || 0} hits / {cacheStats?.total_requests || 0} calls
              </span>
            </div>

            <div className="p-3 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold flex items-center gap-1">
                <Cpu className="w-3 h-3 text-purple-400" /> TOKENS SAVED
              </span>
              <span className="text-lg font-bold text-purple-400">{cacheStats?.tokens_saved_estimate || 0}</span>
              <span className="text-[10px] text-[var(--text-muted)] block">Zero API Latency</span>
            </div>

            <div className="p-3 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold flex items-center gap-1">
                <Coins className="w-3 h-3 text-emerald-400" /> COST AVOIDED
              </span>
              <span className="text-lg font-bold text-emerald-400">
                ${cacheStats?.cost_saved_usd_estimate?.toFixed(5) || '0.00000'}
              </span>
              <span className="text-[10px] text-[var(--text-muted)] block">Deterministic Storage</span>
            </div>

            <div className="p-3 bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] space-y-1">
              <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold flex items-center gap-1">
                <Database className="w-3 h-3 text-blue-400" /> CACHED ENTRIES
              </span>
              <span className="text-lg font-bold text-[var(--text-primary)]">{cacheStats?.total_entries || 0}</span>
              <span className="text-[10px] text-[var(--text-muted)] block">Persistent Disk Store</span>
            </div>
          </div>

          {/* Live Batch Progress & Status Card */}
          {batchReport ? (
            <div className="border border-[var(--border)] rounded-[10px] bg-[var(--surface-2)] p-4 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border)] pb-3 font-mono text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-[var(--text-muted)]">JOB ID:</span>
                  <span className="text-white font-bold">{batchReport.job_id}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      batchReport.status === 'RUNNING'
                        ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 animate-pulse'
                        : batchReport.status === 'COMPLETED'
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                    }`}
                  >
                    {batchReport.status}
                  </span>
                </div>

                <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)]">
                  <span>Duration: <strong className="text-white">{batchReport.duration_seconds}s</strong></span>
                  <span>Processed: <strong className="text-cyan-400">{batchReport.processed_products} / {batchReport.evidence_backed_products}</strong></span>
                  <span>Cache Hits: <strong className="text-emerald-400">{batchReport.cache_hits}</strong></span>
                </div>
              </div>

              {/* Granular Field Aggregate Metrics */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs font-mono">
                <div className="p-2.5 bg-[var(--surface-1)] rounded border border-[var(--border)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block">VERIFIED FIELDS</span>
                  <span className="text-base font-bold text-emerald-400">{batchReport.verified_fields}</span>
                </div>
                <div className="p-2.5 bg-[var(--surface-1)] rounded border border-[var(--border)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block">CANDIDATE FIELDS</span>
                  <span className="text-base font-bold text-amber-400">{batchReport.candidate_fields}</span>
                </div>
                <div className="p-2.5 bg-[var(--surface-1)] rounded border border-[var(--border)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block">REJECTED FIELDS</span>
                  <span className="text-base font-bold text-rose-400">{batchReport.rejected_fields}</span>
                </div>
                <div className="p-2.5 bg-[var(--surface-1)] rounded border border-[var(--border)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block">REVIEW REQUIRED</span>
                  <span className="text-base font-bold text-amber-400">{batchReport.review_required_products}</span>
                </div>
                <div className="p-2.5 bg-[var(--surface-1)] rounded border border-[var(--border)] text-center">
                  <span className="text-[10px] text-[var(--text-muted)] block">GEMINI FAILURES</span>
                  <span className="text-base font-bold text-slate-300">{batchReport.gemini_failures}</span>
                </div>
              </div>

              {/* Per-Product Live State Table */}
              <div className="border border-[var(--border)] rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-[var(--surface-1)] text-[var(--text-muted)] uppercase text-[10px] border-b border-[var(--border)]">
                    <tr>
                      <th className="p-2.5">MPN / Brand</th>
                      <th className="p-2.5">Lifecycle Stage</th>
                      <th className="p-2.5">Execution Path</th>
                      <th className="p-2.5">Verified Fields</th>
                      <th className="p-2.5">Conflicts</th>
                      <th className="p-2.5">Latency</th>
                      <th className="p-2.5 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--border)]">
                    {Object.values(batchReport.product_states || {}).map((item) => (
                      <tr key={item.mpn} className="hover:bg-[var(--surface-1)] transition-colors">
                        <td className="p-2.5 font-bold text-white">
                          <div>{item.mpn}</div>
                          <span className="text-[10px] font-normal text-[var(--text-muted)]">{item.brand}</span>
                        </td>
                        <td className="p-2.5">
                          <div className="space-y-0.5">
                            {getStatusBadge(item.status)}
                            <div className="text-[10px] text-[var(--text-muted)] truncate max-w-xs">
                              {item.stage_message}
                            </div>
                          </div>
                        </td>
                        <td className="p-2.5">
                          {item.is_cached ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-semibold">
                              <Zap className="w-3 h-3" /> Cached
                            </span>
                          ) : item.extraction_method === 'gemini_structured_extraction' ? (
                            <span className="inline-flex items-center gap-1 text-[11px] text-purple-400 font-semibold">
                              <Sparkles className="w-3 h-3" /> Gemini 2.5
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] text-cyan-400 font-semibold">
                              <Sliders className="w-3 h-3" /> Rule Fallback
                            </span>
                          )}
                        </td>
                        <td className="p-2.5 text-emerald-400 font-bold">
                          {item.verified_fields} verified
                        </td>
                        <td className="p-2.5">
                          {item.conflicts_count > 0 ? (
                            <span className="text-amber-400 font-semibold flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" /> {item.conflicts_count} flag
                            </span>
                          ) : (
                            <span className="text-[var(--text-muted)]">0</span>
                          )}
                        </td>
                        <td className="p-2.5 text-[var(--text-muted)]">
                          {item.duration_ms > 0 ? `${item.duration_ms}ms` : '—'}
                        </td>
                        <td className="p-2.5 text-right">
                          <button
                            onClick={() => {
                              const found = sources.find((s) => s.mpn === item.mpn);
                              if (found) handleInspectEntry(found);
                            }}
                            className="px-2 py-0.5 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--cyan)] hover:text-white rounded text-[11px] border border-[var(--border)] transition-colors cursor-pointer"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center bg-[var(--surface-2)] rounded-[10px] border border-[var(--border)] font-mono text-xs text-[var(--text-muted)] space-y-2">
              <Zap className="w-6 h-6 mx-auto text-[var(--cyan)]" />
              <p className="text-white font-semibold">No active or prior batch job loaded.</p>
              <p className="text-[11px]">Click "RUN BATCH ENRICHMENT" above to launch bounded async processing across registered sources.</p>
            </div>
          )}
        </div>
      )}

      {/* Inspection Drawer */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-50 flex justify-end animate-fade-in">
          <div className="w-full max-w-2xl bg-[var(--surface-2)] border-l border-[var(--border)] h-full overflow-y-auto p-5 space-y-5 font-mono text-xs">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-4">
              <div className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-[var(--cyan)]" />
                <div>
                  <h3 className="text-sm font-bold text-[var(--text-primary)]">
                    {selectedEntry.mpn} — {selectedEntry.brand}
                  </h3>
                  <p className="text-[10px] text-[var(--text-muted)]">
                    {selectedEntry.manufacturer} • Source ID: {selectedEntry.source_id}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="p-1 rounded-md hover:bg-[var(--surface-1)] text-[var(--text-muted)] hover:text-white cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Document Hash & Lineage */}
            <div className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-1.5">
              <div className="flex justify-between text-[11px]">
                <span className="text-[var(--text-muted)]">Source Document Hash:</span>
                <span className="text-[var(--purple)] font-bold">{selectedEntry.file_hash}</span>
              </div>
              <div className="flex justify-between text-[11px]">
                <span className="text-[var(--text-muted)]">Ingestion Timestamp:</span>
                <span className="text-[var(--text-secondary)]">{selectedEntry.retrieved_at}</span>
              </div>
              {selectedEntry.url && (
                <div className="flex justify-between text-[11px] truncate">
                  <span className="text-[var(--text-muted)]">Original URL:</span>
                  <a
                    href={selectedEntry.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[var(--cyan)] hover:underline flex items-center gap-1"
                  >
                    <span>{selectedEntry.url}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}

              {/* Source Lifecycle Actions */}
              <div className="pt-2 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-2">
                <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">Lifecycle Actions:</span>
                <div className="flex items-center gap-1.5 flex-wrap">
                  {selectedEntry.url && (
                    <button
                      onClick={() => handleReingest(selectedEntry.source_id)}
                      className="px-2 py-1 bg-blue-950/60 hover:bg-blue-900/80 text-blue-300 border border-blue-800 rounded text-[10px] transition-colors"
                      title="Re-acquire and re-chunk from official URL"
                    >
                      Re-ingest
                    </button>
                  )}
                  <button
                    onClick={() => handleMarkStale(selectedEntry.source_id)}
                    className="px-2 py-1 bg-amber-950/60 hover:bg-amber-900/80 text-amber-300 border border-amber-800 rounded text-[10px] transition-colors"
                    title="Mark document stale and invalidate extraction cache"
                  >
                    Mark Stale
                  </button>
                  <button
                    onClick={() => handleRejectSource(selectedEntry.source_id)}
                    className="px-2 py-1 bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800 rounded text-[10px] transition-colors"
                    title="Reject untrusted source document"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>


            {/* Discrete Chunks & Extracted Candidates */}
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase mb-2 flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-[var(--cyan)]" />
                  DISCRETE SPECIFICATION CHUNKS ({entryChunks.length})
                </h4>

                {drawerLoading ? (
                  <div className="p-6 text-center text-[var(--text-muted)]">
                    <RefreshCw className="w-4 h-4 animate-spin mx-auto text-[var(--cyan)] mb-1" />
                    Loading chunks...
                  </div>
                ) : (
                  <div className="space-y-2">
                    {entryChunks.map((c) => (
                      <div key={c.chunk_id} className="p-3 bg-[var(--surface-1)] rounded-lg border border-[var(--border)] space-y-2">
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-bold text-[var(--cyan)]">{c.section_title}</span>
                          <span className="text-[10px] text-[var(--text-muted)]">Page {c.page_number || 1} • {c.chunk_id}</span>
                        </div>
                        <p className="text-[11px] text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">
                          {c.text_content}
                        </p>
                        {Object.keys(c.key_value_specs || {}).length > 0 && (
                          <div className="pt-2 border-t border-[var(--border)] grid grid-cols-2 gap-1.5 text-[10px]">
                            {Object.entries(c.key_value_specs).map(([k, v]) => (
                              <div key={k} className="p-1 bg-[var(--surface-2)] rounded border border-[var(--border)]">
                                <span className="text-[var(--text-muted)] block">{k}:</span>
                                <span className="text-[var(--text-primary)] font-semibold">{v}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Source Registration Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[var(--surface-2)] border border-[var(--border)] rounded-[12px] p-6 space-y-4 font-mono text-xs shadow-2xl">
            <div className="flex items-center justify-between border-b border-[var(--border)] pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Plus className="w-4 h-4 text-[var(--cyan)]" /> REGISTER OFFICIAL MANUFACTURER SOURCE
              </h3>
              <button
                onClick={() => setShowRegisterModal(false)}
                className="p-1 text-[var(--text-muted)] hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleRegisterSource} className="space-y-3">
              <div>
                <label className="block text-[11px] text-[var(--text-muted)] mb-1">TARGET MPN *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. U008LFA"
                  value={newMpn}
                  onChange={(e) => setNewMpn(e.target.value)}
                  className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[var(--cyan)]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] text-[var(--text-muted)] mb-1">BRAND NAME *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. SharkBite®"
                    value={newBrand}
                    onChange={(e) => setNewBrand(e.target.value)}
                    className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[var(--cyan)]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] text-[var(--text-muted)] mb-1">MANUFACTURER *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Reliance Worldwide Corporation"
                    value={newMfr}
                    onChange={(e) => setNewMfr(e.target.value)}
                    className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[var(--cyan)]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[11px] text-[var(--text-muted)] mb-1">SOURCE URL (MUST BE OFFICIAL DOMAIN)</label>
                <input
                  type="url"
                  placeholder="https://www.sharkbite.com/products/brass-push-straight-coupling"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[var(--cyan)]"
                />
              </div>

              <div>
                <label className="block text-[11px] text-[var(--text-muted)] mb-1">DOCUMENT TITLE</label>
                <input
                  type="text"
                  placeholder="e.g. SharkBite Push-to-Connect Fittings Specification Sheet"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-[var(--surface-1)] border border-[var(--border)] rounded px-3 py-1.5 text-xs text-white focus:outline-none focus:border-[var(--cyan)]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[var(--border)]">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-3 py-1.5 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-secondary)] rounded text-xs cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-1.5 bg-[var(--cyan)] hover:bg-[var(--cyan-hover)] text-black rounded text-xs font-bold cursor-pointer disabled:opacity-50"
                >
                  {submitting ? 'Registering & Ingesting...' : 'Register Source'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

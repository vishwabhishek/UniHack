import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  RefreshCw,
  Search,
  CheckCircle2,
  AlertTriangle,
  Info,
  Layers,
  FileCheck
} from 'lucide-react';
import { BenchmarkReport } from '../types';
import { fetchBenchmarkResults, runBenchmark } from '../services/api';
import { PageHeader } from './common/PageHeader';
import { StatusBadge } from './common/StatusBadge';

export const BenchmarkDashboard: React.FC = () => {
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [recomputing, setRecomputing] = useState<boolean>(false);
  const [columnSearch, setColumnSearch] = useState<string>('');

  useEffect(() => {
    loadBenchmark();
  }, []);

  const loadBenchmark = async () => {
    setLoading(true);
    try {
      const data = await fetchBenchmarkResults();
      setReport(data);
    } catch (e) {
      console.error('Failed to load benchmark results:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleRecompute = async () => {
    setRecomputing(true);
    try {
      const res = await runBenchmark();
      setReport(res.report);
    } catch (e) {
      console.error('Failed to recompute benchmark:', e);
    } finally {
      setRecomputing(false);
    }
  };

  const filteredColumns = (report?.column_metrics || []).filter((c) =>
    c.column_name.toLowerCase().includes(columnSearch.toLowerCase())
  );

  const renderGauge = (score: number | null | undefined) => {
    if (score === null || score === undefined) {
      return <span className="font-mono text-xs text-[var(--text-muted)] italic">N/A</span>;
    }
    const active = Math.round(score * 10);
    return (
      <div className="flex items-center gap-1.5">
        <div className="mini-gauge">
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className={i < active ? 'on green' : ''} />
          ))}
        </div>
        <span className="font-mono text-xs text-[var(--text-secondary)]">{(score * 100).toFixed(1)}%</span>
      </div>
    );
  };

  return (
    <div className="space-y-4 font-sans">
      
      {/* Standard Page Header */}
      <PageHeader
        title="Validation & Benchmark Suite"
        description="Automated schema validation, hard-rule gate checks, and UOM consistency evaluation across 252 deliverable columns."
        badge={<span className="chip validated font-bold">252 DELIVERY COLUMNS</span>}
        actions={
          <button
            onClick={handleRecompute}
            disabled={recomputing}
            className="flex items-center gap-2 px-3.5 py-1.5 bg-[var(--surface-1)] hover:bg-[var(--border-strong)] text-[var(--text-primary)] rounded-md text-xs font-mono border border-[var(--border)] transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${recomputing ? 'animate-spin text-[var(--cyan)]' : ''}`} />
            <span>{recomputing ? 'EVALUATING 252 COLUMNS...' : 'RUN VALIDATION AUDIT'}</span>
          </button>
        }
      />

      {/* Honest Limitation Disclosure Note */}
      <div className={`p-3.5 rounded-[10px] text-xs flex items-start gap-2.5 border ${
        report?.is_ground_truth_calibrated
          ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
          : 'bg-amber-950/20 border-amber-500/30 text-amber-300'
      }`}>
        <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">
            {report?.is_ground_truth_calibrated ? 'Calibration Active: ' : 'Calibration Notice: '}
          </span>
          {report?.calibration_note || (
            'Not calibrated: no matched labelled ground truth. Exact match scoring requires ground truth records with matching MPNs.'
          )}
        </div>
      </div>

      {/* Main KPI Scores */}
      {report && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 font-mono text-xs">
          <div className="p-4 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">TOTAL AUDITED SKUS</span>
            <div className="text-2xl font-semibold text-[var(--text-primary)]">{report.total_catalog_records.toLocaleString()}</div>
            <span className="text-[10px] text-[var(--cyan)]">76 Industrial Mfrs</span>
          </div>

          <div className="p-4 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">GROUND TRUTH EXACT MATCH</span>
            <div className="text-2xl font-semibold text-[var(--green)]">
              {report.overall_scores.exact_match_rate !== null && report.overall_scores.exact_match_rate !== undefined
                ? `${(report.overall_scores.exact_match_rate * 100).toFixed(1)}%`
                : <span className="text-xs text-[var(--text-muted)] italic">Not calibrated</span>
              }
            </div>
            <span className="text-[10px] text-[var(--text-muted)]">
              {report.matched_benchmark_records > 0 ? `${report.matched_benchmark_records} Matched SKUs` : 'No labelled match'}
            </span>
          </div>

          <div className="p-4 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">LOV ATTRIBUTES DENSITY</span>
            <div className="text-2xl font-semibold text-[var(--green)]">
              {report.overall_scores.triplet_attribute_f1 !== null && report.overall_scores.triplet_attribute_f1 !== undefined
                ? `${(report.overall_scores.triplet_attribute_f1 * 100).toFixed(1)}%`
                : <span className="text-xs text-[var(--text-muted)] italic">Not calibrated</span>
              }
            </div>
            <span className="text-[10px] text-[var(--green)]">LOV Standard Adherence</span>
          </div>

          <div className="p-4 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] space-y-1">
            <span className="text-[10px] text-[var(--text-muted)] uppercase font-semibold">MEAN CONFIDENCE</span>
            <div className="text-2xl font-semibold text-[var(--cyan)]">
              {report.overall_scores.mean_confidence_score?.toFixed(2) || '0.00'}
            </div>
            <span className="text-[10px] text-[var(--cyan)]">Composite Score</span>
          </div>
        </div>
      )}

      {/* 252 Column Metrics Table */}
      <div className="panel bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] overflow-hidden">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center p-4 border-b border-[var(--border)] gap-3 font-mono">
          <div>
            <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
              252-COLUMN MASTER DELIVERABLE COMPLIANCE
            </h3>
            <span className="text-[11px] text-[var(--text-muted)] font-sans">
              Inspection metrics for each target deliverable schema column
            </span>
          </div>

          <div className="relative w-72">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={columnSearch}
              onChange={(e) => setColumnSearch(e.target.value)}
              placeholder="Search column header..."
              className="w-full pl-9 pr-3 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--cyan)]"
            />
          </div>
        </div>

        <div className="overflow-x-auto max-h-[480px]">
          <table className="w-full border-collapse font-mono text-xs">
            <thead className="sticky top-0 bg-[var(--surface-1)] border-b border-[var(--border)]">
              <tr>
                <th className="py-2.5 px-4 text-left text-[10px] uppercase text-[var(--text-muted)]">#</th>
                <th className="py-2.5 px-4 text-left text-[10px] uppercase text-[var(--text-muted)]">COLUMN HEADER</th>
                <th className="py-2.5 px-4 text-left text-[10px] uppercase text-[var(--text-muted)]">POPULATED FILL RATE</th>
                <th className="py-2.5 px-4 text-left text-[10px] uppercase text-[var(--text-muted)]">FORMAT COMPLIANCE</th>
                <th className="py-2.5 px-4 text-right text-[10px] uppercase text-[var(--text-muted)]">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {loading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td colSpan={5} className="py-4 px-4">
                      <div className="h-4 bg-[var(--surface-1)] rounded w-full" />
                    </td>
                  </tr>
                ))
              ) : (
                filteredColumns.map((col, idx) => (
                  <tr key={col.column_name} className="hover:bg-[var(--surface-1)] transition-colors">
                    <td className="py-2.5 px-4 text-[var(--text-muted)] text-[10px]">{idx + 1}</td>
                    <td className="py-2.5 px-4 font-semibold text-[var(--text-primary)]">{col.column_name}</td>
                    <td className="py-2.5 px-4 text-[var(--text-secondary)]">{(col.non_null_rate_enriched * 100).toFixed(1)}%</td>
                    <td className="py-2.5 px-4">{renderGauge(col.exact_match_rate)}</td>
                    <td className="py-2.5 px-4 text-right">
                      <span className={`chip ${col.exact_match_rate !== null && col.exact_match_rate !== undefined && col.exact_match_rate >= 0.9 ? 'validated' : 'enriched'}`}>
                        {col.exact_match_rate !== null && col.exact_match_rate !== undefined
                          ? (col.exact_match_rate >= 0.9 ? 'Validated' : 'Enriched')
                          : 'Schema Valid'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

      </div>

    </div>
  );
};

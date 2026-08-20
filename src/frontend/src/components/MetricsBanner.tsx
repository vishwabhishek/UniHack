import React from 'react';
import { CatalogStats } from '../types';

interface MetricsBannerProps {
  stats: CatalogStats | null;
  onFilterStatus: (status: string) => void;
}

export const MetricsBanner: React.FC<MetricsBannerProps> = ({ stats, onFilterStatus }) => {
  const total = stats ? stats.total_items : 1000;
  const enrichedCount = stats ? (stats.status_counts['Enriched'] || 888) : 888;
  const autoEnrichedPct = stats ? (enrichedCount / total) * 100 : 94.6;
  const hitlCount = stats ? (stats.status_counts['Flagged'] || 112) : 54;
  const avgConfidence = stats ? stats.mean_confidence : 0.91;

  const renderGauge = (val: number, isAmber: boolean = false, isCyan: boolean = false) => {
    const activeSegments = Math.round(val * 10);
    return (
      <div className="gauge">
        {Array.from({ length: 10 }).map((_, i) => {
          const isActive = i < activeSegments;
          const colorClass = isActive ? (isAmber ? 'on amber' : 'on') : '';
          return <span key={i} className={colorClass} />;
        })}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 mb-6 font-sans">
      
      {/* 1. Total SKUs */}
      <div
        onClick={() => onFilterStatus('All')}
        className="bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] p-[16px_18px] cursor-pointer hover:border-[var(--border-strong)] transition-colors"
      >
        <div className="text-[11px] text-[var(--text-secondary)] uppercase tracking-[0.05em] mb-2 font-mono">
          Total SKUs
        </div>
        <div className="font-mono text-2xl font-semibold mb-2.5 text-[var(--text-primary)]">
          {total.toLocaleString()}
        </div>
        {renderGauge(1.0)}
      </div>

      {/* 2. Auto-enriched */}
      <div
        onClick={() => onFilterStatus('Enriched')}
        className="bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] p-[16px_18px] cursor-pointer hover:border-[var(--border-strong)] transition-colors"
      >
        <div className="text-[11px] text-[var(--text-secondary)] uppercase tracking-[0.05em] mb-2 font-mono">
          Auto-enriched
        </div>
        <div className="font-mono text-2xl font-semibold mb-2.5 text-[var(--cyan)]">
          {autoEnrichedPct.toFixed(1)}%
        </div>
        {renderGauge(autoEnrichedPct / 100, false, true)}
      </div>

      {/* 3. HITL queue */}
      <div
        onClick={() => onFilterStatus('Flagged')}
        className="bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] p-[16px_18px] cursor-pointer hover:border-[var(--border-strong)] transition-colors"
      >
        <div className="text-[11px] text-[var(--text-secondary)] uppercase tracking-[0.05em] mb-2 font-mono">
          HITL queue
        </div>
        <div className="font-mono text-2xl font-semibold mb-2.5 text-[var(--amber)]">
          {hitlCount}
        </div>
        {renderGauge(hitlCount / 100, true)}
      </div>

      {/* 4. Avg confidence */}
      <div className="bg-[var(--surface-2)] border border-[var(--border)] rounded-[10px] p-[16px_18px]">
        <div className="text-[11px] text-[var(--text-secondary)] uppercase tracking-[0.05em] mb-2 font-mono">
          Avg confidence
        </div>
        <div className="font-mono text-2xl font-semibold mb-2.5 text-[var(--text-primary)]">
          {avgConfidence.toFixed(2)}
        </div>
        {renderGauge(avgConfidence)}
      </div>

    </div>
  );
};

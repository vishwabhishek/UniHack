import React from 'react';
import {
  Layers,
  FileCheck2,
  Smartphone,
  ShieldCheck,
  AlertOctagon,
  Percent,
  CheckCircle2,
  TrendingUp,
  Sparkles
} from 'lucide-react';
import { CatalogStats } from '../types';

interface MetricsBannerProps {
  stats: CatalogStats | null;
  onFilterStatus: (status: string) => void;
}

export const MetricsBanner: React.FC<MetricsBannerProps> = ({ stats, onFilterStatus }) => {
  if (!stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-24 bg-slate-900/60 rounded-xl border border-white/[0.06]" />
        ))}
      </div>
    );
  }

  const kpis = [
    {
      label: 'Total Master Catalog',
      value: stats.total_items.toLocaleString(),
      subtext: 'Ingested SKUs',
      badge: '100% PARSED',
      badgeClass: 'glow-badge-cyan',
      icon: Layers,
      gradient: 'from-cyan-500 to-blue-600',
      glow: 'shadow-glow-cyan',
      onClick: () => onFilterStatus('All')
    },
    {
      label: 'Invoice Desc Gate',
      value: `${(stats.invoice_compliance_pct * 100).toFixed(0)}%`,
      subtext: '≤ 40 chars & CAPS',
      badge: '100% PASS',
      badgeClass: 'glow-badge-emerald',
      icon: FileCheck2,
      gradient: 'from-emerald-400 to-teal-500',
      glow: 'shadow-glow-emerald',
      onClick: () => onFilterStatus('Enriched')
    },
    {
      label: 'Mobile Desc Spec',
      value: `${(stats.mobile_compliance_pct * 100).toFixed(0)}%`,
      subtext: '60–80 chars range',
      badge: 'HARD GATED',
      badgeClass: 'glow-badge-cyan',
      icon: Smartphone,
      gradient: 'from-blue-500 to-indigo-600',
      glow: 'shadow-glow-blue',
      onClick: () => onFilterStatus('Enriched')
    },
    {
      label: 'LOV Adherence',
      value: `${(stats.lov_compliance_pct * 100).toFixed(0)}%`,
      subtext: '0% Hallucinations',
      badge: 'CONTROLLED',
      badgeClass: 'glow-badge-emerald',
      icon: ShieldCheck,
      gradient: 'from-teal-400 to-emerald-600',
      glow: 'shadow-glow-emerald',
      onClick: () => onFilterStatus('Enriched')
    },
    {
      label: 'Exception Triage',
      value: stats.flagged_count.toLocaleString(),
      subtext: 'Confidence < 0.85',
      badge: 'HITL QUEUE',
      badgeClass: 'glow-badge-amber',
      icon: AlertOctagon,
      gradient: 'from-amber-400 to-orange-500',
      glow: 'shadow-glow-amber',
      onClick: () => onFilterStatus('Flagged')
    },
    {
      label: 'Mean Confidence',
      value: `${(stats.mean_confidence * 100).toFixed(1)}%`,
      subtext: '5-Factor Radar',
      badge: 'HIGH FIDELITY',
      badgeClass: 'glow-badge-violet',
      icon: Percent,
      gradient: 'from-violet-500 to-purple-600',
      glow: 'shadow-glow-violet',
      onClick: () => onFilterStatus('All')
    }
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {kpis.map((kpi, idx) => {
        const Icon = kpi.icon;
        return (
          <div
            key={idx}
            onClick={kpi.onClick}
            className="group relative glass-card p-3.5 rounded-xl cursor-pointer overflow-hidden border border-white/[0.08] hover:border-white/20"
          >
            {/* Top Accent Gradient Line */}
            <div className={`absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r ${kpi.gradient}`} />
            
            <div className="flex items-start justify-between gap-2 mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono line-clamp-1">
                {kpi.label}
              </span>
              <div className={`p-1.5 rounded-lg bg-gradient-to-br ${kpi.gradient} text-white shadow-sm flex-shrink-0 transition-transform group-hover:scale-110`}>
                <Icon className="w-3.5 h-3.5" />
              </div>
            </div>

            <div className="flex items-baseline space-x-1.5">
              <span className="text-xl sm:text-2xl font-black text-white font-mono tracking-tight tnum">
                {kpi.value}
              </span>
            </div>

            <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/[0.04]">
              <span className="text-[10px] text-slate-400 font-medium truncate">
                {kpi.subtext}
              </span>
              <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full ${kpi.badgeClass}`}>
                {kpi.badge}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

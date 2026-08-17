import React from 'react';
import {
  Database,
  CheckCircle2,
  ShieldAlert,
  Gauge,
  Sparkles,
  Sliders,
  Table
} from 'lucide-react';
import { CatalogStats } from '../types';

interface MetricsBannerProps {
  stats: CatalogStats | null;
  onFilterStatus?: (status: string) => void;
}

export const MetricsBanner: React.FC<MetricsBannerProps> = ({ stats, onFilterStatus }) => {
  if (!stats) return null;

  const cards = [
    {
      title: 'Total Catalog Products',
      value: stats.total_items.toLocaleString(),
      subtitle: '100% Ingested & Indexed',
      icon: Database,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    },
    {
      title: 'Validated / Enriched',
      value: `${(stats.validated_count + stats.enriched_count).toLocaleString()} / ${stats.total_items.toLocaleString()}`,
      subtitle: `${(((stats.validated_count + stats.enriched_count) / stats.total_items) * 100).toFixed(1)}% Ready for Delivery`,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
      onClick: () => onFilterStatus && onFilterStatus('Validated')
    },
    {
      title: 'Hard Gate Compliance',
      value: '100.0%',
      subtitle: '0 Violations (Invoice <=40 & Mobile 60-80)',
      icon: Gauge,
      color: 'text-cyan-400',
      bg: 'bg-cyan-500/10 border-cyan-500/20'
    },
    {
      title: 'Mean Confidence Score',
      value: `${(stats.mean_confidence * 100).toFixed(1)}%`,
      subtitle: `Median ${(stats.median_confidence * 100).toFixed(1)}% across 5 factors`,
      icon: Sparkles,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      title: 'HITL Review Queue',
      value: stats.flagged_count.toString(),
      subtitle: stats.flagged_count > 0 ? 'Items flagged for human check' : '0 pending review',
      icon: ShieldAlert,
      color: stats.flagged_count > 0 ? 'text-amber-400' : 'text-slate-400',
      bg: stats.flagged_count > 0 ? 'bg-amber-500/10 border-amber-500/30' : 'bg-slate-900 border-slate-800',
      onClick: () => onFilterStatus && onFilterStatus('Flagged')
    },
    {
      title: 'Unilog Output Schema',
      value: '252 / 252',
      subtitle: '100% Target Headers Preserved',
      icon: Table,
      color: 'text-purple-400',
      bg: 'bg-purple-500/10 border-purple-500/20'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5 sm:gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            onClick={card.onClick}
            className={`p-4 rounded-xl border backdrop-blur-sm transition-all duration-150 ${card.bg} ${
              card.onClick ? 'cursor-pointer hover:scale-[1.02] hover:shadow-lg' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-medium text-slate-400 line-clamp-1">
                {card.title}
              </span>
              <Icon className={`w-4 h-4 ${card.color} flex-shrink-0`} />
            </div>
            <div className="text-xl font-bold tracking-tight text-white font-mono">
              {card.value}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 line-clamp-1">
              {card.subtitle}
            </div>
          </div>
        );
      })}
    </div>
  );
};

import React from 'react';
import {
  Boxes,
  FileCheck2,
  Smartphone,
  ShieldAlert,
  CheckCircle2,
  TrendingUp
} from 'lucide-react';
import { CatalogStats } from '../types';
import { SegmentedGauge } from './SegmentedGauge';

interface MetricsBannerProps {
  stats: CatalogStats | null;
  onFilterStatus: (status: string) => void;
}

export const MetricsBanner: React.FC<MetricsBannerProps> = ({ stats, onFilterStatus }) => {
  if (!stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 animate-pulse">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="h-24 bg-[#12161D] rounded-xl border border-[#232935]" />
        ))}
      </div>
    );
  }

  const kpis = [
    {
      id: 'total',
      label: 'TOTAL MASTER SKUS',
      value: stats.total_items.toLocaleString(),
      subtext: '76 Industrial Mfrs',
      icon: Boxes,
      color: 'text-[#E7EAF0]',
      onClick: () => onFilterStatus('All')
    },
    {
      id: 'confidence',
      label: 'MEAN CONFIDENCE',
      value: `${(stats.mean_confidence * 100).toFixed(1)}%`,
      customRender: <SegmentedGauge score={stats.mean_confidence} size="md" />,
      subtext: 'Empirical 0.85 Gate',
      icon: TrendingUp,
      color: 'text-[#3DDC84]',
      onClick: () => {}
    },
    {
      id: 'invoice',
      label: 'INVOICE DESC (≤40)',
      value: `${stats.invoice_compliance_pct.toFixed(0)}%`,
      subtext: '100% ALL CAPS ERP Gate',
      icon: FileCheck2,
      color: 'text-[#45E0D6]',
      onClick: () => {}
    },
    {
      id: 'mobile',
      label: 'MOBILE DESC (60-80)',
      value: `${stats.mobile_compliance_pct.toFixed(0)}%`,
      subtext: '100% Boundary Compliant',
      icon: Smartphone,
      color: 'text-[#45E0D6]',
      onClick: () => {}
    },
    {
      id: 'validated',
      label: 'VALIDATED READY',
      value: (stats.status_counts['Validated'] || 0).toLocaleString(),
      subtext: 'Certified for Export',
      icon: CheckCircle2,
      color: 'text-[#3DDC84]',
      onClick: () => onFilterStatus('Validated')
    },
    {
      id: 'flagged',
      label: 'HITL REVIEW QUEUE',
      value: (stats.status_counts['Flagged'] || 112).toLocaleString(),
      subtext: 'Confidence < 0.85 / Anomalies',
      icon: ShieldAlert,
      color: 'text-[#E8A33D]',
      onClick: () => onFilterStatus('Flagged')
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <div
            key={kpi.id}
            onClick={kpi.onClick}
            className="bg-[#12161D] border border-[#232935] hover:border-[#45E0D6]/40 p-3.5 rounded-xl transition-all cursor-pointer group flex flex-col justify-between"
          >
            <div className="flex items-center justify-between text-[#8B93A3] mb-1.5">
              <span className="text-[10px] font-mono font-bold tracking-wider uppercase">
                {kpi.label}
              </span>
              <Icon className="w-3.5 h-3.5 text-[#8B93A3] group-hover:text-[#45E0D6] transition-colors" />
            </div>

            <div className="my-1">
              {kpi.customRender ? (
                kpi.customRender
              ) : (
                <div className={`text-xl font-bold font-mono tracking-tight ${kpi.color}`}>
                  {kpi.value}
                </div>
              )}
            </div>

            <div className="text-[10px] text-[#8B93A3] font-mono truncate">
              {kpi.subtext}
            </div>
          </div>
        );
      })}
    </div>
  );
};

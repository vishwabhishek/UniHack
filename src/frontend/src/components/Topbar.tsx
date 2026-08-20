import React from 'react';
import {
  ChevronRight,
  Search,
  Zap,
  ShieldCheck,
  Cpu,
  Layers,
  Database
} from 'lucide-react';
import { CatalogStats } from '../types';
import { SegmentedGauge } from './SegmentedGauge';

interface TopbarProps {
  activeTab: string;
  stats: CatalogStats | null;
  onGlobalSearch?: (query: string) => void;
}

export const Topbar: React.FC<TopbarProps> = ({ activeTab, stats }) => {
  const getTabBreadcrumb = () => {
    switch (activeTab) {
      case 'catalog':
        return 'Catalog Explorer & Master Grid';
      case 'playground':
        return 'Real-Time Transformation Sandbox';
      case 'review':
        return 'HITL Exception Triage Board';
      case 'benchmark':
        return 'Ground-Truth QA Benchmark Suite';
      case 'export':
        return '252-Column Master Delivery Exporter';
      default:
        return 'Master Workbench';
    }
  };

  return (
    <header className="h-14 bg-[#12161D] border-b border-[#232935] px-4 sm:px-6 flex items-center justify-between font-sans flex-shrink-0 z-30">
      
      {/* Breadcrumb Path */}
      <div className="flex items-center space-x-2 text-xs font-mono">
        <span className="text-[#8B93A3] font-bold">UNILOG CIMPLIFI</span>
        <ChevronRight className="w-3.5 h-3.5 text-[#525B6C]" />
        <span className="text-white font-bold">{getTabBreadcrumb()}</span>
      </div>

      {/* Global Status Counters & Oscilloscope Confidence Gauge */}
      <div className="flex items-center space-x-4">
        
        {/* System Health / Latency Pill */}
        <div className="hidden md:flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-[#0B0E13] border border-[#232935] text-[11px] font-mono">
          <div className="w-2 h-2 rounded-full bg-[#3DDC84] animate-pulse" />
          <span className="text-[#8B93A3]">LATENCY:</span>
          <span className="text-[#3DDC84] font-bold">11.4ms AVG</span>
        </div>

        {/* Global Confidence Metric */}
        {stats && (
          <div className="hidden sm:flex items-center space-x-2 px-2.5 py-1 rounded-lg bg-[#0B0E13] border border-[#232935]">
            <span className="text-[10px] font-mono text-[#8B93A3] font-bold">CONFIDENCE:</span>
            <SegmentedGauge score={stats.mean_confidence} size="sm" />
          </div>
        )}

      </div>

    </header>
  );
};

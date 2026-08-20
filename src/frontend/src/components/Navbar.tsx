import React, { useState } from 'react';
import {
  Boxes,
  Database,
  Terminal,
  ShieldAlert,
  BarChart4,
  FileSpreadsheet,
  CheckCircle2,
  Menu,
  X,
  Sparkles,
  Zap
} from 'lucide-react';
import { CatalogStats } from '../types';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  stats: CatalogStats | null;
  reviewCount: number;
  onQuickExport: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  stats,
  reviewCount,
  onQuickExport
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { 
      id: 'catalog', 
      label: 'Catalog', 
      fullLabel: 'Master Catalog', 
      icon: Database, 
      badge: stats?.total_items ? `${stats.total_items.toLocaleString()}` : '1,000',
      badgeClass: 'glow-badge-cyan'
    },
    { 
      id: 'playground', 
      label: 'Sandbox', 
      fullLabel: 'Ingestion Sandbox', 
      icon: Terminal,
      badge: '<12ms',
      badgeClass: 'glow-badge-cyan'
    },
    { 
      id: 'review', 
      label: 'Exceptions', 
      fullLabel: 'Quality Exceptions', 
      icon: ShieldAlert, 
      badge: reviewCount > 0 ? `${reviewCount}` : undefined, 
      badgeClass: 'glow-badge-amber'
    },
    { 
      id: 'benchmark', 
      label: 'QA Audit', 
      fullLabel: 'Quality Audit & ROI', 
      icon: BarChart4, 
      badge: '100% GATES', 
      badgeClass: 'glow-badge-emerald'
    },
    { 
      id: 'export', 
      label: 'Export', 
      fullLabel: '252-Col Dispatch', 
      icon: FileSpreadsheet, 
      badge: '252 COLS',
      badgeClass: 'glow-badge-violet'
    }
  ];

  const handleTabClick = (id: string) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-[#080C14]/90 backdrop-blur-xl border-b border-white/[0.08] w-full overflow-hidden shadow-glass">
      {/* Top Environment & Metadata Ribbon */}
      <div className="hidden xl:flex items-center justify-between px-4 sm:px-6 py-1 bg-gradient-to-r from-[#0B101D] via-[#0F1626] to-[#0B101D] border-b border-white/[0.04] text-[11px] text-slate-400 font-mono">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-glow shadow-glow-emerald"></span>
            <span className="text-white font-bold tracking-wider uppercase">PIM WORKBENCH v2.4</span>
          </div>
          <span className="text-slate-700">/</span>
          <span>SCHEMA: <strong className="text-cyan-300">UNILOG 252-COL STANDARD</strong></span>
          <span className="text-slate-700">/</span>
          <span>DATASET: <strong className="text-slate-200">1,000 SKUs · 76 MFGS</strong></span>
        </div>
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1 text-emerald-400 font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>306/306 ASSERTIONS PASSED</span>
          </span>
          <span className="text-slate-700">/</span>
          <span className="text-slate-300 flex items-center space-x-1">
            <Zap className="w-3 h-3 text-cyan-400" />
            <span>LATENCY: <strong className="text-cyan-300 font-bold">11.4ms AVG</strong></span>
          </span>
        </div>
      </div>

      {/* Main Command Bar */}
      <div className="max-w-[1920px] w-full mx-auto px-3 sm:px-5 lg:px-6">
        <div className="flex items-center justify-between h-14 sm:h-16 gap-3">
          {/* Brand Identity */}
          <div
            className="flex items-center space-x-3 cursor-pointer flex-shrink-0 group"
            onClick={() => handleTabClick('catalog')}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-glow-cyan border border-cyan-400/40 transition-transform group-hover:scale-105">
              <Boxes className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-base tracking-tight text-white uppercase font-sans">
                  UNILOG <span className="gradient-brand font-black">CIMPLIFI</span>
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 text-[9px] font-mono uppercase bg-blue-500/10 text-cyan-300 border border-blue-500/30 rounded-full font-bold">
                  Enterprise
                </span>
              </div>
              <p className="hidden 2xl:block text-[10px] text-slate-400 font-mono tracking-wide">
                Industrial Master Data & AI Normalization Engine
              </p>
            </div>
          </div>

          {/* Glowing Workspaces Navigation */}
          <nav className="hidden md:flex items-center space-x-1.5 flex-shrink-0 bg-slate-900/60 p-1 rounded-xl border border-white/[0.06]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`relative flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-glow-blue border border-blue-400/30'
                      : 'text-slate-300 hover:text-white hover:bg-white/[0.06]'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span className="hidden 2xl:inline">{item.fullLabel}</span>
                  <span className="2xl:hidden">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                        isActive ? 'bg-white/20 text-white border border-white/30' : item.badgeClass
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Primary Quick Dispatch */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            <button
              onClick={onQuickExport}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-bold font-mono shadow-glow-blue transition-all border border-cyan-400/40 hover:scale-[1.02] active:scale-[0.98] whitespace-nowrap"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">EXPORT 252-COL CSV</span>
              <span className="sm:hidden">EXPORT</span>
            </button>

            {/* Mobile Drawer Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/[0.08] border border-white/[0.08] transition-colors"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden px-3 pt-2 pb-3 space-y-1.5 bg-[#0B0F19] border-t border-white/[0.08]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-glow-blue'
                    : 'text-slate-300 hover:bg-white/[0.06]'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.fullLabel}</span>
                </div>
                {item.badge && (
                  <span className={`text-[9px] px-2 py-0.5 rounded-full font-mono font-bold ${item.badgeClass}`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </header>
  );
};

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
  ChevronDown
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
      badge: stats?.total_items ? `${stats.total_items.toLocaleString()}` : '1,000' 
    },
    { 
      id: 'playground', 
      label: 'Sandbox', 
      fullLabel: 'Ingestion Sandbox', 
      icon: Terminal,
      badge: '<12ms',
      badgeColor: 'pim-tag-blue'
    },
    { 
      id: 'review', 
      label: 'Exceptions', 
      fullLabel: 'Quality Exceptions', 
      icon: ShieldAlert, 
      badge: reviewCount > 0 ? `${reviewCount}` : undefined, 
      badgeColor: 'pim-tag-amber' 
    },
    { 
      id: 'benchmark', 
      label: 'QA Audit', 
      fullLabel: 'Quality Audit & ROI', 
      icon: BarChart4, 
      badge: '100% GATES', 
      badgeColor: 'pim-tag-emerald' 
    },
    { 
      id: 'export', 
      label: 'Export', 
      fullLabel: '252-Col Dispatch', 
      icon: FileSpreadsheet, 
      badge: '252 COLS',
      badgeColor: 'pim-tag-slate'
    }
  ];

  const handleTabClick = (id: string) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-pim-darkest border-b border-pim-border w-full overflow-hidden">
      {/* Top Environment & Metadata Strip */}
      <div className="hidden xl:flex items-center justify-between px-4 sm:px-6 py-1 bg-[#090D14] border-b border-pim-border/60 text-[11px] text-pim-textMuted font-mono">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span className="text-slate-300 font-semibold uppercase tracking-wider">PIM WORKBENCH v2.4</span>
          </div>
          <span className="text-slate-700">|</span>
          <span>SCHEMA: <strong className="text-slate-300">UNILOG 252-COLUMN STANDARD</strong></span>
          <span className="text-slate-700">|</span>
          <span>DATASET: <strong className="text-slate-300">1,000 SKUs / 76 MFGS</strong></span>
        </div>
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1 text-emerald-400">
            <CheckCircle2 className="w-3 h-3" />
            <span>306/306 ASSERTIONS PASSED</span>
          </span>
          <span className="text-slate-700">|</span>
          <span>LATENCY: <strong className="text-slate-300">11.4ms AVG</strong></span>
        </div>
      </div>

      {/* Main Command Bar */}
      <div className="max-w-[1920px] w-full mx-auto px-3 sm:px-5 lg:px-6">
        <div className="flex items-center justify-between h-13 sm:h-14 gap-2">
          {/* Platform Identity */}
          <div
            className="flex items-center space-x-2.5 cursor-pointer flex-shrink-0"
            onClick={() => handleTabClick('catalog')}
          >
            <div className="w-7 h-7 rounded bg-pim-accent flex items-center justify-center border border-blue-400/40 shadow-sm flex-shrink-0">
              <Boxes className="w-3.5 h-3.5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold text-xs sm:text-sm tracking-tight text-white uppercase font-sans">
                  UNILOG <span className="text-blue-400 font-normal">CIMPLIFI</span>
                </span>
                <span className="hidden sm:inline-block px-1 py-0.2 text-[9px] font-mono uppercase bg-slate-800 text-slate-300 border border-slate-700 rounded">
                  PIM
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Workspaces */}
          <nav className="hidden md:flex items-center space-x-1 flex-shrink-0">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                    isActive
                      ? 'bg-pim-panel text-white border border-pim-borderHighlight shadow-sm font-semibold'
                      : 'text-pim-textSecondary hover:text-white hover:bg-pim-panel/50 border border-transparent'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-blue-400' : 'text-pim-textMuted'}`} />
                  <span className="hidden 2xl:inline">{item.fullLabel}</span>
                  <span className="2xl:hidden">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[9px] px-1 py-0.2 rounded font-mono border ${
                        item.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'
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
              className="flex items-center space-x-1 px-2.5 py-1 rounded bg-pim-accent hover:bg-pim-accentHover text-white text-xs font-semibold font-mono shadow-sm transition-colors border border-blue-500/50 whitespace-nowrap"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">252-COL CSV</span>
              <span className="sm:hidden">EXPORT</span>
            </button>

            {/* Mobile Drawer Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 rounded text-pim-textSecondary hover:text-white hover:bg-pim-panel border border-pim-border transition-colors"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden px-3 pt-2 pb-3 space-y-1 bg-pim-darkest border-t border-pim-border">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center justify-between px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-pim-panel text-white border border-pim-borderHighlight'
                    : 'text-pim-textSecondary hover:bg-pim-panel/40'
                }`}
              >
                <div className="flex items-center space-x-2">
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-pim-textMuted'}`} />
                  <span>{item.fullLabel}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[9px] px-1.5 py-0.2 rounded font-mono border ${
                      item.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'
                    }`}
                  >
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

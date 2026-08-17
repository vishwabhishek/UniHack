import React, { useState } from 'react';
import {
  Layers,
  Database,
  Zap,
  ShieldCheck,
  BarChart3,
  Download,
  Menu,
  X
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
    { id: 'catalog', label: 'Catalog', fullLabel: 'Catalog Explorer', icon: Database, badge: stats?.total_items ? `${stats.total_items}` : '1,000' },
    { id: 'playground', label: 'Sandbox', fullLabel: 'Sandbox Playground', icon: Zap, highlight: true },
    { id: 'review', label: 'HITL Review', fullLabel: 'HITL Review Queue', icon: ShieldCheck, badge: reviewCount > 0 ? `${reviewCount}` : undefined, badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40' },
    { id: 'benchmark', label: 'Benchmarks', fullLabel: 'QA Benchmarks', icon: BarChart3, badge: '100%', badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' },
    { id: 'export', label: 'Export 252', fullLabel: '252-Col Delivery Exporter', icon: Download, badge: '252 Cols' }
  ];

  const handleTabClick = (id: string) => {
    setActiveTab(id);
    setMobileMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-md border-b border-slate-800 w-full overflow-x-clip">
      <div className="max-w-[1920px] w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-10">
        <div className="flex items-center justify-between h-16 gap-3">
          {/* Brand & Logo */}
          <div
            className="flex items-center space-x-3 cursor-pointer flex-shrink-0"
            onClick={() => handleTabClick('catalog')}
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 via-blue-600 to-indigo-700 flex items-center justify-center shadow-md shadow-sky-500/20 border border-sky-400/30 flex-shrink-0">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-base sm:text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  UniHack PIM
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/30 rounded-full font-mono">
                  252-Col Standard
                </span>
              </div>
              <p className="hidden 2xl:block text-[11px] text-slate-400 font-medium line-clamp-1">
                Industrial Product Catalog Normalization & Enrichment Engine
              </p>
            </div>
          </div>

          {/* Navigation Tabs (Desktop & Tablet) */}
          <nav className="hidden md:flex items-center space-x-1.5 flex-shrink">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`relative flex items-center space-x-1.5 px-2.5 lg:px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-150 whitespace-nowrap ${
                    isActive
                      ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30 shadow-sm shadow-sky-500/10 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span className="hidden lg:inline">{item.fullLabel}</span>
                  <span className="lg:hidden">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded-full font-mono border ${
                        item.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                  {item.highlight && !isActive && (
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
            <button
              onClick={onQuickExport}
              className="flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all border border-sky-400/30 whitespace-nowrap active:scale-95"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Export 252-Col CSV</span>
              <span className="sm:hidden">Export</span>
            </button>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 border border-slate-800 transition-colors"
              aria-label="Toggle navigation"
            >
              {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden px-3 pt-2 pb-4 space-y-1 bg-slate-950 border-t border-slate-800/80 animate-in slide-in-from-top-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                    : 'text-slate-300 hover:bg-slate-900'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                  <span>{item.fullLabel}</span>
                </div>
                {item.badge && (
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono border ${
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

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
  Zap,
  User as UserIcon,
  LogOut,
  LogIn,
  Shield,
  KeyRound
} from 'lucide-react';
import { CatalogStats } from '../types';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  stats: CatalogStats | null;
  reviewCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  stats,
  reviewCount
}) => {
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();
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

  const getRoleBadgeClass = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'glow-badge-cyan';
      case 'specialist':
        return 'glow-badge-emerald';
      case 'reviewer':
        return 'glow-badge-amber';
      case 'viewer':
        return 'glow-badge-violet';
      default:
        return 'glow-badge-slate';
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-[#080C14]/90 backdrop-blur-xl border-b border-white/[0.08] w-full overflow-hidden shadow-glass">
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
                  Enterprise PIM
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

          {/* Right Side: Security & User Profile */}
          <div className="flex items-center space-x-2.5 flex-shrink-0">
            {isAuthenticated && user ? (
              <div className="flex items-center space-x-2 bg-slate-950/80 p-1.5 sm:px-3 sm:py-1.5 rounded-xl border border-white/[0.08] shadow-sm">
                <div
                  onClick={openAuthModal}
                  className="flex items-center space-x-2 cursor-pointer group"
                  title="Click to Switch Role or View Security Credentials"
                >
                  <div className={`w-7 h-7 rounded-lg bg-gradient-to-br ${user.avatar_color} text-white flex items-center justify-center text-xs font-extrabold shadow-sm flex-shrink-0`}>
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="hidden sm:block text-left">
                    <div className="text-xs font-bold text-white leading-tight group-hover:text-cyan-300 transition-colors flex items-center space-x-1">
                      <span>{user.name}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full ${getRoleBadgeClass(user.role)}`}>
                        {user.role.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="h-4 w-[1px] bg-white/[0.08] hidden sm:block" />

                <button
                  onClick={openAuthModal}
                  title="Switch Role / View Security Gate"
                  className="p-1.5 text-slate-400 hover:text-cyan-300 rounded-lg hover:bg-white/[0.08] transition-colors"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-white/[0.08] transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={openAuthModal}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-xs font-bold font-mono shadow-glow-blue transition-all border border-cyan-400/40 hover:scale-[1.02]"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>SIGN IN</span>
              </button>
            )}

            {/* Mobile Drawer Button */}
            <div className="flex md:hidden items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-slate-300 hover:text-white hover:bg-white/[0.08] border border-white/[0.08] transition-colors"
                aria-label="Toggle navigation"
              >
                {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </button>
            </div>
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

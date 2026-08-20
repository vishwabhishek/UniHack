import React, { useState } from 'react';
import {
  Boxes,
  Terminal,
  ShieldAlert,
  BarChart3,
  Download,
  KeyRound,
  LogOut,
  Menu,
  X,
  Database
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
      label: 'Catalog Explorer',
      fullLabel: '1,000 SKU Master Catalog',
      icon: Boxes,
      badge: stats ? `${stats.total_items}` : '1,000',
      badgeClass: 'bg-[#1A1F29] text-[#8B93A3] border border-[#232935]'
    },
    {
      id: 'playground',
      label: 'Playground',
      fullLabel: 'Real-Time Sandbox',
      icon: Terminal,
      badge: 'Live',
      badgeClass: 'bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/20'
    },
    {
      id: 'review',
      label: 'Review Queue',
      fullLabel: 'HITL Review Queue',
      icon: ShieldAlert,
      badge: reviewCount > 0 ? `${reviewCount}` : '112',
      badgeClass: 'bg-[#E8A33D]/10 text-[#E8A33D] border border-[#E8A33D]/25'
    },
    {
      id: 'benchmark',
      label: 'QA Benchmark',
      fullLabel: 'Ground-Truth QA',
      icon: BarChart3,
      badge: '100%',
      badgeClass: 'bg-[#3DDC84]/10 text-[#3DDC84] border border-[#3DDC84]/20'
    },
    {
      id: 'export',
      label: '252-Col Export',
      fullLabel: '252-Col Delivery Exporter',
      icon: Download,
      badge: '252 Col',
      badgeClass: 'bg-[#1A1F29] text-[#E7EAF0] border border-[#232935]'
    }
  ];

  const handleTabClick = (tabId: string) => {
    setActiveTab(tabId);
    setMobileMenuOpen(false);
  };

  const getRoleBadgeClass = (role?: string) => {
    switch (role) {
      case 'admin':
        return 'bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/30';
      case 'specialist':
        return 'bg-[#3B82F6]/10 text-[#60A5FA] border border-[#3B82F6]/30';
      case 'reviewer':
        return 'bg-[#3DDC84]/10 text-[#3DDC84] border border-[#3DDC84]/30';
      default:
        return 'bg-[#8B93A3]/10 text-[#8B93A3] border border-[#8B93A3]/30';
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-[#12161D] border-b border-[#232935] w-full shadow-sm">
      <div className="max-w-[1920px] w-full mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-14 sm:h-16 gap-3">
          
          {/* Brand Identity */}
          <div
            className="flex items-center space-x-3 cursor-pointer flex-shrink-0 group"
            onClick={() => handleTabClick('catalog')}
          >
            <div className="w-8 h-8 rounded-lg bg-[#1A1F29] border border-[#232935] flex items-center justify-center text-[#45E0D6] group-hover:border-[#45E0D6]/50 transition-colors">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-sm tracking-tight text-white font-mono uppercase">
                  UNILOG <span className="text-[#45E0D6]">CIMPLIFI</span>
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 text-[9px] font-mono uppercase bg-[#1A1F29] text-[#8B93A3] border border-[#232935] rounded-full font-bold">
                  PIM 2.4
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="hidden md:flex items-center space-x-1.5 flex-shrink-0 bg-[#0B0E13] p-1 rounded-xl border border-[#232935]">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => handleTabClick(item.id)}
                  className={`relative flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all whitespace-nowrap font-sans ${
                    isActive
                      ? 'bg-[#1A1F29] text-white border border-[#232935] shadow-sm'
                      : 'text-[#8B93A3] hover:text-white hover:bg-[#12161D]'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-[#45E0D6]' : 'text-[#8B93A3]'}`} />
                  <span className="hidden 2xl:inline">{item.fullLabel}</span>
                  <span className="2xl:hidden">{item.label}</span>
                  {item.badge && (
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-bold ${item.badgeClass}`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* User Profile & Security */}
          <div className="flex items-center space-x-2.5 flex-shrink-0">
            {isAuthenticated && user && (
              <div className="flex items-center space-x-2 bg-[#0B0E13] p-1.5 sm:px-3 sm:py-1.5 rounded-xl border border-[#232935]">
                <div
                  onClick={openAuthModal}
                  className="flex items-center space-x-2 cursor-pointer group"
                  title="Switch Role or View Security Settings"
                >
                  <div className="w-6 h-6 rounded-md bg-[#1A1F29] border border-[#232935] text-[#45E0D6] flex items-center justify-center text-xs font-extrabold font-mono">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="hidden sm:block text-left">
                    <div className="text-xs font-semibold text-white leading-tight group-hover:text-[#45E0D6] transition-colors font-sans">
                      {user.name}
                    </div>
                    <div className="flex items-center space-x-1">
                      <span className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded ${getRoleBadgeClass(user.role)}`}>
                        {user.role.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="h-4 w-[1px] bg-[#232935] hidden sm:block" />

                <button
                  onClick={openAuthModal}
                  title="Security Gate"
                  className="p-1 text-[#8B93A3] hover:text-[#45E0D6] rounded hover:bg-[#1A1F29] transition-colors"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={logout}
                  title="Sign Out"
                  className="p-1 text-[#8B93A3] hover:text-[#EF5A5A] rounded hover:bg-[#1A1F29] transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Mobile Menu Button */}
            <div className="flex md:hidden items-center">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-lg text-[#8B93A3] hover:text-white bg-[#0B0E13] border border-[#232935]"
              >
                {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </button>
            </div>

          </div>

        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-[#232935] bg-[#12161D] px-4 py-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold ${
                  isActive
                    ? 'bg-[#1A1F29] text-white border border-[#232935]'
                    : 'text-[#8B93A3] hover:text-white'
                }`}
              >
                <div className="flex items-center space-x-2.5">
                  <Icon className="w-4 h-4 text-[#45E0D6]" />
                  <span>{item.fullLabel}</span>
                </div>
                {item.badge && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${item.badgeClass}`}>
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

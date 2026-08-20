import React from 'react';
import {
  Boxes,
  Terminal,
  ShieldAlert,
  BarChart3,
  Download,
  Shield,
  KeyRound,
  LogOut,
  Database,
  ChevronRight,
  Layers,
  Sparkles
} from 'lucide-react';
import { CatalogStats } from '../types';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  stats: CatalogStats | null;
  reviewCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  stats,
  reviewCount
}) => {
  const { user, logout, openAuthModal } = useAuth();

  const navigationGroups = [
    {
      groupTitle: 'DATA & WORKBENCH',
      items: [
        {
          id: 'catalog',
          label: 'Catalog Explorer',
          subLabel: '1,000 SKU Master Table',
          icon: Boxes,
          badge: stats ? `${stats.total_items}` : '1,000',
          badgeClass: 'bg-[#1A1F29] text-[#8B93A3] border border-[#232935]'
        },
        {
          id: 'playground',
          label: 'Live Sandbox',
          subLabel: 'Real-Time Transformation',
          icon: Terminal,
          badge: 'Live',
          badgeClass: 'bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/20'
        },
        {
          id: 'benchmark',
          label: 'QA Benchmark',
          subLabel: '252-Col Ground Truth',
          icon: BarChart3,
          badge: '100%',
          badgeClass: 'bg-[#3DDC84]/10 text-[#3DDC84] border border-[#3DDC84]/20'
        }
      ]
    },
    {
      groupTitle: 'GOVERNANCE & EXPORT',
      items: [
        {
          id: 'review',
          label: 'HITL Review Queue',
          subLabel: 'Exception Triage Board',
          icon: ShieldAlert,
          badge: reviewCount > 0 ? `${reviewCount}` : '112',
          badgeClass: 'bg-[#E8A33D]/10 text-[#E8A33D] border border-[#E8A33D]/25'
        },
        {
          id: 'export',
          label: 'Delivery Exporter',
          subLabel: '252-Column CSV / XLSX',
          icon: Download,
          badge: '252 Col',
          badgeClass: 'bg-[#1A1F29] text-[#E7EAF0] border border-[#232935]'
        }
      ]
    }
  ];

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
    <aside className="w-64 bg-[#12161D] border-r border-[#232935] flex flex-col justify-between flex-shrink-0 min-h-screen select-none font-sans">
      
      {/* Top Header: Brand Identity */}
      <div>
        <div className="p-4 border-b border-[#232935] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-[#1A1F29] border border-[#232935] flex items-center justify-center text-[#45E0D6] shadow-sm">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-sm tracking-tight text-white font-mono">
                  UNILOG
                </span>
                <span className="text-[10px] font-bold text-[#45E0D6] font-mono">
                  CIMPLIFI
                </span>
              </div>
              <p className="text-[10px] text-[#8B93A3] font-mono leading-none mt-0.5">
                Industrial PIM v2.4
              </p>
            </div>
          </div>
        </div>

        {/* Grouped Navigation Links */}
        <div className="p-3 space-y-5">
          {navigationGroups.map((group, gIdx) => (
            <div key={gIdx} className="space-y-1">
              <div className="px-2.5 py-1 text-[10px] font-mono font-bold tracking-wider text-[#8B93A3] uppercase">
                {group.groupTitle}
              </div>

              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-semibold transition-all group ${
                        isActive
                          ? 'bg-[#1A1F29] text-white border border-[#232935] shadow-sm'
                          : 'text-[#8B93A3] hover:text-white hover:bg-[#1A1F29]/50'
                      }`}
                    >
                      <div className="flex items-center space-x-2.5 truncate">
                        <Icon
                          className={`w-4 h-4 flex-shrink-0 transition-colors ${
                            isActive ? 'text-[#45E0D6]' : 'text-[#8B93A3] group-hover:text-white'
                          }`}
                        />
                        <div className="text-left truncate">
                          <div className="text-xs font-medium text-[#E7EAF0] truncate">{item.label}</div>
                          <div className="text-[10px] text-[#8B93A3] truncate font-mono">{item.subLabel}</div>
                        </div>
                      </div>

                      {item.badge && (
                        <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold flex-shrink-0 ${item.badgeClass}`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Footer: User Session & Security Controls */}
      <div className="p-3 border-t border-[#232935] bg-[#0B0E13] space-y-2">
        {user && (
          <div className="p-2.5 rounded-xl bg-[#12161D] border border-[#232935] flex items-center justify-between">
            <div className="flex items-center space-x-2.5 truncate">
              <div className="w-7 h-7 rounded-lg bg-[#1A1F29] border border-[#232935] text-[#45E0D6] flex items-center justify-center text-xs font-bold font-mono">
                {user.name.charAt(0).toUpperCase()}
              </div>
              <div className="truncate text-left">
                <div className="text-xs font-bold text-white truncate">{user.name}</div>
                <span className={`inline-block text-[9px] font-mono font-bold px-1.5 py-0.2 rounded mt-0.5 ${getRoleBadgeClass(user.role)}`}>
                  {user.role.toUpperCase()}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={openAuthModal}
                title="Security Settings & Role Switcher"
                className="p-1.5 text-[#8B93A3] hover:text-[#45E0D6] hover:bg-[#1A1F29] rounded-lg transition-colors"
              >
                <KeyRound className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={logout}
                title="Sign Out"
                className="p-1.5 text-[#8B93A3] hover:text-[#EF5A5A] hover:bg-[#1A1F29] rounded-lg transition-colors"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

    </aside>
  );
};

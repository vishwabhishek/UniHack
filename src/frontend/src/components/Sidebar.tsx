import React from 'react';
import { useAuth } from '../context/AuthContext';
import { KeyRound, LogOut } from 'lucide-react';
import { CatalogStats } from '../types';

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

  const navItems = [
    { id: 'catalog', label: 'Catalog explorer', badge: null },
    { id: 'playground', label: 'Playground', badge: null },
    { id: 'review', label: 'Review queue', badge: reviewCount > 0 ? `${reviewCount}` : '112' },
    { id: 'benchmark', label: 'QA Benchmark', badge: '100%' },
    { id: 'export', label: 'Export 252-Col', badge: null },
  ];

  return (
    <aside className="w-[220px] bg-[var(--surface-1)] border-r border-[var(--border)] p-[22px_14px] flex flex-col justify-between flex-shrink-0 min-h-screen select-none font-sans">
      <div>
        {/* Brand */}
        <div className="flex items-center gap-2 px-2 pb-6">
          <div className="w-2.5 h-2.5 rounded-[2px] bg-[var(--cyan)]" />
          <div className="font-mono text-xs tracking-[0.06em] text-[var(--text-primary)] font-medium">
            UNIHACK SIMPLIFI
          </div>
        </div>

        {/* Navigation */}
        <div className="flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <div
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center justify-between gap-2.5 px-2.5 py-2 rounded-md text-[13px] cursor-pointer transition-colors ${
                  isActive
                    ? 'bg-[var(--cyan-bg)] text-[var(--cyan)] font-medium'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-1.5 h-1.5 rounded-[1px] ${
                      isActive ? 'bg-[var(--cyan)]' : 'bg-[var(--text-muted)]'
                    }`}
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span className="font-mono text-[10px] bg-[var(--amber-bg)] text-[var(--amber)] px-1.5 py-0.5 rounded-full font-bold">
                    {item.badge}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-auto pt-3 border-t border-[var(--border)] px-2.5">
        <div className="flex items-center justify-between">
          <div className="text-[11px] text-[var(--text-muted)] leading-relaxed">
            Signed in as <b className="text-[var(--text-secondary)]">{user?.name || 'A. Vishwakarma'}</b>
            <br />
            Role: <span className="font-mono text-[var(--cyan)]">{user?.role || 'specialist'}</span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={openAuthModal}
              title="Security & Permissions"
              className="p-1 text-[var(--text-muted)] hover:text-[var(--cyan)] cursor-pointer"
            >
              <KeyRound className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1 text-[var(--text-muted)] hover:text-[var(--red)] cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};

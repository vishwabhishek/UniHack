import React from 'react';
import { useAuth } from '../context/AuthContext';
import { CatalogStats } from '../types';
import { Menu, Search, Shield } from 'lucide-react';

interface TopbarProps {
  activeTab: string;
  stats: CatalogStats | null;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
  onToggleMobileMenu?: () => void;
}

const TAB_TITLES: Record<string, { section: string; title: string }> = {
  catalog: { section: 'WORKSPACE', title: 'Catalog Explorer' },
  playground: { section: 'WORKSPACE', title: 'Enrichment Playground' },
  evidence: { section: 'GOVERNANCE', title: 'Evidence Inbox & Sources' },
  review: { section: 'GOVERNANCE', title: 'Field-Level Review Queue' },
  benchmark: { section: 'GOVERNANCE', title: 'Validation & Benchmark' },
  export: { section: 'DELIVERY', title: '252-Column Delivery Export' },
  users: { section: 'ADMINISTRATION', title: 'Enterprise User Management & RBAC' }
};


export const Topbar: React.FC<TopbarProps> = ({
  activeTab,
  stats,
  searchQuery = '',
  onSearchChange,
  onToggleMobileMenu
}) => {
  const { user } = useAuth();
  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'AV';

  const tabInfo = TAB_TITLES[activeTab] || { section: 'WORKSPACE', title: 'Catalog Explorer' };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 py-3 bg-[var(--surface-2)]/95 backdrop-blur-sm border-b border-[var(--border)] font-sans flex-shrink-0">
      
      {/* Left: Mobile Menu Toggle & Breadcrumbs */}
      <div className="flex items-center gap-3">
        {onToggleMobileMenu && (
          <button
            onClick={onToggleMobileMenu}
            className="p-1.5 rounded-md text-[var(--text-muted)] hover:text-white hover:bg-[var(--surface-1)] md:hidden cursor-pointer"
            title="Toggle Menu"
          >
            <Menu className="w-4 h-4" />
          </button>
        )}

        <div className="flex items-center gap-1.5 text-xs font-mono">
          <span className="text-[var(--text-muted)] uppercase tracking-wider text-[11px]">
            {tabInfo.section}
          </span>
          <span className="text-[var(--border-strong)]">/</span>
          <span className="text-[var(--text-primary)] font-bold">
            {tabInfo.title}
          </span>
        </div>
      </div>

      {/* Right: Search & User Info */}
      <div className="flex items-center gap-3">
        {/* Scoped Search Input */}
        <div className="relative hidden sm:block w-64">
          <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            placeholder="Search SKU, MPN, Brand..."
            className="w-full bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md pl-9 pr-3 py-1.5 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] font-mono focus:outline-none focus:border-[var(--cyan)]"
          />
        </div>

        {/* User Role Badge & Avatar */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-[var(--border)]">
          <span className="text-[10px] font-mono font-bold bg-[var(--surface-1)] text-[var(--cyan)] border border-[var(--border-strong)] px-2 py-0.5 rounded uppercase">
            {user?.role || 'specialist'}
          </span>
          <div
            title={user?.email || 'Logged in user'}
            className="w-7 h-7 rounded-full bg-[var(--cyan-bg)] text-[var(--cyan)] border border-[var(--cyan)] flex items-center justify-center text-xs font-semibold font-mono"
          >
            {initials}
          </div>
        </div>
      </div>

    </header>
  );
};

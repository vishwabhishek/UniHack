import React from 'react';
import { useAuth } from '../context/AuthContext';
import { CatalogStats } from '../types';

interface TopbarProps {
  activeTab: string;
  stats: CatalogStats | null;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
}

export const Topbar: React.FC<TopbarProps> = ({ searchQuery = '', onSearchChange }) => {
  const { user } = useAuth();
  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'AV';

  return (
    <header className="flex items-center justify-between px-6 py-3.5 bg-[var(--surface-2)] border-b border-[var(--border)] font-sans">
      <input
        type="text"
        value={searchQuery}
        onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
        placeholder="search SKU, MPN, brand, UNSPSC…"
        className="bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md px-3 py-2 text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] w-72 font-mono focus:outline-none focus:border-[var(--cyan)]"
      />

      <div className="flex items-center gap-3.5">
        <div className="text-[11px] font-mono bg-[var(--gray-chip)] text-[var(--text-secondary)] px-2.5 py-1 rounded-md">
          {user?.role || 'specialist'}
        </div>
        <div className="w-[30px] h-[30px] rounded-full bg-[var(--cyan-bg)] text-[var(--cyan)] flex items-center justify-center text-xs font-semibold font-mono">
          {initials}
        </div>
      </div>
    </header>
  );
};

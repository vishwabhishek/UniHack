import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  Database,
  Sliders,
  ShieldAlert,
  BarChart3,
  Download,
  KeyRound,
  LogOut,
  FileSearch,
  PanelLeftClose,
  PanelLeftOpen,
  ChevronRight,
  ShieldCheck,
  User as UserIcon
} from 'lucide-react';
import { CatalogStats } from '../types';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  stats: CatalogStats | null;
  reviewCount: number;
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  stats,
  reviewCount,
  mobileOpen = false,
  onCloseMobile,
  collapsed: controlledCollapsed,
  onToggleCollapse: controlledToggleCollapse
}) => {
  const { user, logout, openAuthModal } = useAuth();

  // Internal collapsed state if not controlled externally
  const [internalCollapsed, setInternalCollapsed] = useState<boolean>(() => {
    const saved = localStorage.getItem('unilog_sidebar_collapsed');
    return saved === 'true';
  });

  const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;

  const toggleCollapsed = () => {
    if (controlledToggleCollapse) {
      controlledToggleCollapse();
    } else {
      setInternalCollapsed((prev) => {
        const next = !prev;
        localStorage.setItem('unilog_sidebar_collapsed', String(next));
        return next;
      });
    }
  };

  // Keyboard shortcut: [ or Ctrl+B to toggle sidebar collapse
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA' ||
        document.activeElement?.tagName === 'SELECT'
      ) {
        return;
      }
      if (e.key === '[' || (e.ctrlKey && e.key.toLowerCase() === 'b')) {
        e.preventDefault();
        toggleCollapsed();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const navGroups = [
    {
      group: 'WORKSPACE',
      items: [
        { id: 'catalog', label: 'Catalog', icon: Database, shortcut: '1', badge: stats ? `${stats.total_items}` : '1,000' },
        { id: 'playground', label: 'Enrichment Playground', icon: Sliders, shortcut: '2', badge: null }
      ]
    },
    {
      group: 'GOVERNANCE',
      items: [
        { id: 'evidence', label: 'Evidence Inbox', icon: FileSearch, shortcut: '3', badge: null },
        {
          id: 'review',
          label: 'Review Queue',
          icon: ShieldAlert,
          shortcut: '4',
          badge: reviewCount > 0 ? `${reviewCount}` : null,
          badgeColor: 'amber'
        },
        {
          id: 'benchmark',
          label: 'Validation & Benchmark',
          icon: BarChart3,
          shortcut: '5',
          badge: '100%'
        }
      ]
    },
    {
      group: 'DELIVERY',
      items: [
        { id: 'export', label: 'Delivery Export', icon: Download, shortcut: '6', badge: '252' }
      ]
    },
    ...(user?.role === 'admin' ? [
      {
        group: 'ADMINISTRATION',
        items: [
          { id: 'users', label: 'User Management', icon: UserIcon, shortcut: '7', badge: null }
        ]
      }
    ] : [])
  ];

  const handleNavClick = (tabId: string) => {
    setActiveTab(tabId);
    if (onCloseMobile) onCloseMobile();
  };


  return (
    <aside
      className={`bg-[var(--surface-1)] border-r border-[var(--border)] flex flex-col justify-between flex-shrink-0 select-none font-sans transition-all duration-200 z-40 ${
        mobileOpen
          ? 'fixed inset-y-0 left-0 w-64 shadow-2xl flex p-4'
          : `hidden md:flex sticky top-0 h-screen overflow-y-auto overflow-x-hidden ${
              isCollapsed ? 'w-[72px] p-3' : 'w-[230px] p-4'
            }`
      }`}
    >
      <div className="space-y-5">
        {/* Brand Header & Collapse Toggle */}
        <div className={`flex items-center ${isCollapsed ? 'justify-center flex-col gap-2' : 'justify-between'} pt-1 pb-2 border-b border-[var(--border)]`}>
          <div className="flex items-center gap-2.5 overflow-hidden">
            <div className="w-2.5 h-2.5 rounded-[2px] bg-[var(--cyan)] flex-shrink-0 shadow-[0_0_8px_rgba(69,224,214,0.6)]" />
            {!isCollapsed && (
              <div className="truncate">
                <div className="font-mono text-xs tracking-[0.06em] text-[var(--text-primary)] font-bold truncate">
                  UNIHACK SIMPLIFI
                </div>
                <div className="text-[9px] font-mono text-[var(--text-muted)] tracking-wider truncate">
                  EVIDENCE-BASED PIM
                </div>
              </div>
            )}
          </div>

          {/* Collapse/Expand Toggle Button */}
          <button
            type="button"
            onClick={toggleCollapsed}
            title={isCollapsed ? 'Expand sidebar ([)' : 'Collapse sidebar ([)'}
            className="p-1.5 text-[var(--text-muted)] hover:text-[var(--cyan)] hover:bg-[var(--surface-2)] rounded transition-colors cursor-pointer"
          >
            {isCollapsed ? (
              <PanelLeftOpen className="w-4 h-4 text-[var(--cyan)]" />
            ) : (
              <PanelLeftClose className="w-4 h-4" />
            )}
          </button>
        </div>

        {/* Grouped Navigation Sections */}
        <div className="space-y-4">
          {navGroups.map((grp) => (
            <div key={grp.group} className="space-y-1">
              {!isCollapsed ? (
                <div className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[var(--text-muted)] px-2 py-0.5">
                  {grp.group}
                </div>
              ) : (
                <div className="h-px bg-[var(--border)] mx-1 my-1.5 opacity-60" />
              )}

              <div className="space-y-1">
                {grp.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <div key={item.id} className="relative group">
                      <button
                        type="button"
                        onClick={() => handleNavClick(item.id)}
                        className={`w-full flex items-center ${
                          isCollapsed ? 'justify-center px-0 py-2.5' : 'justify-between px-2.5 py-2'
                        } rounded-md text-xs transition-all text-left cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--cyan)] ${
                          isActive
                            ? 'bg-[var(--cyan-bg)] text-[var(--cyan)] font-semibold shadow-xs border border-[var(--cyan)]/30'
                            : 'text-[var(--text-secondary)] hover:text-white hover:bg-[var(--surface-2)] border border-transparent'
                        }`}
                      >
                        <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'gap-2.5'} truncate`}>
                          <div className="relative flex items-center justify-center">
                            <Icon
                              className={`w-4 h-4 flex-shrink-0 transition-transform group-hover:scale-110 ${
                                isActive ? 'text-[var(--cyan)]' : 'text-[var(--text-muted)]'
                              }`}
                            />
                            {/* Collapsed dot badge for alerts */}
                            {isCollapsed && item.badge && item.badgeColor === 'amber' && (
                              <span className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-[var(--amber)] shadow-[0_0_6px_rgba(232,163,61,0.8)]" />
                            )}
                          </div>
                          {!isCollapsed && <span className="truncate">{item.label}</span>}
                        </div>

                        {!isCollapsed && (
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            {item.badge && (
                              <span
                                className={`font-mono text-[10px] px-1.5 py-0.5 rounded font-bold ${
                                  item.badgeColor === 'amber'
                                    ? 'bg-[var(--amber-bg)] text-[var(--amber)] border border-[var(--amber)]/40'
                                    : 'bg-[var(--surface-2)] text-[var(--text-muted)] border border-[var(--border)]'
                                }`}
                              >
                                {item.badge}
                              </span>
                            )}
                            <span className="font-mono text-[9px] text-[var(--text-muted)] opacity-50">
                              {item.shortcut}
                            </span>
                          </div>
                        )}
                      </button>

                      {/* Tooltip for collapsed mode */}
                      {isCollapsed && (
                        <div className="absolute left-full top-1/2 -translate-y-1/2 ml-3 px-2.5 py-1.5 bg-[#12161D] border border-[var(--border-strong)] text-white text-xs rounded shadow-xl whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 font-sans flex items-center gap-2">
                          <span className="font-medium">{item.label}</span>
                          {item.badge && (
                            <span
                              className={`font-mono text-[10px] px-1.5 py-0.2 rounded ${
                                item.badgeColor === 'amber'
                                  ? 'bg-[var(--amber-bg)] text-[var(--amber)]'
                                  : 'bg-[var(--cyan-bg)] text-[var(--cyan)]'
                              }`}
                            >
                              {item.badge}
                            </span>
                          )}
                          <span className="font-mono text-[10px] text-[var(--cyan)] bg-[var(--surface-2)] px-1 rounded">
                            [{item.shortcut}]
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer Profile & Auth Actions */}
      <div className={`mt-auto pt-3 border-t border-[var(--border)] ${isCollapsed ? 'px-0 flex flex-col items-center gap-2' : 'px-1'}`}>
        {!isCollapsed ? (
          <div className="flex items-center justify-between">
            <div className="text-[11px] text-[var(--text-muted)] leading-tight space-y-0.5 overflow-hidden">
              <div className="text-[var(--text-secondary)] font-medium truncate max-w-[110px]">
                {user?.name || 'A. Vishwakarma'}
              </div>
              <div className="font-mono text-[9px] text-[var(--cyan)] uppercase flex items-center gap-1">
                <ShieldCheck className="w-2.5 h-2.5" />
                <span>{user?.role || 'specialist'}</span>
              </div>
            </div>

            <div className="flex items-center gap-0.5">
              <button
                type="button"
                onClick={openAuthModal}
                title="Security & Permissions"
                className="p-1.5 text-[var(--text-muted)] hover:text-[var(--cyan)] rounded hover:bg-[var(--surface-2)] cursor-pointer"
              >
                <KeyRound className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={logout}
                title="Sign Out"
                className="p-1.5 text-[var(--text-muted)] hover:text-[var(--red)] rounded hover:bg-[var(--surface-2)] cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1.5 w-full">
            <button
              type="button"
              onClick={openAuthModal}
              title={`Logged in as ${user?.name || 'User'} (${user?.role || 'specialist'})\nClick for Security & Permissions`}
              className="w-8 h-8 rounded-full bg-[var(--surface-2)] border border-[var(--border)] flex items-center justify-center text-[var(--cyan)] hover:border-[var(--cyan)] cursor-pointer transition-colors"
            >
              <UserIcon className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              onClick={logout}
              title="Sign Out"
              className="p-1 text-[var(--text-muted)] hover:text-[var(--red)] rounded hover:bg-[var(--surface-2)] cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;

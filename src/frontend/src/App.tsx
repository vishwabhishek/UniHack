import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { MetricsBanner } from './components/MetricsBanner';
import { CatalogExplorer } from './components/CatalogExplorer';
import { TransformationInspector } from './components/TransformationInspector';
import { InteractivePlayground } from './components/InteractivePlayground';
import { ReviewQueue } from './components/ReviewQueue';
import { BenchmarkDashboard } from './components/BenchmarkDashboard';
import { DeliveryExporter } from './components/DeliveryExporter';
import { ToastProvider, useToast } from './components/Toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './components/LoginPage';
import { AuthModal } from './components/AuthModal';
import { fetchStats, fetchReviewQueue } from './services/api';
import { CatalogStats } from './types';

const DashboardContent: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<string>('catalog');
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [inspectProductId, setInspectProductId] = useState<string | null>(null);
  const [catalogFilterStatus, setCatalogFilterStatus] = useState<string>('All');
  const [globalSearch, setGlobalSearch] = useState<string>('');

  useEffect(() => {
    if (isAuthenticated) {
      loadGlobalState();
    }
  }, [isAuthenticated]);

  // Keyboard shortcut listeners (1-5 to switch tabs)
  useEffect(() => {
    if (!isAuthenticated) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA' ||
        document.activeElement?.tagName === 'SELECT'
      ) {
        return;
      }

      if (e.key === '1') setActiveTab('catalog');
      else if (e.key === '2') setActiveTab('playground');
      else if (e.key === '3') setActiveTab('review');
      else if (e.key === '4') setActiveTab('benchmark');
      else if (e.key === '5') setActiveTab('export');
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isAuthenticated]);

  const loadGlobalState = async () => {
    try {
      const statsData = await fetchStats();
      setStats(statsData);
      const queueData = await fetchReviewQueue();
      setReviewCount(queueData.total);
    } catch (e) {
      console.error('Failed to load global dashboard state:', e);
    }
  };

  const handleInspect = (id: string) => {
    setInspectProductId(id);
  };

  const handleEdit = (id: string) => {
    setActiveTab('review');
  };

  const handleFilterStatusFromBanner = (status: string) => {
    if (status === 'Flagged') {
      setActiveTab('review');
    } else {
      setCatalogFilterStatus(status);
      setActiveTab('catalog');
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[var(--bg)] text-[var(--text-primary)] flex flex-col items-center justify-center font-sans space-y-4">
        <div className="w-10 h-10 rounded-xl bg-[var(--surface-1)] border border-[var(--border-strong)] flex items-center justify-center text-[var(--cyan)] shadow-[0_0_20px_rgba(69,224,214,0.15)] animate-pulse">
          <div className="w-3 h-3 rounded-[2px] bg-[var(--cyan)]" />
        </div>
        <div className="text-center font-mono space-y-1">
          <p className="text-xs font-semibold text-[var(--cyan)] tracking-wider">VERIFYING SECURE SESSION</p>
          <p className="text-[11px] text-[var(--text-muted)]">Connecting to UniHack Simplifi API...</p>
        </div>
      </div>
    );
  }

  // Strict Authentication Gate: If unauthenticated, render the split Login Portal only!
  if (!isAuthenticated || !user) {
    return <LoginPage />;
  }

  return (
    <div className="dash grid grid-cols-[220px_1fr] min-h-screen bg-[var(--bg)] text-[var(--text-primary)] font-sans">
      
      {/* SIDEBAR (220px) */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        reviewCount={reviewCount}
      />

      {/* MAIN VIEWPORT */}
      <div className="main flex flex-col min-w-0 min-h-screen overflow-y-auto">
        
        {/* TOPBAR */}
        <Topbar
          activeTab={activeTab}
          stats={stats}
          searchQuery={globalSearch}
          onSearchChange={(q) => {
            setGlobalSearch(q);
            if (activeTab !== 'catalog') setActiveTab('catalog');
          }}
        />

        {/* CONTENT AREA */}
        <div className="content p-[26px] flex-1">
          
          {/* KPI Metrics Grid */}
          <MetricsBanner
            stats={stats}
            onFilterStatus={handleFilterStatusFromBanner}
          />

          {/* Active Workspace View */}
          <div>
            {activeTab === 'catalog' && (
              <CatalogExplorer
                onInspectProduct={handleInspect}
                onEditProduct={handleEdit}
                initialStatus={catalogFilterStatus}
                globalSearch={globalSearch}
              />
            )}

            {activeTab === 'playground' && (
              <InteractivePlayground />
            )}

            {activeTab === 'review' && (
              <ReviewQueue
                onInspectProduct={handleInspect}
                onRefreshCatalog={loadGlobalState}
              />
            )}

            {activeTab === 'benchmark' && (
              <BenchmarkDashboard />
            )}

            {activeTab === 'export' && (
              <DeliveryExporter />
            )}
          </div>
        </div>

      </div>

      {/* Dual-Pane Transformation Workbench Modal */}
      {inspectProductId && (
        <TransformationInspector
          productId={inspectProductId}
          onClose={() => setInspectProductId(null)}
          onEdit={handleEdit}
          onApproved={loadGlobalState}
        />
      )}

      {/* Security & Authentication Modal */}
      <AuthModal />

    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <DashboardContent />
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;

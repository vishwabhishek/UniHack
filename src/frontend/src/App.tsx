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
import { Database } from 'lucide-react';

const DashboardContent: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<string>('catalog');
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [inspectProductId, setInspectProductId] = useState<string | null>(null);
  const [catalogFilterStatus, setCatalogFilterStatus] = useState<string>('All');

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
      <div className="min-h-screen bg-[#0B0E13] text-[#E7EAF0] flex flex-col items-center justify-center font-sans space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-[#12161D] border border-[#232935] flex items-center justify-center text-[#45E0D6] shadow-[0_0_24px_rgba(69,224,214,0.2)] animate-pulse">
          <Database className="w-6 h-6" />
        </div>
        <div className="text-center font-mono space-y-1">
          <p className="text-xs font-bold text-[#45E0D6] tracking-wider">VERIFYING SECURE SESSION</p>
          <p className="text-[11px] text-[#8B93A3]">Connecting to Unilog PIM API...</p>
        </div>
      </div>
    );
  }

  // Strict Authentication Gate: If unauthenticated, render the split Login Portal only!
  if (!isAuthenticated || !user) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-[#0B0E13] text-[#E7EAF0] flex font-sans overflow-hidden">
      
      {/* ZONE 2: PRIMARY SIDEBAR (Left Navigation) */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        reviewCount={reviewCount}
      />

      {/* RIGHT VIEWPORT CONTAINER */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen overflow-y-auto">
        
        {/* ZONE 1: GLOBAL TOPBAR (Fixed Top Header) */}
        <Topbar
          activeTab={activeTab}
          stats={stats}
        />

        {/* ZONE 3: CONTEXTUAL CONTENT AREA */}
        <main className="flex-1 p-4 sm:p-6 space-y-5 max-w-[1800px] w-full">
          
          {/* KPI Metrics Strip */}
          <MetricsBanner
            stats={stats}
            onFilterStatus={handleFilterStatusFromBanner}
          />

          {/* Active Workspace View */}
          <div className="transition-all duration-150">
            {activeTab === 'catalog' && (
              <CatalogExplorer
                onInspectProduct={handleInspect}
                onEditProduct={handleEdit}
                initialStatus={catalogFilterStatus}
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
        </main>

        {/* Footer Audit Bar */}
        <footer className="bg-[#12161D] border-t border-[#232935] px-6 py-3 text-xs text-[#8B93A3] font-mono flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-white">UNILOG CIMPLIFI™</span>
            <span>·</span>
            <span>252-COLUMN MASTER DELIVERY STANDARD</span>
            <span>·</span>
            <span className="text-[#3DDC84] font-bold">100% LOV COMPLIANCE</span>
          </div>
          <div className="flex items-center space-x-3 text-[11px]">
            <span className="text-[#3DDC84]">FASTAPI ENGINE :8000</span>
            <span>·</span>
            <span className="text-[#45E0D6] font-bold">&lt; 12ms LATENCY</span>
          </div>
        </footer>

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

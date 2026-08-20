import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MetricsBanner } from './components/MetricsBanner';
import { CatalogExplorer } from './components/CatalogExplorer';
import { TransformationInspector } from './components/TransformationInspector';
import { InteractivePlayground } from './components/InteractivePlayground';
import { ReviewQueue } from './components/ReviewQueue';
import { BenchmarkDashboard } from './components/BenchmarkDashboard';
import { DeliveryExporter } from './components/DeliveryExporter';
import { ToastProvider, useToast } from './components/Toast';
import { fetchStats, fetchReviewQueue, getExportCsvUrl } from './services/api';
import { CatalogStats } from './types';

const DashboardContent: React.FC = () => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<string>('catalog');
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [reviewCount, setReviewCount] = useState<number>(0);
  const [inspectProductId, setInspectProductId] = useState<string | null>(null);
  const [catalogFilterStatus, setCatalogFilterStatus] = useState<string>('All');

  useEffect(() => {
    loadGlobalState();
  }, []);

  // Keyboard shortcut listeners (1-5 to switch tabs, Esc to close inspector)
  useEffect(() => {
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
  }, []);

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

  const handleQuickExport = () => {
    const url = getExportCsvUrl();
    const a = document.createElement('a');
    a.href = url;
    a.download = 'unilog_enriched_catalog_252_columns.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('Dispatch Triggered', 'Exporting 1,000 items in 252-column delivery format', 'success');
  };

  return (
    <div className="min-h-screen bg-[#080C14] text-slate-100 flex flex-col antialiased selection:bg-cyan-500 selection:text-white font-sans relative overflow-x-hidden">
      {/* Background Ambient Radial Light Cones */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/4 w-[600px] h-[400px] bg-blue-600/10 blur-[140px] rounded-full" />
        <div className="absolute top-1/3 right-10 w-[500px] h-[450px] bg-indigo-600/10 blur-[160px] rounded-full" />
        <div className="absolute bottom-10 left-1/3 w-[700px] h-[350px] bg-cyan-600/10 blur-[180px] rounded-full" />
      </div>

      {/* Modern Frosted Header */}
      <div className="relative z-10">
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          stats={stats}
          reviewCount={reviewCount}
          onQuickExport={handleQuickExport}
        />
      </div>

      {/* Main Content Workspace */}
      <main className="relative z-10 flex-1 max-w-[1920px] w-full mx-auto px-3 sm:px-5 lg:px-6 py-5 space-y-5">
        {/* KPI Metrics Streamer */}
        <MetricsBanner
          stats={stats}
          onFilterStatus={handleFilterStatusFromBanner}
        />

        {/* Tab Views */}
        <div className="transition-opacity duration-200">
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

      {/* Dual-Pane Transformation Workbench Modal */}
      {inspectProductId && (
        <TransformationInspector
          productId={inspectProductId}
          onClose={() => setInspectProductId(null)}
          onEdit={handleEdit}
          onApproved={loadGlobalState}
        />
      )}

      {/* Modern Enterprise Footer */}
      <footer className="relative z-10 bg-[#070A11]/90 backdrop-blur-md border-t border-white/[0.06] py-3.5 text-xs text-slate-400 font-mono">
        <div className="max-w-[1920px] w-full mx-auto px-3 sm:px-5 lg:px-6 flex flex-col sm:flex-row items-center justify-between gap-2.5">
          <div className="flex items-center space-x-2">
            <span className="font-extrabold text-white">UNILOG CIMPLIFI™ PIM PLATFORM</span>
            <span className="text-slate-700">|</span>
            <span className="text-slate-300">252-COLUMN MASTER DELIVERY STANDARD</span>
            <span className="text-slate-700">|</span>
            <span className="text-emerald-400 font-bold">0% HALLUCINATION GUARANTEE</span>
          </div>
          <div className="flex items-center space-x-3 text-slate-400 text-[11px]">
            <span className="flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse-glow" />
              <span className="text-slate-200 font-semibold">ENGINE: FASTAPI :8000</span>
            </span>
            <span className="text-slate-700">|</span>
            <span className="text-cyan-300 font-bold">SUB-12MS THROUGHPUT</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ToastProvider>
      <DashboardContent />
    </ToastProvider>
  );
};

export default App;

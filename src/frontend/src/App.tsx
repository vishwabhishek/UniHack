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

  // Keyboard shortcut listeners (1-5 to change tabs, Esc to close inspector)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger shortcuts if user is typing in an input or textarea
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
    showToast('Download Started', 'Exporting 1,000 items in 252-column delivery format', 'success');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased selection:bg-sky-500 selection:text-white font-sans">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        reviewCount={reviewCount}
        onQuickExport={handleQuickExport}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1920px] w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-10 py-6 space-y-6">
        {/* KPI Metrics Banner */}
        <MetricsBanner
          stats={stats}
          onFilterStatus={handleFilterStatusFromBanner}
        />

        {/* Tab Views */}
        <div className="transition-all duration-200">
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

      {/* Side-by-Side Modal Inspector */}
      {inspectProductId && (
        <TransformationInspector
          productId={inspectProductId}
          onClose={() => setInspectProductId(null)}
          onEdit={handleEdit}
          onApproved={loadGlobalState}
        />
      )}

      {/* Modern Industrial Footer */}
      <footer className="bg-slate-950 border-t border-slate-800/80 py-4 text-xs text-slate-500">
        <div className="max-w-[1920px] w-full mx-auto px-4 sm:px-6 lg:px-8 xl:px-10 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-300">UniHack PIM Intelligence</span>
            <span className="text-slate-600">•</span>
            <span>252 Target Delivery Columns</span>
            <span className="text-slate-600">•</span>
            <span>100% Deterministic Rule-Engine & AI Normalization</span>
          </div>
          <div className="flex items-center space-x-3 text-slate-400 font-mono text-[11px]">
            <span className="flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
              <span>FastAPI :8000</span>
            </span>
            <span>•</span>
            <span>React Vite Frontend</span>
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

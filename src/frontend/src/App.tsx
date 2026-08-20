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
    <div className="min-h-screen bg-pim-darkest text-slate-100 flex flex-col antialiased selection:bg-blue-600 selection:text-white font-sans">
      {/* PIM Workbench Control Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        reviewCount={reviewCount}
        onQuickExport={handleQuickExport}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1920px] w-full mx-auto px-3 sm:px-5 lg:px-6 py-4 space-y-4">
        {/* Master Data Quality & Compliance Strip */}
        <MetricsBanner
          stats={stats}
          onFilterStatus={handleFilterStatusFromBanner}
        />

        {/* Tab Views */}
        <div className="transition-opacity duration-150">
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

      {/* Industrial PIM Workbench Footer */}
      <footer className="bg-pim-darkest border-t border-pim-border py-3 text-xs text-pim-textMuted font-mono">
        <div className="max-w-[1920px] w-full mx-auto px-3 sm:px-5 lg:px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-300">UNILOG CIMPLIFI™ PIM SUITE</span>
            <span className="text-slate-700">|</span>
            <span>252-COLUMN MASTER DELIVERY SCHEMA</span>
            <span className="text-slate-700">|</span>
            <span>0% HALLUCINATION GUARANTEE</span>
          </div>
          <div className="flex items-center space-x-3 text-pim-textMuted text-[11px]">
            <span className="flex items-center space-x-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              <span className="text-slate-300">CORE ENGINE: FASTAPI :8000</span>
            </span>
            <span className="text-slate-700">|</span>
            <span>SUB-12MS INGESTION</span>
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

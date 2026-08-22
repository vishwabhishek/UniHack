import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  FileText,
  Search,
  Clock,
  Shield,
  Copy,
  Check,
  RefreshCw
} from 'lucide-react';
import { fetchExportColumns, getExportCsvUrl, getExportXlsxUrl, fetchProducts, fetchExportHistory } from '../services/api';
import { ProductListItem, ExportHistoryRecord } from '../types';
import { PageHeader } from './common/PageHeader';

export const DeliveryExporter: React.FC = () => {
  const [columnsData, setColumnsData] = useState<{
    total_columns: number;
    headers: string[];
    groups: Record<string, string[]>;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exportStatus, setExportStatus] = useState<string>('Validated');
  const [previewProducts, setPreviewProducts] = useState<ProductListItem[]>([]);
  const [activeGroup, setActiveGroup] = useState<string>('Core Identifiers (1-10)');
  const [exportHistory, setExportHistory] = useState<ExportHistoryRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState<boolean>(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  useEffect(() => {
    loadColumns();
    loadPreview();
    loadHistory();
  }, [exportStatus]);

  const loadColumns = async () => {
    try {
      const data = await fetchExportColumns();
      setColumnsData(data);
    } catch (e) {
      console.error('Failed to load columns:', e);
    }
  };

  const loadHistory = async () => {
    setHistoryLoading(true);
    try {
      const res = await fetchExportHistory(10);
      setExportHistory(res.exports || []);
    } catch (e) {
      console.error('Failed to load export history:', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  const loadPreview = async () => {
    setLoading(true);
    try {
      const data = await fetchProducts({
        page: 1,
        limit: 10,
        status: exportStatus !== 'All' ? exportStatus : undefined
      });
      setPreviewProducts(data.items);
    } catch (e) {
      console.error('Failed to load preview items:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const csvUrl = getExportCsvUrl(exportStatus);
  const xlsxUrl = getExportXlsxUrl(exportStatus);

  return (
    <div className="space-y-6 font-sans">
      
      {/* Standard Page Header */}
      <PageHeader
        title="252-Column Master Delivery Exporter"
        description="Export enriched product catalog into the certified 252-column enterprise distributor schema with CWE-1236 formula defense and SHA-256 audit traceability."
        badge={<span className="chip validated font-bold">CWE-1236 DEFENSE ON</span>}
        actions={
          <div className="flex items-center gap-2">
            <a
              href={csvUrl}
              download="unilog_252_catalog_export.csv"
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[var(--cyan)] hover:opacity-90 text-[#06201D] rounded-md text-xs font-semibold font-mono transition-opacity cursor-pointer shadow-xs"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>EXPORT 252-COL CSV</span>
            </a>
            <a
              href={xlsxUrl}
              download="unilog_252_catalog_export.xlsx"
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[var(--green-bg)] hover:opacity-90 text-[var(--green)] border border-[var(--green)] rounded-md text-xs font-semibold font-mono transition-opacity cursor-pointer shadow-xs"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>EXPORT EXCEL (.XLSX)</span>
            </a>
          </div>
        }
      />

      {/* Filter & Schema Scope Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Scope & Groups (4 cols) */}
        <div className="lg:col-span-4 bg-[var(--surface-2)] rounded-[10px] p-4.5 border border-[var(--border)] space-y-4 font-mono text-xs">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase text-[var(--text-muted)] block">
                EXPORT STATUS FILTER (DEFAULT: VALIDATED)
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {['Validated', 'All', 'Enriched', 'Flagged'].map((status) => (
                <button
                  key={status}
                  onClick={() => setExportStatus(status)}
                  className={`chip-filter cursor-pointer ${
                    exportStatus === status
                      ? 'border-[var(--cyan)] text-[var(--cyan)] bg-[var(--cyan-bg)] font-bold'
                      : ''
                  }`}
                >
                  {status.toLowerCase()}
                </button>
              ))}
            </div>
            <p className="text-[10px] text-[var(--text-muted)] font-sans mt-2">
              Enterprise delivery standard: Only human-reviewed and verified records with official manufacturer evidence are released by default.
            </p>
          </div>

          <div>
            <span className="text-[10px] font-bold uppercase text-[var(--text-muted)] block mb-2">
              COLUMN GROUPS ({columnsData?.total_columns || 252} TOTAL)
            </span>
            <div className="space-y-1">
              {columnsData &&
                Object.keys(columnsData.groups).map((grp) => (
                  <button
                    key={grp}
                    onClick={() => setActiveGroup(grp)}
                    className={`w-full text-left p-2 rounded-md transition-colors flex items-center justify-between text-xs cursor-pointer ${
                      activeGroup === grp
                        ? 'bg-[var(--surface-1)] text-[var(--cyan)] font-semibold border border-[var(--border-strong)]'
                        : 'text-[var(--text-muted)] hover:text-white'
                    }`}
                  >
                    <span className="truncate">{grp}</span>
                    <span className="text-[10px] text-[var(--text-muted)]">
                      {columnsData.groups[grp].length} cols
                    </span>
                  </button>
                ))}
            </div>
          </div>
        </div>

        {/* Right Column: Column Headers In Active Group (8 cols) */}
        <div className="lg:col-span-8 bg-[var(--surface-2)] rounded-[10px] p-4.5 border border-[var(--border)] space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
            <span className="text-[10px] font-bold uppercase text-[var(--cyan)]">
              ACTIVE GROUP: {activeGroup}
            </span>
            <span className="text-[10px] text-[var(--text-muted)]">
              {columnsData?.groups[activeGroup]?.length || 0} columns
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[400px] overflow-y-auto">
            {columnsData?.groups[activeGroup]?.map((colName, idx) => (
              <div
                key={colName}
                className="p-2 bg-[var(--surface-1)] rounded border border-[var(--border)] flex items-center gap-2"
              >
                <span className="text-[10px] text-[var(--text-muted)] w-6">{idx + 1}.</span>
                <span className="text-[var(--text-primary)] font-semibold text-xs truncate">{colName}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Export History & Cryptographic Traceability Audit */}
      <div className="bg-[var(--surface-2)] rounded-[10px] p-4.5 border border-[var(--border)] space-y-3 font-mono text-xs">
        <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-[var(--cyan)]" />
            <h3 className="font-bold text-xs uppercase tracking-wider text-[var(--text-primary)]">
              Export History &amp; Cryptographic Delivery Traceability
            </h3>
          </div>
          <button
            onClick={loadHistory}
            disabled={historyLoading}
            className="flex items-center gap-1 text-[11px] text-[var(--text-muted)] hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3 h-3 ${historyLoading ? 'animate-spin' : ''}`} />
            Refresh History
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[10px] text-[var(--text-muted)] uppercase border-b border-[var(--border)] font-semibold">
              <tr>
                <th className="py-2 px-3">Export ID</th>
                <th className="py-2 px-3">Date &amp; Time</th>
                <th className="py-2 px-3">Operator</th>
                <th className="py-2 px-3">Product Count</th>
                <th className="py-2 px-3">Filter</th>
                <th className="py-2 px-3">SHA-256 Checksum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {historyLoading ? (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-[var(--text-muted)]">
                    Loading export delivery history...
                  </td>
                </tr>
              ) : exportHistory.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-4 text-center text-[var(--text-muted)]">
                    No recorded exports yet. Downloads are logged immutably.
                  </td>
                </tr>
              ) : (
                exportHistory.map((rec) => (
                  <tr key={rec.id} className="hover:bg-[var(--surface-1)] transition-colors">
                    <td className="py-2 px-3 text-[var(--cyan)] font-bold">{rec.id}</td>
                    <td className="py-2 px-3 text-[var(--text-muted)]">
                      {new Date(rec.created_at * 1000).toLocaleString()}
                    </td>
                    <td className="py-2 px-3 text-[var(--text-primary)]">{rec.user_email}</td>
                    <td className="py-2 px-3 font-bold text-emerald-400">{rec.product_count} rows</td>
                    <td className="py-2 px-3 text-[var(--text-secondary)]">
                      {rec.filters?.status || 'Validated'}
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-[11px] text-[var(--text-muted)] truncate max-w-[140px]" title={rec.checksum_sha256}>
                          {rec.checksum_sha256?.slice(0, 16)}...
                        </span>
                        <button
                          onClick={() => handleCopyHash(rec.checksum_sha256)}
                          className="p-1 hover:bg-[var(--surface-2)] rounded text-[var(--text-muted)] hover:text-white transition-colors"
                          title="Copy SHA-256 Hash"
                        >
                          {copiedHash === rec.checksum_sha256 ? (
                            <Check className="w-3 h-3 text-emerald-400" />
                          ) : (
                            <Copy className="w-3 h-3" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};


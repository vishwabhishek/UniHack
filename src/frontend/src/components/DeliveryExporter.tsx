import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  FileText,
} from 'lucide-react';
import { fetchExportColumns, getExportCsvUrl, getExportXlsxUrl, fetchProducts } from '../services/api';
import { ProductListItem } from '../types';

export const DeliveryExporter: React.FC = () => {
  const [columnsData, setColumnsData] = useState<{
    total_columns: number;
    headers: string[];
    groups: Record<string, string[]>;
  } | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [exportStatus, setExportStatus] = useState<string>('All');
  const [previewProducts, setPreviewProducts] = useState<ProductListItem[]>([]);
  const [activeGroup, setActiveGroup] = useState<string>('Core Identifiers (1-10)');

  useEffect(() => {
    loadColumns();
    loadPreview();
  }, [exportStatus]);

  const loadColumns = async () => {
    try {
      const data = await fetchExportColumns();
      setColumnsData(data);
    } catch (e) {
      console.error('Failed to load columns:', e);
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

  const csvUrl = getExportCsvUrl(exportStatus);
  const xlsxUrl = getExportXlsxUrl(exportStatus);

  return (
    <div className="space-y-4 font-sans">
      
      {/* Header Summary */}
      <div className="p-[16px_18px] rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-mono font-semibold text-[var(--text-primary)] uppercase tracking-wider">
              252-COLUMN MASTER DELIVERY SYNDICATION EXPORTER
            </h2>
            <span className="chip validated">
              CWE-1236 FORMULA DEFENSE ON
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Export enriched product catalog into the certified 252-column enterprise distributor schema
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <a
            href={csvUrl}
            download="unilog_252_catalog_export.csv"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[var(--cyan)] hover:opacity-90 text-[#06201D] rounded-md text-xs font-semibold font-mono transition-opacity cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>EXPORT 252-COL CSV</span>
          </a>
          <a
            href={xlsxUrl}
            download="unilog_252_catalog_export.xlsx"
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[var(--green-bg)] hover:opacity-90 text-[var(--green)] border border-[var(--green)] rounded-md text-xs font-semibold font-mono transition-opacity cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>EXPORT EXCEL (.XLSX)</span>
          </a>
        </div>
      </div>

      {/* Filter & Schema Scope Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Scope & Groups (4 cols) */}
        <div className="lg:col-span-4 bg-[var(--surface-2)] rounded-[10px] p-4.5 border border-[var(--border)] space-y-4 font-mono text-xs">
          <div>
            <span className="text-[10px] font-bold uppercase text-[var(--text-muted)] block mb-2">
              EXPORT STATUS FILTER
            </span>
            <div className="flex flex-wrap gap-1.5">
              {['All', 'Validated', 'Enriched', 'Flagged'].map((status) => (
                <button
                  key={status}
                  onClick={() => setExportStatus(status)}
                  className={`chip-filter cursor-pointer ${
                    exportStatus === status
                      ? 'border-[var(--cyan)] text-[var(--cyan)] bg-[var(--cyan-bg)]'
                      : ''
                  }`}
                >
                  {status.toLowerCase()}
                </button>
              ))}
            </div>
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

    </div>
  );
};

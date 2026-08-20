import React, { useState, useEffect } from 'react';
import {
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  Layers,
  RefreshCw,
  CheckCircle2
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
    <div className="space-y-4">
      {/* Header & Export Download Banner */}
      <div className="bg-pim-panel border border-pim-border rounded p-4 shadow-sm font-mono">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 rounded bg-blue-950 border border-blue-800/50 flex items-center justify-center">
                <FileSpreadsheet className="w-4 h-4 text-blue-400" />
              </div>
              <h2 className="text-xs font-bold text-white uppercase tracking-wider">
                MASTER 252-COLUMN UNILOG DELIVERY EXPORTER & DISPATCH
              </h2>
              <span className="px-1.5 py-0.2 text-[10px] font-bold bg-blue-950 text-blue-400 border border-blue-800/50 rounded">
                252 HEADERS
              </span>
            </div>
            <p className="text-[11px] text-pim-textMuted font-sans">
              Export 100% normalized catalog records formatted to exact Unilog delivery specifications, uppercase invoice limits, and LOV attributes
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <a
              href={csvUrl}
              download="unilog_enriched_catalog_252_columns.csv"
              className="flex-1 md:flex-none flex items-center justify-center space-x-1.5 px-3.5 py-2 bg-pim-accent hover:bg-pim-accentHover text-white rounded text-xs font-bold font-mono transition-colors shadow-sm"
            >
              <Download className="w-3.5 h-3.5" />
              <span>DOWNLOAD 252-COL CSV</span>
            </a>

            <a
              href={xlsxUrl}
              download="unilog_enriched_catalog_252_columns.xlsx"
              className="flex-1 md:flex-none flex items-center justify-center space-x-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold font-mono transition-colors shadow-sm"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>DOWNLOAD EXCEL (.XLSX)</span>
            </a>
          </div>
        </div>

        {/* Filter Selection Bar */}
        <div className="flex items-center space-x-2 mt-4 pt-3 border-t border-pim-border text-xs">
          <span className="text-pim-textMuted text-[10px] uppercase font-semibold flex items-center space-x-1">
            <Filter className="w-3 h-3" />
            <span>EXPORT SCOPE:</span>
          </span>
          {['All', 'Validated', 'Enriched'].map((st) => (
            <button
              key={st}
              onClick={() => setExportStatus(st)}
              className={`px-2.5 py-0.5 rounded text-xs font-mono border transition-colors ${
                exportStatus === st
                  ? 'bg-blue-950 text-blue-400 border-blue-800 font-bold'
                  : 'bg-pim-surface text-pim-textMuted border-pim-border hover:text-white'
              }`}
            >
              {st === 'All' ? 'FULL 1,000 CATALOG' : `${st.toUpperCase()} ONLY`}
            </button>
          ))}
        </div>
      </div>

      {/* Column Groups Navigator */}
      {columnsData && (
        <div className="bg-pim-panel border border-pim-border rounded p-4 space-y-3 shadow-sm font-mono">
          <div className="flex items-center justify-between border-b border-pim-border pb-2">
            <h3 className="text-xs font-bold uppercase text-white flex items-center space-x-2">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              <span>252 DELIVERY HEADERS CATEGORIZED SCHEMA GROUPS</span>
            </h3>
            <span className="text-xs text-pim-textMuted">
              {columnsData.total_columns} TOTAL COLUMNS DEFINED
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {Object.keys(columnsData.groups).map((groupName) => (
              <button
                key={groupName}
                onClick={() => setActiveGroup(groupName)}
                className={`px-2.5 py-1 rounded text-xs font-mono border transition-colors ${
                  activeGroup === groupName
                    ? 'bg-blue-950 text-blue-400 border-blue-600 font-bold'
                    : 'bg-pim-surface text-pim-textMuted border-pim-border hover:text-white'
                }`}
              >
                {groupName} ({columnsData.groups[groupName].length})
              </button>
            ))}
          </div>

          {/* Active Group Header Pills */}
          <div className="p-2.5 bg-pim-surface rounded border border-pim-border">
            <span className="text-[10px] text-pim-textMuted uppercase font-bold block mb-1.5">
              HEADERS IN GROUP: <span className="text-white">{activeGroup}</span>
            </span>
            <div className="flex flex-wrap gap-1">
              {columnsData.groups[activeGroup]?.map((header) => (
                <span
                  key={header}
                  className="px-1.5 py-0.5 text-[10px] font-mono bg-pim-panel text-slate-300 border border-pim-border rounded"
                >
                  {header}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Export Preview Table */}
      <div className="bg-pim-panel border border-pim-border rounded p-4 space-y-3 shadow-sm font-mono">
        <div className="flex items-center justify-between border-b border-pim-border pb-2">
          <h3 className="text-xs font-bold uppercase text-white">
            SERIALIZED DELIVERY STREAM PREVIEW (FIRST 10 ROWS)
          </h3>
          <span className="text-xs text-pim-textMuted">MATCHING UNILOG SCHEMA</span>
        </div>

        <div className="overflow-x-auto border border-pim-border rounded">
          <table className="w-full text-left text-xs border-collapse font-mono">
            <thead>
              <tr className="bg-pim-darkest border-b border-pim-border text-pim-textMuted text-[10px] uppercase">
                <th className="py-2 px-3">#</th>
                <th className="py-2 px-3">MPN</th>
                <th className="py-2 px-3">BRAND</th>
                <th className="py-2 px-3">INVOICE_DESC (≤ 40)</th>
                <th className="py-2 px-3">MOBILE_DESC (60-80)</th>
                <th className="py-2 px-3">SHORT_DESC</th>
                <th className="py-2 px-3">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pim-border/60 text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-pim-textMuted">
                    <RefreshCw className="w-4 h-4 animate-spin mx-auto text-blue-400" />
                  </td>
                </tr>
              ) : (
                previewProducts.map((p) => (
                  <tr key={p.id} className="hover:bg-pim-surface">
                    <td className="py-1.5 px-3 text-pim-textMuted">{p.row_id}</td>
                    <td className="py-1.5 px-3 font-bold text-white">{p.mfg_part_number}</td>
                    <td className="py-1.5 px-3 text-blue-400 font-sans">{p.brand_name}</td>
                    <td className="py-1.5 px-3 text-emerald-300">{p.invoice_desc}</td>
                    <td className="py-1.5 px-3 text-slate-200 font-sans">{p.mobile_desc}</td>
                    <td className="py-1.5 px-3 text-slate-300 font-sans truncate max-w-xs">{p.short_desc}</td>
                    <td className="py-1.5 px-3">
                      <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/50">
                        {p.status}
                      </span>
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

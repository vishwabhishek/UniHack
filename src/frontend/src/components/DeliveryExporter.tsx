import React, { useState, useEffect } from 'react';
import {
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  Layers,
  RefreshCw,
  CheckCircle2,
  Sparkles
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
      {/* Header & Export Download Action Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-violet-500/20 shadow-glass font-mono">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-glow-violet">
                <FileSpreadsheet className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-sm font-extrabold text-white uppercase tracking-wider flex items-center space-x-2">
                  <span>MASTER 252-COLUMN UNILOG DELIVERY EXPORTER & DISPATCH</span>
                  <span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse-glow" />
                </h2>
                <span className="glow-badge-violet text-[10px] px-2 py-0.5 rounded-full font-bold">
                  252 TARGET HEADERS
                </span>
              </div>
            </div>
            <p className="text-xs text-slate-400 font-sans">
              Export 100% normalized catalog records formatted to exact Unilog delivery specifications, uppercase invoice limits, and LOV attributes
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center space-x-2.5 w-full md:w-auto">
            <a
              href={csvUrl}
              download="unilog_enriched_catalog_252_columns.csv"
              className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold font-mono shadow-glow-blue transition-all hover:scale-105"
            >
              <Download className="w-4 h-4" />
              <span>DOWNLOAD 252-COL CSV</span>
            </a>

            <a
              href={xlsxUrl}
              download="unilog_enriched_catalog_252_columns.xlsx"
              className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white rounded-xl text-xs font-bold font-mono shadow-glow-emerald transition-all hover:scale-105"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>DOWNLOAD EXCEL (.XLSX)</span>
            </a>
          </div>
        </div>

        {/* Filter Selection Bar */}
        <div className="flex items-center space-x-2 mt-5 pt-3.5 border-t border-white/[0.06] text-xs">
          <span className="text-slate-400 text-[10px] uppercase font-bold flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <span>EXPORT SCOPE:</span>
          </span>
          {['All', 'Validated', 'Enriched'].map((st) => (
            <button
              key={st}
              onClick={() => setExportStatus(st)}
              className={`px-3 py-1 rounded-xl text-xs font-mono transition-all border ${
                exportStatus === st
                  ? 'bg-blue-600/20 text-cyan-300 border-cyan-500/50 shadow-glow-cyan font-bold'
                  : 'bg-slate-950/60 text-slate-400 border-white/[0.06] hover:text-white'
              }`}
            >
              {st === 'All' ? 'FULL 1,000 CATALOG' : `${st.toUpperCase()} ONLY`}
            </button>
          ))}
        </div>
      </div>

      {/* Column Groups Navigator */}
      {columnsData && (
        <div className="glass-panel p-5 rounded-2xl space-y-3.5 border border-white/[0.08] shadow-glass font-mono">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
            <h3 className="text-xs font-bold uppercase text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-violet-400" />
              <span>252 DELIVERY HEADERS CATEGORIZED SCHEMA GROUPS</span>
            </h3>
            <span className="text-xs text-slate-400">
              {columnsData.total_columns} TOTAL COLUMNS DEFINED
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {Object.keys(columnsData.groups).map((groupName) => (
              <button
                key={groupName}
                onClick={() => setActiveGroup(groupName)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono transition-all border ${
                  activeGroup === groupName
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-glow-blue border-blue-400/40 font-bold'
                    : 'bg-slate-950/60 text-slate-400 border-white/[0.06] hover:text-white'
                }`}
              >
                {groupName} ({columnsData.groups[groupName].length})
              </button>
            ))}
          </div>

          {/* Active Group Header Pills */}
          <div className="p-3 bg-slate-950/80 rounded-xl border border-white/[0.06]">
            <span className="text-[10px] text-slate-400 uppercase font-bold block mb-2">
              HEADERS IN GROUP: <span className="text-cyan-300">{activeGroup}</span>
            </span>
            <div className="flex flex-wrap gap-1.5">
              {columnsData.groups[activeGroup]?.map((header) => (
                <span
                  key={header}
                  className="px-2 py-0.5 text-[10px] font-mono bg-slate-900 text-slate-300 border border-white/[0.06] rounded-md"
                >
                  {header}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Export Preview Table */}
      <div className="glass-panel p-5 rounded-2xl space-y-3.5 border border-white/[0.08] shadow-glass font-mono">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
          <h3 className="text-xs font-bold uppercase text-white">
            SERIALIZED DELIVERY STREAM PREVIEW (FIRST 10 ROWS)
          </h3>
          <span className="text-xs text-slate-400">MATCHING UNILOG SCHEMA</span>
        </div>

        <div className="overflow-x-auto border border-white/[0.08] rounded-xl">
          <table className="w-full text-left text-xs border-collapse font-mono">
            <thead>
              <tr className="bg-[#090D17] border-b border-white/[0.08] text-slate-400 text-[10px] uppercase">
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">MPN</th>
                <th className="py-2.5 px-3">BRAND</th>
                <th className="py-2.5 px-3">INVOICE_DESC (≤ 40)</th>
                <th className="py-2.5 px-3">MOBILE_DESC (60-80)</th>
                <th className="py-2.5 px-3">SHORT_DESC</th>
                <th className="py-2.5 px-3">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-cyan-400" />
                  </td>
                </tr>
              ) : (
                previewProducts.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/30">
                    <td className="py-2 px-3 text-slate-400">{p.row_id}</td>
                    <td className="py-2 px-3 font-bold text-white">{p.mfg_part_number}</td>
                    <td className="py-2 px-3 text-cyan-300 font-sans">{p.brand_name}</td>
                    <td className="py-2 px-3 text-emerald-300">{p.invoice_desc}</td>
                    <td className="py-2 px-3 text-slate-200 font-sans">{p.mobile_desc}</td>
                    <td className="py-2 px-3 text-slate-300 font-sans truncate max-w-xs">{p.short_desc}</td>
                    <td className="py-2 px-3">
                      <span className="glow-badge-emerald px-2 py-0.5 rounded-full text-[10px] font-bold">
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

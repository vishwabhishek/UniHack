import React, { useState, useEffect } from 'react';
import {
  Download,
  FileSpreadsheet,
  FileText,
  Table,
  CheckCircle2,
  Filter,
  Layers,
  Sparkles,
  RefreshCw
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
    <div className="space-y-6">
      {/* Header & Export Download Action Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950/40 to-slate-900 border border-slate-800 rounded-xl p-6 shadow-2xl backdrop-blur-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="w-9 h-9 rounded-lg bg-sky-500/20 border border-sky-500/30 flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5 text-sky-400" />
              </div>
              <h2 className="text-base font-bold text-white">
                Master 252-Column Unilog Delivery Exporter
              </h2>
              <span className="px-2 py-0.5 text-xs font-mono font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 rounded-full">
                252 Target Headers
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Export 100% normalized catalog records formatted to exact Unilog specifications, uppercase invoice limits, LOV attributes, and 64th fraction standards
            </p>
          </div>

          {/* Export Buttons */}
          <div className="flex items-center space-x-3 w-full md:w-auto">
            <a
              href={csvUrl}
              download="unilog_enriched_catalog_252_columns.csv"
              className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white rounded-lg text-xs font-bold shadow-lg shadow-sky-500/20 transition-all border border-sky-400/30"
            >
              <Download className="w-4 h-4" />
              <span>Download 252-Col CSV</span>
            </a>

            <a
              href={xlsxUrl}
              download="unilog_enriched_catalog_252_columns.xlsx"
              className="flex-1 md:flex-none flex items-center justify-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-lg text-xs font-bold shadow-lg shadow-emerald-500/20 transition-all border border-emerald-400/30"
            >
              <FileSpreadsheet className="w-4 h-4" />
              <span>Download Excel (.xlsx)</span>
            </a>
          </div>
        </div>

        {/* Filter Selection Bar */}
        <div className="flex items-center space-x-3 mt-5 pt-4 border-t border-slate-800/80 text-xs">
          <span className="text-slate-400 font-medium flex items-center space-x-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Export Scope Filter:</span>
          </span>
          {['All', 'Validated', 'Enriched'].map((st) => (
            <button
              key={st}
              onClick={() => setExportStatus(st)}
              className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${
                exportStatus === st
                  ? 'bg-sky-500/20 text-sky-300 border-sky-500/40 shadow-sm'
                  : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border-slate-800'
              }`}
            >
              {st === 'All' ? 'Full 1,000 Catalog Records' : `${st} Only`}
            </button>
          ))}
        </div>
      </div>

      {/* Column Groups Navigator */}
      {columnsData && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <span>252 Delivery Headers Categorized Groups</span>
            </h3>
            <span className="text-xs font-mono text-slate-400">
              {columnsData.total_columns} Total Columns Defined
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            {Object.keys(columnsData.groups).map((groupName) => (
              <button
                key={groupName}
                onClick={() => setActiveGroup(groupName)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  activeGroup === groupName
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/50 shadow-sm'
                    : 'bg-slate-950 hover:bg-slate-800 text-slate-400 border-slate-800'
                }`}
              >
                {groupName} ({columnsData.groups[groupName].length})
              </button>
            ))}
          </div>

          {/* Active Group Header Pills */}
          <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block mb-2">
              Headers in group: <span className="text-sky-300">{activeGroup}</span>
            </span>
            <div className="flex flex-wrap gap-1.5">
              {columnsData.groups[activeGroup]?.map((header) => (
                <span
                  key={header}
                  className="px-2 py-0.5 text-[11px] font-mono bg-slate-900 text-slate-300 border border-slate-800 rounded"
                >
                  {header}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Export Preview Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
            <Table className="w-4 h-4 text-purple-400" />
            <span>Export Data Live Preview (First 10 Rows)</span>
          </h3>
          <span className="text-xs text-slate-500">Live serialized stream</span>
        </div>

        <div className="overflow-x-auto border border-slate-800 rounded-lg">
          <table className="w-full text-left text-xs border-collapse font-mono">
            <thead>
              <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 text-[10px] uppercase font-semibold">
                <th className="py-2.5 px-3">#</th>
                <th className="py-2.5 px-3">MPN</th>
                <th className="py-2.5 px-3">Brand</th>
                <th className="py-2.5 px-3">INVOICE_DESC (≤ 40)</th>
                <th className="py-2.5 px-3">MOBILE_DESC (60-80)</th>
                <th className="py-2.5 px-3">SHORT_DESC</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto text-sky-400" />
                  </td>
                </tr>
              ) : (
                previewProducts.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 text-slate-500">{p.row_id}</td>
                    <td className="py-2.5 px-3 font-bold text-white">{p.mfg_part_number}</td>
                    <td className="py-2.5 px-3 font-sans text-sky-300">{p.brand_name}</td>
                    <td className="py-2.5 px-3 text-emerald-300">{p.invoice_desc}</td>
                    <td className="py-2.5 px-3 font-sans text-slate-200">{p.mobile_desc}</td>
                    <td className="py-2.5 px-3 font-sans text-slate-300 truncate max-w-xs">{p.short_desc}</td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
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

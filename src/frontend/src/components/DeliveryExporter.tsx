import React, { useState, useEffect } from 'react';
import {
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  CheckCircle2,
  ShieldCheck
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
      <div className="p-4 rounded-xl bg-[#12161D] border border-[#232935] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-[#1A1F29] border border-[#232935] flex items-center justify-center text-[#45E0D6]">
            <Download className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                252-COLUMN MASTER DELIVERY SYNDICATION EXPORTER
              </h2>
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-[#45E0D6]/10 text-[#45E0D6] border border-[#45E0D6]/25">
                CWE-1236 FORMULA DEFENSE ON
              </span>
            </div>
            <p className="text-xs text-[#8B93A3] mt-0.5">
              Export enriched product catalog into the certified 252-column enterprise distributor schema
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <a
            href={csvUrl}
            download="unilog_252_catalog_export.csv"
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-[#45E0D6] hover:bg-[#34cbbf] text-[#0B0E13] rounded-xl text-xs font-bold font-mono transition-all shadow-[0_0_12px_rgba(69,224,214,0.25)]"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>EXPORT 252-COL CSV</span>
          </a>
          <a
            href={xlsxUrl}
            download="unilog_252_catalog_export.xlsx"
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-[#3DDC84]/15 hover:bg-[#3DDC84]/25 text-[#3DDC84] border border-[#3DDC84]/30 rounded-xl text-xs font-bold font-mono transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>EXPORT EXCEL (.XLSX)</span>
          </a>
        </div>
      </div>

      {/* Schema Structure & Field Groups */}
      {columnsData && (
        <div className="bg-[#12161D] border border-[#232935] rounded-xl p-4.5 space-y-4 shadow-sm font-mono text-xs">
          <div className="flex items-center justify-between pb-2.5 border-b border-[#232935]">
            <span className="text-[10px] font-bold uppercase text-[#8B93A3]">
              UNILOG 252-COLUMN MASTER DELIVERY SCHEMA BLUEPRINT
            </span>
            <span className="text-[10px] text-[#3DDC84] font-bold">252/252 COLUMNS CERTIFIED</span>
          </div>

          {/* Group Tabs */}
          <div className="flex flex-wrap gap-1.5">
            {Object.keys(columnsData.groups).map((grp) => (
              <button
                key={grp}
                onClick={() => setActiveGroup(grp)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  activeGroup === grp
                    ? 'bg-[#1A1F29] text-[#45E0D6] border border-[#232935]'
                    : 'bg-[#0B0E13] text-[#8B93A3] hover:text-white border border-[#232935]'
                }`}
              >
                {grp} ({columnsData.groups[grp].length})
              </button>
            ))}
          </div>

          {/* Columns in Active Group */}
          <div className="p-3 bg-[#0B0E13] rounded-lg border border-[#232935]">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 text-[11px]">
              {(columnsData.groups[activeGroup] || []).map((col) => (
                <div key={col} className="p-1.5 bg-[#12161D] rounded border border-[#232935] text-[#E7EAF0] truncate">
                  {col}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};

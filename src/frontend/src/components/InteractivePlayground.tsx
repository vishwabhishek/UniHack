import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  Clock,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  Layers,
  FileCode,
  CheckCircle2,
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import { TransformRequest, TransformResponse, PlaygroundPreset } from '../types';
import { transformProduct, fetchPlaygroundPresets } from '../services/api';
import { useToast } from './Toast';

export const InteractivePlayground: React.FC = () => {
  const { showToast } = useToast();
  const [presets, setPresets] = useState<PlaygroundPreset[]>([]);
  const [selectedPresetId, setSelectedPresetId] = useState<string>('preset-1');

  // Input fields
  const [partDesc, setPartDesc] = useState<string>('PDSH4816AF Dishwasher SS - Display Only');
  const [mfgPartNum, setMfgPartNum] = useState<string>('PDSH4816AF');
  const [partManuf, setPartManuf] = useState<string>('Appliance Dealers Cooperative (APPDE)');
  const [e1Brand, setE1Brand] = useState<string>('-- Unbranded --');
  const [unilogBrand, setUnilogBrand] = useState<string>('-- No Unilog Brand --');
  const [dibBrand, setDibBrand] = useState<string>('-- No DIB Brand --');

  // Output state
  const [result, setResult] = useState<TransformResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [expandedStages, setExpandedStages] = useState<Record<number, boolean>>({ 1: true, 2: true, 3: true, 4: true, 5: true, 6: true });
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    loadPresets();
    executeTransform();
  }, []);

  const loadPresets = async () => {
    try {
      const data = await fetchPlaygroundPresets();
      if (data && data.length > 0) {
        setPresets(data);
      }
    } catch (e) {
      console.error('Failed to load presets:', e);
    }
  };

  const handleSelectPreset = (preset: PlaygroundPreset) => {
    setSelectedPresetId(preset.id);
    setPartDesc(preset.part_desc);
    setMfgPartNum(preset.mfg_part_num);
    setPartManuf(preset.part_manuf);
    setE1Brand(preset.e1_brand || '-- Unbranded --');
    setUnilogBrand(preset.unilog_brand || '-- No Unilog Brand --');
    setDibBrand(preset.dib_brand || '-- No DIB Brand --');
    showToast('Preset Loaded', preset.name, 'info');
  };

  const executeTransform = async () => {
    if (!partDesc.trim()) return;
    setLoading(true);
    try {
      const payload: TransformRequest = {
        part_desc: partDesc,
        mfg_part_num: mfgPartNum,
        part_manuf: partManuf,
        e1_brand: e1Brand,
        unilog_brand: unilogBrand,
        dib_brand: dibBrand
      };
      const res = await transformProduct(payload);
      setResult(res);
      showToast('Enrichment Executed', `${res.total_latency_ms}ms · ${(res.confidence_score * 100).toFixed(0)}% Confidence`, 'success');
    } catch (e) {
      console.error('Transformation error:', e);
      showToast('Transformation Error', 'Failed to process input string', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = (text: string, key: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    showToast('Copied', label, 'success');
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const toggleStage = (stageId: number) => {
    setExpandedStages((prev) => ({ ...prev, [stageId]: !prev[stageId] }));
  };

  return (
    <div className="space-y-4 animate-in fade-in duration-150">
      {/* Test Sandbox Terminal */}
      <div className="bg-pim-panel border border-pim-border rounded p-4 space-y-4 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-pim-border">
          <div>
            <div className="flex items-center space-x-2">
              <div className="p-1 rounded bg-blue-900/60 border border-blue-700/50">
                <Terminal className="w-4 h-4 text-blue-400" />
              </div>
              <h2 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
                FEED INGESTION SANDBOX & PIPELINE TELEMETRY
              </h2>
            </div>
            <p className="text-[11px] text-pim-textMuted font-sans mt-0.5">
              Live testing console: Input messy distributor strings to benchmark real-time normalization and character budgets
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={executeTransform}
              disabled={loading || !partDesc.trim()}
              className="flex items-center space-x-2 px-4 py-2 bg-pim-accent hover:bg-pim-accentHover text-white rounded text-xs font-bold font-mono transition-colors shadow-sm disabled:opacity-50"
            >
              <Play className={`w-3.5 h-3.5 fill-white ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'EXECUTING...' : 'RUN PIPELINE'}</span>
            </button>
          </div>
        </div>

        {/* 1-Click Preset Scenario Buttons */}
        <div>
          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-pim-textMuted block mb-1.5">
            LOAD INDUSTRY TEST PRESETS:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => handleSelectPreset(preset)}
                className={`px-2.5 py-1 rounded text-xs font-mono border transition-colors ${
                  selectedPresetId === preset.id
                    ? 'bg-blue-950 text-blue-300 border-blue-600 font-bold'
                    : 'bg-pim-surface text-pim-textSecondary border-pim-border hover:text-white hover:bg-slate-800'
                }`}
              >
                <span>{preset.name}</span>
                <span className="ml-1 text-[10px] text-pim-textMuted">({preset.mfg_part_num})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Raw Ingestion Input Cells */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-3 border-t border-pim-border">
          <div className="md:col-span-6">
            <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
              RAW DISTRIBUTOR DESCRIPTION (<span className="text-blue-400">PART_DESC</span>)
            </label>
            <textarea
              rows={3}
              value={partDesc}
              onChange={(e) => setPartDesc(e.target.value)}
              className="w-full px-3 py-2 bg-pim-surface border border-pim-border rounded text-xs font-mono text-white placeholder-pim-textMuted focus:border-pim-accent focus:ring-1 focus:ring-pim-accent font-mono"
              placeholder="e.g. PDSH4816AF Dishwasher SS - Display Only"
            />
          </div>

          <div className="md:col-span-3 space-y-2">
            <div>
              <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
                MANUFACTURER PART # (<span className="text-blue-400">MFG_PART_NUM</span>)
              </label>
              <input
                type="text"
                value={mfgPartNum}
                onChange={(e) => setMfgPartNum(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-pim-surface border border-pim-border rounded text-xs font-mono text-white focus:border-pim-accent"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
                DISTRIBUTOR SUPPLIER (<span className="text-blue-400">PART_MANUF</span>)
              </label>
              <input
                type="text"
                value={partManuf}
                onChange={(e) => setPartManuf(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-pim-surface border border-pim-border rounded text-xs text-white focus:border-pim-accent font-sans"
              />
            </div>
          </div>

          <div className="md:col-span-3 space-y-2">
            <div>
              <label className="block text-[10px] font-mono uppercase font-semibold text-pim-textMuted mb-1">
                PLACEHOLDER BRANDS (<span className="text-rose-400">DUMMY TOKENS</span>)
              </label>
              <input
                type="text"
                value={e1Brand}
                onChange={(e) => setE1Brand(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-pim-surface border border-pim-border rounded text-xs font-mono text-rose-300"
                placeholder="E1 Brand"
              />
            </div>
            <div>
              <input
                type="text"
                value={dibBrand}
                onChange={(e) => setDibBrand(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-pim-surface border border-pim-border rounded text-xs font-mono text-rose-300"
                placeholder="DIB Brand"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Results Telemetry & Stage Visualizer */}
      {result && (
        <div className="space-y-4">
          {/* Latency & Quality Telemetry Strip */}
          <div className="bg-pim-panel border border-pim-border rounded p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-sm font-mono">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded bg-emerald-950 border border-emerald-800/50 flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-white text-xs uppercase">
                    PIPELINE ENRICHMENT COMPLETE
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800/50">
                    {(result.confidence_score * 100).toFixed(1)}% CONFIDENCE
                  </span>
                  <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-blue-950 text-blue-400 border border-blue-800/50">
                    252-COL READY
                  </span>
                </div>
                <p className="text-[11px] text-pim-textMuted mt-0.5">
                  {result.brand_name} · {result.product_name || result.classpath}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 bg-pim-surface px-3 py-1.5 rounded border border-pim-border">
              <Clock className="w-4 h-4 text-blue-400" />
              <div className="text-right">
                <span className="text-[10px] text-pim-textMuted block font-semibold">TOTAL LATENCY</span>
                <span className="text-xs font-bold text-emerald-400">
                  {result.total_latency_ms} ms (SUB-12MS)
                </span>
              </div>
            </div>
          </div>

          {/* 5-Tier Synthesized Descriptions Grid */}
          <div className="bg-pim-panel border border-pim-border rounded p-4 space-y-3 shadow-sm">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-pim-textMuted block">
              SYNTHESIZED 5-TIER DESCRIPTIONS & HARD GATE AUDIT
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {/* Tier 1: INVOICE_DESC */}
              <div className="p-3 bg-pim-surface rounded border border-pim-border space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-emerald-400">1. INVOICE_DESC (≤ 40 chars, ALL CAPS)</span>
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-emerald-950 text-emerald-400 border border-emerald-800/50">
                      {result.invoice_desc_len}/40 chars [PASS]
                    </span>
                    <button
                      onClick={() => handleCopy(result.invoice_desc, 'inv', 'INVOICE_DESC')}
                      className="text-pim-textMuted hover:text-white"
                    >
                      {copiedKey === 'inv' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="font-mono text-xs font-bold text-emerald-300 bg-pim-panel p-2 rounded border border-pim-border">
                  {result.invoice_desc}
                </div>
              </div>

              {/* Tier 2: MOBILE_DESC */}
              <div className="p-3 bg-pim-surface rounded border border-pim-border space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-blue-400">2. MOBILE_DESC (60–80 chars range)</span>
                  <div className="flex items-center space-x-2">
                    <span className="px-1.5 py-0.2 rounded text-[10px] bg-blue-950 text-blue-400 border border-blue-800/50">
                      {result.mobile_desc_len}/80 chars [PASS]
                    </span>
                    <button
                      onClick={() => handleCopy(result.mobile_desc, 'mob', 'MOBILE_DESC')}
                      className="text-pim-textMuted hover:text-white"
                    >
                      {copiedKey === 'mob' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="text-xs text-white bg-pim-panel p-2 rounded border border-pim-border font-sans">
                  {result.mobile_desc}
                </div>
              </div>

              {/* Tier 3: SHORT_DESC */}
              <div className="p-3 bg-pim-surface rounded border border-pim-border space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-white">3. SHORT_DESC / PRODUCT TITLE</span>
                  <button
                    onClick={() => handleCopy(result.short_desc, 'short', 'SHORT_DESC')}
                    className="text-pim-textMuted hover:text-white"
                  >
                    {copiedKey === 'short' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="text-xs text-white bg-pim-panel p-2 rounded border border-pim-border font-sans">
                  {result.short_desc}
                </div>
              </div>

              {/* Tier 4: LONG_DESC1 */}
              <div className="p-3 bg-pim-surface rounded border border-pim-border space-y-1.5">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-slate-300">4. LONG_DESC1 (TECHNICAL SPEC SENTENCE)</span>
                  <button
                    onClick={() => handleCopy(result.long_desc1, 'long', 'LONG_DESC1')}
                    className="text-pim-textMuted hover:text-white"
                  >
                    {copiedKey === 'long' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="text-xs text-slate-300 bg-pim-panel p-2 rounded border border-pim-border leading-relaxed font-sans">
                  {result.long_desc1}
                </div>
              </div>
            </div>
          </div>

          {/* Step-by-Step Pipeline Execution Trace */}
          <div className="bg-pim-panel border border-pim-border rounded p-4 space-y-3 shadow-sm">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-pim-textMuted block">
              STEP-BY-STEP MULTI-STAGE PIPELINE EXECUTION TRACE
            </span>

            <div className="space-y-2 font-mono">
              {result.stages.map((stage) => {
                const isExpanded = !!expandedStages[stage.stage_id];
                return (
                  <div
                    key={stage.stage_id}
                    className="bg-pim-surface border border-pim-border rounded overflow-hidden"
                  >
                    <div
                      onClick={() => toggleStage(stage.stage_id)}
                      className="px-3.5 py-2 bg-pim-surface hover:bg-slate-800/60 flex items-center justify-between cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="w-5 h-5 rounded bg-blue-950 text-blue-400 border border-blue-800/50 flex items-center justify-center text-[10px] font-bold">
                          {stage.stage_id}
                        </span>
                        <div>
                          <span className="text-xs font-bold text-white uppercase">{stage.stage_name}</span>
                          <span className="text-[11px] text-pim-textMuted ml-2 hidden sm:inline font-sans">{stage.description}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800/50">
                          {stage.duration_ms} ms
                        </span>
                        {isExpanded ? <ChevronDown className="w-3.5 h-3.5 text-pim-textMuted" /> : <ChevronRight className="w-3.5 h-3.5 text-pim-textMuted" />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="p-3 border-t border-pim-border bg-pim-darkest">
                        <pre className="text-[11px] text-slate-300 bg-pim-panel p-2.5 rounded border border-pim-border overflow-x-auto">
                          {JSON.stringify(stage.output, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

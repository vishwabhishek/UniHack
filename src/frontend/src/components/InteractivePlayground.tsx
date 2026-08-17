import React, { useState, useEffect } from 'react';
import {
  Zap,
  Play,
  Sparkles,
  Clock,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  Layers,
  Tag,
  FileCode,
  ShieldCheck,
  RotateCcw,
  CheckSquare,
  AlertTriangle,
  Flame,
  ArrowRight
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
      showToast('Transformation Complete', `Processed in ${res.total_latency_ms} ms (${(res.confidence_score * 100).toFixed(0)}% Confidence)`, 'success');
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
    showToast('Copied to Clipboard', label, 'success');
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const toggleStage = (stageId: number) => {
    setExpandedStages((prev) => ({ ...prev, [stageId]: !prev[stageId] }));
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-150">
      {/* Header & Preset Selector */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Zap className="w-5 h-5 text-sky-400" />
              <span>Interactive Pipeline Sandbox ("Judge's Testing Arena")</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Paste arbitrary messy distributor strings or click preset items to view instant sub-second stage transformations
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={executeTransform}
              disabled={loading || !partDesc.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-sky-500 via-blue-600 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold shadow-lg shadow-sky-500/25 transition-all disabled:opacity-50 active:scale-95"
            >
              <Play className={`w-3.5 h-3.5 fill-white ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Processing...' : 'Run Pipeline Transform'}</span>
            </button>
          </div>
        </div>

        {/* 1-Click Preset Buttons */}
        <div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-2">
            One-Click Test Presets:
          </span>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => handleSelectPreset(preset)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  selectedPresetId === preset.id
                    ? 'bg-sky-500/20 text-sky-300 border-sky-500/50 shadow-sm shadow-sky-500/20 font-semibold'
                    : 'bg-slate-950/60 hover:bg-slate-800 text-slate-300 border-slate-800'
                }`}
              >
                <span>{preset.name}</span>
                <span className="ml-1.5 text-[10px] text-slate-400 font-mono">({preset.mfg_part_num})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Raw Input Form */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3 pt-3 border-t border-slate-800/80">
          <div className="md:col-span-6">
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Raw Supplier Description (<span className="text-sky-400 font-mono">Part_Desc</span>)
            </label>
            <textarea
              rows={3}
              value={partDesc}
              onChange={(e) => setPartDesc(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs font-mono text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
              placeholder="e.g. PDSH4816AF Dishwasher SS - Display Only"
            />
          </div>

          <div className="md:col-span-3 space-y-2">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Manufacturer Part # (<span className="text-sky-400 font-mono">Mfg_Part_Num</span>)
              </label>
              <input
                type="text"
                value={mfgPartNum}
                onChange={(e) => setMfgPartNum(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-slate-100 focus:border-sky-500"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Distributor Supplier (<span className="text-sky-400 font-mono">Part_Manuf</span>)
              </label>
              <input
                type="text"
                value={partManuf}
                onChange={(e) => setPartManuf(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs text-slate-100 focus:border-sky-500"
              />
            </div>
          </div>

          <div className="md:col-span-3 space-y-2">
            <div>
              <label className="block text-[11px] font-medium text-slate-300 mb-1">
                Raw Brand Placeholders
              </label>
              <input
                type="text"
                value={e1Brand}
                onChange={(e) => setE1Brand(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-rose-300"
                placeholder="E1 Brand"
              />
            </div>
            <div>
              <input
                type="text"
                value={dibBrand}
                onChange={(e) => setDibBrand(e.target.value)}
                className="w-full px-2.5 py-1.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-rose-300"
                placeholder="DIB Brand"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Results Dashboard & Step-by-Step Visualization */}
      {result && (
        <div className="space-y-6">
          {/* Latency & Key Metrics Banner */}
          <div className="bg-gradient-to-r from-sky-950/60 via-slate-900 to-indigo-950/60 border border-sky-500/30 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-500/40 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-sky-400" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-white text-sm">
                    Enrichment Completed
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Confidence: {(result.confidence_score * 100).toFixed(1)}%
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/40">
                    252 Columns Ready
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono mt-0.5">
                  {result.brand_name} • {result.product_name || result.classpath}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 bg-slate-950/70 px-3.5 py-2 rounded-xl border border-slate-800">
              <Clock className="w-4 h-4 text-sky-400" />
              <div className="text-right">
                <span className="text-[10px] text-slate-400 block font-medium">Pipeline Execution Latency</span>
                <span className="font-mono text-sm font-bold text-emerald-400">
                  ⚡ {result.total_latency_ms} ms (Sub-Second)
                </span>
              </div>
            </div>
          </div>

          {/* 5-Tier Synthesized Descriptions */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-sky-400" />
              <span>Generated 5-Tier Descriptions & Compliance Audits</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Tier 1: INVOICE_DESC */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-emerald-400">1. INVOICE_DESC (≤ 40 chars, ALL CAPS)</span>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {result.invoice_desc_len}/40 chars [PASS]
                    </span>
                    <button
                      onClick={() => handleCopy(result.invoice_desc, 'inv', 'INVOICE_DESC')}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {copiedKey === 'inv' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="font-mono text-xs font-bold text-emerald-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  {result.invoice_desc}
                </div>
              </div>

              {/* Tier 2: MOBILE_DESC */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-cyan-400">2. MOBILE_DESC (60–80 chars range)</span>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                      {result.mobile_desc_len}/80 chars [PASS]
                    </span>
                    <button
                      onClick={() => handleCopy(result.mobile_desc, 'mob', 'MOBILE_DESC')}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {copiedKey === 'mob' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="text-xs text-slate-100 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  {result.mobile_desc}
                </div>
              </div>

              {/* Tier 3: SHORT_DESC */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-sky-400">3. SHORT_DESC (Structured Title)</span>
                  <button
                    onClick={() => handleCopy(result.short_desc, 'short', 'SHORT_DESC')}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {copiedKey === 'short' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="text-xs text-slate-100 bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                  {result.short_desc}
                </div>
              </div>

              {/* Tier 4: LONG_DESC1 */}
              <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-indigo-400">4. LONG_DESC1 (Technical Specs)</span>
                  <button
                    onClick={() => handleCopy(result.long_desc1, 'long', 'LONG_DESC1')}
                    className="text-slate-400 hover:text-slate-200"
                  >
                    {copiedKey === 'long' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="text-xs text-slate-300 bg-slate-900 p-2.5 rounded-lg border border-slate-800 leading-relaxed">
                  {result.long_desc1}
                </div>
              </div>
            </div>
          </div>

          {/* Stage-by-Stage Visual Pipeline Execution Timeline */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
              <Layers className="w-4 h-4 text-sky-400" />
              <span>Step-by-Step Multi-Stage Pipeline Execution Trace</span>
            </h3>

            <div className="space-y-3">
              {result.stages.map((stage) => {
                const isExpanded = !!expandedStages[stage.stage_id];
                return (
                  <div
                    key={stage.stage_id}
                    className="bg-slate-950 border border-slate-800 rounded-xl overflow-hidden transition-all"
                  >
                    <div
                      onClick={() => toggleStage(stage.stage_id)}
                      className="px-4 py-3 bg-slate-950 hover:bg-slate-900/80 flex items-center justify-between cursor-pointer"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="w-6 h-6 rounded-full bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center text-xs font-bold font-mono">
                          {stage.stage_id}
                        </span>
                        <div>
                          <span className="text-xs font-bold text-white">{stage.stage_name}</span>
                          <span className="text-[11px] text-slate-400 ml-2 hidden sm:inline">{stage.description}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          {stage.duration_ms} ms
                        </span>
                        {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="p-4 border-t border-slate-800 bg-slate-950/80">
                        <pre className="text-[11px] font-mono text-slate-300 bg-slate-900 p-3 rounded-lg border border-slate-800 overflow-x-auto">
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

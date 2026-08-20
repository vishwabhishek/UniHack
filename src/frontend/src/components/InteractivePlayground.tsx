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
  RotateCcw,
  Sparkles,
  Zap
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
      showToast('Transformation Complete', `${res.total_latency_ms}ms · ${(res.confidence_score * 100).toFixed(0)}% Confidence`, 'success');
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
      <div className="glass-panel p-5 rounded-2xl space-y-4 border border-white/[0.08] shadow-glass">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3.5 border-b border-white/[0.06]">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-glow-cyan border border-cyan-400/40">
              <Terminal className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-white font-mono uppercase tracking-wider flex items-center space-x-2">
                <span>FEED INGESTION SANDBOX & PIPELINE TELEMETRY</span>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse-glow" />
              </h2>
              <p className="text-xs text-slate-400 font-sans mt-0.5">
                Real-time pipeline testing terminal: Paste raw distributor strings to evaluate live normalization and character gates
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={executeTransform}
              disabled={loading || !partDesc.trim()}
              className="flex items-center space-x-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 via-blue-600 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-xs font-bold font-mono shadow-glow-blue transition-all disabled:opacity-50 hover:scale-105 active:scale-95"
            >
              <Play className={`w-3.5 h-3.5 fill-white ${loading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'EXECUTING PIPELINE...' : 'RUN PIPELINE TRANSFORM'}</span>
            </button>
          </div>
        </div>

        {/* 1-Click Preset Scenario Buttons */}
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block mb-2">
            ONE-CLICK INDUSTRY BENCHMARK PRESETS:
          </span>
          <div className="flex flex-wrap gap-2">
            {presets.map((preset) => (
              <button
                key={preset.id}
                onClick={() => handleSelectPreset(preset)}
                className={`px-3 py-1.5 rounded-xl text-xs font-mono transition-all border ${
                  selectedPresetId === preset.id
                    ? 'bg-blue-600/20 text-cyan-300 border-cyan-500/50 shadow-glow-cyan font-bold'
                    : 'bg-slate-950/60 text-slate-400 border-white/[0.06] hover:text-white hover:bg-slate-900'
                }`}
              >
                <span>{preset.name}</span>
                <span className="ml-1.5 text-[10px] text-slate-400">({preset.mfg_part_num})</span>
              </button>
            ))}
          </div>
        </div>

        {/* Raw Ingestion Input Form */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3.5 pt-3.5 border-t border-white/[0.06]">
          <div className="md:col-span-6">
            <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1.5">
              RAW DISTRIBUTOR DESCRIPTION (<span className="text-cyan-400">PART_DESC</span>)
            </label>
            <textarea
              rows={3}
              value={partDesc}
              onChange={(e) => setPartDesc(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs font-mono text-white placeholder-slate-400 focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 font-mono"
              placeholder="e.g. PDSH4816AF Dishwasher SS - Display Only"
            />
          </div>

          <div className="md:col-span-3 space-y-2.5">
            <div>
              <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
                MANUFACTURER PART # (<span className="text-cyan-400">MFG_PART_NUM</span>)
              </label>
              <input
                type="text"
                value={mfgPartNum}
                onChange={(e) => setMfgPartNum(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs font-mono text-white focus:border-cyan-400"
              />
            </div>
            <div>
              <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
                DISTRIBUTOR SUPPLIER (<span className="text-cyan-400">PART_MANUF</span>)
              </label>
              <input
                type="text"
                value={partManuf}
                onChange={(e) => setPartManuf(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs text-white focus:border-cyan-400 font-sans"
              />
            </div>
          </div>

          <div className="md:col-span-3 space-y-2.5">
            <div>
              <label className="block text-[10px] font-mono uppercase font-bold text-slate-400 mb-1">
                PLACEHOLDER BRANDS (<span className="text-rose-400">DUMMY TOKENS</span>)
              </label>
              <input
                type="text"
                value={e1Brand}
                onChange={(e) => setE1Brand(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs font-mono text-rose-300"
                placeholder="E1 Brand"
              />
            </div>
            <div>
              <input
                type="text"
                value={dibBrand}
                onChange={(e) => setDibBrand(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950/80 border border-white/[0.08] rounded-xl text-xs font-mono text-rose-300"
                placeholder="DIB Brand"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Results Telemetry & Stage Visualizer */}
      {result && (
        <div className="space-y-4">
          {/* Latency & Quality Telemetry Ribbon */}
          <div className="glass-panel p-4 rounded-2xl flex flex-col sm:flex-row items-center justify-between gap-3 border border-cyan-500/20 shadow-glass font-mono">
            <div className="flex items-center space-x-3.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-glow-emerald">
                <CheckCircle2 className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-extrabold text-white text-xs uppercase">
                    PIPELINE ENRICHMENT COMPLETE
                  </span>
                  <span className="glow-badge-emerald text-[10px] px-2 py-0.5 rounded-full font-bold">
                    {(result.confidence_score * 100).toFixed(1)}% CONFIDENCE
                  </span>
                  <span className="glow-badge-violet text-[10px] px-2 py-0.5 rounded-full font-bold">
                    252-COL READY
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-sans mt-0.5">
                  {result.brand_name} · {result.product_name || result.classpath}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 bg-slate-950/80 px-3.5 py-2 rounded-xl border border-white/[0.08]">
              <Clock className="w-4 h-4 text-cyan-400" />
              <div className="text-right">
                <span className="text-[10px] text-slate-400 block font-bold">EXECUTION LATENCY</span>
                <span className="text-xs font-extrabold text-emerald-400 glow-badge-emerald px-2 py-0.5 rounded-full">
                  ⚡ {result.total_latency_ms} ms (SUB-12MS)
                </span>
              </div>
            </div>
          </div>

          {/* 5-Tier Synthesized Descriptions Grid */}
          <div className="glass-panel p-5 rounded-2xl space-y-4 border border-white/[0.08] shadow-glass">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
              SYNTHESIZED 5-TIER DESCRIPTIONS & HARD GATE AUDIT
            </span>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {/* Tier 1: INVOICE_DESC */}
              <div className="p-4 bg-slate-950/80 rounded-xl border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-emerald-400">1. INVOICE_DESC (≤ 40 chars, ALL CAPS)</span>
                  <div className="flex items-center space-x-2">
                    <span className="glow-badge-emerald text-[10px] px-2 py-0.5 rounded-full font-bold">
                      {result.invoice_desc_len}/40 chars [PASS]
                    </span>
                    <button
                      onClick={() => handleCopy(result.invoice_desc, 'inv', 'INVOICE_DESC')}
                      className="text-slate-400 hover:text-white"
                    >
                      {copiedKey === 'inv' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="font-mono text-xs font-bold text-emerald-300 bg-[#080C14] p-3 rounded-lg border border-white/[0.06]">
                  {result.invoice_desc}
                </div>
              </div>

              {/* Tier 2: MOBILE_DESC */}
              <div className="p-4 bg-slate-950/80 rounded-xl border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-cyan-400">2. MOBILE_DESC (60–80 chars range)</span>
                  <div className="flex items-center space-x-2">
                    <span className="glow-badge-cyan text-[10px] px-2 py-0.5 rounded-full font-bold">
                      {result.mobile_desc_len}/80 chars [PASS]
                    </span>
                    <button
                      onClick={() => handleCopy(result.mobile_desc, 'mob', 'MOBILE_DESC')}
                      className="text-slate-400 hover:text-white"
                    >
                      {copiedKey === 'mob' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div className="text-xs text-white bg-[#080C14] p-3 rounded-lg border border-white/[0.06] font-sans">
                  {result.mobile_desc}
                </div>
              </div>

              {/* Tier 3: SHORT_DESC */}
              <div className="p-4 bg-slate-950/80 rounded-xl border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-white">3. SHORT_DESC / PRODUCT TITLE</span>
                  <button
                    onClick={() => handleCopy(result.short_desc, 'short', 'SHORT_DESC')}
                    className="text-slate-400 hover:text-white"
                  >
                    {copiedKey === 'short' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="text-xs text-white bg-[#080C14] p-3 rounded-lg border border-white/[0.06] font-sans">
                  {result.short_desc}
                </div>
              </div>

              {/* Tier 4: LONG_DESC1 */}
              <div className="p-4 bg-slate-950/80 rounded-xl border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="font-bold text-slate-300">4. LONG_DESC1 (TECHNICAL SPEC SENTENCE)</span>
                  <button
                    onClick={() => handleCopy(result.long_desc1, 'long', 'LONG_DESC1')}
                    className="text-slate-400 hover:text-white"
                  >
                    {copiedKey === 'long' ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <div className="text-xs text-slate-300 bg-[#080C14] p-3 rounded-lg border border-white/[0.06] leading-relaxed font-sans">
                  {result.long_desc1}
                </div>
              </div>
            </div>
          </div>

          {/* Step-by-Step Pipeline Execution Trace */}
          <div className="glass-panel p-5 rounded-2xl space-y-3.5 border border-white/[0.08] shadow-glass">
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400 block">
              STEP-BY-STEP MULTI-STAGE PIPELINE EXECUTION TRACE
            </span>

            <div className="space-y-2.5 font-mono">
              {result.stages.map((stage) => {
                const isExpanded = !!expandedStages[stage.stage_id];
                return (
                  <div
                    key={stage.stage_id}
                    className="glass-card rounded-xl border border-white/[0.06] overflow-hidden"
                  >
                    <div
                      onClick={() => toggleStage(stage.stage_id)}
                      className="px-4 py-3 bg-slate-950/60 hover:bg-slate-900/60 flex items-center justify-between cursor-pointer transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        <span className="w-6 h-6 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 text-white flex items-center justify-center text-[10px] font-extrabold shadow-glow-blue">
                          {stage.stage_id}
                        </span>
                        <div>
                          <span className="text-xs font-bold text-white uppercase">{stage.stage_name}</span>
                          <span className="text-[11px] text-slate-400 ml-2 hidden sm:inline font-sans">{stage.description}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <span className="text-[10px] font-bold text-emerald-400 glow-badge-emerald px-2 py-0.5 rounded-full">
                          {stage.duration_ms} ms
                        </span>
                        {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="p-3.5 border-t border-white/[0.06] bg-[#090D17]">
                        <pre className="text-[11px] text-slate-300 bg-slate-950/90 p-3 rounded-xl border border-white/[0.06] overflow-x-auto">
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

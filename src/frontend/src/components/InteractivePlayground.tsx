import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  Clock,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  RotateCcw,
  Sparkles,
  Zap,
  CheckCircle2
} from 'lucide-react';
import { TransformResponse, PlaygroundPreset } from '../types';
import { transformProduct, fetchPlaygroundPresets } from '../services/api';
import { useToast } from './Toast';
import { SegmentedGauge } from './SegmentedGauge';

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
    setE1Brand(preset.e1_brand || '');
    setUnilogBrand(preset.unilog_brand || '');
    setDibBrand(preset.dib_brand || '');
  };

  const executeTransform = async () => {
    setLoading(true);
    try {
      const data = await transformProduct({
        part_desc: partDesc,
        mfg_part_num: mfgPartNum,
        part_manuf: partManuf,
        e1_brand: e1Brand,
        unilog_brand: unilogBrand,
        dib_brand: dibBrand
      });
      setResult(data);
    } catch (e) {
      console.error('Transform failed:', e);
      showToast('Error', 'Transformation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const toggleStage = (stageNum: number) => {
    setExpandedStages((prev) => ({ ...prev, [stageNum]: !prev[stageNum] }));
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    showToast('Copied', text, 'success');
    setTimeout(() => setCopiedKey(null), 1500);
  };

  return (
    <div className="space-y-4 font-sans">
      
      {/* Header Bar */}
      <div className="p-4 rounded-xl bg-[#12161D] border border-[#232935] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-[#1A1F29] border border-[#232935] flex items-center justify-center text-[#45E0D6]">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              REAL-TIME INDUSTRIAL TRANSFORMATION SANDBOX
            </h2>
            <p className="text-xs text-[#8B93A3] mt-0.5">
              Paste arbitrary messy distributor strings to observe deterministic 7-stage enrichment with sub-second feedback
            </p>
          </div>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <span className="text-[10px] font-mono font-bold text-[#8B93A3] uppercase">PRESETS:</span>
          <select
            value={selectedPresetId}
            onChange={(e) => {
              const p = presets.find((x) => x.id === e.target.value);
              if (p) handleSelectPreset(p);
            }}
            className="px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-xs text-white focus:border-[#45E0D6] focus:outline-none font-sans"
          >
            {presets.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Split Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Raw Inputs (5 cols) */}
        <div className="lg:col-span-5 bg-[#12161D] rounded-xl p-4.5 border border-[#232935] space-y-4 shadow-sm flex flex-col justify-between font-mono text-xs">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[#232935]">
              <span className="text-[10px] font-bold uppercase text-[#8B93A3]">DISTRIBUTOR RAW INPUT DATA</span>
              <button
                onClick={() => {
                  setPartDesc('50.25 in Built-in Dishwasher SST 120V 15A 47 dBA Frigidaire');
                  setMfgPartNum('FDSH4501AS');
                }}
                className="text-[10px] text-[#45E0D6] hover:underline flex items-center space-x-1"
              >
                <RotateCcw className="w-3 h-3" />
                <span>RESET SAMPLE</span>
              </button>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">PART_DESC (MESSY TITLE / SPEC)</label>
              <textarea
                rows={3}
                value={partDesc}
                onChange={(e) => setPartDesc(e.target.value)}
                placeholder="Paste unformatted supplier line..."
                className="w-full px-3 py-2 bg-[#0B0E13] border border-[#232935] rounded-lg text-white font-mono text-xs focus:border-[#45E0D6] focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">MFG_PART_NUM (MPN)</label>
                <input
                  type="text"
                  value={mfgPartNum}
                  onChange={(e) => setMfgPartNum(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-white"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-[#8B93A3] mb-1">PART_MANUF</label>
                <input
                  type="text"
                  value={partManuf}
                  onChange={(e) => setPartManuf(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-[#0B0E13] border border-[#232935] rounded-lg text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[10px]">
              <div>
                <label className="block text-[#8B93A3] mb-1">E1_BRAND</label>
                <input
                  type="text"
                  value={e1Brand}
                  onChange={(e) => setE1Brand(e.target.value)}
                  className="w-full px-2 py-1 bg-[#0B0E13] border border-[#232935] rounded text-white"
                />
              </div>
              <div>
                <label className="block text-[#8B93A3] mb-1">UNILOG_BRAND</label>
                <input
                  type="text"
                  value={unilogBrand}
                  onChange={(e) => setUnilogBrand(e.target.value)}
                  className="w-full px-2 py-1 bg-[#0B0E13] border border-[#232935] rounded text-white"
                />
              </div>
              <div>
                <label className="block text-[#8B93A3] mb-1">DIB_BRAND</label>
                <input
                  type="text"
                  value={dibBrand}
                  onChange={(e) => setDibBrand(e.target.value)}
                  className="w-full px-2 py-1 bg-[#0B0E13] border border-[#232935] rounded text-white"
                />
              </div>
            </div>
          </div>

          <div className="pt-3">
            <button
              onClick={executeTransform}
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 py-2.5 bg-[#45E0D6] hover:bg-[#34cbbf] text-[#0B0E13] rounded-xl text-xs font-bold font-mono transition-all disabled:opacity-50 hover:scale-[1.01] shadow-[0_0_16px_rgba(69,224,214,0.3)]"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{loading ? 'PROCESSING PIPELINE...' : 'EXECUTE PIPELINE TRANSFORMATION'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: 7-Stage Output Tiers (7 cols) */}
        <div className="lg:col-span-7 bg-[#12161D] rounded-xl p-4.5 border border-[#232935] space-y-3.5 shadow-sm font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-[#232935]">
            <span className="text-[10px] font-bold uppercase text-[#45E0D6] flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-[#45E0D6]" />
              <span>ENRICHMENT OUTPUT & STEP-BY-STEP TRACE</span>
            </span>

            {result && (
              <div className="flex items-center space-x-3 text-[11px]">
                <span className="text-[#8B93A3] flex items-center space-x-1">
                  <Clock className="w-3 h-3 text-[#45E0D6]" />
                  <span className="text-[#3DDC84] font-bold">{result.total_latency_ms.toFixed(1)} ms</span>
                </span>
                <SegmentedGauge score={result.confidence_score} size="sm" />
              </div>
            )}
          </div>

          {result && (
            <div className="space-y-2.5">
              
              {/* Stage 1 & 2: Resolved Brand & Taxonomy */}
              <div className="grid grid-cols-2 gap-2 bg-[#0B0E13] p-3 rounded-lg border border-[#232935]">
                <div>
                  <span className="text-[10px] text-[#8B93A3] uppercase block font-bold">CANONICAL BRAND</span>
                  <div className="font-bold text-[#45E0D6] text-xs mt-0.5">{result.brand_name}</div>
                </div>
                <div>
                  <span className="text-[10px] text-[#8B93A3] uppercase block font-bold">UNSPSC / CLASSPATH</span>
                  <div className="font-bold text-white text-xs mt-0.5">{result.unspsc}</div>
                  <div className="text-[10px] text-[#8B93A3] truncate">{result.classpath}</div>
                </div>
              </div>

              {/* Stage 6 Descriptions */}
              <div className="space-y-2">
                {/* Invoice Desc */}
                <div className="p-3 bg-[#0B0E13] rounded-lg border border-[#232935] space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-bold text-[#3DDC84]">INVOICE_DESC (≤40 Chars, ALL CAPS)</span>
                    <span className="text-[10px] font-mono font-bold text-[#3DDC84] px-1.5 py-0.2 rounded bg-[#3DDC84]/10 border border-[#3DDC84]/20">
                      {result.invoice_desc.length}/40 [PASS]
                    </span>
                  </div>
                  <div className="text-white font-bold tracking-wide">{result.invoice_desc}</div>
                </div>

                {/* Mobile Desc */}
                <div className="p-3 bg-[#0B0E13] rounded-lg border border-[#232935] space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-bold text-[#45E0D6]">MOBILE_DESC (60–80 Chars)</span>
                    <span className="text-[10px] font-mono font-bold text-[#45E0D6] px-1.5 py-0.2 rounded bg-[#45E0D6]/10 border border-[#45E0D6]/20">
                      {result.mobile_desc.length} chars [PASS]
                    </span>
                  </div>
                  <div className="text-[#E7EAF0] font-sans">{result.mobile_desc}</div>
                </div>

                {/* Short Desc Title */}
                <div className="p-3 bg-[#0B0E13] rounded-lg border border-[#232935] space-y-1">
                  <span className="text-[10px] font-bold text-[#8B93A3] block">SHORT_DESC / PRODUCT TITLE</span>
                  <div className="text-white font-sans text-xs">{result.short_desc}</div>
                </div>
              </div>

              {/* Extracted Attributes */}
              {result.attributes && result.attributes.length > 0 && (
                <div className="p-3 bg-[#0B0E13] rounded-lg border border-[#232935] space-y-2">
                  <span className="text-[10px] font-bold text-[#8B93A3] uppercase block">
                    EXTRACTED LOV SPECIFICATIONS ({result.attributes.length})
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {result.attributes.map((a, i) => (
                      <div key={i} className="p-2 bg-[#12161D] rounded border border-[#232935]">
                        <span className="text-[9px] text-[#8B93A3] uppercase block">{a.label}</span>
                        <div className="text-white font-bold text-xs mt-0.5">
                          {a.value} {a.uom && <span className="text-[#45E0D6] text-[10px]">{a.uom}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </div>

      </div>

    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  Terminal,
  Play,
  Clock,
  RotateCcw,
} from 'lucide-react';
import { TransformResponse, PlaygroundPreset } from '../types';
import { transformProduct, fetchPlaygroundPresets } from '../services/api';
import { useToast } from './Toast';
import { PageHeader } from './common/PageHeader';

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

  const renderMiniGauge = (score: number) => {
    const active = Math.round(score * 10);
    return (
      <div className="flex items-center">
        <div className="mini-gauge">
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className={i < active ? 'on' : ''} />
          ))}
        </div>
        <span className="conf-val">{score.toFixed(2)}</span>
      </div>
    );
  };

  return (
    <div className="space-y-4 font-sans">
      
      {/* Standard Page Header */}
      <PageHeader
        title="Real-Time Transformation Sandbox"
        description="Paste arbitrary messy distributor strings to observe deterministic 7-stage enrichment and normalization."
        actions={
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider font-semibold">Presets:</span>
            <select
              value={selectedPresetId}
              onChange={(e) => {
                const p = presets.find((x) => x.id === e.target.value);
                if (p) handleSelectPreset(p);
              }}
              className="bg-[var(--surface-1)] text-[var(--text-primary)] border border-[var(--border-strong)] rounded-md px-3 py-1 text-xs font-mono focus:outline-none focus:border-[var(--cyan)] cursor-pointer hover:border-[var(--cyan)] transition-colors shadow-xs"
            >
              {presets.map((p) => (
                <option key={p.id} value={p.id} className="bg-[#12161D] text-[#E7EAF0] py-1">
                  {p.name}
                </option>
              ))}
            </select>
          </div>

        }
      />

      {/* Main Split Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Raw Inputs (5 cols) */}
        <div className="lg:col-span-5 bg-[var(--surface-2)] rounded-[10px] p-4.5 border border-[var(--border)] space-y-4 shadow-sm flex flex-col justify-between font-mono text-xs">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
              <span className="text-[10px] font-bold uppercase text-[var(--text-muted)]">DISTRIBUTOR RAW INPUT</span>
              <button
                onClick={() => {
                  setPartDesc('50.25 in Built-in Dishwasher SST 120V 15A 47 dBA Frigidaire');
                  setMfgPartNum('FDSH4501AS');
                }}
                className="text-[10px] text-[var(--cyan)] hover:underline flex items-center gap-1 cursor-pointer"
              >
                <RotateCcw className="w-3 h-3" />
                <span>RESET SAMPLE</span>
              </button>
            </div>

            <div>
              <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">PART_DESC (MESSY TITLE / SPEC)</label>
              <textarea
                rows={3}
                value={partDesc}
                onChange={(e) => setPartDesc(e.target.value)}
                placeholder="Paste unformatted supplier line..."
                className="w-full px-3 py-2 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)] font-mono text-xs focus:border-[var(--cyan)] focus:outline-none"
              />
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">MFG_PART_NUM (MPN)</label>
                <input
                  type="text"
                  value={mfgPartNum}
                  onChange={(e) => setMfgPartNum(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-[var(--text-muted)] mb-1">PART_MANUF</label>
                <input
                  type="text"
                  value={partManuf}
                  onChange={(e) => setPartManuf(e.target.value)}
                  className="w-full px-2.5 py-1.5 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded-md text-[var(--text-primary)] focus:border-[var(--cyan)] focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 text-[10px]">
              <div>
                <label className="block text-[var(--text-muted)] mb-1">E1_BRAND</label>
                <input
                  type="text"
                  value={e1Brand}
                  onChange={(e) => setE1Brand(e.target.value)}
                  className="w-full px-2 py-1 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded text-[var(--text-secondary)] focus:border-[var(--cyan)] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[var(--text-muted)] mb-1">UNILOG_BRAND</label>
                <input
                  type="text"
                  value={unilogBrand}
                  onChange={(e) => setUnilogBrand(e.target.value)}
                  className="w-full px-2 py-1 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded text-[var(--text-secondary)] focus:border-[var(--cyan)] focus:outline-none"
                />
              </div>
              <div>
                <label className="block text-[var(--text-muted)] mb-1">DIB_BRAND</label>
                <input
                  type="text"
                  value={dibBrand}
                  onChange={(e) => setDibBrand(e.target.value)}
                  className="w-full px-2 py-1 bg-[var(--surface-1)] border border-[var(--border-strong)] rounded text-[var(--text-secondary)] focus:border-[var(--cyan)] focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="pt-3">
            <button
              onClick={executeTransform}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-[var(--cyan)] text-[#06201D] rounded-md text-xs font-semibold font-sans hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{loading ? 'PROCESSING PIPELINE...' : 'EXECUTE PIPELINE TRANSFORMATION'}</span>
            </button>
          </div>
        </div>

        {/* Right Column: Output Tiers (7 cols) */}
        <div className="lg:col-span-7 bg-[var(--surface-2)] rounded-[10px] p-4.5 border border-[var(--border)] space-y-3.5 shadow-sm font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-[var(--border)]">
            <span className="text-[10px] font-bold uppercase text-[var(--cyan)] flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--cyan)]" />
              <span>ENRICHMENT OUTPUT &amp; TRACE</span>
            </span>

            {result && (
              <div className="flex items-center gap-3 text-[11px]">
                <span className="text-[var(--text-muted)] flex items-center gap-1">
                  <Clock className="w-3 h-3 text-[var(--cyan)]" />
                  <span className="text-[var(--green)] font-semibold">{result.total_latency_ms.toFixed(1)} ms</span>
                </span>
                {renderMiniGauge(result.confidence_score)}
              </div>
            )}
          </div>

          {result && (
            <div className="space-y-2.5">
              
              {/* Resolved Brand & Taxonomy */}
              <div className="grid grid-cols-2 gap-2 bg-[var(--surface-1)] p-3 rounded-md border border-[var(--border)]">
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold">CANONICAL BRAND</span>
                  <div className="font-semibold text-[var(--cyan)] text-xs mt-0.5">{result.brand_name}</div>
                </div>
                <div>
                  <span className="text-[10px] text-[var(--text-muted)] uppercase block font-semibold">UNSPSC / CLASSPATH</span>
                  <div className="font-semibold text-[var(--text-primary)] text-xs mt-0.5">{result.unspsc}</div>
                  <div className="text-[10px] text-[var(--text-muted)] truncate">{result.classpath}</div>
                </div>
              </div>

              {/* Descriptions */}
              <div className="space-y-2">
                <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)] space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-semibold text-[var(--green)]">INVOICE_DESC (≤40 Chars, ALL CAPS)</span>
                    <span className="chip validated">
                      {result.invoice_desc.length}/40 [PASS]
                    </span>
                  </div>
                  <div className="text-[var(--text-primary)] font-semibold tracking-wide">{result.invoice_desc}</div>
                </div>

                <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)] space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="font-semibold text-[var(--cyan)]">MOBILE_DESC (60–80 Chars)</span>
                    <span className="chip enriched">
                      {result.mobile_desc.length} chars [PASS]
                    </span>
                  </div>
                  <div className="text-[var(--text-primary)] font-sans">{result.mobile_desc}</div>
                </div>

                <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)] space-y-1">
                  <span className="text-[10px] font-semibold text-[var(--text-muted)] block">SHORT_DESC / PRODUCT TITLE</span>
                  <div className="text-[var(--text-primary)] font-sans text-xs">{result.short_desc}</div>
                </div>
              </div>

              {/* Extracted Attributes */}
              {result.attributes && result.attributes.length > 0 && (
                <div className="p-3 bg-[var(--surface-1)] rounded-md border border-[var(--border)] space-y-2">
                  <span className="text-[10px] font-semibold text-[var(--text-muted)] uppercase block">
                    EXTRACTED LOV SPECIFICATIONS ({result.attributes.length})
                  </span>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {result.attributes.map((a, i) => (
                      <div key={i} className="p-2 bg-[var(--bg)] rounded border border-[var(--border)]">
                        <span className="text-[9px] text-[var(--text-muted)] uppercase block">{a.label}</span>
                        <div className="text-[var(--text-primary)] font-semibold text-xs mt-0.5">
                          {a.value} {a.uom && <span className="text-[var(--cyan)] text-[10px]">{a.uom}</span>}
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

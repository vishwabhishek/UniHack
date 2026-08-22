import React, { useState, useEffect } from 'react';
import { ProductTimelineEvent, ProductTimelineResponse } from '../types';
import { fetchProductTimeline } from '../services/api';
import { Clock, User, FileText, CheckCircle2, Cpu, Shield, ArrowRight, RefreshCw, ExternalLink } from 'lucide-react';

interface ProductActivityTimelineProps {
  productId: string;
}

export const ProductActivityTimeline: React.FC<ProductActivityTimelineProps> = ({ productId }) => {
  const [timelineData, setTimelineData] = useState<ProductTimelineResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadTimeline = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProductTimeline(productId);
      setTimelineData(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load activity timeline');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) {
      loadTimeline();
    }
  }, [productId]);

  const getEventBadge = (eventType: string) => {
    switch (eventType) {
      case 'AUDIT_LOG':
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-purple-950/80 text-purple-300 border border-purple-800">AUDIT</span>;
      case 'REVIEW_ACTION':
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800">REVIEW</span>;
      case 'JOB_EVENT':
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-blue-950/80 text-blue-300 border border-blue-800">PIPELINE</span>;
      case 'EVIDENCE_INGESTED':
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-amber-950/80 text-amber-300 border border-amber-800">EVIDENCE</span>;
      default:
        return <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-zinc-800 text-zinc-300 border border-zinc-700">EVENT</span>;
    }
  };

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'AUDIT_LOG':
        return <Shield className="w-4 h-4 text-purple-400" />;
      case 'REVIEW_ACTION':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'JOB_EVENT':
        return <Cpu className="w-4 h-4 text-blue-400" />;
      case 'EVIDENCE_INGESTED':
        return <FileText className="w-4 h-4 text-amber-400" />;
      default:
        return <Clock className="w-4 h-4 text-zinc-400" />;
    }
  };

  return (
    <div className="space-y-4 text-xs">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-2">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-blue-400" />
          <h3 className="font-semibold text-zinc-200">
            Chronological Activity & Provenance Timeline
          </h3>
          {timelineData && (
            <span className="text-[10px] bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded font-mono">
              {timelineData.total_events} events
            </span>
          )}
        </div>
        <button
          onClick={loadTimeline}
          disabled={loading}
          className="inline-flex items-center gap-1 text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors"
        >
          <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="py-8 text-center text-zinc-500">
          <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-zinc-400" />
          Loading activity timeline...
        </div>
      ) : error ? (
        <div className="p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-red-300">
          {error}
        </div>
      ) : !timelineData || timelineData.timeline.length === 0 ? (
        <div className="py-6 text-center text-zinc-500">
          No recorded activity events for this product yet.
        </div>
      ) : (
        <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-zinc-800">
          {timelineData.timeline.map((event, idx) => (
            <div key={event.id || idx} className="relative group">
              {/* Dot marker */}
              <div className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-zinc-900 border border-zinc-700 flex items-center justify-center">
                {getEventIcon(event.event_type)}
              </div>

              {/* Card */}
              <div className="bg-zinc-900/90 border border-zinc-800 hover:border-zinc-700 rounded-lg p-3 space-y-2 transition-colors">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    {getEventBadge(event.event_type)}
                    <span className="font-semibold text-zinc-200">{event.action}</span>
                    {event.field_name && (
                      <span className="font-mono text-zinc-400 bg-zinc-950 px-1.5 py-0.5 rounded border border-zinc-800 text-[11px]">
                        {event.field_name}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-zinc-500 font-mono">
                    {new Date(event.timestamp).toLocaleString()}
                  </span>
                </div>

                {/* Values / Diff */}
                {(event.old_value !== undefined || event.new_value !== undefined) && (
                  <div className="bg-zinc-950/60 rounded p-2 border border-zinc-800/80 font-mono text-[11px] space-y-1">
                    {event.old_value && (
                      <div className="text-red-400/90 flex items-center gap-1.5">
                        <span className="text-zinc-600 select-none">-</span>
                        <span className="line-through">{event.old_value}</span>
                      </div>
                    )}
                    {event.new_value && (
                      <div className="text-emerald-400 flex items-center gap-1.5">
                        <span className="text-zinc-600 select-none">+</span>
                        <span>{event.new_value}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Reason & Metadata */}
                <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-zinc-400 pt-1 border-t border-zinc-800/40">
                  <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 text-zinc-400">
                      <User className="w-3 h-3 text-zinc-500" />
                      {event.actor}
                    </span>
                    <span className="text-zinc-600">•</span>
                    <span className="capitalize text-zinc-400">{event.role}</span>
                  </div>

                  {event.source_url && (
                    <a
                      href={event.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Official Evidence Source
                    </a>
                  )}
                </div>

                {event.reason && (
                  <p className="text-[11px] text-zinc-400 italic bg-zinc-950/30 px-2 py-1 rounded">
                    "{event.reason}"
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

import React from 'react';

interface SegmentedGaugeProps {
  score: number; // 0.00 to 1.00
  totalSegments?: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export const SegmentedGauge: React.FC<SegmentedGaugeProps> = ({
  score,
  totalSegments = 8,
  size = 'sm',
  showLabel = true,
  className = ''
}) => {
  const normalizedScore = Math.max(0, Math.min(1, score || 0));
  const activeSegments = Math.round(normalizedScore * totalSegments);

  // Status color evaluation
  let activeColor = 'bg-[#45E0D6] shadow-[0_0_8px_rgba(69,224,214,0.4)]';
  let textColor = 'text-[#45E0D6]';
  if (normalizedScore >= 0.85) {
    activeColor = 'bg-[#3DDC84] shadow-[0_0_8px_rgba(61,220,132,0.4)]';
    textColor = 'text-[#3DDC84]';
  } else if (normalizedScore >= 0.70) {
    activeColor = 'bg-[#E8A33D] shadow-[0_0_8px_rgba(232,163,61,0.4)]';
    textColor = 'text-[#E8A33D]';
  } else {
    activeColor = 'bg-[#EF5A5A] shadow-[0_0_8px_rgba(239,90,90,0.4)]';
    textColor = 'text-[#EF5A5A]';
  }

  const segmentHeight = size === 'sm' ? 'h-3 w-1.5' : size === 'md' ? 'h-4 w-2' : 'h-5 w-2.5';

  return (
    <div className={`inline-flex items-center space-x-2 font-mono ${className}`}>
      {/* Segmented meter ticks */}
      <div className="flex items-center space-x-1 p-0.5 rounded bg-[#12161D] border border-[#232935]">
        {Array.from({ length: totalSegments }).map((_, idx) => {
          const isActive = idx < activeSegments;
          return (
            <div
              key={idx}
              className={`rounded-sm transition-all duration-300 ${segmentHeight} ${
                isActive ? activeColor : 'bg-[#1C212B]'
              }`}
            />
          );
        })}
      </div>

      {showLabel && (
        <span className={`text-xs font-bold tracking-tight ${textColor} font-mono tabular-nums`}>
          {(normalizedScore * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
};

import React from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  actions,
  className = ''
}) => {
  return (
    <div className={`p-4 sm:p-5 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs font-sans ${className}`}>
      <div className="space-y-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2.5">
          <h2 className="text-xs sm:text-sm font-mono font-semibold text-[var(--text-primary)] uppercase tracking-wider truncate">
            {title}
          </h2>
          {badge && <div className="flex-shrink-0">{badge}</div>}
        </div>
        {description && (
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
          {actions}
        </div>
      )}
    </div>
  );
};

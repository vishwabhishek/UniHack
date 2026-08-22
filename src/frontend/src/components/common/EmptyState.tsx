import React from 'react';
import { HelpCircle } from 'lucide-react';

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon = HelpCircle,
  title,
  description,
  action,
  className = ''
}) => {
  return (
    <div className={`p-8 sm:p-12 rounded-[10px] bg-[var(--surface-2)] border border-[var(--border)] text-center space-y-3 font-sans ${className}`}>
      <div className="w-10 h-10 rounded-full bg-[var(--surface-1)] border border-[var(--border-strong)] text-[var(--cyan)] flex items-center justify-center mx-auto shadow-xs">
        <Icon className="w-5 h-5" />
      </div>
      <div className="space-y-1 max-w-md mx-auto">
        <h3 className="text-xs sm:text-sm font-mono font-semibold text-[var(--text-primary)] uppercase tracking-wider">
          {title}
        </h3>
        {description && (
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
};

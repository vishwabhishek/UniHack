import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'warning' | 'info' | 'error';

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type?: ToastType;
}

interface ToastContextValue {
  showToast: (title: string, description?: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const showToast = useCallback((title: string, description?: string, type: ToastType = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, description, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col space-y-2 max-w-sm w-full pointer-events-none font-sans">
        {toasts.map((toast) => {
          let borderStyle = 'border-[var(--border-strong)]';
          let iconColor = 'text-[var(--cyan)]';
          let Icon = Info;

          if (toast.type === 'success') {
            borderStyle = 'border-[var(--green)]';
            iconColor = 'text-[var(--green)]';
            Icon = CheckCircle2;
          } else if (toast.type === 'warning') {
            borderStyle = 'border-[var(--amber)]';
            iconColor = 'text-[var(--amber)]';
            Icon = AlertTriangle;
          } else if (toast.type === 'error') {
            borderStyle = 'border-[var(--red)]';
            iconColor = 'text-[var(--red)]';
            Icon = AlertTriangle;
          }

          return (
            <div
              key={toast.id}
              className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-lg border ${borderStyle} bg-[var(--surface-2)] shadow-2xl backdrop-blur-md transition-all font-sans`}
            >
              <Icon className={`w-4 h-4 flex-shrink-0 mt-0.5 ${iconColor}`} />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-[var(--text-primary)] leading-tight">{toast.title}</p>
                {toast.description && (
                  <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-snug">{toast.description}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-[var(--text-muted)] hover:text-white p-0.5 rounded transition-colors cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextValue => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

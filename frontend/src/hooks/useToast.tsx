import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { CheckCircle2, AlertCircle, X, Info } from 'lucide-react';
import { cn } from '../lib/utils/cn';

type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message: string;
}

interface ToastContextType {
  toast: (type: ToastType, title: string, message: string) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const toast = useCallback((type: ToastType, title: string, message: string) => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts(prev => [...prev, { id, type, title, message }]);
    
    // Auto remove after 5 seconds
    setTimeout(() => removeToast(id), 5000);
  }, [removeToast]);

  return (
    <ToastContext.Provider value={{ toast, removeToast }}>
      {children}
      <div className="fixed top-6 right-6 z-[200] flex flex-col gap-3 w-full max-w-sm pointer-events-none">
        {toasts.map(t => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto w-full glass-card p-4 flex items-start gap-4 animate-in slide-in-from-right-full duration-500 shadow-2xl border",
              t.type === 'success' && "border-emerald-500/20 bg-emerald-500/[0.02]",
              t.type === 'error' && "border-rose-500/20 bg-rose-500/[0.02]",
              t.type === 'info' && "border-blue-500/20 bg-blue-500/[0.02]"
            )}
          >
            <div className={cn(
              "shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border",
              t.type === 'success' && "bg-emerald-500/10 border-emerald-500/20 text-emerald-500",
              t.type === 'error' && "bg-rose-500/10 border-rose-500/20 text-rose-500",
              t.type === 'info' && "bg-blue-500/10 border-blue-500/20 text-blue-500"
            )}>
              {t.type === 'success' && <CheckCircle2 className="w-5 h-5" />}
              {t.type === 'error' && <AlertCircle className="w-5 h-5" />}
              {t.type === 'info' && <Info className="w-5 h-5" />}
            </div>
            
            <div className="flex-1 min-w-0">
              <p className="font-bold text-sm tracking-tight">{t.title}</p>
              <p className="text-xs text-zinc-500 font-medium leading-relaxed mt-0.5">{t.message}</p>
            </div>

            <button
              onClick={() => removeToast(t.id)}
              className="p-1 hover:bg-black/5 rounded-md transition-colors text-zinc-400 hover:text-black"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};

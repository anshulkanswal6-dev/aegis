import { X, AlertCircle } from 'lucide-react';
import { Button } from './UIPack';
import { cn } from '../../lib/utils/cn';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  variant?: 'danger' | 'primary';
}

export function ConfirmationModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isLoading = false,
  variant = 'primary'
}: ConfirmationModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[150] flex items-center justify-center p-6 bg-black/5 backdrop-blur-md animate-in fade-in duration-200">
      <div className="max-w-md w-full p-8 rounded-2xl border border-[#eeeeee] bg-white shadow-2xl space-y-8 relative overflow-hidden group">
        <button
          onClick={onClose}
          className="absolute right-6 top-6 p-2 rounded-lg text-zinc-300 hover:text-black hover:bg-zinc-50 transition-all active:scale-95"
        >
          <X className="w-4 h-4" />
        </button>

        <div className="flex items-center gap-5 border-b border-[#f5f5f5] pb-6">
          <div className={cn(
            "w-12 h-12 rounded-xl flex items-center justify-center shadow-sm border",
            variant === 'danger' ? "bg-rose-50 border-rose-100 text-rose-500" : "bg-zinc-50 border-zinc-100 text-black"
          )}>
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="space-y-0.5">
            <h2 className="text-sm font-bold text-black tracking-tight">{title}</h2>
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-none">Authorization Required</p>
          </div>
        </div>

        <p className="text-xs text-zinc-500 font-medium leading-relaxed tracking-tight">
          {message}
        </p>

        <div className="flex gap-3 pt-6 border-t border-[#f5f5f5]">
          <Button
            onClick={onClose}
            variant="outline"
            className="flex-1 h-11 rounded-xl text-xs font-bold"
          >
            {cancelText}
          </Button>
          <Button
            onClick={onConfirm}
            isLoading={isLoading}
            variant={variant}
            className="flex-1 h-11 rounded-xl text-xs font-bold shadow-lg shadow-black/5"
          >
            {confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}


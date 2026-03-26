import type { TerminalLog } from '../../types/terminal';
import { ExternalLink, CheckCircle, Info, Loader2, XCircle, Wallet, ArrowUpRight } from 'lucide-react';
import { cn } from '../../lib/utils/cn';

export function TerminalLogLine({ log }: { log: TerminalLog }) {
  const IconMap = {
    info: Info,
    wallet: Wallet,
    pending: Loader2,
    success: CheckCircle,
    error: XCircle,
    explorer: ArrowUpRight,
  };

  const Icon = IconMap[log.type as keyof typeof IconMap] || Info;

  const colors = {
    info: 'text-zinc-400',
    wallet: 'text-blue-600',
    pending: 'text-amber-600',
    success: 'text-emerald-600',
    error: 'text-rose-600',
    explorer: 'text-indigo-600',
  }[log.type as keyof typeof IconMap] || 'text-zinc-400';

  const timeString = new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return (
    <div className="flex gap-2.5 py-1.5 px-3 font-mono text-[9.5px] border-b border-black/[0.01] hover:bg-black/[0.02] transition-all group items-center">
      <span className="text-zinc-300 shrink-0 select-none tabular-nums">[{timeString}]</span>
      <Icon className={cn("w-3.5 h-3.5 shrink-0", colors, log.type === 'pending' && "animate-spin")} strokeWidth={3} />
      
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <span className={cn("uppercase text-[8px] font-bold shrink-0 w-12 select-none text-right tracking-widest", colors)}>
          {log.type}
        </span>
        <span className="text-zinc-500 truncate tracking-tight font-medium">{log.message}</span>
        
        {log.txHash && !log.explorerUrl && (
          <span className="text-[8px] text-zinc-300 truncate font-bold ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
            H: {log.txHash.slice(0, 10)}...
          </span>
        )}

        {log.explorerUrl && (
          <a 
            href={log.explorerUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="ml-auto flex items-center gap-1 text-[8px] font-bold text-indigo-600 hover:text-indigo-700 transition-all bg-indigo-50/50 px-2 py-0.5 rounded border border-indigo-100 shadow-sm"
          >
            EXPLORE
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
        )}
      </div>
    </div>
  );
}


import { useTerminalStore } from '../../store/terminalStore';
import { TerminalLogLine } from './TerminalLogLine';
import { Trash2, ChevronDown, ChevronUp, Activity } from 'lucide-react';
import { useEffect, useRef } from 'react';
import { cn } from '../../lib/utils/cn';

export function TerminalDrawer() {
  const { logs, clearLogs, isExpanded, toggleExpanded } = useTerminalStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isExpanded) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isExpanded]);

  return (
    <div 
      className={cn(
        "fixed bottom-6 left-[25%] right-[25%] z-[60] transition-all duration-300 ease-in-out border border-[#eeeeee] bg-white shadow-xl rounded-xl overflow-hidden",
        isExpanded ? "h-64 translate-y-0" : "h-11 translate-y-0 hover:bg-zinc-50"
      )}
    >
      {/* Header Area */}
      <div 
        className="flex items-center justify-between px-5 h-11 cursor-pointer select-none border-b border-[#f5f5f5] group"
        onClick={toggleExpanded}
      >
        <div className="flex items-center gap-3">
          <Activity className={cn("w-4 h-4 transition-all duration-300", logs.some(l => l.type === 'pending') ? "text-black animate-pulse" : "text-zinc-400 group-hover:text-black")} />
          <span className="text-[11px] font-bold text-zinc-400 group-hover:text-black uppercase tracking-wider transition-colors">
            Activity Logs {logs.length > 0 && `(${logs.length})`}
          </span>
          {logs.some(l => l.type === 'pending') && (
            <div className="flex items-center gap-2 ml-2">
              <span className="w-1.5 h-1.5 rounded-full bg-black animate-ping" />
              <span className="text-[9px] font-bold text-black uppercase tracking-widest">Running</span>
            </div>
          )}
        </div>

        
        <div className="flex items-center gap-4">
          <button 
            onClick={(e) => { e.stopPropagation(); clearLogs(); }}
            className="p-1.5 text-zinc-300 hover:text-rose-500 transition-all hover:bg-rose-50 rounded"
            title="Clear Console"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-zinc-100" />
          <div className="p-1 rounded text-zinc-400 group-hover:text-black transition-all">
             {isExpanded ? (
               <ChevronDown className="w-4 h-4" />
             ) : (
               <ChevronUp className="w-4 h-4" />
             )}
          </div>
        </div>
      </div>

      {/* Narrative Region */}
      {isExpanded && (
        <div className="h-[calc(100%-44px)] overflow-y-auto custom-scrollbar bg-black/[0.02]">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-zinc-300 font-medium italic text-xs uppercase tracking-widest">
               No recent activity
            </div>
          ) : (
            <div className="p-4 space-y-1 font-mono">
              {logs.map((log) => (
                <TerminalLogLine key={log.id} log={log} />
              ))}
              <div ref={bottomRef} className="h-4" />
            </div>
          )}
        </div>
      )}
    </div>
  );
}


import { Trash2, Activity, ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils/cn';
import { usePlaygroundStore } from '../../store/playgroundStore';
import { useEffect, useRef } from 'react';

interface TerminalPanelProps {
  onClose?: () => void;
}

export function TerminalPanel({ onClose }: TerminalPanelProps) {
  const { 
    terminalLogs, 
    automationLogs,
    activeBottomTab,
    status, 
    clearWorkspace 
  } = usePlaygroundStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const logsToDisplay = activeBottomTab === 'automation' ? automationLogs : terminalLogs;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logsToDisplay]);

  return (
    <div className="flex-1 flex flex-col bg-white overflow-hidden scroll-smooth">
      {/* Terminal Header */}
      <div className="h-11 px-6 flex items-center justify-between border-b border-[#f5f5f5] bg-white shrink-0">
         <div className="flex items-center gap-3">
            <Activity className={cn(
              "w-4 h-4 transition-all duration-300", 
              activeBottomTab === 'automation' ? "text-emerald-500" :
               status === 'generating_code' || status === 'understanding' || status === 'analyzing' ? "text-black animate-pulse" : "text-zinc-400"
            )} />
            <span className="text-[11px] font-black text-black uppercase tracking-widest">
              {activeBottomTab === 'automation' ? 'Automation Activity' : 'System Activity'} 
              {logsToDisplay.length > 0 && ` (${logsToDisplay.length})`}
            </span>
         </div>
         <div className="flex items-center gap-4">
            <button 
               onClick={clearWorkspace}
               className="p-1 px-2 rounded hover:bg-[#F5F5F5] flex items-center gap-1.5 transition-colors group"
            >
               <Trash2 className="w-3 h-3 text-zinc-300 group-hover:text-rose-500 transition-colors" />
               <span className="text-[9px] font-black uppercase tracking-widest text-zinc-400 group-hover:text-rose-600 transition-colors">Clear Workspace</span>
            </button>
            {onClose && (
              <>
                <div className="w-px h-4 bg-zinc-100" />
                <button onClick={onClose} className="p-1 rounded hover:bg-[#F5F5F5] transition-colors text-zinc-400 hover:text-black">
                   <ChevronDown className="w-4 h-4" />
                </button>
              </>
            )}
         </div>
      </div>

      {/* Terminal Content */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 font-mono text-[11px] leading-relaxed custom-scrollbar bg-white"
      >
         <div className="space-y-1">
            {logsToDisplay.map((log: string, idx: number) => (
               <div key={idx} className="flex gap-4 group animate-in slide-in-from-left-2 duration-300">
                  <span className="text-zinc-300 w-10 shrink-0 text-right selection:hidden tabular-nums font-bold">
                     {activeBottomTab === 'automation' ? 'evt' : `$${idx + 1}`}
                  </span>
                  <p className={cn(
                    "font-bold",
                    log.includes('[Internal]') || log.includes('[System]') ? "text-blue-500" :
                    log.includes('Success') || log.includes('OK') ? "text-emerald-500" :
                    log.includes('CRITICAL') || log.includes('ERROR') ? "text-rose-500" :
                    "text-black opacity-80"
                  )}>{log}</p>
               </div>
            ))}
            {activeBottomTab !== 'automation' && (
              <div className="flex gap-4 pt-1">
                 <span className="text-[#FF4D4D] w-10 shrink-0 text-right font-black selection:hidden">$</span>
                 <div className="w-1 h-4 bg-black opacity-20 rounded-sm" />
              </div>
            )}
         </div>
      </div>
    </div>
  );
}

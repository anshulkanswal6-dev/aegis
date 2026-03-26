import { useAccount } from 'wagmi';
import { useAgentWallet } from '../../hooks/useAgentWallet';
import { Bot, ArrowRight, ShieldCheck, Zap } from 'lucide-react';
import { Button } from '../ui/UIPack';
import { useState, useEffect } from 'react';

export function CreateAgentWalletPanel() {
  const { isConnected, address } = useAccount();
  const { createWallet, isCreating } = useAgentWallet();
  const [executor, setExecutor] = useState('');
  const [limit, setLimit] = useState('0.1');

  useEffect(() => {
    if (address && !executor) setExecutor(address);
  }, [address, executor]);

  const handleCreate = () => {
    if (!address || !executor || !limit) return;
    createWallet(executor, limit);
  };

  if (!isConnected) return null;

  return (
    <div className="p-8 bg-white border border-[#eeeeee] rounded-2xl shadow-sm space-y-8 relative overflow-hidden group hover:border-[#dadada] transition-all">
      <div className="flex items-center gap-4 pb-6 border-b border-[#f5f5f5]">
        <div className="w-10 h-10 rounded-xl bg-black flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
          <Bot className="w-5 h-5" />
        </div>
        <div className="space-y-0.5">
          <h2 className="text-sm font-bold text-black uppercase tracking-wider">Initialize Node</h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-none">Agent Cluster Deployment</p>
        </div>
      </div>

      <div className="space-y-6">
         <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase text-zinc-400 tracking-wider ml-1">Executor Signature</label>
            <input 
              type="text" 
              value={executor}
              onChange={(e) => setExecutor(e.target.value)}
              placeholder="0x..."
              className="w-full h-12 bg-zinc-50 border border-[#eeeeee] rounded-xl px-5 text-sm text-black font-bold placeholder:text-zinc-300 outline-none focus:bg-white focus:border-black transition-all font-mono shadow-inner"
            />
         </div>

         <div className="space-y-2">
            <label className="text-[10px] font-bold uppercase text-zinc-400 tracking-wider ml-1">Daily Resource Quota (BNB)</label>
            <div className="relative group/input">
              <input 
                type="number" 
                step="0.01"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
                placeholder="0.1"
                className="w-full h-12 bg-zinc-50 border border-[#eeeeee] rounded-xl px-5 text-sm text-black font-bold placeholder:text-zinc-300 outline-none focus:bg-white focus:border-black transition-all font-mono shadow-inner"
              />
              <div className="absolute right-5 top-1/2 -translate-y-1/2 text-[10px] font-bold text-zinc-300 tracking-widest pointer-events-none group-focus-within/input:text-black transition-colors">BNB/DAY</div>
            </div>
         </div>
      </div>

      <div className="space-y-4">
        <Button
          onClick={handleCreate}
          isLoading={isCreating}
          className="w-full h-12 rounded-xl bg-black text-white font-bold text-xs shadow-lg hover:translate-y-[-1px] active:translate-y-0 transition-all flex items-center justify-center gap-2"
          disabled={!executor || !limit}
        >
          Deploy Cluster Node <ArrowRight className="w-4 h-4" />
        </Button>

        <div className="grid grid-cols-2 gap-3">
           <div className="flex items-center gap-2 justify-center py-2.5 rounded-xl bg-zinc-50 border border-[#eeeeee]">
              <ShieldCheck className="w-3.5 h-3.5 text-zinc-300" />
              <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">P2P Verified</span>
           </div>
           <div className="flex items-center gap-2 justify-center py-2.5 rounded-xl bg-zinc-50 border border-[#eeeeee]">
              <Zap className="w-3.5 h-3.5 text-zinc-300" />
              <span className="text-[9px] font-bold uppercase tracking-widest text-zinc-400">Zero-Sync</span>
           </div>
        </div>
      </div>
    </div>
  );
}


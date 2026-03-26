import { useAgentWallet } from '../../hooks/useAgentWallet';
import { Bot, ExternalLink, Copy, Check, RefreshCw, ShieldCheck, Database } from 'lucide-react';
import { formatAddress } from '../../lib/utils/format';
import { getExplorerUrl } from '../../lib/utils/explorer';
import { useChainId } from 'wagmi';
import { useState, useEffect } from 'react';
import { cn } from '../../lib/utils/cn';
import { Button } from '../ui/UIPack';
import type { Address } from 'viem';

export function AgentWalletCard() {
  const { 
    agentWalletAddress, formatBalance, refetchBalance, chainSymbol,
    authorizePlatformExecutor, getExecutor 
  } = useAgentWallet();
  const chainId = useChainId();
  const [copied, setCopied] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [currentExecutor, setCurrentExecutor] = useState<Address | null>(null);
  const [platformAddress, setPlatformAddress] = useState<Address | null>(null);
  const [isAuthorizing, setIsAuthorizing] = useState(false);

  useEffect(() => {
    const init = async () => {
      if (!agentWalletAddress) return;
      const [executor, resp] = await Promise.all([
        getExecutor(),
        fetch('http://localhost:8002/automations/executor/address').then(r => r.json()).catch(() => ({ address: null }))
      ]);
      setCurrentExecutor(executor);
      setPlatformAddress(resp.address);
    };
    init();
  }, [agentWalletAddress, refreshing]);

  const isPlatformAuthorized = platformAddress && currentExecutor && platformAddress?.toLowerCase() === currentExecutor?.toLowerCase();

  const handleCopy = () => {
    if (!agentWalletAddress) return;
    navigator.clipboard.writeText(agentWalletAddress);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetchBalance();
    setTimeout(() => setRefreshing(false), 800);
  };

  const handleAuthorize = async () => {
    setIsAuthorizing(true);
    try {
      await authorizePlatformExecutor();
      setRefreshing(true);
      setTimeout(() => setRefreshing(false), 500);
    } finally {
      setIsAuthorizing(false);
    }
  };

  if (!agentWalletAddress) return null;

  return (
    <div className="p-6 bg-white border border-[#eeeeee] rounded-2xl shadow-sm space-y-6 relative overflow-hidden group">
      
      <div className="flex items-center justify-between pb-6 border-b border-[#f5f5f5] relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-black flex items-center justify-center text-white shadow-md">
            <Bot className="w-5 h-5" />
          </div>
          <div className="space-y-0.5">
            <h3 className="text-xs font-bold text-black uppercase tracking-wider">Proxy Node</h3>
            <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-none">On-chain Signature</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-emerald-50 rounded-full border border-emerald-100 text-emerald-600 text-[10px] font-bold uppercase tracking-wider">
            <ShieldCheck className="w-3 h-3" />
            {isPlatformAuthorized ? 'Platform Authorized' : 'Active'}
        </div>
      </div>

      <div className="space-y-4 relative z-10">
        {/* Deployed Address Matrix */}
        <div className="p-4 rounded-xl border border-[#eeeeee] bg-zinc-50 group/sub transition-all hover:bg-white relative overflow-hidden">
           <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider flex items-center gap-2">
                <Database className="w-3 h-3 opacity-40" />
                Wallet Address
              </span>
              <div className="flex items-center gap-1.5 opacity-40 group-hover/sub:opacity-100 transition-all">
                <button 
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg text-zinc-400 hover:text-black hover:bg-zinc-100 transition-all active:scale-95"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
                <a 
                   href={getExplorerUrl(chainId, agentWalletAddress, 'address')} 
                   target="_blank" 
                   rel="noopener noreferrer"
                   className="p-1.5 rounded-lg text-zinc-400 hover:text-black hover:bg-zinc-100 transition-all active:scale-95"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              </div>
           </div>
           <span className="font-mono text-black text-xs font-bold block truncate tracking-tight">
             {formatAddress(agentWalletAddress!)}
           </span>
        </div>

        {/* Tactical Balance Unit - High Density */}
        <div className="p-6 rounded-xl bg-zinc-50 border border-[#eeeeee] transition-all hover:bg-white active:scale-[0.98] shadow-sm relative overflow-hidden group/bal cursor-pointer" onClick={handleRefresh}>
           <div className="flex items-center justify-between mb-3 relative z-10">
              <span className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider">Available Balance</span>
              <div className={cn("text-zinc-400 hover:text-black transition-colors", refreshing && 'animate-spin')}>
                <RefreshCw className="w-3.5 h-3.5" />
              </div>
           </div>
           <div className="flex items-baseline gap-2 relative z-10">
            <span className="text-3xl font-bold tabular-nums tracking-tighter text-black transition-all duration-700">{formatBalance}</span>
            <span className="text-xs text-zinc-400 font-bold uppercase tracking-wider">{chainSymbol}</span>
         </div>
        </div>

        {!isPlatformAuthorized && platformAddress && (
          <Button
            onClick={handleAuthorize}
            isLoading={isAuthorizing}
            className="w-full h-11 bg-black text-white rounded-xl font-bold text-[10px] uppercase tracking-widest shadow-md hover:bg-zinc-800 transition-all flex items-center justify-center gap-2"
          >
            Authorize Platform Agent <ShieldCheck className="w-3.5 h-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}


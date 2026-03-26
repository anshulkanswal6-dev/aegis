import { useState } from 'react';
import { useAgentWallet } from '../../hooks/useAgentWallet';
import { ArrowUpRight, Info, ArrowLeftRight } from 'lucide-react';
import { Button } from '../ui/UIPack';

export function WithdrawFundsPanel() {
  const [amount, setAmount] = useState('0.1');
  const { withdraw, isWithdrawing, chainSymbol } = useAgentWallet();

  const handleWithdraw = async () => {
    if (!amount || isNaN(Number(amount)) || Number(amount) <= 0) return;
    await withdraw(amount);
  };

  return (
    <div className="p-8 bg-white border border-[#eeeeee] rounded-2xl shadow-sm space-y-8 relative overflow-hidden group hover:border-[#dadada] transition-all">
      <div className="flex items-center gap-4 pb-6 border-b border-[#f5f5f5]">
        <div className="w-10 h-10 rounded-xl bg-zinc-50 border border-[#eeeeee] flex items-center justify-center text-black shadow-sm group-hover:scale-105 transition-transform">
          <ArrowLeftRight className="w-5 h-5" />
        </div>
        <div className="space-y-0.5">
          <h2 className="text-sm font-bold text-black uppercase tracking-wider">Withdraw Funds</h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-none">Move to Own Wallet</p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <label className="text-[10px] font-bold uppercase text-zinc-400 tracking-wider">Amount ({chainSymbol})</label>
          <div className="relative group/input">
             <input 
                type="number" 
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.1"
                className="w-full h-12 bg-zinc-50 border border-[#eeeeee] rounded-xl px-5 text-sm text-black font-bold placeholder:text-zinc-300 outline-none focus:bg-white focus:border-black transition-all font-mono shadow-inner"
             />
             <div className="absolute right-5 top-1/2 -translate-y-1/2 text-[10px] font-bold text-zinc-300 tracking-widest pointer-events-none group-focus-within/input:text-black transition-colors">{chainSymbol}</div>
          </div>
        </div>

        <Button
          onClick={handleWithdraw}
          isLoading={isWithdrawing}
          variant="outline"
          className="w-full h-11 rounded-xl text-[10px] font-black uppercase tracking-widest border-[#eeeeee] hover:border-black transition-all flex items-center justify-center gap-2"
        >
          Withdraw Funds <ArrowUpRight className="w-3.5 h-3.5" />
        </Button>
      </div>
      
      <div className="mt-6 flex items-start gap-4 p-4 rounded-xl bg-zinc-50 border border-[#eeeeee]">
         <div className="p-1.5 rounded-lg bg-white border border-[#eeeeee] shadow-sm">
            <Info className="w-3.5 h-3.5 text-black" />
         </div>
         <p className="text-[10px] text-zinc-500 font-bold leading-relaxed uppercase tracking-widest opacity-80">
            Transfer funds from your agent back to your connected wallet.
         </p>
      </div>
    </div>
  );
}



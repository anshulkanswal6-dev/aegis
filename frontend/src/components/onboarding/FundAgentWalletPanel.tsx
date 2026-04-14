import { useState } from 'react';
import { useAgentWallet } from '../../hooks/useAgentWallet';
import { Button } from '../ui/UIPack';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import { useThemeStore } from '../../hooks/useTheme';

export function FundAgentWalletPanel() {
  const { deposit, isFunding, chainSymbol } = useAgentWallet();
  const { resolvedTheme } = useThemeStore();
  const [amount, setAmount] = useState('0.1');

  const handleFund = () => {
    if (amount) deposit(amount);
  };

  return (
    <div className="p-8 th-surface border border-[var(--th-border-strong)] rounded-2xl shadow-sm space-y-8 relative overflow-hidden group hover:border-[var(--th-text-tertiary)] transition-all">
      <div className="flex items-center gap-4 pb-6 border-b border-[var(--th-border)]">
        <div className="w-12 h-12 flex items-center justify-center text-3xl shrink-0">
          💰
        </div>
        <div className="space-y-0.5">
          <h2 className="text-sm font-bold th-text uppercase tracking-wider">Deposit Funds</h2>
          <p className="text-[10px] font-bold th-text-tertiary uppercase tracking-widest leading-none">Add to Balance</p>
        </div>
      </div>

      <div className="space-y-6">
        <div className="space-y-2">
          <label className="text-[10px] font-bold uppercase th-text-tertiary tracking-wider">Amount ({chainSymbol})</label>
          <div className="relative group/input">
            <input 
              type="number" 
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.1"
              className="w-full h-12 th-surface-input border border-[var(--th-border-strong)] rounded-xl px-5 text-sm th-text font-bold placeholder:th-text-tertiary outline-none focus:th-surface focus:border-blue-500 transition-all font-mono shadow-inner"
            />
            <div className="absolute right-5 top-1/2 -translate-y-1/2 text-[10px] font-bold th-text-tertiary tracking-widest pointer-events-none group-focus-within/input:th-text transition-colors">{chainSymbol}</div>
          </div>
        </div>

        <Button
          onClick={handleFund}
          isLoading={isFunding}
          className="w-full h-12 rounded-xl bg-blue-950 text-white font-bold text-xs shadow-lg hover:translate-y-[-1px] active:translate-y-0 transition-all flex items-center justify-center gap-2"
        >
          Deposit Funds <ArrowRight className="w-4 h-4" />
        </Button>

        <div className="flex items-center gap-2 justify-center py-2.5 rounded-lg th-surface-elevated border border-[var(--th-border-strong)] mt-4">
           <ShieldCheck className="w-3.5 h-3.5 th-text-tertiary" />
           <span className="text-[9px] font-bold th-text-tertiary uppercase tracking-widest">Secure Payment</span>
        </div>
      </div>
    </div>
  );
}



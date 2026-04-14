import { ConnectKitButton } from 'connectkit';
import { useAccount, useChainId, useSwitchChain } from 'wagmi';
import { BRANDING } from '../../lib/config/branding';

import { Button } from '../ui/UIPack';
import { Wallet, ShieldCheck, ArrowRight } from 'lucide-react';

export function ConnectWalletCard() {
  const { isConnected, address } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();

  const isWrongChain = isConnected && address && chainId !== BRANDING.chainId;

  if (isConnected && address && !isWrongChain) return null;

  return (
    <div className="p-8 th-surface border border-[var(--th-border-strong)] rounded-2xl shadow-sm space-y-8 relative overflow-hidden group hover:border-[var(--th-text-tertiary)] transition-all">
      <div className="flex items-center gap-4 pb-6 border-b border-[var(--th-border)]">
        <div className="w-10 h-10 rounded-xl bg-blue-950 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
          <Wallet className="w-5 h-5" />
        </div>
        <div className="space-y-0.5">
          <h2 className="text-sm font-bold th-text uppercase tracking-wider">Connect Wallet</h2>
          <p className="text-[10px] font-bold th-text-tertiary uppercase tracking-widest leading-none">Identity Authorization</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-3">
          {isWrongChain ? (
            <Button
              onClick={() => switchChain({ chainId: BRANDING.chainId })}
              className="w-full h-12 rounded-xl text-[10px] font-bold uppercase tracking-widest bg-[#FF4D4D] hover:bg-rose-600 text-white transition-all flex items-center justify-center gap-2 shadow-lg shadow-rose-200 dark:shadow-rose-500/10"
            >
              Switch to {BRANDING.networkName}
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          ) : (
            <ConnectKitButton.Custom>
              {({ isConnected, show, truncatedAddress, ensName }: any) => {
                return (
                  <Button
                    onClick={show}
                    variant="outline"
                    className="w-full h-12 rounded-xl text-[10px] font-bold uppercase tracking-widest group border-[var(--th-border-strong)] hover:border-current transition-all flex items-center justify-center gap-2"
                  >
                    {isConnected ? (ensName ?? truncatedAddress) : "Connect Wallet"}
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </Button>
                );
              }}
            </ConnectKitButton.Custom>
          )}
        </div>

        <div className="flex items-center gap-2 justify-center py-2.5 rounded-lg th-surface-elevated border border-[var(--th-border-strong)] mt-4">
           <ShieldCheck className="w-3.5 h-3.5 th-text-tertiary" />
           <span className="text-[9px] font-bold th-text-tertiary uppercase tracking-widest">Auth Protocol: SECURE</span>
        </div>
      </div>
    </div>
  );
}


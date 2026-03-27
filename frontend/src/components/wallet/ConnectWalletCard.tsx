import { useConnect, useAccount, useChainId, useSwitchChain } from 'wagmi';
import { MONAD_TESTNET_ID } from '../../lib/config/chains';

import { Button } from '../ui/UIPack';
import { Wallet, ShieldCheck, ArrowRight } from 'lucide-react';

export function ConnectWalletCard() {
  const { connect, connectors, isPending } = useConnect();
  const { isConnected, address } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();

  const isWrongChain = isConnected && address && chainId !== MONAD_TESTNET_ID;

  if (isConnected && address && !isWrongChain) return null;

  return (
    <div className="p-8 bg-white border border-[#eeeeee] rounded-2xl shadow-sm space-y-8 relative overflow-hidden group hover:border-[#dadada] transition-all">
      <div className="flex items-center gap-4 pb-6 border-b border-[#f5f5f5]">
        <div className="w-10 h-10 rounded-xl bg-black flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
          <Wallet className="w-5 h-5" />
        </div>
        <div className="space-y-0.5">
          <h2 className="text-sm font-bold text-black uppercase tracking-wider">Connect Wallet</h2>
          <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest leading-none">Identity Authorization</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-3">
          {isWrongChain ? (
            <Button
              onClick={() => switchChain({ chainId: MONAD_TESTNET_ID })}
              className="w-full h-12 rounded-xl text-[10px] font-bold uppercase tracking-widest bg-[#FF4D4D] hover:bg-rose-600 text-white transition-all flex items-center justify-center gap-2 shadow-lg shadow-rose-200"
            >
              Switch to Monad Testnet
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
          ) : (
            connectors.map((connector) => (
              <Button
                key={connector.id}
                onClick={() => connect({ connector })}
                isLoading={isPending}
                variant="outline"
                className="w-full h-12 rounded-xl text-[10px] font-bold uppercase tracking-widest group border-[#eeeeee] hover:border-black transition-all flex items-center justify-center gap-2"
              >
                Sign with {connector.name}
                <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </Button>
            ))
          )}
        </div>

        <div className="flex items-center gap-2 justify-center py-2.5 rounded-lg bg-zinc-50 border border-[#eeeeee] mt-4">
           <ShieldCheck className="w-3.5 h-3.5 text-zinc-300" />
           <span className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest">Auth Protocol: SECURE</span>
        </div>
      </div>
    </div>
  );
}


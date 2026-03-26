import { useAccount } from 'wagmi';
import { cn } from '../../lib/utils/cn';
import { Bell, Search } from 'lucide-react';
import { useLayoutStore } from '../../store/layoutStore';
import { ProfileMenu } from '../account/ProfileMenu';
import { useAgentWallet } from '../../hooks/useAgentWallet';

export function Header({ title }: { title?: string }) {
  const { isConnected } = useAccount();
  const { ethBalance, formatBalance, chainSymbol } = useAgentWallet();

  return (
    <header className="h-16 px-8 border-b border-[#eeeeee] bg-white/80 backdrop-blur-md flex items-center justify-between z-40 sticky top-0 shadow-sm">
      <div className="flex items-center gap-8">
        <h2 className="text-sm font-semibold tracking-tight text-black">{title || 'Aegis Platform'}</h2>
        
        <div className="hidden lg:flex items-center gap-3 bg-zinc-50 border border-zinc-100 rounded-md px-3 h-9 w-[320px] group transition-all focus-within:ring-1 focus-within:ring-black/5">
          <Search className="w-4 h-4 text-zinc-400 group-focus-within:text-black transition-colors" />
          <input 
            type="text" 
            placeholder="Search projects or agents..." 
            className="bg-transparent border-none outline-none text-xs text-black placeholder:text-zinc-400 w-full"
          />
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Agent Wallet Balance Pill */}
        {isConnected && ethBalance !== undefined && (
          <div className="flex items-center gap-2.5 px-3 py-1.5 bg-zinc-50 border border-zinc-100 rounded-full shadow-sm hover:bg-zinc-100 transition-colors cursor-pointer group">
            <div className="w-2 h-2 rounded-full bg-black shadow-[0_0_8px_rgba(0,0,0,0.2)]" />
            <span className="text-[11px] font-bold text-black uppercase tracking-wider">
              {formatBalance} {chainSymbol}
            </span>
          </div>
        )}

        <div className="flex items-center gap-1">
           <button className="p-2 rounded-md hover:bg-zinc-50 text-zinc-400 hover:text-black transition-all active:scale-95">
              <Bell className="w-4.5 h-4.5" />
           </button>
        </div>

        <div className="pl-6 border-l border-[#eeeeee]">
           <ProfileMenu />
        </div>
      </div>
    </header>
  );
}

export function PageContainer({ children }: { children: React.ReactNode }) {
  const { isSidebarCollapsed } = useLayoutStore();
  
  return (
    <div className={cn(
      "min-h-screen bg-[#f9f9f9] flex flex-col pt-0 transition-all duration-300 ease-in-out relative",
      isSidebarCollapsed ? "ml-16 w-[calc(100%-64px)]" : "ml-64 w-[calc(100%-256px)]"
    )}>
      <div className="relative z-10 flex flex-col flex-1">
        {children}
      </div>
    </div>
  );
}


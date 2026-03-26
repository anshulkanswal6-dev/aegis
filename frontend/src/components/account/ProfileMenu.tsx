import { useAccount, useDisconnect } from 'wagmi';
import { LogOut, Settings, Github, MessageSquare, HelpCircle, ChevronRight, Globe, User } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { cn } from '../../lib/utils/cn';
import { formatAddress } from '../../lib/utils/format';
import { useNavigate } from 'react-router-dom';

export function ProfileMenu() {
  const { address, isConnected } = useAccount();
  const { disconnect } = useDisconnect();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!isConnected) return null;

  return (
    <div className="relative z-50" ref={menuRef}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 p-1 rounded-full hover:bg-zinc-50 transition-all active:scale-95 group",
          isOpen && "bg-zinc-50"
        )}
      >
        <div className="w-8 h-8 rounded-full bg-zinc-100 border border-zinc-200 flex items-center justify-center overflow-hidden">
           <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${address}`} alt="Avatar" className="w-full h-full object-cover" />
        </div>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-4 w-64 bg-white border border-[#eeeeee] rounded-xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.1)] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Account Header */}
          <div className="p-4 border-b border-[#eeeeee]">
             <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-zinc-50 flex items-center justify-center text-black border border-zinc-100">
                   <User className="w-5 h-5 text-zinc-400" />
                </div>
                <div className="flex flex-col min-w-0">
                   <span className="text-xs font-bold text-black truncate">{formatAddress(address!)}</span>
                   <span className="text-[10px] text-zinc-400 font-medium">Owner Account</span>
                </div>
             </div>
          </div>

          {/* Menu Sections */}
          <div className="py-2">
             <div className="px-3 py-1 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Account</div>
             <button 
                onClick={() => { navigate('/wallet'); setIsOpen(false); }}
                className="w-full flex items-center px-4 py-2 hover:bg-zinc-50 text-xs font-medium text-black transition-colors"
             >
                <Settings className="w-4 h-4 mr-3 text-zinc-400" />
                Account Settings
                <ChevronRight className="w-3 h-3 ml-auto text-zinc-300" />
             </button>
             <button className="w-full flex items-center px-4 py-2 hover:bg-zinc-50 text-xs font-medium text-black transition-colors">
                <Globe className="w-4 h-4 mr-3 text-zinc-400" />
                Language
                <span className="ml-auto text-[10px] text-zinc-400">EN</span>
             </button>
          </div>

          <div className="py-2 border-t border-[#eeeeee]">
             <div className="px-3 py-1 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Platform</div>
             <a href="https://github.com/ansbulkanswal6-dev" target="_blank" rel="noopener noreferrer" className="w-full flex items-center px-4 py-2 hover:bg-zinc-50 text-xs font-medium text-black transition-colors">
                <Github className="w-4 h-4 mr-3 text-zinc-400" />
                GitHub Repositories
             </a>
             <button className="w-full flex items-center px-4 py-2 hover:bg-zinc-50 text-xs font-medium text-black transition-colors">
                <MessageSquare className="w-4 h-4 mr-3 text-zinc-400" />
                Join Community
             </button>
             <button className="w-full flex items-center px-4 py-2 hover:bg-zinc-50 text-xs font-medium text-black transition-colors">
                <HelpCircle className="w-4 h-4 mr-3 text-zinc-400" />
                Help Center
             </button>
          </div>

          <div className="mt-2 border-t border-[#eeeeee]">
             <button 
               onClick={() => { disconnect(); setIsOpen(false); }}
               className="w-full flex items-center px-4 py-3 hover:bg-rose-50 text-xs font-bold text-rose-500 transition-colors"
             >
                <LogOut className="w-4 h-4 mr-3" />
                Logout
             </button>
          </div>
        </div>
      )}
    </div>
  );
}


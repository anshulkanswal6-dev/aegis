import { NavLink } from 'react-router-dom';
import { Bot, Wallet, LayoutGrid, Play, ChevronRight, ChevronLeft, Settings, HelpCircle } from 'lucide-react';
import { cn } from '../../lib/utils/cn';
import { useLayoutStore } from '../../store/layoutStore';

const NAV_ITEMS = [
  { label: 'Overview', to: '/', icon: Bot },
  { label: 'Network Wallet', to: '/wallet', icon: Wallet },
  { label: 'Playground', to: '/playground', icon: Play },
  { label: 'Projects', to: '/projects', icon: LayoutGrid },
];

export function Sidebar() {
  const { isSidebarCollapsed, toggleSidebar } = useLayoutStore();

  return (
    <aside className={cn(
      "fixed left-0 top-0 bottom-0 bg-white border-r border-[#eeeeee] z-50 flex flex-col transition-all duration-300 ease-in-out shadow-sm",
      isSidebarCollapsed ? "w-16" : "w-64"
    )}>
      {/* Brand Section */}
      <div className={cn(
        "h-16 flex items-center border-b border-[#eeeeee] transition-all",
        isSidebarCollapsed ? "justify-center" : "px-6 gap-3"
      )}>
        <div 
          className="w-8 h-8 bg-black rounded flex items-center justify-center text-white shrink-0 cursor-pointer shadow-md active:scale-95 transition-transform"
          onClick={() => window.location.href = '/'}
        >
          <Bot className="w-5 h-5" />
        </div>
        {!isSidebarCollapsed && (
          <div className="overflow-hidden whitespace-nowrap">
            <h1 className="font-bold text-sm tracking-tight text-black leading-tight">Aegis</h1>
            <p className="text-[10px] text-zinc-400 font-medium uppercase tracking-wider">Automation OS</p>
          </div>
        )}
      </div>

      <nav className="flex-1 px-3 py-6 space-y-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => cn(
              "flex items-center rounded-md transition-all h-10 overflow-hidden group",
              isActive 
                ? "bg-zinc-50 text-black border border-zinc-100 shadow-sm" 
                : "text-zinc-500 hover:text-black hover:bg-zinc-50"
            )}
          >
            {({ isActive }) => (
              <div className={cn("flex items-center h-full w-full", isSidebarCollapsed ? "justify-center" : "px-3")}>
                <item.icon className={cn("w-4.5 h-4.5 shrink-0 transition-colors", isActive ? "text-black" : "text-zinc-400 group-hover:text-black")} />
                {!isSidebarCollapsed && (
                  <span className="ml-3 font-medium text-[13px]">{item.label}</span>
                )}
                {isActive && !isSidebarCollapsed && (
                  <div className="w-1.5 h-1.5 rounded-full bg-black ml-auto" />
                )}
              </div>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-[#eeeeee] space-y-1">
        {!isSidebarCollapsed && (
          <>
            <button className="w-full flex items-center px-3 h-10 rounded-md text-zinc-500 hover:text-black hover:bg-zinc-50 transition-all group">
              <Settings className="w-4.5 h-4.5 text-zinc-400 group-hover:text-black transition-colors" />
              <span className="ml-3 font-medium text-[13px]">Settings</span>
            </button>
            <button className="w-full flex items-center px-3 h-10 rounded-md text-zinc-500 hover:text-black hover:bg-zinc-50 transition-all group">
              <HelpCircle className="w-4.5 h-4.5 text-zinc-400 group-hover:text-black transition-colors" />
              <span className="ml-3 font-medium text-[13px]">Help Center</span>
            </button>
          </>
        )}
        
        <button 
          onClick={toggleSidebar}
          className={cn(
            "w-full h-10 rounded-md flex items-center text-zinc-400 hover:text-black hover:bg-zinc-50 transition-all group",
            isSidebarCollapsed ? "justify-center" : "px-3"
          )}
          title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {isSidebarCollapsed ? <ChevronRight className="w-4.5 h-4.5" /> : <ChevronLeft className="w-4.5 h-4.5" />}
          {!isSidebarCollapsed && <span className="ml-3 font-medium text-[13px]">Collapse</span>}
        </button>
      </div>
    </aside>
  );
}


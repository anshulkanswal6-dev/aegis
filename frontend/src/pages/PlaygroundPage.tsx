
import { 
  Code2, FileJson, 
  Cpu, Network,
  Layout,
  Activity,
  Terminal as TerminalIcon,
  X,
  FileCode,
  FileSearch,
  Globe,
  User,
  LogOut,
  PanelLeft,
  PanelRight,
  Monitor,
  Sparkles
} from 'lucide-react';
import { cn } from '../lib/utils/cn';
import { usePlaygroundStore } from '../store/playgroundStore';
import { WorkspaceSidebar } from '../components/playground/WorkspaceSidebar';
import { AgentChatPanel } from '../components/playground/AgentChatPanel';
import { TerminalPanel } from '../components/playground/TerminalPanel';
import { IDEEditor } from '../components/playground/IDEEditor';
import { useState, useEffect } from 'react';
import { useAccount, useChainId, useConfig } from 'wagmi';
import { agentService } from '../services/agentService';
import { formatEther } from 'viem';
import { useLayoutStore } from '../store/layoutStore';
import { useAgentWallet } from '../hooks/useAgentWallet';
import { useLocation } from 'react-router-dom';

export default function PlaygroundPage() {
  const { address } = useAccount();
  const chainId = useChainId();
  const config = useConfig();
  const location = useLocation();
  const currentChain = config.chains.find(c => c.id === chainId);
  const [showProfile, setShowProfile] = useState(false);
  
  const { 
    ethBalance: agentBalance,
    chainSymbol 
  } = useAgentWallet();

  const { 
    isSidebarCollapsed, toggleSidebar,
    isChatCollapsed, toggleChat,
    isTerminalCollapsed, toggleTerminal
  } = useLayoutStore();

  const { 
    currentPrompt, 
    spec, planMd,
    activeTab, setActiveTab,
    openFiles, closeFile,
    updateContent,
    fileTree,
    customFiles,
    activeView, setActiveView,
    automationLogs,
    activeAutomationId,
    deployAutomation,
    submitPrompt,
    loadAutomation
  } = usePlaygroundStore();

  // =========================================================
  // Handle Redeploy State
  // =========================================================
  useEffect(() => {
    if (location.state?.automation) {
      loadAutomation(location.state.automation);
      // Clear state to prevent re-load on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.state, loadAutomation]);

  const [cursorPos, setCursorPos] = useState({ line: 1, column: 1 });

  // =========================================================
  // Log Polling Loop
  // =========================================================
  useEffect(() => {
    if (!activeAutomationId) return;

    let pollCount = 0;
    const interval = setInterval(async () => {
      try {
        const data = await agentService.getAutomationLogs(activeAutomationId, 20);
        if (data && data.logs) {
           // Format and update logs in store
           const newLogs = data.logs.map((l: any) => `- ${l.message}`);
           // Simple diff to only add new ones or replace
           usePlaygroundStore.setState({ automationLogs: newLogs });
        }
      } catch (e) {
        console.error("Log fetch failed", e);
      }
      
      pollCount++;
      // Stop polling after 1 hour of activity as safety or if component unmounts
      if (pollCount > 720) clearInterval(interval); 
    }, 5000);

    return () => clearInterval(interval);
  }, [activeAutomationId]);


  const findNode = (id: string, nodes: any[]): any => {
    for (const n of nodes) {
      if (n.id === id) return n;
      if (n.children) {
        const found = findNode(id, n.children);
        if (found) return found;
      }
    }
    return null;
  };

  const getTabIcon = (id: string) => {
    const node = findNode(id, fileTree);
    const name = node?.name || id;

    if (id === 'prompt' || name === 'Global Strategy') return <Globe className="w-3.5 h-3.5 text-[#FF4D4D]" />;
    if (name.endsWith('.py')) return <FileCode className="w-3.5 h-3.5 text-blue-500" />;
    if (name.endsWith('.json')) return <FileJson className="w-3.5 h-3.5 text-amber-500" />;
    if (name.endsWith('.md')) return <FileSearch className="w-3.5 h-3.5 text-rose-500" />;
    return <Code2 className="w-3.5 h-3.5 text-zinc-400" />;
  };

  const getTabLabel = (id: string) => {
    if (id === 'plan_md') return 'PLAN.MD';
    const node = findNode(id, fileTree);
    return node?.name.toUpperCase() || id.toUpperCase();
  };

  const getActiveContent = () => {
    if (activeTab === 'plan_md') return planMd;
    if (activeTab && customFiles[activeTab]) return customFiles[activeTab];
    return '';
  };

  const getActiveLanguage = () => {
    if (activeTab === 'spec' || activeTab === 'meta') return 'json';
    if (activeTab === 'prompt' || activeTab === 'plan_md') return 'markdown';
    const node = activeTab ? findNode(activeTab, fileTree) : null;
    if (node?.name.endsWith('.py')) return 'python';
    if (node?.name.endsWith('.json')) return 'json';
    if (node?.name.endsWith('.md')) return 'markdown';
    if (node?.name.endsWith('.txt')) return 'plaintext';
    return 'python';
  };



  const handleDeploy = () => {
    // If we have a spec, it's a runtime deployment
    if (spec && spec !== '{}') {
       deployAutomation();
    } else if (currentPrompt) {
       submitPrompt(currentPrompt);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <header className="h-14 border-b border-[#eeeeee] flex items-center justify-between px-6 shrink-0 bg-white relative z-50">
        <div className="flex items-center gap-8">
           <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-black flex items-center justify-center text-white shadow-xl rotate-[-4deg]">
                 <Cpu className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                 <h1 className="text-[12px] font-black uppercase tracking-[0.25em] text-black italic">Aegis IDE</h1>
                 <div className="flex items-center gap-1.5 px-1.5 py-0.5 bg-emerald-50 rounded-full border border-emerald-100/50 w-fit">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[8px] font-black text-emerald-600 tracking-widest uppercase">Core Sync: Active</span>
                 </div>
              </div>
           </div>

           <div className="flex items-center gap-1 px-1 py-1 bg-[#F5F5F5] rounded-xl border border-[#eeeeee]">
              <button 
                onClick={() => setActiveView('compile')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all",
                  activeView === 'compile' ? "bg-white text-black shadow-sm border border-[#eeeeee]" : "text-zinc-400 hover:text-black hover:bg-white/50"
                )}
              >
                 <Sparkles className={cn("w-3.5 h-3.5", activeView === 'compile' ? "text-[#FF4D4D]" : "text-zinc-300")} /> Compile
              </button>
              <button 
                onClick={() => setActiveView('simulation')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all",
                  activeView === 'simulation' ? "bg-white text-black shadow-sm border border-[#eeeeee]" : "text-zinc-400 hover:text-black hover:bg-white/50"
                )}
              >
                 <Layout className={cn("w-3.5 h-3.5", activeView === 'simulation' ? "text-amber-500" : "text-zinc-300")} /> Simulation
              </button>
              <button 
                onClick={() => setActiveView('automation')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all",
                  activeView === 'automation' ? "bg-white text-black shadow-sm border border-[#eeeeee]" : "text-zinc-400 hover:text-black hover:bg-white/50"
                )}
              >
                 <Activity className={cn("w-3.5 h-3.5", activeView === 'automation' ? "text-emerald-500" : "text-zinc-300")} /> Automation Logs
              </button>
           </div>
        </div>

        <div className="flex items-center gap-4">
           <div className="flex items-center gap-1 px-1 py-1 bg-[#F5F5F5] rounded-xl border border-[#eeeeee] mr-2">
              <button 
                onClick={toggleSidebar}
                className={cn("p-2 rounded-lg transition-all", !isSidebarCollapsed ? "bg-white text-black shadow-sm" : "text-zinc-400 hover:text-black")}
                title="Toggle Sidebar"
              >
                 <PanelLeft className="w-4 h-4" />
              </button>
              <button 
                onClick={toggleTerminal}
                className={cn("p-2 rounded-lg transition-all", !isTerminalCollapsed ? "bg-white text-black shadow-sm" : "text-zinc-400 hover:text-black")}
                title="Toggle Terminal"
              >
                 <Monitor className="w-4 h-4" />
              </button>
              <button 
                onClick={toggleChat}
                className={cn("p-2 rounded-lg transition-all", !isChatCollapsed ? "bg-white text-black shadow-sm" : "text-zinc-400 hover:text-black")}
                title="Toggle Chat"
              >
                 <PanelRight className="w-4 h-4" />
              </button>
           </div>

           <div className="h-9 px-4 flex items-center gap-2.5 bg-[#F5F5F5] rounded-xl border border-[#eeeeee] group hover:border-zinc-300 transition-all cursor-pointer">
              <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
              <span className="text-[10px] font-bold text-black tracking-widest uppercase">
                 {currentChain?.name || 'Avalanche Fuji'}
              </span>
           </div>

           <div className="relative">
              <button 
                onClick={() => setShowProfile(!showProfile)}
                className="h-10 flex items-center gap-3 px-1.5 bg-white border border-[#eeeeee] rounded-2xl hover:border-black transition-all group overflow-hidden"
              >
                 <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-[#FF4D4D] to-rose-600 flex items-center justify-center text-white text-[10px] font-black shadow-lg">
                    {address?.slice(0, 2).toUpperCase() || 'AE'}
                 </div>
                 <div className="flex flex-col items-start pr-2">
                    <span className="text-[9px] font-black text-zinc-400 uppercase tracking-widest leading-none mb-1">Agent Balance</span>
                    <span className="text-[11px] font-bold text-black tracking-tight leading-none">
                       {formatEther(agentBalance).slice(0, 6)} {chainSymbol}
                    </span>
                 </div>
              </button>

              {showProfile && (
                <div className="absolute top-full right-0 mt-2 w-64 bg-white border border-[#eeeeee] rounded-2xl shadow-2xl p-2 z-[100] animate-in slide-in-from-top-2 duration-200">
                   <div className="p-4 border-b border-[#eeeeee] mb-1">
                      <p className="text-[10px] font-black text-zinc-400 uppercase tracking-widest mb-1">Signed in as</p>
                      <p className="text-xs font-bold text-black truncate">{address || '0x000...000'}</p>
                   </div>
                   <div className="space-y-0.5">
                      <button className="w-full px-4 py-2 flex items-center gap-3 hover:bg-zinc-50 transition-colors group">
                         <User className="w-3.5 h-3.5 text-zinc-400 group-hover:text-black" />
                         <span className="text-xs font-semibold text-zinc-600 group-hover:text-black">Profile Settings</span>
                      </button>
                      <button className="w-full px-4 py-3 flex items-center gap-3 hover:bg-rose-50 transition-colors group mt-1">
                         <LogOut className="w-3.5 h-3.5 text-rose-500" />
                         <span className="text-xs font-bold text-rose-600">Logout</span>
                      </button>
                   </div>
                </div>
              )}
           </div>
           <button 
             onClick={handleDeploy}
             className="h-9 px-4 flex items-center gap-2 bg-black text-white rounded-full shadow-lg shadow-black/10 hover:bg-zinc-800 hover:scale-[1.02] transition-all group shrink-0"
           >
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span className="text-[11px] font-black uppercase tracking-wider">Deploy Agent</span>
           </button>
        </div>
      </header>
      
      <div className="flex-1 flex overflow-hidden">
        {!isSidebarCollapsed && <WorkspaceSidebar />}

        <div className="flex-1 flex overflow-hidden relative border-r border-[#eeeeee]">
          <div className="flex-1 flex flex-col min-w-0 bg-white relative">
            <main className="flex-1 flex flex-col relative">
               {activeView === 'compile' && (
                 <div className="flex-1 flex flex-col h-full overflow-hidden" key="view-compile">
                    <div className="h-10 flex items-center bg-[#FAF9F8] border-b border-[#eeeeee] px-2 gap-1 overflow-x-auto custom-scrollbar-hide">
                        {openFiles.map(fileId => (
                          <div 
                            key={fileId}
                            onClick={() => setActiveTab(fileId)}
                            className={cn(
                              "px-4 h-full flex items-center gap-2.5 text-[10px] font-black uppercase tracking-[0.15em] cursor-pointer border-r border-[#eeeeee] transition-all relative z-10 group",
                              activeTab === fileId ? "bg-white text-black" : "text-zinc-400 hover:text-zinc-500 bg-[#FAF9F8]"
                            )}
                          >
                             {activeTab === fileId && <div className="absolute top-0 left-0 right-0 h-[2px] bg-[#FF4D4D]" />}
                             {getTabIcon(fileId)} 
                             {getTabLabel(fileId)}
                             <X 
                              onClick={(e) => { e.stopPropagation(); closeFile(fileId); }}
                              className="w-3 h-3 ml-1 opacity-0 group-hover:opacity-100 hover:text-rose-500 transition-all" 
                             />
                          </div>
                        ))}
                    </div>

                    <div className="flex-1 flex flex-col relative overflow-hidden bg-white">
                       {activeTab ? (
                          <IDEEditor 
                             id={findNode(activeTab, fileTree)?.name || activeTab}
                             value={getActiveContent()} 
                             language={getActiveLanguage()}
                             onChange={(val) => updateContent(activeTab, val)}
                             onCursorChange={setCursorPos}
                             className="animate-in fade-in duration-300"
                          />
                       ) : (
                            <div className="flex-1 flex items-center justify-center bg-[#FAF9F8]">
                               <div className="text-center space-y-4 opacity-20">
                                  <TerminalIcon className="w-12 h-12 mx-auto text-black" />
                                  <p className="text-[10px] font-black uppercase tracking-[0.3em]">No File Opened Here</p>
                               </div>
                            </div>
                       )}
                    </div>
                 </div>
               )}

               {activeView === 'simulation' && (
                  <div className="flex-1 relative bg-white overflow-hidden flex items-center justify-center" key="view-simulation" style={{ backgroundImage: 'radial-gradient(circle, #f0f0f0 1px, transparent 1px)', backgroundSize: '24px 24px' }}>
                     <div className="absolute top-8 left-8 flex flex-col gap-2 scale-in duration-500">
                        <h2 className="text-[12px] font-black uppercase tracking-widest text-black/40">Neural Simulation Canvas</h2>
                        <p className="text-[9px] font-bold text-zinc-400 uppercase tracking-widest bg-zinc-50 px-3 py-1 rounded-full border border-[#eeeeee] w-fit">Live Interaction Sandbox</p>
                     </div>
                     <div className="text-center space-y-6 max-w-md animate-in zoom-in duration-700">
                        <div className="w-20 h-20 mx-auto bg-black rounded-3xl flex items-center justify-center shadow-2xl rotate-[-6deg] group hover:rotate-0 transition-transform cursor-pointer">
                           <Layout className="w-10 h-10 text-white" />
                        </div>
                        <div className="space-y-2">
                           <h3 className="text-lg font-black tracking-tighter text-black uppercase">Simulation Mode Active</h3>
                           <p className="text-[11px] font-medium text-zinc-500 leading-relaxed max-w-[280px] mx-auto italic">
                              Your agent's behavioral logic will manifest here as a functional preview.
                           </p>
                        </div>
                     </div>
                  </div>
               )}

               {activeView === 'automation' && (
                  <div className="flex-1 flex flex-col bg-white" key="view-automation">
                     <div className="h-14 px-8 border-b border-[#eeeeee] flex items-center justify-between bg-[#FAF9F8]">
                        <div className="flex items-center gap-3">
                           <Activity className="w-4 h-4 text-emerald-500" />
                           <h2 className="text-[11px] font-black uppercase tracking-widest text-black">Aegis Automation Stream</h2>
                        </div>
                     </div>
                     <div className="flex-1 overflow-y-auto p-8 space-y-2 font-mono text-[11px] bg-[#0A0A0A] text-zinc-400">
                        {automationLogs.map((log, idx) => (
                           <div key={idx} className="flex gap-4">
                              <span className="text-zinc-600 w-8">{idx + 1}</span>
                              <span className="flex-1">{log}</span>
                           </div>
                        ))}
                     </div>
                  </div>
               )}
            </main>

            {!isTerminalCollapsed && (
               <div className="h-[240px] border-t border-[#eeeeee] flex flex-col bg-white overflow-hidden">
                  <TerminalPanel onClose={toggleTerminal} />
               </div>
            )}

            <footer className="h-7 bg-[#FAF9F8] border-t border-[#eeeeee] flex items-center justify-between px-6 shrink-0 z-30">
               <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#FF4D4D]">
                     <Network className="w-3.5 h-3.5" />
                     BSC TESTNET
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-zinc-400">
                     <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                     Node Synchronized
                  </div>
               </div>
               <div className="flex items-center gap-6">
                  <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                     Ln {cursorPos.line}, Col {cursorPos.column}
                  </span>
                  <div className="flex items-center gap-1.5 text-[10px] font-black text-black tracking-widest uppercase italic">
                     Powered by Aegis
                  </div>
               </div>
            </footer>
          </div>

          {!isChatCollapsed && <AgentChatPanel />}
        </div>
      </div>
    </div>
  );
}

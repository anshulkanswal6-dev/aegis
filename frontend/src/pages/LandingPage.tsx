import { ConnectWalletCard } from '../components/wallet/ConnectWalletCard';
import { CreateAgentWalletPanel } from '../components/onboarding/CreateAgentWalletPanel';
import { FundAgentWalletPanel } from '../components/onboarding/FundAgentWalletPanel';
import { useAccount } from 'wagmi';
import { useAgentWallet } from '../hooks/useAgentWallet';
import { ShieldCheck, ArrowRight, LayoutDashboard, Terminal, Search, Sparkles, Clock, CheckCircle2, PlayCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/UIPack';
import { cn } from '../lib/utils/cn';

const RECENT_TASKS = [
  { id: '#7821', name: 'Daily Treasury Swap', modified: '2 mins ago', status: 'Running', chain: 'Ethereum' },
  { id: '#7819', name: 'Liquidity Rebalancer', modified: '12 hours ago', status: 'Complete', chain: 'Base' },
  { id: '#7815', name: 'Yield Optimizer V3', modified: '2 days ago', status: 'Paused', chain: 'Mainnet' },
];

export default function LandingPage() {
  const { isConnected } = useAccount();
  const { agentWalletAddress, ethBalance } = useAgentWallet();
  const navigate = useNavigate();

  const currentStep = !isConnected ? 1 : !agentWalletAddress ? 2 : ethBalance === 0n ? 3 : 4;

  const steps = [
    { number: 1, title: 'Connect Wallet', description: 'Authorize your node session.' },
    { number: 2, title: 'Create Agent', description: 'Initialize your on-chain worker.' },
    { number: 3, title: 'Fund Account', description: 'Enable autonomous transactions.' },
    { number: 4, title: 'Ready to Build', description: 'Launch your first automation.' },
  ];

  return (
    <div className="min-h-screen bg-[#f9f9f9] text-black">
      {/* Hero Section */}
      <section className="pt-24 pb-20 px-8 flex flex-col items-center text-center">
        <div className="max-w-4xl w-full space-y-8">
          <div className="space-y-4">
             <div className="inline-flex items-center gap-2 px-3 py-1 bg-black text-white rounded-full text-[10px] font-bold uppercase tracking-widest shadow-lg">
                <Sparkles className="w-3.5 h-3.5" />
                Next-Gen Automation
             </div>
             <h1 className="text-6xl font-black tracking-tight leading-[0.95] text-black md:text-7xl">
                Scale your on-chain <br /> operations with AI.
             </h1>
             <p className="text-zinc-500 text-lg font-medium max-w-2xl mx-auto tracking-tight">
                The first intelligent operating system for decentralized autonomous agents. 
                Build, deploy, and scale complex automations in plain English.
             </p>
          </div>

          {/* Premium Prompt Input */}
          <div className="max-w-2xl mx-auto w-full group relative">
             <div className="absolute inset-0 bg-black/5 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-1000 -z-10" />
             <div className="bg-white border border-[#eeeeee] p-2 rounded-2xl shadow-[0_10px_40px_-10px_rgba(0,0,0,0.05)] flex items-center gap-4 focus-within:ring-1 focus-within:ring-black/10 transition-all">
                <div className="w-12 h-12 rounded-xl bg-zinc-50 flex items-center justify-center border border-zinc-100 transition-transform group-hover:scale-95">
                   <Search className="w-5 h-5 text-zinc-400" />
                </div>
                <input 
                  type="text" 
                  placeholder="What will you build today? (e.g. Daily treasury swap for USDC to ETH)"
                  className="flex-1 bg-transparent border-none outline-none text-base font-medium placeholder:text-zinc-300"
                />
                <button 
                  onClick={() => navigate('/playground')}
                  className="bg-black text-white h-12 px-6 rounded-xl font-bold text-sm hover:scale-[1.02] active:scale-95 transition-all shadow-lg"
                >
                   Build
                </button>
             </div>
          </div>
        </div>
      </section>

      {/* Onboarding Section */}
      <section className="max-w-5xl mx-auto px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-start">
          {/* Stepper Side */}
          <div className="lg:col-span-5 space-y-12">
             <div className="space-y-4">
                <h2 className="text-3xl font-black tracking-tight">Onboarding Guide</h2>
                <p className="text-zinc-400 font-medium">Follow these steps to initialize your agent workspace and start building.</p>
             </div>
             <div className="space-y-8">
                {steps.map((step) => (
                   <div key={step.number} className={cn(
                      "flex items-start gap-5 transition-opacity",
                      currentStep < step.number && "opacity-30"
                   )}>
                      <div className={cn(
                         "w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0 border transition-all",
                         currentStep === step.number ? "bg-black text-white border-black shadow-lg scale-110" : "bg-white text-zinc-400 border-[#eeeeee]"
                      )}>
                         {currentStep > step.number ? <CheckCircle2 className="w-6 h-6 text-black" /> : `0${step.number}`}
                      </div>
                      <div className="space-y-1 pt-1">
                         <h3 className="font-bold text-sm tracking-tight">{step.title}</h3>
                         <p className="text-[11px] text-zinc-400 font-medium leading-relaxed">{step.description}</p>
                      </div>
                   </div>
                ))}
             </div>
          </div>

          {/* Interaction Card Side */}
          <div className="lg:col-span-7">
             <div className="surface-card bg-white p-10 rounded-[32px] border border-[#eeeeee] shadow-[0_20px_50px_-15px_rgba(0,0,0,0.03)] min-h-[400px] flex flex-col justify-center">
                {currentStep === 1 && <ConnectWalletCard />}
                {currentStep === 2 && <CreateAgentWalletPanel />}
                {currentStep === 3 && <FundAgentWalletPanel />}

                {currentStep === 4 && (
                  <div className="text-center space-y-10 py-6">
                     <div className="w-20 h-20 bg-emerald-50 text-emerald-600 rounded-3xl flex items-center justify-center mx-auto shadow-sm border border-emerald-100">
                        <ShieldCheck className="w-10 h-10" />
                     </div>
                     <div className="space-y-3">
                        <h2 className="text-3xl font-black tracking-tight">Node Activated</h2>
                        <p className="text-zinc-400 font-medium max-w-sm mx-auto">Your on-chain cluster is persistent and ready for deployment.</p>
                     </div>
                     <div className="flex flex-col gap-3 max-w-xs mx-auto pt-4">
                        <Button 
                            onClick={() => navigate('/playground')} 
                            size="lg"
                            className="bg-black hover:bg-zinc-800 h-14 rounded-2xl text-sm font-bold shadow-xl shadow-black/5"
                        >
                           <Terminal className="mr-3 w-5 h-5" /> Launch Playground
                        </Button>
                        <Button 
                            onClick={() => navigate('/projects')} 
                            variant="secondary"
                            size="lg"
                            className="h-14 rounded-2xl text-sm font-bold border-[#eeeeee] hover:bg-zinc-50"
                        >
                           <LayoutDashboard className="mr-3 w-5 h-5" /> View Projects
                        </Button>
                     </div>
                  </div>
                )}
             </div>
          </div>
        </div>
      </section>

      {/* Recent Activity Table */}
      <section className="max-w-5xl mx-auto px-8 py-24">
        <div className="space-y-8">
           <div className="flex items-center justify-between">
              <div className="space-y-1">
                 <h2 className="text-2xl font-black tracking-tight">Recent Activity</h2>
                 <p className="text-zinc-400 text-xs font-medium">Track your active on-chain automations and agents.</p>
              </div>
              <button className="text-xs font-bold text-zinc-400 hover:text-black transition-colors flex items-center gap-2">
                 View all <ArrowRight className="w-3.5 h-3.5" />
              </button>
           </div>

           <div className="bg-white border border-[#eeeeee] rounded-2xl overflow-hidden shadow-sm">
              <table className="w-full text-left border-collapse">
                 <thead>
                    <tr className="bg-zinc-50 border-b border-[#eeeeee]">
                       <th className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">ID</th>
                       <th className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Automation Task</th>
                       <th className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Chain</th>
                       <th className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Last Modified</th>
                       <th className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Status</th>
                       <th className="px-6 py-4 text-[10px] font-bold text-zinc-400 uppercase tracking-wider">Action</th>
                    </tr>
                 </thead>
                 <tbody className="divide-y divide-[#f5f5f5]">
                    {RECENT_TASKS.map((task) => (
                       <tr key={task.id} className="hover:bg-zinc-50/50 transition-colors group">
                          <td className="px-6 py-5 text-xs font-bold text-zinc-400 font-mono">{task.id}</td>
                          <td className="px-6 py-5 text-sm font-bold text-black">{task.name}</td>
                          <td className="px-6 py-5">
                             <span className="px-2 py-1 rounded bg-zinc-100 text-zinc-500 text-[10px] font-bold border border-zinc-200 uppercase tracking-tight">{task.chain}</span>
                          </td>
                          <td className="px-6 py-5 text-xs font-medium text-zinc-400 flex items-center gap-2">
                             <Clock className="w-3.5 h-3.5" /> {task.modified}
                          </td>
                          <td className="px-6 py-5">
                             <div className={cn(
                                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border",
                                task.status === 'Running' ? "bg-emerald-50 text-emerald-600 border-emerald-100" :
                                task.status === 'Complete' ? "bg-zinc-50 text-zinc-600 border-zinc-100" :
                                "bg-amber-50 text-amber-600 border-amber-100"
                             )}>
                                <div className={cn("w-1.5 h-1.5 rounded-full", task.status === 'Running' ? "bg-emerald-500" : task.status === 'Complete' ? "bg-zinc-400" : "bg-amber-500")} />
                                {task.status}
                             </div>
                          </td>
                          <td className="px-6 py-5">
                             <button 
                                onClick={() => navigate('/playground')}
                                className="p-2 text-zinc-400 hover:text-black opacity-0 group-hover:opacity-100 transition-all active:scale-95"
                                title="Open in Playground"
                             >
                                <PlayCircle className="w-5 h-5" />
                             </button>
                          </td>
                       </tr>
                    ))}
                 </tbody>
              </table>
           </div>
        </div>
      </section>

      {/* Minimal Footer */}
      <footer className="border-t border-[#eeeeee] py-12 px-8">
         <div className="max-w-5xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6 text-zinc-400 text-xs font-medium">
            <div className="flex items-center gap-6">
               <span className="text-black font-bold">© 2026 Aegis Node Clusters</span>
               <a href="#" className="hover:text-black transition-colors">Documentation</a>
               <a href="#" className="hover:text-black transition-colors">API Reference</a>
               <a href="#" className="hover:text-black transition-colors">GitHub</a>
            </div>
            <div className="flex items-center gap-4">
               <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  System Operational
               </div>
               <div className="w-px h-3 bg-zinc-200 hidden md:block" />
               <span>Latency: 12ms</span>
            </div>
         </div>
      </footer>
    </div>
  );
}


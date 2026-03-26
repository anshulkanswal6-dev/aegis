import { useParams, useNavigate } from 'react-router-dom';
import { useProjectStore } from '../store/projectStore';
import { 
  ArrowLeft, Clock, Database, ExternalLink, 
  ShieldCheck, Zap, Activity, 
  Copy, Check, Sparkles
} from 'lucide-react';
import { cn } from '../lib/utils/cn';
import { Button, Badge } from '../components/ui/UIPack';
import { Header } from '../components/layout/LayoutPack';
import { useState } from 'react';
import { DangerZoneCard } from '../components/wallet/DangerZoneCard';

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { projects } = useProjectStore();
  const [activeTab, setActiveTab] = useState<'spec' | 'code'>('spec');
  const [copied, setCopied] = useState(false);

  const project = projects.find(p => p.id === projectId);

  if (!project) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen text-center p-20 bg-[#f9f9f9] animate-in fade-in duration-1000">
        <Activity className="w-16 h-16 mb-8 text-zinc-200" />
        <h2 className="text-2xl font-bold text-zinc-400">Project Not Found</h2>
        <Button onClick={() => navigate('/projects')} variant="secondary" className="mt-8 rounded-xl h-12 px-8 font-bold">
           Back to Projects
        </Button>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(activeTab === 'spec' ? project.spec : project.code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9] text-black selection:bg-black selection:text-white">
      <Header title="Project Details" />
      
      <main className="flex-1 p-8 md:p-12 max-w-7xl mx-auto w-full space-y-12 transition-all animate-in fade-in duration-700 relative z-10">
        
        {/* Project Header */}
        <section className="flex flex-col md:flex-row md:items-end justify-between gap-8 pb-12 border-b border-[#eeeeee]">
           <div className="space-y-8">
              <button 
                onClick={() => navigate('/projects')}
                className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400 hover:text-black transition-all group active:scale-95"
              >
                 <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                 Back to Projects
              </button>
              
              <div className="space-y-4">
                 <div className="flex items-center gap-4">
                    <h1 className="text-5xl font-bold tracking-tight text-black leading-tight uppercase">{project.name}</h1>
                    <Badge variant={project.status === 'active' ? 'success' : 'neutral'} className="h-7 px-4 shadow-sm">
                      {project.status === 'active' ? 'Running' : project.status}
                    </Badge>
                 </div>

                 
                 <div className="flex flex-wrap items-center gap-8 text-[11px] font-bold uppercase tracking-wider text-zinc-400">
                    <div className="flex items-center gap-2 px-3 py-1 bg-white rounded-lg border border-[#eeeeee] text-black shadow-sm">
                       <Database className="w-3.5 h-3.5" />
                       {project.chain} Network
                    </div>
                    <div className="flex items-center gap-2">
                       <Clock className="w-3.5 h-3.5" />
                       Updated {project.lastUpdated}
                    </div>
                    <button className="flex items-center gap-2 hover:text-black transition-colors group">
                       <ExternalLink className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
                       View on Explorer
                    </button>
                 </div>
              </div>
           </div>
           
           <div className="flex items-center gap-4">
              <Button 
                onClick={() => navigate(`/playground`)}
                className="h-12 rounded-xl bg-black text-white px-8 font-bold text-xs shadow-lg hover:translate-y-[-1px] active:translate-y-0 transition-all flex items-center gap-2"
              >
                <Zap className="w-4 h-4" /> Open Editor
              </Button>
           </div>
        </section>

        {/* Layout Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
           
           {/* Left Column: Goal & Metadata */}
           <div className="lg:col-span-4 space-y-10">
              <section className="space-y-4">
                 <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                    <ShieldCheck className="w-4 h-4 opacity-40" />
                    Project Goal
                 </div>
                 <div className="p-8 rounded-2xl bg-white border border-[#eeeeee] shadow-sm relative overflow-hidden group">
                    <p className="text-md font-bold text-black leading-relaxed tracking-tight">
                      {project.prompt}
                    </p>
                 </div>
              </section>

              <section className="space-y-4">
                 <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider text-zinc-400">
                    <Activity className="w-4 h-4 opacity-40" />
                    Setup & Settings
                 </div>
                 <div className="space-y-3">
                    <div className="p-5 rounded-xl bg-white border border-[#eeeeee] shadow-sm flex items-center justify-between group hover:border-black transition-all">
                       <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-zinc-50 border border-[#f5f5f5] flex items-center justify-center text-black group-hover:scale-110 transition-transform">
                             <Zap className="w-5 h-5" />
                          </div>
                          <div className="flex flex-col">
                             <span className="text-sm font-bold text-black">Active Automation</span>
                             <span className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest mt-0.5">Running</span>
                          </div>
                       </div>
                    </div>
                 </div>
              </section>

              <DangerZoneCard />
           </div>

           {/* Right Column: Files */}
           <div className="lg:col-span-8 space-y-8">
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-black flex items-center justify-center text-white shadow-md">
                       <Sparkles className="w-4 h-4" />
                    </div>
                    <h2 className="text-sm font-bold text-black uppercase tracking-wider">Project Files</h2>
                 </div>

                 <div className="flex p-1 bg-zinc-50 border border-[#eeeeee] rounded-xl shadow-sm">
                    <button 
                      onClick={() => setActiveTab('spec')}
                      className={cn(
                        "px-6 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                        activeTab === 'spec' ? "bg-white text-black border border-[#eeeeee] shadow-sm" : "text-zinc-400 hover:text-black"
                      )}
                    >Spec</button>
                    <button 
                      onClick={() => setActiveTab('code')}
                      className={cn(
                        "px-6 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all",
                        activeTab === 'code' ? "bg-white text-black border border-[#eeeeee] shadow-sm" : "text-zinc-400 hover:text-black"
                      )}
                    >Code</button>
                 </div>
              </div>

              <div className="relative group/artifact rounded-2xl border border-[#eeeeee] bg-white shadow-sm overflow-hidden min-h-[500px]">
                 <div className="absolute top-6 right-6 flex items-center gap-2 z-10 opacity-0 group-hover/artifact:opacity-100 transition-all duration-300">
                    <button 
                      onClick={handleCopy}
                      className="p-3 rounded-lg bg-white border border-[#eeeeee] text-zinc-400 hover:text-black hover:border-black transition-all shadow-md active:scale-95"
                    >
                       {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
                    </button>
                 </div>
                 
                 <div className="h-[500px] overflow-y-auto p-10 custom-scrollbar font-mono text-xs leading-relaxed bg-[#f9f9f9]/50">
                    {activeTab === 'spec' ? (
                       <pre className="text-indigo-600 font-bold opacity-80">{project.spec}</pre>
                    ) : (
                       <pre className="text-emerald-600 font-bold opacity-80">{project.code}</pre>
                    )}
                 </div>
              </div>
           </div>
        </div>
      </main>
    </div>
  );
}

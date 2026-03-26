import { useEffect, useState, useMemo } from 'react';
import { useProjectStore } from '../store/projectStore';
import { useAutomationStore } from '../store/automationStore';
import type { DeployedAutomation } from '../store/automationStore';
import { 
  Plus, Clock, Database, ChevronRight, 
  Search, Filter, MoreVertical, LayoutGrid, 
  List, Activity, Zap, Pause, Play, RefreshCw
} from 'lucide-react';
import { cn } from '../lib/utils/cn';
import { Button, Card, Badge } from '../components/ui/UIPack';
import { Header } from '../components/layout/LayoutPack';
import { useNavigate } from 'react-router-dom';

interface ProjectDisplay {
  id: string;
  name: string;
  prompt: string;
  status: 'draft' | 'ready' | 'active' | 'error' | 'paused' | 'failed' | 'ready_for_deploy';
  chain: string;
  lastUpdated: string;
  isDeployed: boolean;
  automation?: DeployedAutomation;
}

export default function ProjectsPage() {
  const { projects, searchQuery, setSearchQuery, selectedFilter, setSelectedFilter } = useProjectStore();
  const { automations, fetchAutomations, pauseAutomation, resumeAutomation } = useAutomationStore();
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    fetchAutomations();
  }, [fetchAutomations]);

  // Merge runtime automations with local project store data
  const combinedProjects = useMemo(() => {
    const deployedItems: ProjectDisplay[] = automations.map(a => ({
      id: a.id,
      name: a.name,
      prompt: a.description || (a.spec_json?.prompt) || "No prompt provided",
      status: a.status as any,
      chain: a.spec_json?.chain?.name || 'Unknown',
      lastUpdated: a.updated_at,
      isDeployed: true,
      automation: a
    }));

    const localItems: ProjectDisplay[] = projects.map(p => ({
      ...p,
      isDeployed: false
    }));

    return [...deployedItems, ...localItems];
  }, [automations, projects]);

  const filteredProjects = combinedProjects.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.prompt.toLowerCase().includes(searchQuery.toLowerCase())
  ).filter(p => 
    selectedFilter === 'all' || p.status.toLowerCase() === selectedFilter.toLowerCase()
  );

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9] text-black">
      <Header title="Project Dashboard" />
      
      <main className="flex-1 p-8 md:p-12 max-w-7xl mx-auto w-full space-y-12 transition-all animate-in fade-in duration-700 relative z-10">
        
        {/* Strategic Header Cluster */}
        <section className="flex flex-col md:flex-row md:items-end justify-between gap-8">
          <div className="space-y-4">
             <div className="flex items-center gap-2 px-3 py-1 bg-white border border-[#eeeeee] text-zinc-400 text-[10px] font-bold uppercase tracking-wider w-fit rounded-lg shadow-sm">
                <Activity className="w-3.5 h-3.5 text-emerald-500" />
                Real-time Intelligence
             </div>
             <h1 className="text-5xl font-bold tracking-tight text-black leading-tight">My Automations</h1>
             <p className="text-zinc-500 font-medium text-sm max-w-md">Orchestrate and monitor your cross-chain automation clusters with precision.</p>
          </div>
          
          <div className="flex items-center gap-4">
             <div className="flex items-center gap-1 p-1 bg-white border border-[#eeeeee] rounded-xl shadow-sm">
                <button 
                  onClick={() => setViewMode('grid')}
                  className={cn("p-2 rounded-lg transition-all active:scale-95", viewMode === 'grid' ? "bg-black text-white shadow-md" : "text-zinc-400 hover:text-black")}
                >
                   <LayoutGrid className="w-4 h-4" />
                </button>
                <button 
                  onClick={() => setViewMode('list')}
                  className={cn("p-2 rounded-lg transition-all active:scale-95", viewMode === 'list' ? "bg-black text-white shadow-md" : "text-zinc-400 hover:text-black")}
                >
                   <List className="w-4 h-4" />
                </button>
             </div>
             <Button 
               onClick={() => navigate('/playground')}
               className="h-11 rounded-xl bg-black text-white px-6 font-bold text-xs shadow-lg hover:translate-y-[-1px] active:translate-y-0 transition-all flex items-center gap-2"
             >
               <Plus className="w-4 h-4" /> New Automation
             </Button>
          </div>
        </section>

        {/* Tactical Search & Filter Vector */}
        <section className="flex flex-col md:flex-row items-center gap-4 p-2 bg-white rounded-2xl border border-[#eeeeee] shadow-sm">
           <div className="relative flex-1 group">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300 group-focus-within:text-black transition-colors" />
              <input 
                type="text" 
                placeholder="Search projects or parameters..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-12 bg-transparent rounded-xl pl-11 pr-4 text-sm font-medium text-black outline-none placeholder:text-zinc-300 transition-all"
              />
           </div>
           
           <div className="flex items-center gap-2 px-4 h-12 overflow-x-auto no-scrollbar lg:border-l lg:border-[#f5f5f5]">
              <Filter className="w-4 h-4 text-zinc-300 shrink-0" />
              {['all', 'active', 'ready', 'draft', 'error'].map(f => (
                <button
                  key={f}
                  onClick={() => setSelectedFilter(f as any)}
                  className={cn(
                    "px-4 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all shrink-0 active:scale-95",
                    selectedFilter === f ? "bg-zinc-100 text-black border border-[#eeeeee]" : "text-zinc-400 hover:text-black"
                  )}
                >
                  {f}
                </button>
              ))}
           </div>
        </section>

        {/* Mission Matrix Display */}
        {filteredProjects.length === 0 ? (
          <div className="py-32 flex flex-col items-center justify-center text-center space-y-6">
             <div className="w-24 h-24 rounded-3xl bg-zinc-50 border border-zinc-100 flex items-center justify-center shadow-inner group">
                <Database className="w-10 h-10 text-zinc-200 group-hover:scale-110 transition-transform" />
             </div>
             <div className="space-y-2">
                <h3 className="text-sm font-bold text-black uppercase tracking-wider opacity-60">No clusters found</h3>
                <p className="text-xs text-zinc-400 font-medium max-w-[240px]">Initialize your first automation sequence in the playground.</p>
             </div>
          </div>
        ) : (
          <section className={cn(
            "grid gap-6 animate-in fade-in duration-700",
            viewMode === 'grid' ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" : "grid-cols-1"
          )}>
            {filteredProjects.map((project) => (
              <Card 
                key={project.id}
                className="group relative cursor-pointer hover:border-[#dadada] hover:shadow-xl hover:translate-y-[-4px] transition-all p-8 flex flex-col h-full bg-white border border-[#eeeeee] shadow-sm overflow-hidden rounded-2xl"
              >
                <div className="flex items-center justify-between mb-8">
                   <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-black flex items-center justify-center text-white shadow-md group-hover:scale-110 transition-transform">
                         <Zap className={cn("w-5 h-5 fill-current", project.status.toLowerCase() === 'active' ? "text-emerald-400" : "text-white")} />
                      </div>
                      <div className="flex flex-col">
                         <h3 className="text-sm font-bold text-black tracking-tight group-hover:text-zinc-700 transition-colors">
                           {project.name}
                         </h3>
                         <div className="flex items-center gap-1.5 mt-0.5 text-zinc-400">
                            <Clock className="w-3 h-3" />
                            <span className="text-[10px] font-medium">Updated {new Date(project.lastUpdated).toLocaleDateString()}</span>
                         </div>
                      </div>
                   </div>
                   <Badge 
                    variant={project.status.toLowerCase() === 'active' ? 'success' : project.status.toLowerCase() === 'error' ? 'error' : 'neutral'}
                    className="rounded-full px-3 py-1 font-bold shadow-sm"
                   >
                     {project.status}
                   </Badge>
                </div>

                <div className="flex-1 space-y-6">
                   <div className="p-4 rounded-xl bg-zinc-50 border border-[#f5f5f5] group-hover:bg-white transition-all min-h-[80px]">
                      <p className="text-xs text-zinc-500 font-medium leading-relaxed line-clamp-3">
                        {project.prompt}
                      </p>
                   </div>
                   
                   <div className="flex items-center gap-2 flex-wrap">
                      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white border border-[#eeeeee] shadow-sm">
                         <div className="w-2 h-2 rounded-full bg-black/10" />
                         <span className="text-[10px] font-bold text-black uppercase tracking-wider">{project.chain}</span>
                      </div>
                      {project.isDeployed && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-100 shadow-sm">
                           <Activity className="w-3 h-3 text-emerald-500" />
                           <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">Deployed</span>
                        </div>
                      )}
                   </div>
                </div>

                <div className="mt-8 pt-6 border-t border-[#f5f5f5] flex items-center justify-between group/footer">
                   <div className="flex items-center gap-2">
                     {project.isDeployed ? (
                       <>
                         {project.status.toLowerCase() === 'active' ? (
                           <Button 
                             onClick={(e) => { e.stopPropagation(); pauseAutomation(project.id); }}
                             variant="ghost" 
                             className="h-8 w-8 p-0 rounded-lg hover:bg-zinc-100 text-zinc-600"
                           >
                             <Pause className="w-4 h-4" />
                           </Button>
                         ) : (
                           <Button 
                             onClick={(e) => { e.stopPropagation(); resumeAutomation(project.id); }}
                             variant="ghost" 
                             className="h-8 w-8 p-0 rounded-lg hover:bg-zinc-100 text-emerald-600"
                           >
                             <Play className="w-4 h-4" />
                           </Button>
                         )}
                         <Button 
                           onClick={(e) => { 
                             e.stopPropagation(); 
                             navigate('/playground', { state: { automation: project.automation } }); 
                           }}
                           variant="ghost" 
                           className="h-8 w-8 p-0 rounded-lg hover:bg-zinc-100 text-blue-600"
                           title="Redeploy"
                         >
                           <RefreshCw className="w-4 h-4" />
                         </Button>
                       </>
                     ) : (
                       <div className="flex items-center gap-1.5 text-[10px] font-bold text-zinc-400 uppercase tracking-widest group-hover/footer:text-black transition-colors" onClick={() => navigate(`/projects/${project.id}`)}>
                          Open Project
                          <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                       </div>
                     )}
                   </div>
                   <button className="p-2 rounded-lg hover:bg-zinc-50 text-zinc-300 hover:text-black transition-all" onClick={(e) => e.stopPropagation()}>
                      <MoreVertical className="w-4 h-4" />
                   </button>
                </div>
              </Card>
            ))}
          </section>
        )}
      </main>
    </div>
  );
}


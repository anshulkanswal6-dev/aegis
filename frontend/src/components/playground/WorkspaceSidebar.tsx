
import { 
  FileCode, FileJson, Plus, ChevronDown, ChevronRight, 
  HardDrive, FileSearch, Globe, Trash2, FolderPlus, FilePlus,
  PanelLeftClose
} from 'lucide-react';
import { cn } from '../../lib/utils/cn';
import { usePlaygroundStore } from '../../store/playgroundStore';
import { useLayoutStore } from '../../store/layoutStore';
import type { FileNode } from '../../store/playgroundStore';
import { useState } from 'react';

export function WorkspaceSidebar() {
  const { toggleSidebar } = useLayoutStore();
  const { activeTab, openFile, deleteFile, fileTree, createFile, createFolder } = usePlaygroundStore();
  const [openFolders, setOpenFolders] = useState<Record<string, boolean>>({
    'contracts': true,
    'build': true,
    'strategies': true
  });

  const [creating, setCreating] = useState<{ type: 'file' | 'folder', parentId: string | null } | null>(null);
  const [newItemName, setNewItemName] = useState('');

  const toggleFolder = (id: string) => {
    setOpenFolders(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItemName || !creating) {
      setCreating(null);
      return;
    }

    if (creating?.type === 'file') {
      createFile(newItemName, creating.parentId);
    } else {
      createFolder(newItemName, creating.parentId);
    }

    setNewItemName('');
    setCreating(null);
  };

  const renderNode = (node: FileNode, depth: number = 0) => {
    const isFolder = node.type === 'folder';
    const isOpen = openFolders[node.id];
    const isActive = activeTab === node.id;

    const getIcon = () => {
      if (node.id === 'prompt') return Globe;
      if (node.name.endsWith('.py')) return FileCode;
      if (node.name.endsWith('.json')) return FileJson;
      if (node.name.endsWith('.md')) return FileSearch;
      return FileCode;
    };

    const NodeIcon = getIcon();

    return (
      <div key={node.id} className="select-none">
        <div 
          onClick={() => isFolder ? toggleFolder(node.id) : openFile(node.id)}
          style={{ paddingLeft: `${depth * 12 + 12}px` }}
          className={cn(
            "group flex items-center gap-2 h-7 cursor-pointer transition-colors text-[11px] font-medium tracking-tight",
            isActive ? "bg-[#eeeeee] text-black" : "text-[#616161] hover:bg-[#f3f3f3] hover:text-black",
            isFolder && "font-bold text-[10px] tracking-wider text-zinc-400 mt-2"
          )}
        >
          {isFolder ? (
            isOpen ? <ChevronDown className="w-3 h-3 shrink-0" /> : <ChevronRight className="w-3 h-3 shrink-0" />
          ) : (
             <div className="w-3" />
          )}
          
          {!isFolder && (
            <NodeIcon className={cn(
              "w-3.5 h-3.5 shrink-0",
              node.name.endsWith('.py') ? "text-blue-500" : 
              node.name.endsWith('.json') ? "text-amber-500" : "text-zinc-400"
            )} />
          )}
          
          <span className="truncate uppercase">{node.name}</span>
          
          {!isFolder && (
            <Trash2 
              onClick={(e) => { e.stopPropagation(); deleteFile(node.id); }}
              className="ml-auto mr-3 w-3 h-3 text-zinc-300 hover:text-rose-500 opacity-0 group-hover:opacity-100 transition-all" 
            />
          )}

          {isFolder && (
            <div className="ml-auto mr-3 flex items-center gap-1.5 opacity-0 group-hover:opacity-100">
               <Plus 
                 onClick={(e) => { e.stopPropagation(); setCreating({ type: 'file', parentId: node.id }); }}
                 className="w-3 h-3 text-zinc-400 hover:text-black" 
               />
            </div>
          )}
        </div>

        {isFolder && isOpen && (
          <div className="animate-in fade-in slide-in-from-top-1 duration-200">
            {creating?.parentId === node.id && (
              <form onSubmit={handleCreate} className="px-4 py-1">
                <input
                  autoFocus
                  className="w-full bg-white border border-[#FF4D4D] rounded px-2 py-0.5 text-[10px] outline-none"
                  value={newItemName}
                  onChange={(e) => setNewItemName(e.target.value)}
                  onBlur={() => setCreating(null)}
                  placeholder={creating.type === 'file' ? "file.py" : "folder name"}
                />
              </form>
            )}
            {node.children?.map(child => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="w-[280px] flex flex-col bg-[#FAF9F8] border-r border-[#eeeeee] h-full shadow-[inset_-1px_0_0_rgba(0,0,0,0.02)] relative z-20">
      <div className="h-9 px-4 flex items-center justify-between border-b border-[#eeeeee] bg-[#FAF9F8]">
        <div className="flex items-center gap-2">
           <PanelLeftClose 
             onClick={toggleSidebar}
             className="w-3.5 h-3.5 text-zinc-400 hover:text-black cursor-pointer transition-colors" 
           />
           <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-[#616161]">Explorer</h3>
        </div>
        <div className="flex items-center gap-2">
           <FilePlus 
            onClick={() => setCreating({ type: 'file', parentId: null })}
            className="w-3.5 h-3.5 text-zinc-400 hover:text-black cursor-pointer" 
           />
           <FolderPlus 
            onClick={() => setCreating({ type: 'folder', parentId: null })}
            className="w-3.5 h-3.5 text-zinc-400 hover:text-black cursor-pointer" 
           />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pt-2">
        {creating && creating.parentId === null && (
          <form onSubmit={handleCreate} className="px-3 mb-2">
            <div className="flex items-center gap-2 h-7 bg-white border border-[#FF4D4D] rounded-md px-2 shadow-sm">
              {creating.type === 'file' ? <FilePlus className="w-3 h-3 text-[#FF4D4D]" /> : <FolderPlus className="w-3 h-3 text-[#FF4D4D]" />}
              <input
                autoFocus
                value={newItemName}
                onChange={(e) => setNewItemName(e.target.value)}
                onBlur={() => { if (!newItemName) setCreating(null); }}
                className="flex-1 bg-transparent border-none outline-none text-[11px] font-medium text-black placeholder:text-zinc-300"
                placeholder={creating.type === 'file' ? "file.py" : "folder_name..."}
              />
            </div>
          </form>
        )}
        {fileTree && fileTree.length > 0 ? (
          fileTree.map(node => renderNode(node))
        ) : (
          <div className="px-4 py-8 text-center">
             <p className="text-[10px] text-zinc-400 font-medium">No files in workspace.</p>
          </div>
        )}
      </div>

      {/* Connection Info */}
      <div className="p-4 border-t border-[#eeeeee] bg-[#FAF9F8]">
        <div className="flex items-center gap-3 p-3 bg-white border border-[#eeeeee] rounded-xl shadow-sm group hover:border-zinc-300 transition-all cursor-pointer">
           <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
              <HardDrive className="w-4 h-4" />
           </div>
           <div className="flex flex-col">
              <span className="text-[9px] font-black uppercase tracking-widest text-zinc-400">Environment</span>
              <span className="text-[11px] font-bold text-black group-hover:text-[#FF4D4D] transition-colors">Port 8002 Active</span>
           </div>
        </div>
      </div>
    </div>
  );
}

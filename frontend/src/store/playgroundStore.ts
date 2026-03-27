
import { create } from 'zustand';
import { agentService, type StructuredQuestion } from '../services/agentService';
import { useAgentWalletStore } from './walletStore';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'agent_status';
  content: string;
  timestamp: string;
  agentStatus?: string;
  icon?: string;
}

export interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileNode[];
}

interface ValidationResult {
  id: string;
  type: 'success' | 'warning' | 'error';
  message: string;
}

export type PlaygroundStatus = 
  | 'idle' 
  | 'understanding' 
  | 'analyzing' 
  | 'asking_questions' 
  | 'waiting_for_input' 
  | 'validating' 
  | 'planning' 
  | 'awaiting_approval' 
  | 'generating_code' 
  | 'generating' 
  | 'creating_files' 
  | 'success' 
  | 'error';

export interface PlaygroundState {
  currentPrompt: string;
  messages: ChatMessage[];
  status: PlaygroundStatus;
  sessionId: string | null;
  walletAddress: string | null;
  
  // Model Config
  planningModel: string;
  codegenModel: string;
  availableModels: any[];
  
  // Agent Planning Data
  intentSummary: string;
  candidateTriggers: any[];
  candidateActions: any[];
  reasoning: string;
  extractedFields: Record<string, any>;
  missingFields: any[];
  followUpQuestions: any[];
  structuredQuestions: StructuredQuestion[];
  
  // Workspace Artifacts
  activeView: 'compile' | 'simulation' | 'automation';
  activeTab: string | null;
  openFiles: string[];
  spec: string;
  code: string;
  planMd: string;
  customFiles: Record<string, string>;
  terminalLogs: string[];
  automationLogs: string[];
  activeBottomTab: 'compile' | 'simulation' | 'automation';
  validations: ValidationResult[];
  fileTree: FileNode[];
  activeAutomationId: string | null;

  // Actions
  setPrompt: (p: string) => void;
  setActiveView: (view: 'compile' | 'simulation' | 'automation') => void;
  setActiveTab: (tab: string | null) => void;
  setActiveBottomTab: (tab: 'compile' | 'simulation' | 'automation') => void;
  updateContent: (id: string, content: string) => void;
  openFile: (id: string) => void;
  closeFile: (id: string) => void;
  deleteFile: (id: string) => void;
  createFile: (name: string, folderId: string | null) => void;
  createFolder: (name: string, parentId: string | null) => void;
  addTerminalLog: (log: string) => void;
  addAutomationLog: (log: string) => void;
  setModels: (planning: string, codegen: string) => void;
  setWalletAddress: (address: string | null) => void;
  fetchModels: () => Promise<void>;
  pollTerminalLogs: () => Promise<void>;
  addMessage: (m: Omit<ChatMessage, 'id' | 'timestamp'>) => void;
  addAgentStatus: (status: string, icon: string, content: string) => void;
  submitPrompt: (prompt: string) => Promise<void>;
  submitFields: (fields: Record<string, any>) => Promise<void>;
  approvePlan: (approved: boolean, changes?: string) => Promise<void>;
  deployAutomation: () => Promise<void>;
  clearWorkspace: () => void;
  loadAutomation: (automation: any) => void;
}

const DEFAULT_FILE_TREE: FileNode[] = [];

export const usePlaygroundStore = create<PlaygroundState>((set, get) => ({
  currentPrompt: '',
  messages: [],
  status: 'idle',
  sessionId: null,
  walletAddress: null,
  activeView: 'compile',
  activeBottomTab: 'compile',
  
  planningModel: 'gemini_flash',
  codegenModel: 'gemini_flash',
  availableModels: [],
  
  intentSummary: '',
  candidateTriggers: [],
  candidateActions: [],
  reasoning: '',
  extractedFields: {},
  missingFields: [],
  followUpQuestions: [],
  structuredQuestions: [],
  
  spec: '{}',
  code: '',
  planMd: '',
  customFiles: {},
  openFiles: [],
  activeTab: null,
  terminalLogs: [],
  automationLogs: [],
  validations: [],
  fileTree: [...DEFAULT_FILE_TREE],
  activeAutomationId: null,

  setPrompt: (p) => set({ currentPrompt: p }),

  setActiveView: (view) => set({ 
    activeView: view,
    activeBottomTab: view
  }),

  setActiveTab: (tab) => set({ 
    activeTab: tab,
    activeView: 'compile'
  }),
  
  setActiveBottomTab: (tab) => set({ activeBottomTab: tab }),

  updateContent: (id, content) => set((state) => {
    if (id === 'prompt') return { currentPrompt: content };
    if (id === 'code') return { code: content };
    if (id === 'spec') return { spec: content };
    if (id === 'plan_md') return { planMd: content };
    return { 
      customFiles: { ...state.customFiles, [id]: content } 
    };
  }),

  openFile: (id) => set((state) => ({
    openFiles: state.openFiles.includes(id) ? state.openFiles : [...state.openFiles, id],
    activeTab: id,
    activeView: 'compile'
  })),

  closeFile: (id) => set((state) => {
    const newOpenFiles = state.openFiles.filter(fid => fid !== id);
    return {
      openFiles: newOpenFiles,
      activeTab: state.activeTab === id ? (newOpenFiles[0] || null) : state.activeTab
    };
  }),

  deleteFile: (id) => set((state) => {
    const updates: Partial<PlaygroundState> = {
      openFiles: state.openFiles.filter(fid => fid !== id),
      activeTab: state.activeTab === id ? null : state.activeTab
    };

    const removeFromTree = (nodes: FileNode[]): FileNode[] => {
      return nodes.filter(n => n.id !== id).map(n => ({
        ...n,
        children: n.children ? removeFromTree(n.children) : undefined
      }));
    };

    const newTree = removeFromTree(state.fileTree);
    const newOpenFiles = state.openFiles.filter(fid => fid !== id);
    let newActiveTab = state.activeTab;
    if (newActiveTab === id) {
      newActiveTab = newOpenFiles.length > 0 ? newOpenFiles[newOpenFiles.length - 1] : null;
    }
    
    if (state.customFiles[id]) {
      const newCustomFiles = { ...state.customFiles };
      delete newCustomFiles[id];
      updates.customFiles = newCustomFiles;
    }

    get().addTerminalLog(`[FileSystem] Deleted resource: ${id}`);
    return { ...updates, fileTree: newTree, openFiles: newOpenFiles, activeTab: newActiveTab };
  }),

  createFile: (name, folderId) => set((state) => {
    const fileId = `file_${Date.now()}`;
    const newFile: FileNode = { id: fileId, name, type: 'file' };

    let newTree: FileNode[];
    if (!folderId) {
      newTree = [...state.fileTree, newFile];
    } else {
      const addToTree = (nodes: FileNode[]): FileNode[] => {
        return nodes.map(n => {
          if (n.id === folderId) {
            return { ...n, children: [...(n.children || []), newFile] };
          }
          if (n.children) {
            return { ...n, children: addToTree(n.children) };
          }
          return n;
        });
      };
      newTree = addToTree(state.fileTree);
    }

    get().addTerminalLog(`[FileSystem] Created file: ${name}`);
    return { 
      fileTree: newTree, 
      customFiles: { ...state.customFiles, [fileId]: '# Start writing your logic here...' },
      activeTab: fileId,
      openFiles: [...state.openFiles, fileId]
    };
  }),

  createFolder: (name, parentId) => set((state) => {
    const folderId = `folder_${Date.now()}`;
    const newFolder: FileNode = { id: folderId, name, type: 'folder', children: [] };

    let newTree: FileNode[];
    if (!parentId) {
      newTree = [...state.fileTree, newFolder];
    } else {
      const addToTree = (nodes: FileNode[]): FileNode[] => {
        return nodes.map(n => {
          if (n.id === parentId) {
            return { ...n, children: [...(n.children || []), newFolder] };
          }
          if (n.children) {
            return { ...n, children: addToTree(n.children) };
          }
          return n;
        });
      };
      newTree = addToTree(state.fileTree);
    }

    get().addTerminalLog(`[FileSystem] Created folder: ${name}`);
    return { fileTree: newTree };
  }),

  addTerminalLog: (log) => set((state) => ({
    terminalLogs: [...state.terminalLogs, `[${new Date().toLocaleTimeString()}] ${log}`]
  })),
  
  addAutomationLog: (log) => set((state) => ({
    automationLogs: [...state.automationLogs, log]
  })),
  
  setModels: (planning, codegen) => set({ planningModel: planning, codegenModel: codegen }),
  setWalletAddress: (address) => set({ walletAddress: address }),

  fetchModels: async () => {
    try {
      const models = await agentService.getModels();
      if (models && models.length > 0) {
        set({ 
          availableModels: models,
          planningModel: models[0].id,
          codegenModel: models[0].id
        });
      }
    } catch (error) {
      console.error("[PlaygroundStore] Failed to fetch models:", error);
    }
  },

  pollTerminalLogs: async () => {
    const state = get();
    if (!state.sessionId) return;
    try {
      const data = await agentService.getTerminalLogs(state.sessionId);
      if (data && data.logs) {
        set({ terminalLogs: data.logs.map((l: any) => l.message) });
      }
    } catch (e) {
      console.error("Terminal log poll failed", e);
    }
  },

  deployAutomation: async () => {
    const state = get();
    if (!state.sessionId) return;

    try {
      const specObj = JSON.parse(state.spec);
      const name = state.intentSummary || "Untitled Automation";

      get().addTerminalLog(`[Runtime] Deploying automation: ${name}...`);
      const result = await agentService.deploy(
        name,
        specObj,
        state.walletAddress || undefined,
        state.sessionId,
        state.reasoning,
        state.customFiles
      );

      set({ 
        activeAutomationId: result.automation_id,
        activeView: 'automation',
        automationLogs: [`- Automation "${name}" deployed successfully.`]
      });
      get().addTerminalLog(`[Runtime] Deployment successful! Automation ID: ${result.automation_id}`);
    } catch (e: any) {
      get().addTerminalLog(`[Runtime] Deployment failed: ${e.message}`);
    }
  },

  clearWorkspace: () => set({
     spec: '{}',
     code: '',
     planMd: '',
     validations: [],
     intentSummary: '',
     candidateTriggers: [],
     candidateActions: [],
     extractedFields: {},
     structuredQuestions: [],
     status: 'idle',
     sessionId: null,
     walletAddress: null,
     activeAutomationId: null,
     customFiles: {},
     openFiles: [],
     activeTab: null,
     fileTree: [...DEFAULT_FILE_TREE],
     terminalLogs: ["[System] Workspace cleared."]
  }),

  loadAutomation: (automation) => {
    const { clearWorkspace, addTerminalLog } = get();
    clearWorkspace();

    const specString = JSON.stringify(automation.spec_json, null, 2);
    const incomingFiles: Record<string, string> = automation.files || {};
    
    const customFiles: Record<string, string> = {};
    const fileTree: FileNode[] = [];
    const openFiles: string[] = [];

    Object.entries(incomingFiles).forEach(([name, content]) => {
      const id = `file_${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
      customFiles[id] = content;
      fileTree.push({ id, name, type: 'file' });
      openFiles.push(id);
    });

    // Ensure spec/config is in files if not explicitly there
    if (!incomingFiles['spec.json'] && !incomingFiles['config.json']) {
      const specId = 'file_spec_json';
      customFiles[specId] = specString;
      fileTree.push({ id: specId, name: 'spec.json', type: 'file' });
      openFiles.push(specId);
    }

    set({
      status: 'success',
      sessionId: automation.session_id,
      walletAddress: automation.wallet_address || null,
      intentSummary: automation.name,
      reasoning: automation.description,
      spec: specString,
      customFiles,
      fileTree,
      openFiles,
      activeTab: openFiles.find(id => id.includes('.py')) || openFiles[0] || null,
      activeView: 'compile',
      activeAutomationId: automation.id
    });

    addTerminalLog(`[System] Loaded automation "${automation.name}" for redeploy.`);
  },

  addMessage: (m) => set((state) => ({
    messages: [
      ...state.messages,
      { ...m, id: Math.random().toString(), timestamp: new Date().toISOString() }
    ]
  })),

  addAgentStatus: (status, icon, content) => set((state) => ({
    messages: [
      ...state.messages,
      {
        id: Math.random().toString(),
        role: 'agent_status' as const,
        content,
        timestamp: new Date().toISOString(),
        agentStatus: status,
        icon,
      }
    ]
  })),

  // =========================================================
  // Main chat submission
  // =========================================================
  submitPrompt: async (prompt: string) => {
    const state = get();
    set({ status: 'understanding', currentPrompt: prompt, activeTab: 'prompt' });
    
    // User message
    get().addMessage({ role: 'user', content: prompt });
    
    // Agent status: understanding
    get().addAgentStatus('understanding', '🧠', 'Understanding your request...');
    // Inject Agent Wallet address if available
    const agentWalletAddress = useAgentWalletStore.getState().agentWalletAddress;
    const mergedFields = { ...state.extractedFields };
    if (agentWalletAddress && !mergedFields.wallet_address) {
       mergedFields.wallet_address = agentWalletAddress;
       get().addTerminalLog(`[Agent] Injecting Agent Wallet context: ${agentWalletAddress}`);
    }

    try {
      // Short delay to show understanding state
      await new Promise(r => setTimeout(r, 400));
      
      // Agent status: analyzing
      set({ status: 'analyzing' });
      get().addAgentStatus('analyzing', '📊', 'Analyzing triggers and actions...');

      const data = await agentService.chat(
        prompt,
        state.sessionId || undefined,
        state.walletAddress || undefined,
        mergedFields,
        state.planningModel,
        state.codegenModel
      );

      const sessionId = data.session_id;
      set({ sessionId });

      // Handle different stages
      if (data.stage === 'idle') {
        // Greeting or clarification
        set({ status: 'idle' });
        get().addMessage({ role: 'assistant', content: data.agent_message });
        get().addTerminalLog(`[Agent] Greeting/clarification response sent.`);
        return;
      }

      if (data.stage === 'needs_input') {
        // Needs follow-up questions
        set({
          status: 'asking_questions',
          intentSummary: data.planning?.intent_summary || '',
          candidateTriggers: data.planning?.candidate_triggers || [],
          candidateActions: data.selected_actions || [],
          reasoning: data.planning?.reasoning || '',
          extractedFields: data.planning?.extracted_fields || {},
          missingFields: data.validation?.missing_fields || [],
          followUpQuestions: data.planning?.follow_up_questions || [],
          structuredQuestions: data.structured_questions || [],
        });
        
        get().addAgentStatus('asking', '❓', 'Need some additional details...');
        get().addMessage({ role: 'assistant', content: data.agent_message });
        get().addTerminalLog(`[Agent] Trigger mapped: ${data.selected_trigger}. Awaiting inputs.`);
        
        // After a beat, show waiting status
        await new Promise(r => setTimeout(r, 300));
        set({ status: 'waiting_for_input' });
        get().addAgentStatus('waiting', '⏳', 'Waiting for your input...');
        return;
      }

      if (data.stage === 'awaiting_approval') {
        // Plan generated, show in IDE
        set({
          status: 'awaiting_approval',
          intentSummary: data.planning?.intent_summary || '',
          candidateTriggers: data.planning?.candidate_triggers || [],
          candidateActions: data.selected_actions || [],
          planMd: data.plan_md || '',
        });

        get().addAgentStatus('planning', '📋', 'Creating automation plan...');
        
        // Add plan.md file to the tree and open it
        get().addTerminalLog(`[Agent] Plan generated. Awaiting approval.`);
        
        // Open plan.md in the editor
        const planFileId = 'plan_md';
        set((s) => {
          const hasPlanning = s.fileTree.some(n => n.id === 'planning');
          const newTree = hasPlanning ? s.fileTree : [...s.fileTree, {
            id: 'planning',
            name: 'PLANNING',
            type: 'folder' as const,
            children: [{ id: planFileId, name: 'plan.md', type: 'file' as const }]
          }];
          
          return {
            fileTree: newTree,
            customFiles: { ...s.customFiles, [planFileId]: data.plan_md || '' },
            openFiles: [...new Set([...s.openFiles, planFileId])],
            activeTab: planFileId,
            activeView: 'compile' as const,
          };
        });

        get().addMessage({ role: 'assistant', content: data.agent_message });
        return;
      }

      if (data.stage === 'complete') {
        // Code generated
        handleCodeGenComplete(data);
        return;
      }

    } catch (error: any) {
      console.error("[PlaygroundStore] Chat error:", error);
      set({ status: 'error' });
      const msg = error?.message || "Failed to connect to agent. Ensure backend is running on port 8002.";
      get().addMessage({ role: 'assistant', content: `❌ ${msg}` });
      get().addTerminalLog(`CRITICAL ERROR: ${msg}`);
    }
  },

  // =========================================================
  // Submit fields (follow-up answers)
  // =========================================================
  submitFields: async (fields: Record<string, any>) => {
    const state = get();
    if (!state.sessionId) {
      get().addMessage({ role: 'assistant', content: 'No active session. Please start a new conversation.' });
      return;
    }

    set({ status: 'validating' });
    get().addAgentStatus('validating', '⚙️', 'Validating your inputs...');
    get().addTerminalLog(`[Agent] Validating submitted fields...`);

    try {
      await new Promise(r => setTimeout(r, 300));

      // Inject Agent Wallet address if available
      const agentWalletAddress = useAgentWalletStore.getState().agentWalletAddress;
      const mergedFields = { ...state.extractedFields, ...fields };
      if (agentWalletAddress && !mergedFields.wallet_address) {
         mergedFields.wallet_address = agentWalletAddress;
      }

      const data = await agentService.continueChat(
        state.sessionId,
        mergedFields,
        state.walletAddress || undefined,
        state.planningModel
      );

      if (data.stage === 'needs_input') {
        set({
          status: 'waiting_for_input',
          structuredQuestions: data.structured_questions || [],
          missingFields: data.validation?.missing_fields || [],
        });
        get().addMessage({ role: 'assistant', content: data.agent_message });
        get().addAgentStatus('waiting', '⏳', 'Still need some information...');
        return;
      }

      if (data.stage === 'awaiting_approval') {
        set({
          status: 'awaiting_approval',
          planMd: data.plan_md || '',
          structuredQuestions: [],
          missingFields: [],
        });

        get().addAgentStatus('planning', '📋', 'Creating automation plan...');

        // Open plan.md in the editor
        const planFileId = 'plan_md';
        set((s) => {
          const hasPlanning = s.fileTree.some(n => n.id === 'planning');
          const newTree = hasPlanning ? s.fileTree : [...s.fileTree, {
            id: 'planning',
            name: 'PLANNING',
            type: 'folder' as const,
            children: [{ id: planFileId, name: 'plan.md', type: 'file' as const }]
          }];
          
          return {
            fileTree: newTree,
            customFiles: { ...s.customFiles, [planFileId]: data.plan_md || '' },
            openFiles: [...new Set([...s.openFiles, planFileId])],
            activeTab: planFileId,
            activeView: 'compile' as const,
          };
        });

        get().addMessage({ role: 'assistant', content: data.agent_message });
        get().addTerminalLog(`[Agent] All inputs valid. Plan generated.`);
        return;
      }

    } catch (error: any) {
      console.error("[PlaygroundStore] Continue error:", error);
      set({ status: 'error' });
      get().addMessage({ role: 'assistant', content: `❌ ${error?.message || 'Failed to submit fields.'}` });
      get().addTerminalLog(`ERROR: ${error?.message}`);
    }
  },

  // =========================================================
  // Approve / reject plan
  // =========================================================
  approvePlan: async (approved: boolean, changes?: string) => {
    const state = get();
    if (!state.sessionId) {
      get().addMessage({ role: 'assistant', content: 'No active session.' });
      return;
    }

    if (!approved) {
      get().addMessage({ role: 'user', content: `Request changes: ${changes || 'Please modify the plan.'}` });
      set({ status: 'waiting_for_input' });
      
      try {
        const data = await agentService.approvePlan(state.sessionId, false, changes, state.codegenModel);
        get().addMessage({ role: 'assistant', content: data.agent_message });
      } catch (error: any) {
        get().addMessage({ role: 'assistant', content: `❌ ${error?.message}` });
      }
      return;
    }

    // Approved!
    get().addMessage({ role: 'user', content: '✅ Plan approved. Proceed with code generation.' });
    set({ status: 'generating' });
    get().addAgentStatus('generating', '⚡', 'Synthesizing infrastructure...');
    get().addTerminalLog('[Agent] Plan approved. Synthesizing protocol suite...');

    try {
      const data = await agentService.approvePlan(state.sessionId, true);
      handleCodeGenComplete(data);
    } catch (error: any) {
      set({ status: 'error' });
      get().addMessage({ role: 'assistant', content: '❌ Synthesis failed.' });
    }
  },
}));


// =========================================================
// Helper: process code generation completion
// =========================================================
function handleCodeGenComplete(data: any) {
  const store = usePlaygroundStore.getState();
  const incoming: Record<string, string> = data.files || {};
  
  const customFiles = { ...store.customFiles };
  const fileTree = [...store.fileTree];
  const openFiles = [...store.openFiles];

  Object.entries(incoming).forEach(([name, content]) => {
     const id = `file_${name.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
     customFiles[id] = content;
     if (!fileTree.find(n => n.id === id)) {
        fileTree.push({ id, name, type: 'file' });
     }
     if (!openFiles.includes(id)) openFiles.push(id);
  });

  usePlaygroundStore.setState({
    status: 'success',
    fileTree,
    customFiles,
    openFiles,
    spec: incoming['spec.json'] || incoming['config.json'] || store.spec,
    activeTab: Object.keys(incoming).find(k => k.endsWith('.py')) 
                ? `file_${Object.keys(incoming).find(k => k.endsWith('.py'))?.toLowerCase().replace(/[^a-z0-9]/g, '_')}` 
                : openFiles[0],
    activeView: 'compile'
  });

  store.addAgentStatus('complete', '✅', 'Infrastructure established!');
  store.addMessage({ role: 'assistant', content: data.agent_message || 'Project established in workspace!' });
}

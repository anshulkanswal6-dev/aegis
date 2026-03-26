import { create } from 'zustand';
import { MOCK_PROJECTS, type Project } from '../lib/mock/projects';

interface ProjectState {
  projects: Project[];
  selectedProject: Project | null;
  searchQuery: string;
  selectedFilter: 'all' | 'draft' | 'ready' | 'active' | 'error';
  setSearchQuery: (q: string) => void;
  setSelectedFilter: (f: 'all' | 'draft' | 'ready' | 'active' | 'error') => void;
  selectProject: (id: string | null) => void;
  createProject: (name: string, prompt: string) => void;
  updateProject: (id: string, updates: Partial<Project>) => void;
  deleteProject: (id: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  projects: MOCK_PROJECTS,
  selectedProject: null,
  searchQuery: '',
  selectedFilter: 'all',
  
  setSearchQuery: (q) => set({ searchQuery: q }),
  setSelectedFilter: (f) => set({ selectedFilter: f }),
  
  selectProject: (id) => set((state) => ({
    selectedProject: id ? state.projects.find(p => p.id === id) || null : null
  })),

  createProject: (name, prompt) => set((state) => ({
    projects: [
      {
        id: `proj-${Math.random().toString(36).substr(2, 9)}`,
        name,
        prompt,
        status: 'draft',
        chain: 'BNB',
        lastUpdated: new Date().toISOString(),
        trigger: 'None',
        actions: [],
        spec: '{}',
        code: '// New Project'
      },
      ...state.projects
    ]
  })),

  updateProject: (id, updates) => set((state) => ({
    projects: state.projects.map(p => p.id === id ? { ...p, ...updates, lastUpdated: new Date().toISOString() } : p)
  })),

  deleteProject: (id) => set((state) => ({
    projects: state.projects.filter(p => p.id !== id)
  }))
}));

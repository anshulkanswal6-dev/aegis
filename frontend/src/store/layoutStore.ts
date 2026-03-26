import { create } from 'zustand';

interface LayoutState {
  isSidebarCollapsed: boolean;
  isChatCollapsed: boolean;
  isTerminalCollapsed: boolean;
  toggleSidebar: () => void;
  toggleChat: () => void;
  toggleTerminal: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setChatCollapsed: (collapsed: boolean) => void;
  setTerminalCollapsed: (collapsed: boolean) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  isSidebarCollapsed: false,
  isChatCollapsed: false,
  isTerminalCollapsed: false,
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
  toggleChat: () => set((state) => ({ isChatCollapsed: !state.isChatCollapsed })),
  toggleTerminal: () => set((state) => ({ isTerminalCollapsed: !state.isTerminalCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
  setChatCollapsed: (collapsed) => set({ isChatCollapsed: collapsed }),
  setTerminalCollapsed: (collapsed) => set({ isTerminalCollapsed: collapsed }),
}));

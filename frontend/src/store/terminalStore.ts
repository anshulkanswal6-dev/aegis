import { create } from 'zustand';
import type { TerminalLog } from '../types/terminal';

interface TerminalState {
  logs: TerminalLog[];
  isExpanded: boolean;
  addLog: (log: Omit<TerminalLog, 'id' | 'timestamp'>) => void;
  clearLogs: () => void;
  toggleExpanded: () => void;
  setExpanded: (expanded: boolean) => void;
}

export const useTerminalStore = create<TerminalState>((set) => ({
  logs: [],
  isExpanded: false,
  addLog: (log) =>
    set((state) => ({
      logs: [
        ...state.logs,
        {
          ...log,
          id: Math.random().toString(36).substring(7),
          timestamp: Date.now(),
        },
      ],
      // Auto-expand on new important logs if closed
      isExpanded: log.type !== 'info' ? true : state.isExpanded,
    })),
  clearLogs: () => set({ logs: [] }),
  toggleExpanded: () => set((state) => ({ isExpanded: !state.isExpanded })),
  setExpanded: (expanded: boolean) => set({ isExpanded: expanded }),
}));

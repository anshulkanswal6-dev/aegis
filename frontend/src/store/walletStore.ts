import { create } from 'zustand';
import type { Address } from 'viem';

interface AgentWalletState {
  agentWalletAddress: Address | null;
  ethBalance: bigint;
  isCreating: boolean;
  isFunding: boolean;
  isWithdrawing: boolean;
  setAgentWalletAddress: (address: Address | null) => void;
  setEthBalance: (balance: bigint) => void;
  setCreating: (loading: boolean) => void;
  setFunding: (loading: boolean) => void;
  setWithdrawing: (loading: boolean) => void;
}

export const useAgentWalletStore = create<AgentWalletState>((set) => ({
  agentWalletAddress: null,
  ethBalance: 0n,
  isCreating: false,
  isFunding: false,
  isWithdrawing: false,
  setAgentWalletAddress: (address) => set({ agentWalletAddress: address }),
  setEthBalance: (balance) => set({ ethBalance: balance }),
  setCreating: (loading) => set({ isCreating: loading }),
  setFunding: (loading) => set({ isFunding: loading }),
  setWithdrawing: (loading) => set({ isWithdrawing: loading }),
}));

import type { Address } from 'viem';

// TODO: Replace with actually deployed contract address
export const AGENT_WALLET_FACTORY_ADDRESS: Address = '0xe110b94037decBc6cdFfc499ba4d6B528E4cF1ed';

export const CONTRACT_CONFIG = {
  factory: {
    address: AGENT_WALLET_FACTORY_ADDRESS,
  },
} as const;

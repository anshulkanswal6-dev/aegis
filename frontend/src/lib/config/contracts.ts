import type { Address } from 'viem';

// YOUR manually deployed Factory from Remix
export const AGENT_WALLET_FACTORY_ADDRESS: Address = '0x7030948Eb01d864Fa409884ff3441B13e16681d2';

// The Aegis platform executor
export const PLATFORM_EXECUTOR_ADDRESS: Address = '0xFb63ec4de9354cE2b143B372813Be99680f6880f';

export const CONTRACT_CONFIG = {
  factory: {
    address: AGENT_WALLET_FACTORY_ADDRESS,
  },
  executor: {
    address: PLATFORM_EXECUTOR_ADDRESS,
  }
} as const;

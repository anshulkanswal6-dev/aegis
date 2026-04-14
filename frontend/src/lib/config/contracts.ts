import type { Address } from 'viem';

// deployed Agent Factory from Remix
export const AGENT_WALLET_FACTORY_ADDRESS: Address = '0x8cbb60c06569E93a2A0AE09bc00988f62753E73E';

// The Aegis platform executor
export const PLATFORM_EXECUTOR_ADDRESS: Address = '0xf7C7FfEdc58B49C75C56019710B2C5C597C5E29E';

export const CONTRACT_CONFIG = {
  factory: {
    address: AGENT_WALLET_FACTORY_ADDRESS,
  },
  executor: {
    address: PLATFORM_EXECUTOR_ADDRESS,
  }
} as const;

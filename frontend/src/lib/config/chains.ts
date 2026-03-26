import { bscTestnet } from 'wagmi/chains';

export const SUPPORTED_CHAINS = [bscTestnet] as const;
export const DEFAULT_CHAIN = bscTestnet;

export const EXPLORER_URLS: Record<number, string> = {
  [bscTestnet.id]: 'https://testnet.bscscan.com',
};

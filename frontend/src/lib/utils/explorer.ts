import { EXPLORER_URLS, MONAD_TESTNET_ID } from '../config/chains';

export const getExplorerUrl = (chainId: number | undefined, hash: string, type: 'tx' | 'address' = 'tx'): string => {
  const baseUrl = (chainId && EXPLORER_URLS[chainId]) ? EXPLORER_URLS[chainId] : EXPLORER_URLS[MONAD_TESTNET_ID];
  return `${baseUrl}/${type}/${hash}`;
};

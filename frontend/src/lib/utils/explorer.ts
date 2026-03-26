import { EXPLORER_URLS } from '../config/chains';

export const getExplorerUrl = (chainId: number | undefined, hash: string, type: 'tx' | 'address' = 'tx'): string => {
  const baseUrl = chainId ? EXPLORER_URLS[chainId] || EXPLORER_URLS[1] : EXPLORER_URLS[1];
  return `${baseUrl}/${type}/${hash}`;
};

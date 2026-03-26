import { formatEther } from 'viem';

export const formatAddress = (address: string): string =>
  `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;

export const formatEth = (wei: bigint | string | number | undefined): string => {
  if (!wei) return '0.00';
  const val = typeof wei === 'string' ? BigInt(wei) : BigInt(wei);
  return Number(formatEther(val)).toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
};

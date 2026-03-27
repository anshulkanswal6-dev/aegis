import { WagmiProvider, createConfig, http, createStorage } from 'wagmi';
import { defineChain } from 'viem';
import { injected } from 'wagmi/connectors';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';

const monadTestnet = defineChain({
  id: 10143,
  name: 'Monad Testnet',
  nativeCurrency: { name: 'MON', symbol: 'MON', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://testnet-rpc.monad.xyz'] },
  },
  blockExplorers: {
    default: { name: 'MonadExplorer', url: 'https://testnet.monadexplorer.com' },
  },
  testnet: true,
});

const queryClient = new QueryClient();

// Safe storage fallback for browsers with blocked cookies/storage (like Brave or restricted iframes)
const getSafeStorage = () => {
  if (typeof window === 'undefined') return undefined;

  try {
    // Attempting to even READ the 'localStorage' property can throw a SecurityError
    if (window.localStorage) {
      return window.localStorage;
    }
  } catch (e) {
    // If access is denied, fall back to a dummy memory storage
  }

  return {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
    key: () => null,
    get length() { return 0; },
    clear: () => {},
  } as Storage;
};

const config = createConfig({
  ssr: true, // Enable SSR to avoid early storage access
  storage: createStorage({
    storage: getSafeStorage(),
  }),
  chains: [monadTestnet],
  connectors: [injected()],
  transports: {
    [monadTestnet.id]: http(),
  },
});

export function Web3Provider({ children }: { children: ReactNode }) {
  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    </WagmiProvider>
  );
}

import { WagmiProvider, createConfig, http, createStorage } from "wagmi";
import { defineChain } from "viem";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConnectKitProvider, getDefaultConfig } from "connectkit";
import React, { useMemo } from 'react';

const WALLETCONNECT_PROJECT_ID = "d802ecff1840858c5e070532b09ca450";

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

// Safe storage fallback
const getSafeStorage = () => {
  if (typeof window === 'undefined') return undefined;
  try {
    if (window.localStorage && window.sessionStorage) return window.localStorage;
  } catch (e) {}

  return {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
    key: () => null,
    get length() { return 0; },
    clear: () => {},
  } as Storage;
};

import { useThemeStore } from '../hooks/useTheme';

export const Web3Provider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = useMemo(() => new QueryClient(), []);
  const { resolvedTheme } = useThemeStore();

  const config = useMemo(() => {
    try {
      return createConfig(
        getDefaultConfig({
          chains: [monadTestnet],
          walletConnectProjectId: WALLETCONNECT_PROJECT_ID,
          appName: "AEGIS",
          appDescription: "Build on-chain agents with ease",
          appUrl: "https://aegis.automation",
          appIcon: "https://aegis.automation/logo.png",
          storage: createStorage({
            storage: getSafeStorage(),
          }),
        })
      );
    } catch (e) {
      console.warn("[Web3Provider] Caught initialization error.", e);
      return createConfig({
        chains: [monadTestnet],
        transports: { [monadTestnet.id]: http('https://testnet-rpc.monad.xyz') },
        storage: createStorage({ storage: getSafeStorage() }),
      });
    }
  }, []);

  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>
        <link href="https://fonts.cdnfonts.com/css/pt-root-ui" rel="stylesheet" />
        <ConnectKitProvider theme={resolvedTheme === 'dark' ? 'midnight' : 'nouns'} mode={resolvedTheme}>
          {children}
        </ConnectKitProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
};
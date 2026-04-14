/**
 * AEGIS Branding & Network Configuration
 * This file centralizes all platform identity tokens.
 * Values are mapped from meta.env (Vite) to enable Zero-Touch migration.
 */

export const BRANDING = {
  // --- Platform Identity ---
  siteName: import.meta.env.VITE_SITE_NAME || 'AEGIS',
  tagline: import.meta.env.VITE_TAGLINE || 'On-chain Agentic Automations',

  // --- Network Configuration (EVM) ---
  networkName: import.meta.env.VITE_NETWORK_NAME || 'Monad Testnet',
  currencySymbol: import.meta.env.VITE_CURRENCY_SYMBOL || 'MON',
  chainId: Number(import.meta.env.VITE_CHAIN_ID || '10143'),
  rpcUrl: import.meta.env.VITE_RPC_URL || 'https://testnet-rpc.monad.xyz',
  explorerUrl: import.meta.env.VITE_EXPLORER_URL || 'https://testnet.monadexplorer.com',

  // --- Layout Defaults ---
  defaultAvatar: 'https://api.dicebear.com/7.x/identicon/svg?seed=AEGIS',
};

/**
 * Formats a block explorer link dynamically.
 */
export const getExplorerLink = (type: 'address' | 'tx', value: string) => {
  const base = BRANDING.explorerUrl.replace(/\/$/, '');
  return `${base}/${type}/${value}`;
};

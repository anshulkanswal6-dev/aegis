import { useEffect } from 'react';
import { useAccount, useReadContract, useWriteContract, useChainId, usePublicClient, useSwitchChain } from 'wagmi';
import { parseEther, getAddress } from 'viem';
import type { Address } from 'viem';
import { AgentWalletFactoryABI } from '../lib/abi/AgentWalletFactory';
import { AgentWalletABI } from '../lib/abi/AgentWallet';
import { CONTRACT_CONFIG } from '../lib/config/contracts';
import { useAgentWalletStore } from '../store/walletStore';
import { useTerminalStore } from '../store/terminalStore';
import { getExplorerUrl } from '../lib/utils/explorer';
import { formatEth } from '../lib/utils/format';
import { cleanWeb3Error } from '../lib/utils/errors';
import { useToast } from './useToast';
import { PLATFORM_CHAIN_ID } from '../lib/config/chains';
import { BRANDING } from '../lib/config/branding';


export function useAgentWallet() {
  const { toast } = useToast();
  const { address: userAddress, isConnected, chain } = useAccount();
  const chainSymbol = chain?.nativeCurrency.symbol || 'MON';
  const chainId = useChainId();
  const publicClient = usePublicClient();
  const addLog = useTerminalStore((s) => s.addLog);
  const { 
    agentWalletAddress, setAgentWalletAddress, 
    setEthBalance, ethBalance,
    setCreating, isCreating,
    setFunding, isFunding,
    setWithdrawing, isWithdrawing
  } = useAgentWalletStore();

  const { writeContractAsync } = useWriteContract();
  const { switchChainAsync } = useSwitchChain();


  // Read current agent wallet for the user
  const { data: currentWallet, refetch: refetchWallet } = useReadContract({
    address: CONTRACT_CONFIG.factory.address,
    abi: AgentWalletFactoryABI,
    functionName: 'getMyWallet',
    account: userAddress,
    query: {
      enabled: isConnected && !!userAddress,
    }
  });

  // Effect to update global store when wallet address changes
  useEffect(() => {
    if (currentWallet && currentWallet !== '0x0000000000000000000000000000000000000000') {
      setAgentWalletAddress(currentWallet as Address);
    } else {
      setAgentWalletAddress(null);
    }
  }, [currentWallet, setAgentWalletAddress]);

  // Read agent balance
  const { data: balanceData, refetch: refetchBalance } = useReadContract({
    address: agentWalletAddress || undefined,
    abi: AgentWalletABI,
    functionName: 'getEthBalance',
    query: {
      enabled: !!agentWalletAddress,
    }
  });

  useEffect(() => {
    if (balanceData !== undefined) {
      setEthBalance(balanceData as bigint);
    }
  }, [balanceData, setEthBalance]);

  const createWallet = async (executor: string, limit: string) => {
    if (!userAddress) return;
    setCreating(true);
    addLog({ type: 'info', message: 'Initiating Agent Wallet creation...' });

    try {
      if (chainId !== PLATFORM_CHAIN_ID) {
        addLog({ type: 'info', message: `Switching network to ${BRANDING.networkName}...` });
        await switchChainAsync({ chainId: PLATFORM_CHAIN_ID });
      }

      const hash = await writeContractAsync({
        address: getAddress(CONTRACT_CONFIG.factory.address),
        abi: AgentWalletFactoryABI,
        functionName: 'createWallet',
        args: [getAddress(executor) as Address, parseEther(limit)],
      });

      addLog({ 
        type: 'info', 
        message: 'Wallet creation transaction submitted.',
        explorerUrl: getExplorerUrl(chainId, hash, 'tx')
      });

      const recipe = await publicClient?.waitForTransactionReceipt({ hash });
      
      if (recipe?.status === 'success') {
        addLog({ type: 'success', message: 'Agent Wallet created successfully!' });
        toast('success', 'Wallet Created', 'Your new agent wallet is ready to use.');
        await refetchWallet();
      } else {
        throw new Error('Transaction failed');
      }
    } catch (error: any) {
      const cleanMsg = cleanWeb3Error(error);
      addLog({ type: 'error', message: `Failed to create wallet: ${cleanMsg}` });
      toast('error', 'Creation Failed', cleanMsg);
    } finally {
      setCreating(false);
    }
  };

  const deposit = async (amountEth: string) => {
    if (!userAddress || !agentWalletAddress) return;
    setFunding(true);
    addLog({ type: 'info', message: `Depositing ${amountEth} ${chainSymbol} to Agent Wallet...` });

    try {
      if (chainId !== PLATFORM_CHAIN_ID) {
        addLog({ type: 'info', message: `Switching network to ${BRANDING.networkName}...` });
        await switchChainAsync({ chainId: PLATFORM_CHAIN_ID });
      }

      const hash = await writeContractAsync({
        address: agentWalletAddress,
        abi: AgentWalletABI,
        functionName: 'depositETH',
        value: parseEther(amountEth),
      });

      addLog({ 
        type: 'info', 
        message: 'Deposit transaction submitted.',
        explorerUrl: getExplorerUrl(chainId, hash, 'tx')
      });

      const recipe = await publicClient?.waitForTransactionReceipt({ hash });
      
      if (recipe?.status === 'success') {
        addLog({ type: 'success', message: `${amountEth} ${chainSymbol} deposited to agent wallet` });
        toast('success', 'Deposit Successful', `${amountEth} ${chainSymbol} has been moved to your agent.`);
        await refetchBalance();
      } else {
        throw new Error('Transaction reverted onchain');
      }
    } catch (error: any) {
      const cleanMsg = cleanWeb3Error(error);
      addLog({ type: 'error', message: `Failed to deposit: ${cleanMsg}` });
      toast('error', 'Deposit Failed', cleanMsg);
    } finally {
      setFunding(false);
    }
  };

  const withdraw = async (amountEth: string) => {
    if (!userAddress || !agentWalletAddress) return;
    setWithdrawing(true);
    addLog({ type: 'info', message: `Withdrawing ${amountEth} ${chainSymbol} from Agent Wallet...` });

    try {
      if (chainId !== PLATFORM_CHAIN_ID) {
        addLog({ type: 'info', message: `Switching network to ${BRANDING.networkName}...` });
        await switchChainAsync({ chainId: PLATFORM_CHAIN_ID });
      }

      const hash = await writeContractAsync({
        address: agentWalletAddress,
        abi: AgentWalletABI,
        functionName: 'withdrawETH',
        args: [parseEther(amountEth)],
      });

      addLog({ 
        type: 'info', 
        message: 'Withdrawal transaction submitted.',
        explorerUrl: getExplorerUrl(chainId, hash, 'tx')
      });

      const recipe = await publicClient?.waitForTransactionReceipt({ hash });
      
      if (recipe?.status === 'success') {
        addLog({ type: 'success', message: `${amountEth} ${chainSymbol} withdrawn back to owner wallet` });
        toast('success', 'Withdrawal Successful', `${amountEth} ${chainSymbol} returned to your main wallet.`);
        await refetchBalance();
      } else {
        throw new Error('Transaction reverted onchain');
      }
    } catch (error: any) {
      const cleanMsg = cleanWeb3Error(error);
      addLog({ type: 'error', message: `Failed to withdraw: ${cleanMsg}` });
      toast('error', 'Withdrawal Failed', cleanMsg);
    } finally {
      setWithdrawing(false);
    }
  };

  const authorizePlatformExecutor = async () => {
    if (!userAddress || !agentWalletAddress) return;
    addLog({ type: 'info', message: 'Fetching platform executor address...' });

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8002'}/automations/executor/address`);
      const data = await response.json();

      if (!data.address) {
        throw new Error(data.error || 'No executor address found on platform backend.');
      }

      const platformExecutor = data.address as Address;
      addLog({ type: 'info', message: `Platform executor address: ${platformExecutor}. Initiating authorization...` });

      const hash = await writeContractAsync({
        address: agentWalletAddress,
        abi: AgentWalletABI,
        functionName: 'updateExecutor',
        args: [platformExecutor],
      });

      addLog({ 
        type: 'info', 
        message: 'Authorization transaction submitted.',
        explorerUrl: getExplorerUrl(chainId, hash, 'tx')
      });

      const recipe = await publicClient?.waitForTransactionReceipt({ hash });
      
      if (recipe?.status === 'success') {
        addLog({ type: 'success', message: 'Platform Agent authorized successfully!' });
        toast('success', 'Agent Authorized', 'Platform can now execute transactions on your behalf.');
      } else {
        throw new Error('Transaction reverted onchain');
      }
    } catch (error: any) {
      const cleanMsg = cleanWeb3Error(error);
      addLog({ type: 'error', message: `Authorization failed: ${cleanMsg}` });
      toast('error', 'Authorization Failed', cleanMsg);
    }
  };

  const getExecutor = async (): Promise<Address | null> => {
    if (!agentWalletAddress) return null;
    try {
      const data = await publicClient?.readContract({
        address: agentWalletAddress,
        abi: AgentWalletABI,
        functionName: 'executor',
      });
      return data as Address;
    } catch (e) {
      return null;
    }
  };

  const deleteWallet = async () => {
    if (!userAddress || !agentWalletAddress) {
        toast('error', 'Zero Address', 'No agent wallet found in current factory database.');
        return;
    }
    
    setWithdrawing(true); 
    addLog({ 
      type: 'info', 
      message: `Initiating destruction for wallet: ${agentWalletAddress} on Factory: ${CONTRACT_CONFIG.factory.address}` 
    });

    try {
      const hash = await writeContractAsync({
        address: CONTRACT_CONFIG.factory.address,
        abi: AgentWalletFactoryABI,
        functionName: 'deleteWallet',
        args: [],
      });

      addLog({ 
        type: 'info', 
        message: 'Deletion transaction submitted.',
        explorerUrl: getExplorerUrl(chainId, hash, 'tx')
      });

      const recipe = await publicClient?.waitForTransactionReceipt({ hash });
      
      if (recipe?.status === 'success') {
        addLog({ type: 'success', message: 'Agent Wallet successfully destroyed and mapping cleared.' });
        toast('success', 'Wallet Destroyed', 'Agent wallet decommissioned successfully.');
        await refetchWallet();
        setAgentWalletAddress(null);
      } else {
        throw new Error('Transaction reverted onchain. Ensure you are using the correct Factory version.');
      }
    } catch (error: any) {
      const cleanMsg = cleanWeb3Error(error);
      addLog({ type: 'error', message: `Deletion failed: ${cleanMsg}` });
      toast('error', 'Deletion Failed', cleanMsg);
    } finally {
      setWithdrawing(false);
    }
  };

  return {
    agentWalletAddress,
    ethBalance,
    formatBalance: formatEth(ethBalance),
    isCreating,
    isFunding,
    isWithdrawing,
    createWallet,
    deposit,
    withdraw,
    deleteWallet,
    authorizePlatformExecutor,
    getExecutor,
    refetchBalance,
    refetchWallet,
    chainSymbol
  };
}

import '@rainbow-me/rainbowkit/styles.css';
import { connectorsForWallets } from '@rainbow-me/rainbowkit';
import {
  metaMaskWallet,
  injectedWallet,
  coinbaseWallet,
  rainbowWallet,
} from '@rainbow-me/rainbowkit/wallets';
import { createConfig, http } from 'wagmi';
import { baseSepolia } from 'wagmi/chains';

const projectId = '611d8db7ae43cd6fa0f4bebe67148fbb';

// Force standard browser extension (EOA) instead of Smart Wallet passkeys
coinbaseWallet.preference = 'eoaOnly';

const connectors = connectorsForWallets(
  [
    {
      groupName: 'Installed Wallets',
      wallets: [
        injectedWallet,
        metaMaskWallet,
        coinbaseWallet,
        rainbowWallet,
      ],
    },
  ],
  {
    appName: 'AgentCourt Protocol',
    projectId,
  }
);

export const config = createConfig({
  connectors,
  chains: [baseSepolia],
  transports: {
    [baseSepolia.id]: http('https://base-sepolia-rpc.publicnode.com'),
  },
  ssr: true,
});

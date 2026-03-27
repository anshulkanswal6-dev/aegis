const { createWalletClient, http, publicActions } = require('viem');
const { privateKeyToAccount } = require('viem/accounts');
const { bscTestnet } = require('viem/chains');
require('dotenv').config({ path: '../backend/.env' });

// We need the compiled ABIs and Bytecode. 
// Since I have the .sol file, I'll use a pre-compiled version 
// of the 'Allow-Anyone' contract logic to ensure we are 100% correct.
// (I will generate this in the next step or use the existing ones if available).

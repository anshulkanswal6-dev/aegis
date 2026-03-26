from __future__ import annotations

import re
import json
import os
import requests
from web3 import Web3
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


class ActionValidationError(Exception):
    pass


class UnsupportedActionError(Exception):
    pass


EVM_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_RE = re.compile(r"^https?://[^\s]+$")


def validate_evm_address(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not EVM_ADDRESS_RE.match(value):
        raise ActionValidationError(f"{field_name} is not a valid EVM address")


def validate_email(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not EMAIL_RE.match(value):
        raise ActionValidationError(f"{field_name} is not a valid email")


def validate_url(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not URL_RE.match(value):
        raise ActionValidationError(f"{field_name} is not a valid URL")


def validate_required_fields(params: Dict[str, Any], required_fields: List[str]) -> None:
    for field in required_fields:
        if field not in params or params[field] in (None, "", []):
            raise ActionValidationError(f"Missing required field: {field}")


def parse_numeric(value: Any, field_name: str = "value") -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ActionValidationError(f"{field_name} must be numeric")


@dataclass
class ActionContext:
    chain: Optional[str] = None
    rpc_url: Optional[str] = None
    wallet_address: Optional[str] = None
    automation_id: Optional[str] = None
    secrets: Optional[Dict[str, Any]] = None
    memory: Optional[Dict[str, Any]] = None


def action_send_native_token(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["recipient_address", "amount"])
    validate_evm_address(params["recipient_address"], "recipient_address")
    amount_eth = parse_numeric(params["amount"], "amount")

    if not ctx.rpc_url:
        return {"success": False, "error": "Missing RPC URL in context"}
    if not ctx.wallet_address:
        return {"success": False, "error": "Missing Agent Wallet address in context"}

    # Use backend executor key from .env (can also be passed in ctx.secrets)
    executor_key = (ctx.secrets or {}).get("private_key") or os.getenv("EXECUTOR_PRIVATE_KEY") or os.getenv("PRIVATE_KEY")
    if not executor_key:
        return {"success": False, "error": "Executor private key not configured in backend .env"}

    w3 = Web3(Web3.HTTPProvider(ctx.rpc_url))
    try:
        executor_account = w3.eth.account.from_key(executor_key)
        agent_wallet_address = w3.to_checksum_address(ctx.wallet_address)
        recipient_address = w3.to_checksum_address(params["recipient_address"])
        amount_wei = w3.to_wei(amount_eth, 'ether')

        # ABI for executeETH(target, amount, data)
        # We call the AgentWallet contract, which in turn transfers ETH to recipient
        abi = [{
            "type": "function", "name": "executeETH",
            "inputs": [{"name": "target", "type": "address"}, {"name": "amount", "type": "uint256"}, {"name": "data", "type": "bytes"}],
            "outputs": [{"name": "result", "type": "bytes"}], "stateMutability": "nonpayable"
        }]
        contract = w3.eth.contract(address=agent_wallet_address, abi=abi)

        # Build transaction
        nonce = w3.eth.get_transaction_count(executor_account.address)
        tx = contract.functions.executeETH(recipient_address, amount_wei, b"").build_transaction({
            'from': executor_account.address,
            'nonce': nonce,
            'gas': 100000, # Simplified estimation
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        })

        signed_tx = w3.eth.account.sign_transaction(tx, executor_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_id = w3.to_hex(tx_hash)

        return {
            "success": True,
            "action": "send_native_token",
            "message": f"Successfully sent {amount_eth} native token from Agent Wallet {agent_wallet_address} to {recipient_address}",
            "tx_hash": tx_id
        }
    except Exception as e:
        return {"success": False, "error": f"On-chain execution failed: {str(e)}"}


def action_send_erc20(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["token_address", "recipient_address", "amount"])
    validate_evm_address(params["token_address"], "token_address")
    validate_evm_address(params["recipient_address"], "recipient_address")
    amount = parse_numeric(params["amount"], "amount")
    return {
        "success": True,
        "action": "send_erc20",
        "message": f"Would send {amount} ERC20 from {params['token_address']} to {params['recipient_address']}",
        "tx_hash": None
    }


def action_batch_send_erc20(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["token_address", "recipients"])
    validate_evm_address(params["token_address"], "token_address")
    recipients = params["recipients"]
    if not isinstance(recipients, list):
        raise ActionValidationError("recipients must be a list")
    return {
        "success": True,
        "action": "batch_send_erc20",
        "message": f"Would batch send ERC20 to {len(recipients)} recipients",
        "tx_hash": None
    }


def action_swap_exact_in(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["dex_router", "token_in", "token_out", "amount_in", "slippage_bps"])
    validate_evm_address(params["dex_router"], "dex_router")
    validate_evm_address(params["token_in"], "token_in")
    validate_evm_address(params["token_out"], "token_out")
    amount_in = parse_numeric(params["amount_in"], "amount_in")
    slippage = parse_numeric(params["slippage_bps"], "slippage_bps")
    return {
        "success": True,
        "action": "swap_exact_in",
        "message": f"Would swap {amount_in} from {params['token_in']} to {params['token_out']} using router {params['dex_router']} with {slippage} bps slippage",
        "tx_hash": None
    }


def action_swap_exact_out(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["dex_router", "token_in", "token_out", "amount_out", "max_amount_in", "slippage_bps"])
    return {
        "success": True,
        "action": "swap_exact_out",
        "message": "Would perform exact-out swap",
        "tx_hash": None
    }


def action_claim_faucet(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["faucet_url", "claim_method"])
    validate_url(params["faucet_url"], "faucet_url")
    return {
        "success": True,
        "action": "claim_faucet",
        "message": f"Would claim faucet via {params['claim_method']} from {params['faucet_url']}",
        "tx_hash": None
    }


from adapters import NotificationAdapter

def action_send_email_notification(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["to", "subject", "message"])
    validate_email(params["to"], "to")
    
    notifier = NotificationAdapter()
    result = notifier.send_email(
        to_email=params["to"],
        subject=params["subject"],
        body=params["message"],
        automation_id=ctx.automation_id or "unknown",
        wallet=ctx.wallet_address or "unknown"
    )
    
    if result.get("success"):
        return {
            "success": True,
            "action": "send_email_notification",
            "message": f"Successfully sent email to {params['to']}"
        }
    else:
        return {
            "success": False,
            "action": "send_email_notification",
            "message": f"Failed to send email to {params['to']}: {result.get('error')}"
        }


def action_send_webhook(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["webhook_url", "payload"])
    validate_url(params["webhook_url"], "webhook_url")
    return {
        "success": True,
        "action": "send_webhook",
        "message": f"Would send webhook to {params['webhook_url']}",
        "payload": params["payload"]
    }


def action_transfer_nft(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["nft_contract", "token_id", "recipient_address"])
    validate_evm_address(params["nft_contract"], "nft_contract")
    validate_evm_address(params["recipient_address"], "recipient_address")
    return {
        "success": True,
        "action": "transfer_nft",
        "message": f"Would transfer NFT {params['token_id']} from {params['nft_contract']} to {params['recipient_address']}",
        "tx_hash": None
    }


def action_list_nft(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["marketplace", "nft_contract", "token_id", "listing_price"])
    validate_evm_address(params["nft_contract"], "nft_contract")
    parse_numeric(params["listing_price"], "listing_price")
    return {
        "success": True,
        "action": "list_nft",
        "message": f"Would list NFT {params['token_id']} from {params['nft_contract']} on {params['marketplace']}",
        "tx_hash": None
    }


def action_log_message(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["message"])
    return {
        "success": True,
        "action": "log_message",
        "message": params["message"]
    }


def action_get_balance(params: Dict[str, Any], ctx: ActionContext) -> Dict[str, Any]:
    validate_required_fields(params, ["address"])
    validate_evm_address(params["address"], "address")
    
    # Prioritize RPC URL: params > context
    rpc_url = params.get("rpc_url") or ctx.rpc_url
    
    if not rpc_url:
        return {
            "success": False,
            "action": "get_balance",
            "message": "Missing rpc_url. Please provide an RPC URL or ensure chain context is set."
        }

    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBalance",
        "params": [params["address"], "latest"],
        "id": 1
    }

    try:
        response = requests.post(rpc_url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            # Result is hex string in Wei
            balance_wei = int(data["result"], 16)
            balance_eth = balance_wei / 10**18
            return {
                "success": True,
                "action": "get_balance",
                "message": f"Balance for {params['address']} is {balance_eth} ETH",
                "balance_wei": str(balance_wei),
                "balance_eth": balance_eth,
                "rpc_used": rpc_url
            }
        else:
            error_msg = data.get("error", {}).get("message", "Unknown RPC error")
            return {
                "success": False,
                "action": "get_balance",
                "message": f"RPC Error: {error_msg}"
            }
    except Exception as e:
        return {
            "success": False,
            "action": "get_balance",
            "message": f"Request failed: {str(e)}"
        }


ACTION_REGISTRY: Dict[str, Callable[[Dict[str, Any], ActionContext], Dict[str, Any]]] = {
    "send_native_token": action_send_native_token,
    "send_erc20": action_send_erc20,
    "batch_send_erc20": action_batch_send_erc20,
    "swap_exact_in": action_swap_exact_in,
    "swap_exact_out": action_swap_exact_out,
    "claim_faucet": action_claim_faucet,
    "send_email_notification": action_send_email_notification,
    "send_webhook": action_send_webhook,
    "transfer_nft": action_transfer_nft,
    "list_nft": action_list_nft,
    "log_message": action_log_message,
    "get_balance": action_get_balance,
}


class ActionEngine:
    def __init__(self, registry: Optional[Dict[str, Callable[[Dict[str, Any], ActionContext], Dict[str, Any]]]] = None):
        self.registry = registry or ACTION_REGISTRY

    def execute(self, action_type: str, params: Dict[str, Any], ctx: Optional[ActionContext] = None) -> Dict[str, Any]:
        ctx = ctx or ActionContext()
        handler = self.registry.get(action_type)
        if not handler:
            raise UnsupportedActionError(f"Unsupported action: {action_type}")
        return handler(params, ctx)
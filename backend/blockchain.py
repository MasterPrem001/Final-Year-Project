import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from web3 import Web3


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")
ORACLE_CORE_ADDRESS = os.getenv("ORACLE_CORE_ADDRESS", "")

w3 = Web3(Web3.HTTPProvider(SEPOLIA_RPC_URL))


def _load_oracle_abi() -> Any:
    abi_path = BASE_DIR / "abis" / "OracleCore.json"
    with abi_path.open("r", encoding="utf-8") as abi_file:
        payload = json.load(abi_file)

    if isinstance(payload, dict) and "abi" in payload:
        return payload["abi"]
    return payload


ORACLE_ABI = _load_oracle_abi()
# Replace the module-level oracle = ... with this:
oracle = None
if ORACLE_CORE_ADDRESS:
    try:
        oracle = w3.eth.contract(
            address=Web3.to_checksum_address(ORACLE_CORE_ADDRESS),
            abi=ORACLE_ABI,
        )
    except Exception:
        oracle = None


def push_price_onchain(
    asset: str,
    price: float,
    confidence: int,
    nodes_used: int,
    nodes_rejected: int,
) -> dict[str, Any]:
    try:
        encoded_price = int(round(float(price) * 100))
        nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(WALLET_ADDRESS))

        tx = oracle.functions.updatePrice(
            str(asset),
            encoded_price,
            int(confidence),
            int(nodes_used),
            int(nodes_rejected),
        ).build_transaction(
            {
                "from": Web3.to_checksum_address(WALLET_ADDRESS),
                "nonce": nonce,
                "chainId": CHAIN_ID,
                "gasPrice": w3.eth.gas_price,
            }
        )

        tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)

        signed = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
        raw_tx = getattr(signed, "raw_transaction", None)
        if raw_tx is None:
            raw_tx = getattr(signed, "rawTransaction", None)
        if raw_tx is None:
            raise AttributeError("Signed transaction payload not found (raw_transaction/rawTransaction)")

        tx_hash = w3.eth.send_raw_transaction(raw_tx)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        tx_hex = tx_hash.hex()
        status = "confirmed" if int(receipt.status) == 1 else "failed"
        return {
            "status": status,
            "tx_hash": tx_hex,
            "block": int(receipt.blockNumber),
            "etherscan_url": f"https://sepolia.etherscan.io/tx/{tx_hex}",
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }


def read_latest_price(asset: str) -> dict[str, Any]:
    try:
        price_raw, confidence, timestamp = oracle.functions.getLatestPrice(str(asset)).call()
        return {
            "price_raw": int(price_raw),
            "price_usd": float(price_raw) / 100.0,
            "confidence": int(confidence),
            "timestamp": int(timestamp),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
        }


def check_connection() -> dict[str, Any]:
    try:
        connected = bool(w3.is_connected())
        block_number = int(w3.eth.block_number) if connected else None
        balance_wei = (
            w3.eth.get_balance(Web3.to_checksum_address(WALLET_ADDRESS)) if connected else 0
        )
        balance_eth = float(w3.from_wei(balance_wei, "ether")) if connected else 0.0

        return {
            "connected": connected,
            "block_number": block_number,
            "wallet_balance_eth": balance_eth,
        }
    except Exception:
        return {
            "connected": False,
            "block_number": None,
            "wallet_balance_eth": 0.0,
        }
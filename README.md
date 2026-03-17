# AI-DON — AI-Powered Decentralized Oracle Network

AI-DON is a Final Year Major Project that combines **Blockchain + AI/ML + Federated Learning**.
It fetches live crypto prices from multiple exchanges, simulates oracle node submissions, detects malicious/faulty data with AI, computes a trust-weighted consensus price, and writes the final result on-chain.

---

## Project Overview

AI-DON pipeline:

1. Fetch market prices from multiple exchange APIs
2. Simulate decentralized oracle node submissions (including malicious behavior)
3. Run anomaly detection (Z-Score + Isolation Forest)
4. Compute trust-weighted consensus price
5. Store result in smart contracts
6. Visualize everything in a React dashboard
7. Simulate Federated Learning rounds across nodes

---

## Tech Stack

- **Smart Contracts:** Solidity `0.8.19`, Foundry (`forge`, `cast`, `anvil`)
- **Contract Libraries:** OpenZeppelin
- **Backend:** Python `3.10+`, FastAPI, Uvicorn
- **AI/ML:** scikit-learn, numpy, pandas
- **Scraping:** requests, aiohttp
- **Federated Learning:** Flower (`flwr`)
- **Frontend:** React 18 + Vite + Tailwind CSS + Recharts + ethers.js v6
- **Chain Integration:** web3.py (backend), ethers.js (frontend)

---

## Repository Structure

```text
oracle/
├── ai_engine/
│   ├── anomaly_detector.py
│   └── fl_simulator.py
├── backend/
│   ├── main.py
│   ├── blockchain.py
│   ├── requirements.txt
│   └── abis/
├── contracts/
│   ├── src/
│   ├── script/
│   ├── test/
│   ├── lib/
│   ├── foundry.toml
│   └── .env
├── frontend/
│   ├── src/
│   ├── package.json
│   └── .env
├── oracle_nodes/
│   └── node_simulator.py
└── scraper/
    └── scraper.py
```

---

## How to Run

## 1) Clone and enter project

```bash
git clone https://github.com/MasterPrem001/Final-Year-Project.git
cd Final-Year-Project
```

## 2) Backend setup (FastAPI)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

Run backend:

```bash
python -m backend.main
```

Backend default URL: `http://127.0.0.1:8000`

---

## 3) Frontend setup (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://127.0.0.1:5173`

---

## 4) Smart contracts (Foundry)

Install Foundry (one-time):

```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

Build and test contracts:

```bash
cd contracts
forge build
forge test
```

Run local chain:

```bash
anvil
```

Deploy with script (example):

```bash
forge script script/Deploy.s.sol --rpc-url $SEPOLIA_RPC_URL --private-key $PRIVATE_KEY --broadcast
```

---

## Environment Variables (`.env`) — Required Files

This project uses multiple `.env` files. Create each file in the correct folder.

## A) `contracts/.env`
Used by Foundry scripts and `foundry.toml` variables.

```env
PRIVATE_KEY=your_wallet_private_key
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_key
ETHERSCAN_API_KEY=your_etherscan_api_key
```

## B) `backend/.env`
Used by `backend/blockchain.py` for writing/reading on-chain data.

```env
# Contract addresses
ORACLE_CORE_ADDRESS=0xYourOracleCoreAddress
ORACLE_REGISTRY_ADDRESS=0xYourOracleRegistryAddress
DON_TOKEN_ADDRESS=0xYourDONTokenAddress
REPUTATION_ENGINE_ADDRESS=0xYourReputationEngineAddress
ORACLE_CONSUMER_ADDRESS=0xYourOracleConsumerAddress

# Network + signer
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_key
PRIVATE_KEY=your_wallet_private_key
CHAIN_ID=11155111
WALLET_ADDRESS=0xYourWalletAddress
```

## C) `frontend/.env`
Used by Vite/React (`VITE_` prefix required).

```env
VITE_ORACLE_CORE_ADDRESS=0xYourOracleCoreAddress
VITE_ORACLE_REGISTRY_ADDRESS=0xYourOracleRegistryAddress
VITE_DON_TOKEN_ADDRESS=0xYourDONTokenAddress
VITE_REPUTATION_ENGINE_ADDRESS=0xYourReputationEngineAddress
VITE_ORACLE_CONSUMER_ADDRESS=0xYourOracleConsumerAddress

VITE_CHAIN_ID=11155111
VITE_NETWORK_NAME=sepolia
VITE_SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_key
VITE_DEPLOYER_WALLET=0xYourWalletAddress
VITE_ETHERSCAN_BASE_URL=https://sepolia.etherscan.io
```

---

## Backend API Endpoints

- `GET /api/health` — service health + supported coins
- `GET /api/run-pipeline?coin=ETH` — full AI-DON round
- `GET /api/latest` — latest round output
- `GET /api/nodes` — node profiles + latest AI metrics
- `GET /api/fl-simulation?rounds=3` — run FL simulation
- `GET /api/price-history` — consensus history
- `GET /api/stats` — rounds, anomalies, detection rate
- `GET /api/blockchain-status` — RPC/chain connectivity
- `GET /api/read-price?asset=ETH` — read latest on-chain value

---

## Foundry Commands Cheat Sheet

```bash
forge build
forge test
forge test -vvvv
forge fmt
forge coverage

cast call <address> "getLatestPrice(string)" "ETH"
cast balance <address>
cast receipt <txhash>
```

---

## Prompt/Specification Used

This repository was developed from a detailed build specification for **AI-DON (AI-Powered Decentralized Oracle Network)** covering:

- end-to-end architecture (scraper → nodes → AI → consensus → blockchain)
- required file/folder structure
- Foundry deployment/testing workflow
- backend API behavior
- frontend dashboard components
- federated learning simulation behavior

---

## Security Notes

- Never commit real private keys or production RPC secrets.
- Keep `.env` files local and rotate any leaked keys immediately.
- For open-source demos, always use funded testnet wallets with limited balance.

---

## Demo Flow

1. Start backend (`python -m backend.main`)
2. Start frontend (`npm run dev` in `frontend/`)
3. Open the dashboard
4. Run pipeline for ETH/BTC
5. Observe anomaly detection, trust weights, consensus, and on-chain update status

---

## Author

Final Year Major Project: **AI-DON** by MasterPrem.

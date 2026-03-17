import { useCallback, useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function truncateAddress(address) {
    if (!address || address.length < 10) return address || "N/A";
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

function formatTimestamp(unixSeconds) {
    if (!unixSeconds) return "N/A";
    const date = new Date(Number(unixSeconds) * 1000);
    if (Number.isNaN(date.getTime())) return "N/A";
    return date.toLocaleString();
}

export default function BlockchainPanel() {
    const [loading, setLoading] = useState(false);
    const [status, setStatus] = useState(null);
    const [prices, setPrices] = useState({ ETH: null, BTC: null });
    const [error, setError] = useState("");

    const walletFromEnv = import.meta.env.VITE_DEPLOYER_WALLET || "";
    const etherscanBase = import.meta.env.VITE_ETHERSCAN_BASE_URL || "https://sepolia.etherscan.io";
    const oracleCoreAddress = import.meta.env.VITE_ORACLE_CORE_ADDRESS || "";

    const contractUrl = useMemo(() => {
        if (!oracleCoreAddress) return `${etherscanBase}/address/0xd6eEC694e7774Dc052E8Deb4C0E9FDbd5d855071`;
        return `${etherscanBase}/address/${oracleCoreAddress}`;
    }, [etherscanBase, oracleCoreAddress]);

    const fetchStatus = useCallback(async () => {
        const response = await fetch(`${API_BASE}/api/blockchain-status`);
        if (!response.ok) {
            throw new Error("Failed to fetch blockchain status");
        }
        return response.json();
    }, []);

    const fetchAssetPrice = useCallback(async (asset) => {
        const response = await fetch(`${API_BASE}/api/read-price?asset=${asset}`);
        if (!response.ok) {
            throw new Error(`Failed to read ${asset} price from contract`);
        }
        return response.json();
    }, []);

    const refreshContractData = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const [statusPayload, ethPayload, btcPayload] = await Promise.all([
                fetchStatus(),
                fetchAssetPrice("ETH"),
                fetchAssetPrice("BTC"),
            ]);

            setStatus(statusPayload);
            setPrices({
                ETH: ethPayload,
                BTC: btcPayload,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to refresh contract reads");
        } finally {
            setLoading(false);
        }
    }, [fetchAssetPrice, fetchStatus]);

    useEffect(() => {
        refreshContractData();
    }, [refreshContractData]);

    const resolvedWallet = status?.wallet_address || walletFromEnv;

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6 font-mono">
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <p className="text-xs uppercase tracking-wide text-cyan-400">On-Chain Panel</p>
                    <h3 className="text-lg font-semibold text-slate-100">Sepolia Contract Readout</h3>
                </div>

                <button
                    type="button"
                    onClick={refreshContractData}
                    disabled={loading}
                    className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-900 disabled:opacity-60"
                >
                    {loading ? "Reading..." : "Read from Contract"}
                </button>
            </div>

            {error ? (
                <div className="rounded-lg border border-rose-700 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">{error}</div>
            ) : null}

            <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Wallet</p>
                    <p className="mt-1 text-sm text-cyan-300">{truncateAddress(resolvedWallet)}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Sepolia Balance</p>
                    <p className="mt-1 text-sm text-emerald-400">{Number(status?.wallet_balance_eth || 0).toFixed(6)} ETH</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                    <p className="text-xs uppercase tracking-wide text-slate-400">Current Block</p>
                    <p className="mt-1 text-sm text-slate-200">{status?.block_number ?? "N/A"}</p>
                </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
                {[
                    { symbol: "ETH", payload: prices.ETH },
                    { symbol: "BTC", payload: prices.BTC },
                ].map(({ symbol, payload }) => (
                    <div key={symbol} className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                        <p className="text-xs uppercase tracking-wide text-slate-400">{symbol} On-Chain</p>
                        <p className="mt-1 text-xl font-bold text-cyan-300">
                            ${Number(payload?.price_usd || 0).toFixed(2)}
                        </p>
                        <p className="text-xs text-slate-400">Raw: {payload?.price_raw ?? "N/A"}</p>
                        <p className="text-xs text-slate-400">Timestamp: {formatTimestamp(payload?.timestamp)}</p>
                    </div>
                ))}
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950 p-4 text-sm">
                <p className="text-slate-400">OracleCore Contract</p>
                <a
                    href={contractUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-cyan-300 underline hover:text-cyan-200"
                >
                    View on Etherscan
                </a>
            </div>
        </section>
    );
}
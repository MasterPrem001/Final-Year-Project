import { useEffect, useMemo, useState } from "react";

import AnomalyPanel from "./components/AnomalyPanel";
import BlockchainPanel from "./components/BlockchainPanel";
import ConsensusResult from "./components/ConsensusResult";
import FLSimulation from "./components/FLSimulation";
import LiveFeed from "./components/LiveFeed";
import NodeStatus from "./components/NodeStatus";
import PriceHistory from "./components/PriceHistory";

const API_BASE = "http://127.0.0.1:8000";
const COIN_OPTIONS = ["BTC", "ETH", "SOL", "BNB", "MATIC"];

export default function App() {
    const [activeTab, setActiveTab] = useState("dashboard");
    const [selectedCoin, setSelectedCoin] = useState("ETH");
    const [networkHealth, setNetworkHealth] = useState("checking");
    const [loadingPipeline, setLoadingPipeline] = useState(false);
    const [loadingFL, setLoadingFL] = useState(false);
    const [errorMessage, setErrorMessage] = useState("");

    const [stats, setStats] = useState(null);
    const [latestRound, setLatestRound] = useState(null);
    const [latestRoundsByCoin, setLatestRoundsByCoin] = useState({});
    const [nodes, setNodes] = useState([]);
    const [priceHistory, setPriceHistory] = useState([]);
    const [flResult, setFlResult] = useState(null);

    const isHealthy = networkHealth === "ok";

    const statCards = useMemo(
        () => [
            { label: "Rounds Completed", value: stats?.rounds_completed ?? 0 },
            { label: "Anomalies Caught", value: stats?.anomalies_caught ?? 0 },
            { label: "Active Nodes", value: stats?.active_nodes ?? 5 },
            { label: "Data Sources", value: stats?.data_sources ?? 10 },
        ],
        [stats]
    );

    const selectedRound = useMemo(() => {
        if (latestRoundsByCoin[selectedCoin]) {
            return latestRoundsByCoin[selectedCoin];
        }
        if (latestRound?.asset === selectedCoin) {
            return latestRound;
        }
        return null;
    }, [latestRound, latestRoundsByCoin, selectedCoin]);

    async function fetchHealth() {
        try {
            const response = await fetch(`${API_BASE}/api/health`);
            const payload = await response.json();
            setNetworkHealth(payload.status || "down");
        } catch (error) {
            setNetworkHealth("down");
        }
    }

    async function fetchStats() {
        try {
            const response = await fetch(`${API_BASE}/api/stats`);
            const payload = await response.json();
            setStats(payload);
        } catch (error) {
            setStats(null);
        }
    }

    async function fetchLatest() {
        try {
            const response = await fetch(`${API_BASE}/api/latest`);
            const payload = await response.json();
            if (!payload?.message) {
                setLatestRound(payload);
                if (payload?.asset) {
                    setLatestRoundsByCoin((prev) => ({
                        ...prev,
                        [payload.asset]: payload,
                    }));
                }
            }
        } catch (error) {
            setLatestRound(null);
        }
    }

    async function fetchNodes() {
        try {
            const response = await fetch(`${API_BASE}/api/nodes`);
            const payload = await response.json();
            setNodes(payload.nodes || []);
        } catch (error) {
            setNodes([]);
        }
    }

    async function fetchPriceHistory(coin) {
        try {
            const response = await fetch(`${API_BASE}/api/price-history?asset=${coin}`);
            const payload = await response.json();
            setPriceHistory(payload.history || []);
        } catch (error) {
            setPriceHistory([]);
        }
    }

    async function runPipelineForCoin(coin) {
        const response = await fetch(`${API_BASE}/api/run-pipeline?coin=${coin}`);
        if (!response.ok) {
            throw new Error(`Pipeline request failed for ${coin}`);
        }
        const payload = await response.json();
        setLatestRound(payload);
        setLatestRoundsByCoin((prev) => ({
            ...prev,
            [coin]: payload,
        }));
        return payload;
    }

    async function runPipeline() {
        setLoadingPipeline(true);
        setErrorMessage("");

        try {
            await runPipelineForCoin(selectedCoin);
            await Promise.all([fetchStats(), fetchNodes(), fetchPriceHistory(selectedCoin)]);
        } catch (error) {
            setErrorMessage("Failed to run AI-DON pipeline. Check backend server and try again.");
        } finally {
            setLoadingPipeline(false);
        }
    }

    async function runPipelineForAllCoins() {
        setLoadingPipeline(true);
        setErrorMessage("");

        try {
            for (const coin of COIN_OPTIONS) {
                await runPipelineForCoin(coin);
            }

            await Promise.all([fetchStats(), fetchNodes(), fetchPriceHistory(selectedCoin)]);
        } catch (error) {
            setErrorMessage("Failed to run AI-DON pipeline for all assets. Check backend server and try again.");
        } finally {
            setLoadingPipeline(false);
        }
    }

    async function runFLSimulation() {
        setLoadingFL(true);
        setErrorMessage("");

        try {
            // AI-DON FL demo endpoint returns one complete multi-round simulation payload.
            const response = await fetch(`${API_BASE}/api/fl-simulation?rounds=3`);
            if (!response.ok) {
                throw new Error("FL simulation request failed");
            }
            const payload = await response.json();
            setFlResult(payload.result || null);
            await fetchStats();
        } catch (error) {
            setErrorMessage("Failed to run federated learning simulation.");
        } finally {
            setLoadingFL(false);
        }
    }

    useEffect(() => {
        fetchHealth();
        fetchStats();
        fetchLatest();
        fetchNodes();
        fetchPriceHistory(selectedCoin);
    }, []);

    useEffect(() => {
        fetchPriceHistory(selectedCoin);
    }, [selectedCoin]);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100">
            <header className="sticky top-0 z-20 border-b border-slate-800 bg-slate-950/95 backdrop-blur">
                <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4">
                    <div>
                        <h1 className="text-2xl font-bold">AI-DON Dashboard</h1>
                        <p className="text-sm text-slate-400">AI-Powered Decentralized Oracle Network</p>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="rounded-lg border border-slate-700 px-3 py-2 text-sm">
                            <label htmlFor="coin-select" className="mr-2 text-slate-400">
                                Asset:
                            </label>
                            <select
                                id="coin-select"
                                value={selectedCoin}
                                onChange={(event) => setSelectedCoin(event.target.value)}
                                className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-cyan-300 outline-none"
                            >
                                {COIN_OPTIONS.map((coin) => (
                                    <option key={coin} value={coin}>
                                        {coin}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="rounded-lg border border-slate-700 px-3 py-2 text-sm">
                            Network: {" "}
                            <span className={isHealthy ? "text-emerald-400" : "text-rose-400"}>
                                {isHealthy ? "Online" : networkHealth}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="mx-auto flex max-w-7xl gap-2 px-4 pb-3">
                    <button
                        type="button"
                        onClick={() => setActiveTab("dashboard")}
                        className={`rounded-md px-3 py-2 text-sm font-medium ${activeTab === "dashboard" ? "bg-cyan-500 text-slate-900" : "bg-slate-800 text-slate-300"
                            }`}
                    >
                        Dashboard
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("fl")}
                        className={`rounded-md px-3 py-2 text-sm font-medium ${activeTab === "fl" ? "bg-cyan-500 text-slate-900" : "bg-slate-800 text-slate-300"
                            }`}
                    >
                        Federated Learning
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("onchain")}
                        className={`rounded-md px-3 py-2 text-sm font-medium ${activeTab === "onchain" ? "bg-cyan-500 text-slate-900" : "bg-slate-800 text-slate-300"
                            }`}
                    >
                        On-Chain
                    </button>
                </div>
            </header>

            <main className="mx-auto max-w-7xl space-y-5 px-4 py-6">
                <section className="grid gap-3 md:grid-cols-4">
                    {statCards.map((card) => (
                        <div key={card.label} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                            <p className="text-xs uppercase tracking-wide text-slate-400">{card.label}</p>
                            <p className="mt-2 text-2xl font-semibold">{card.value}</p>
                        </div>
                    ))}
                </section>

                {errorMessage ? (
                    <div className="rounded-lg border border-rose-700 bg-rose-950/40 px-4 py-3 text-rose-200">{errorMessage}</div>
                ) : null}

                {activeTab === "dashboard" ? (
                    <>
                        <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900 p-4">
                            <p className="text-sm text-slate-300">
                                Run one oracle round for <span className="font-semibold text-cyan-400">{selectedCoin}</span>.
                            </p>
                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={runPipeline}
                                    disabled={loadingPipeline}
                                    className="rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-900 disabled:opacity-60"
                                >
                                    {loadingPipeline ? "Running..." : "Run Pipeline"}
                                </button>
                                <button
                                    type="button"
                                    onClick={runPipelineForAllCoins}
                                    disabled={loadingPipeline}
                                    className="rounded-lg border border-cyan-500 px-4 py-2 font-semibold text-cyan-300 disabled:opacity-60"
                                >
                                    {loadingPipeline ? "Running..." : "Run All 5"}
                                </button>
                            </div>
                        </div>
                        <ConsensusResult consensus={selectedRound?.consensus} blockchain={selectedRound?.blockchain} />
                        <LiveFeed sourcePrices={selectedRound?.source_prices} consensus={selectedRound?.consensus} />
                        <NodeStatus nodes={nodes} />
                        <AnomalyPanel submissions={selectedRound?.submissions || []} consensus={selectedRound?.consensus} />
                        <PriceHistory history={priceHistory} coin={selectedCoin} />
                    </>
                ) : activeTab === "fl" ? (
                    <FLSimulation
                        result={flResult}
                        loading={loadingFL}
                        onRunSimulation={runFLSimulation}
                    />
                ) : (
                    <BlockchainPanel />
                )}
            </main>
        </div>
    );
}

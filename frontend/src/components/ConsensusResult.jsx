export default function ConsensusResult({ consensus, blockchain }) {
    if (!consensus) {
        return (
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">No consensus round yet. Run pipeline to view AI result.</p>
            </section>
        );
    }

    const blockchainData = blockchain ?? { status: "simulated" };
    const nodesUsed = consensus.nodes_used ?? 0;
    const nodesRejected = consensus.nodes_rejected ?? 0;
    const totalNodes = Math.max(nodesUsed + nodesRejected, 5);
    const etherscanBase = import.meta.env.VITE_ETHERSCAN_BASE_URL || "https://sepolia.etherscan.io";
    const oracleCoreAddress = import.meta.env.VITE_ORACLE_CORE_ADDRESS || "";
    const contractUrl = oracleCoreAddress ? `${etherscanBase}/address/${oracleCoreAddress}` : "";

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">Final AI Consensus Price</p>
                    <h2 className="mt-1 text-4xl font-bold text-cyan-400">
                        ${Number(consensus.final_price || 0).toFixed(4)}
                    </h2>
                </div>

                <div className="grid gap-2 text-sm text-slate-300">
                    <p>
                        Confidence:{" "}
                        <span className="font-semibold text-emerald-400">{consensus.confidence ?? 0}%</span>
                    </p>
                    <p>
                        Deviation from median:{" "}
                        <span className="font-semibold">
                            {Number(consensus.deviation_from_median || 0).toFixed(4)}%
                        </span>
                    </p>
                </div>
            </div>

            <div>
                <p className="mb-2 text-xs uppercase tracking-wide text-slate-400">Nodes Used / Rejected</p>
                <div className="flex gap-2">
                    {Array.from({ length: totalNodes }).map((_, index) => {
                        const active = index < nodesUsed;
                        return (
                            <span
                                key={`node-box-${index}`}
                                className={`h-3 w-7 rounded ${active ? "bg-emerald-500" : "bg-rose-500"}`}
                            />
                        );
                    })}
                </div>
            </div>

            {(consensus.rejected_nodes || []).length > 0 ? (
                <div className="rounded-lg border border-rose-700 bg-rose-950/30 px-4 py-3 text-sm text-rose-200">
                    Rejected nodes: {consensus.rejected_nodes.join(", ")}
                </div>
            ) : null}

            <div className="rounded-lg border border-slate-700 bg-slate-950/50 px-4 py-3 text-sm">
                {blockchainData.status === "confirmed" ? (
                    <div className="space-y-2 text-emerald-300">
                        <div className="flex items-center gap-2">
                            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-emerald-400" />
                            <span className="font-semibold uppercase tracking-wide">Confirmed on Sepolia</span>
                        </div>
                        <p>
                            Tx Hash:{" "}
                            <a
                                href={blockchainData.etherscan_url}
                                target="_blank"
                                rel="noreferrer"
                                className="font-medium text-cyan-300 underline hover:text-cyan-200"
                            >
                                {blockchainData.tx_hash}
                            </a>
                        </p>
                        <p>Block: {blockchainData.block}</p>
                        {contractUrl ? (
                            <a
                                href={contractUrl}
                                target="_blank"
                                rel="noreferrer"
                                className="font-medium text-cyan-300 underline hover:text-cyan-200"
                            >
                                View Contract
                            </a>
                        ) : (
                            <p className="text-slate-300">Contract link unavailable</p>
                        )}
                    </div>
                ) : blockchainData.status === "failed" ? (
                    <div className="space-y-1 text-rose-300">
                        <p className="font-semibold uppercase tracking-wide">Blockchain Push Failed</p>
                        <p>{blockchainData.error || "Unknown blockchain error"}</p>
                    </div>
                ) : (
                    <div className="text-slate-300">
                        <p className="font-semibold uppercase tracking-wide text-slate-400">Simulated Only</p>
                    </div>
                )}
            </div >
        </section >
    );
}
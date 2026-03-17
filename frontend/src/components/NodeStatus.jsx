function ProgressBar({ value, max, fillClass }) {
    const percent = Math.max(0, Math.min(100, ((value || 0) / max) * 100));

    return (
        <div className="h-2.5 w-full rounded bg-slate-800">
            <div className={`h-2.5 rounded ${fillClass}`} style={{ width: `${percent}%` }} />
        </div>
    );
}

export default function NodeStatus({ nodes }) {
    if (!nodes || nodes.length === 0) {
        return (
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">Node telemetry will appear after at least one pipeline run.</p>
            </section>
        );
    }

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="text-lg font-semibold">Oracle Node Status</h3>

            <div className="grid gap-3 lg:grid-cols-2">
                {nodes.map((node) => {
                    const flagged = Boolean(node.latest_is_anomaly);

                    return (
                        <article
                            key={node.node_id}
                            className={`rounded-lg border p-4 ${flagged ? "border-rose-600 bg-rose-950/20" : "border-slate-800 bg-slate-950"
                                }`}
                        >
                            <div className="mb-3 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <span className={`h-2.5 w-2.5 rounded-full ${flagged ? "bg-rose-500" : "bg-emerald-500"}`} />
                                    <p className="font-semibold">{node.name}</p>
                                    <span className="text-xs text-slate-400">{node.region}</span>
                                </div>
                                {flagged ? (
                                    <span className="rounded bg-rose-600 px-2 py-0.5 text-xs font-semibold">AI FLAGGED</span>
                                ) : null}
                            </div>

                            <div className="space-y-3">
                                <div>
                                    <div className="mb-1 flex justify-between text-xs text-slate-400">
                                        <span>Reputation</span>
                                        <span>{node.reputation ?? 0} / 1000</span>
                                    </div>
                                    <ProgressBar value={node.reputation} max={1000} fillClass="bg-cyan-500" />
                                </div>

                                <div>
                                    <div className="mb-1 flex justify-between text-xs text-slate-400">
                                        <span>AI Trust Weight</span>
                                        <span>{Number(node.latest_trust_weight || 0).toFixed(4)}</span>
                                    </div>
                                    {/* Trust weight is normalized in AI anomaly stage; scale to % for UI bar. */}
                                    <ProgressBar value={(node.latest_trust_weight || 0) * 100} max={100} fillClass="bg-emerald-500" />
                                </div>
                            </div>

                            <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-slate-300">
                                <div>
                                    <p className="text-slate-400">Z-score</p>
                                    <p>{Number(node.latest_z_score || 0).toFixed(4)}</p>
                                </div>
                                <div>
                                    <p className="text-slate-400">IF score</p>
                                    <p>{Number(node.latest_if_score || 0).toFixed(4)}</p>
                                </div>
                                <div>
                                    <p className="text-slate-400">Latency</p>
                                    <p>{node.latest_latency_ms ?? "-"} ms</p>
                                </div>
                            </div>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}

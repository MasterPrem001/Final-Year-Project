import {
    CartesianGrid,
    ReferenceLine,
    ResponsiveContainer,
    Scatter,
    ScatterChart,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

export default function AnomalyPanel({ submissions, consensus }) {
    const allPoints = (submissions || []).map((row) => ({
        node: row.node_name || row.node_id,
        submitted_price: Number(row.submitted_price || 0),
        reputation: Number(row.reputation || 0),
        deviation: Number(row.deviation_from_true || 0),
        z_score: Number(row.z_score || 0),
        if_score: Number(row.if_score || 0),
        is_anomaly: Boolean(row.is_anomaly),
    }));

    const anomalyPoints = allPoints.filter((item) => item.is_anomaly);

    if (allPoints.length === 0) {
        return (
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">Anomaly panel appears after a pipeline round.</p>
            </section>
        );
    }

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="text-lg font-semibold">Anomaly Detection Panel</h3>

            <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis type="number" dataKey="submitted_price" name="Submitted Price" stroke="#94a3b8" />
                        <YAxis type="number" dataKey="reputation" name="Reputation" stroke="#94a3b8" />
                        <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                        {/* Consensus reference: points far from this vertical line are likely suspicious. */}
                        <ReferenceLine x={Number(consensus?.final_price || 0)} stroke="#22d3ee" strokeDasharray="6 4" />
                        <Scatter name="Nodes" data={allPoints} fill="#22c55e" />
                        <Scatter name="Anomalies" data={anomalyPoints} fill="#ef4444" />
                    </ScatterChart>
                </ResponsiveContainer>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
                {anomalyPoints.length === 0 ? (
                    <p className="text-sm text-slate-400">No anomalous nodes detected in this round.</p>
                ) : (
                    anomalyPoints.map((node) => (
                        <article key={`anomaly-${node.node}`} className="rounded-lg border border-rose-700 bg-rose-950/25 p-4">
                            <p className="font-semibold text-rose-300">{node.node}</p>
                            <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-rose-100">
                                <div>
                                    <p className="text-rose-300">Deviation</p>
                                    <p>{node.deviation.toFixed(4)}%</p>
                                </div>
                                <div>
                                    <p className="text-rose-300">Z-score</p>
                                    <p>{node.z_score.toFixed(4)}</p>
                                </div>
                                <div>
                                    <p className="text-rose-300">IF score</p>
                                    <p>{node.if_score.toFixed(4)}</p>
                                </div>
                            </div>
                        </article>
                    ))
                )}
            </div>
        </section>
    );
}

import {
    CartesianGrid,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

const FL_STEPS = [
    {
        title: "Local Training",
        detail: "Each oracle node trains on private local data without sharing raw samples.",
    },
    {
        title: "Gradient Upload",
        detail: "Nodes send model updates/gradients to the aggregation coordinator.",
    },
    {
        title: "FedAvg",
        detail: "Coordinator performs reputation-weighted federated averaging.",
    },
    {
        title: "Broadcast",
        detail: "Updated global model is broadcast to all participating nodes.",
    },
];

export default function FLSimulation({ result, loading, onRunSimulation }) {
    const chartData = (result?.rounds || []).map((round) => ({
        round: round.round,
        global_accuracy: Number(round.global_accuracy || 0),
    }));

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <div className="flex items-center justify-between gap-3">
                <h3 className="text-lg font-semibold">Federated Learning Simulation</h3>
                <button
                    type="button"
                    onClick={onRunSimulation}
                    disabled={loading}
                    className="rounded-lg bg-cyan-500 px-4 py-2 font-semibold text-slate-900 disabled:opacity-60"
                >
                    {loading ? "Running..." : "Run FL Simulation"}
                </button>
            </div>

            <div className="grid gap-3 md:grid-cols-4">
                {FL_STEPS.map((step) => (
                    <article key={step.title} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                        <p className="text-sm font-semibold text-cyan-300">{step.title}</p>
                        <p className="mt-2 text-xs text-slate-400">{step.detail}</p>
                    </article>
                ))}
            </div>

            <div className="h-72 rounded-lg border border-slate-800 bg-slate-950 p-2">
                {chartData.length === 0 ? (
                    <p className="p-4 text-sm text-slate-400">Run simulation to visualize round-by-round global accuracy.</p>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis dataKey="round" stroke="#94a3b8" />
                            <YAxis stroke="#94a3b8" domain={[60, 100]} />
                            <Tooltip />
                            <Line type="monotone" dataKey="global_accuracy" stroke="#22d3ee" strokeWidth={3} />
                        </LineChart>
                    </ResponsiveContainer>
                )}
            </div>

            {result?.rounds?.length ? (
                <div className="space-y-3">
                    {result.rounds.map((round) => (
                        <article key={`round-${round.round}`} className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                            <div className="mb-2 flex items-center justify-between">
                                <p className="font-semibold">Round {round.round}</p>
                                <p className="text-sm text-cyan-300">Global Accuracy: {Number(round.global_accuracy).toFixed(3)}%</p>
                            </div>

                            <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-5">
                                {round.node_updates.map((node) => (
                                    <div key={`${round.round}-${node.node_id}`} className="rounded border border-slate-800 p-2 text-xs">
                                        <p className="font-semibold">{node.node_name}</p>
                                        <p className="text-slate-400">Samples: {node.n_samples}</p>
                                        <p className="text-slate-400">Local Acc: {Number(node.local_accuracy).toFixed(3)}%</p>
                                        <p className="text-slate-400">Grad Norm: {Number(node.gradient_norm).toFixed(3)}</p>
                                        <p className={node.poisoning_detected ? "text-rose-400" : "text-emerald-400"}>
                                            {node.poisoning_detected ? "Poisoning Detected" : "Accepted"}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        </article>
                    ))}
                </div>
            ) : null}

            <div className="rounded-lg border border-cyan-700 bg-cyan-950/30 px-4 py-3 text-sm text-cyan-200">
                Privacy mode: gradients only shared between nodes and coordinator (no raw data transfer).
            </div>
        </section>
    );
}

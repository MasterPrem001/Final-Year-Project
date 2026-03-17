import {
    Area,
    AreaChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";

export default function PriceHistory({ history, coin }) {
    const rows = (history || []).map((item) => ({
        round: item.round_id,
        consensus_price: Number(item.consensus_price || 0),
        confidence: Number(item.confidence || 0),
    }));

    const prices = rows.map((item) => item.consensus_price);
    const low = prices.length ? Math.min(...prices) : 0;
    const high = prices.length ? Math.max(...prices) : 0;
    const spread = high - low;

    if (rows.length === 0) {
        return (
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">Price history will populate after multiple rounds.</p>
            </section>
        );
    }

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="text-lg font-semibold">Consensus Price History ({coin})</h3>

            <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={rows}>
                        <defs>
                            <linearGradient id="consensusFill" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.65} />
                                <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.05} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="round" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip />
                        <Area
                            type="monotone"
                            dataKey="consensus_price"
                            stroke="#22d3ee"
                            fill="url(#consensusFill)"
                            strokeWidth={2}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 text-sm">
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                    <p className="text-slate-400">Low</p>
                    <p className="font-semibold">${low.toFixed(4)}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                    <p className="text-slate-400">High</p>
                    <p className="font-semibold">${high.toFixed(4)}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                    <p className="text-slate-400">Spread</p>
                    <p className="font-semibold">${spread.toFixed(4)}</p>
                </div>
            </div>
        </section>
    );
}

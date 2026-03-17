import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function classifySource(price, median) {
    if (!median || !price) {
        return { label: "failed", className: "text-slate-400", barColor: "#64748b" };
    }

    const deviationPct = (Math.abs(price - median) / median) * 100;

    if (deviationPct <= 0.2) {
        return { label: "aligned", className: "text-emerald-400", barColor: "#22c55e" };
    }

    if (deviationPct <= 0.7) {
        return { label: "slight outlier", className: "text-amber-400", barColor: "#f59e0b" };
    }

    return { label: "outlier", className: "text-slate-400", barColor: "#64748b" };
}

export default function LiveFeed({ sourcePrices, consensus }) {
    const medianPrice = Number(consensus?.median_price || 0);
    const chartData = Object.entries(sourcePrices || {}).map(([source, value]) => {
        const price = Number(value);
        const state = classifySource(price, medianPrice);

        return {
            source,
            price,
            status: state.label,
            fill: state.barColor,
            className: state.className,
        };
    });

    if (chartData.length === 0) {
        return (
            <section className="rounded-xl border border-slate-800 bg-slate-900 p-6">
                <p className="text-sm text-slate-400">Live exchange feed appears after running a pipeline round.</p>
            </section>
        );
    }

    return (
        <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h3 className="text-lg font-semibold">Live Feed (10 Sources)</h3>

            <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                        <XAxis dataKey="source" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip />
                        {/* AI-DON median reference line to compare each exchange quote. */}
                        <ReferenceLine
                            y={medianPrice}
                            stroke="#22d3ee"
                            strokeDasharray="6 4"
                            ifOverflow="extendDomain"
                        />
                        <Bar dataKey="price" radius={[6, 6, 0, 0]}>
                            {chartData.map((item) => (
                                <Cell key={item.source} fill={item.fill} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {chartData.map((item) => (
                    <div key={`card-${item.source}`} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                        <p className="text-sm font-semibold">{item.source}</p>
                        <p className="text-lg font-bold">${item.price.toFixed(4)}</p>
                        <p className={`text-xs ${item.className}`}>{item.status}</p>
                    </div>
                ))}
            </div>
        </section>
    );
}

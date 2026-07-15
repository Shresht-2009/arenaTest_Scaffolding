"use client";

import { GlassCard } from "../ui/GlassCard";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";

export function EvolutionGraph({ timeline }: { timeline: any[] }) {
  if (!timeline || timeline.length === 0) {
    return (
      <GlassCard>
        <p className="text-textMuted text-sm">No evolution data yet</p>
      </GlassCard>
    );
  }

  const data = timeline.map((e) => ({
    gen: e.generation,
    winner: e.winner_fitness,
    avg: e.avg_fitness,
    best: e.best_fitness,
  }));

  return (
    <GlassCard>
      <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Evolution Graph - Fitness Over Generations</h3>
      <div className="h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#232336" />
            <XAxis dataKey="gen" stroke="#64748b" fontSize={10} />
            <YAxis stroke="#64748b" fontSize={10} domain={[0, 1]} />
            <Tooltip
              contentStyle={{ background: "rgba(18,18,26,0.9)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px" }}
            />
            <Legend />
            <Line type="monotone" dataKey="winner" stroke="#10b981" name="Winner Fitness" dot={false} strokeWidth={2} />
            <Line type="monotone" dataKey="avg" stroke="#06b6d4" name="Avg Fitness" dot={false} strokeWidth={1.5} />
            <Line type="monotone" dataKey="best" stroke="#f59e0b" name="Best Overall" dot={false} strokeWidth={1.5} strokeDasharray="4 4" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-xs text-textMuted">
        <p>Shows progressive improvement as cognitive genomes mutate and are selected. Fitness weighted: Reasoning 20%, Correctness 20%, Verification 15%, Planning 10%, Generalization 10%, Robustness 10%, Compression 5%, Token 5%, Novelty 5%, Self-Correction 5%.</p>
      </div>
    </GlassCard>
  );
}

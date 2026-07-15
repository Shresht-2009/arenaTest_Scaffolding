"use client";

import React from "react";
import { GlassCard, StatCard } from "../ui/GlassCard";
import { motion } from "framer-motion";
import { Activity, Brain, Zap, Database, DollarSign, Clock, Layers, TrendingUp } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

export function EvolutionDashboard({ data, isRunning }: { data: any; isRunning: boolean }) {
  if (!data) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <GlassCard key={i} className="animate-pulse">
            <div className="h-20 bg-white/[0.03] rounded" />
          </GlassCard>
        ))}
      </div>
    );
  }

  const timeline = data.evolution_timeline || data.genome_history || [];
  const chartData = timeline.map((e: any, i: number) => ({
    gen: e.generation || i,
    fitness: e.winner_fitness || e.best_fitness || 0,
    avg: e.avg_fitness || 0,
  }));

  return (
    <div className="space-y-6">
      {/* Top Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4">
        <StatCard
          label="Generation"
          value={data.current_generation ?? 0}
          subtext={isRunning ? "● Evolving" : "Idle"}
          trend={isRunning ? "up" : "neutral"}
          icon={<Activity className="w-4 h-4 text-primary" />}
        />
        <StatCard
          label="Fitness Score"
          value={typeof data.fitness_score === "number" ? data.fitness_score.toFixed(3) : data.fitness_score || "0.000"}
          subtext={`Best: ${data.current_genome?.fitness?.toFixed(3) || "N/A"}`}
          trend="up"
          icon={<TrendingUp className="w-4 h-4 text-success" />}
        />
        <StatCard
          label="Token Usage"
          value={data.token_usage?.total_tokens?.toLocaleString() ?? data.memory_usage?.compressed?.total_original_tokens ?? 0}
          subtext={`Cost $${(data.cost_estimate ?? data.token_usage?.estimated_cost ?? 0).toFixed(4)}`}
          icon={<Zap className="w-4 h-4 text-accent" />}
        />
        <StatCard
          label="Latency"
          value={`${Math.round(data.latency ?? data.token_usage?.avg_latency_ms ?? 0)}ms`}
          subtext={`${data.api_requests ?? data.token_usage?.requests ?? 0} requests`}
          icon={<Clock className="w-4 h-4 text-secondary" />}
        />
        <StatCard
          label="Reasoning Depth"
          value={data.reasoning_depth ?? 0}
          subtext={`Recursive depth ${data.recursive_depth ?? 0}`}
          icon={<Layers className="w-4 h-4 text-primary" />}
        />
        <StatCard
          label="Compression"
          value={`${Math.round((data.compression_ratio ?? 0) * 100)}%`}
          subtext={`${data.memory_usage?.compressed?.root_nodes ?? 0} compressed nodes`}
          icon={<Database className="w-4 h-4 text-secondary" />}
        />
        <StatCard
          label="Memory Nodes"
          value={data.memory_usage?.compressed?.total_nodes ?? data.memory_usage?.working?.steps ?? 0}
          subtext={`Working ${data.memory_usage?.working?.steps ?? 0} steps`}
          icon={<Brain className="w-4 h-4 text-primary" />}
        />
        <StatCard
          label="Checkpoints"
          value={data.checkpoint_history?.length ?? 0}
          subtext={`Last gen ${data.checkpoint_history?.[0]?.generation ?? "none"}`}
          icon={<DollarSign className="w-4 h-4 text-success" />}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Evolution Timeline - Fitness</h3>
          <div className="h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <XAxis dataKey="gen" stroke="#64748b" fontSize={10} />
                <YAxis stroke="#64748b" fontSize={10} domain={[0, 1]} />
                <Tooltip
                  contentStyle={{ background: "rgba(18,18,26,0.9)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "12px", backdropFilter: "blur(20px)" }}
                />
                <Area type="monotone" dataKey="fitness" stroke="#6d28d9" fill="rgba(109,40,217,0.2)" strokeWidth={2} />
                <Area type="monotone" dataKey="avg" stroke="#06b6d4" fill="rgba(6,182,214,0.1)" strokeWidth={1} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Current Genome - Performance</h3>
          {data.current_genome ? (
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-textSecondary">ID</span>
                <span className="font-mono text-textPrimary">{data.current_genome.id}</span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                {[
                  ["Planning Depth", data.current_genome.planning_depth],
                  ["Verification Passes", data.current_genome.verification_passes],
                  ["Search Width", data.current_genome.search_width],
                  ["Reflection Depth", data.current_genome.reflection_depth],
                  ["Exploration", `${(data.current_genome.exploration_factor * 100).toFixed(0)}%`],
                  ["Compression", `${(data.current_genome.compression_level * 100).toFixed(0)}%`],
                  ["Critique", `${(data.current_genome.critique_strength * 100).toFixed(0)}%`],
                  ["Abstraction", `${(data.current_genome.abstraction_level * 100).toFixed(0)}%`],
                ].map(([k, v]) => (
                  <div key={k as string} className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.03] flex justify-between">
                    <span className="text-textMuted">{k}</span>
                    <span className="text-textPrimary font-medium">{v as any}</span>
                  </div>
                ))}
              </div>
              <div className="pt-2">
                <p className="text-xs text-textMuted mb-2">Reasoning Order: <span className="text-textPrimary">{data.current_genome.reasoning_order}</span> | Strategy: <span className="text-textPrimary">{data.current_genome.decomposition_style}</span> | Memory: <span className="text-textPrimary">{data.current_genome.memory_retrieval_strategy}</span></p>
                <div className="text-[10px] font-mono p-3 rounded-xl bg-black/30 border border-white/[0.05] text-textSecondary max-h-[120px] overflow-auto">
                  {data.current_genome.id ? `Genome ${data.current_genome.id} Gen ${data.current_genome.generation}` : "No genome"}
                  <br />
                  Temp {data.current_genome.temperature?.toFixed(2)} | TopP {data.current_genome.top_p?.toFixed(2)}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-textMuted text-sm">No genome loaded</p>
          )}
        </GlassCard>
      </div>

      {/* Best Answer & Scaffold */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <h3 className="text-sm uppercase tracking-widest text-textMuted mb-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-success rounded-full animate-pulse" /> Best Answer (Generation {data.current_generation})
          </h3>
          <div className="prose-invert max-h-[320px] overflow-auto text-sm leading-relaxed text-textSecondary whitespace-pre-wrap p-3 rounded-xl bg-black/20 border border-white/[0.03]">
            {data.best_answer || "No answer yet — start evolution"}
          </div>
        </GlassCard>
        <GlassCard>
          <h3 className="text-sm uppercase tracking-widest text-textMuted mb-3">Best Scaffold (Compressed)</h3>
          <div className="max-h-[320px] overflow-auto text-xs font-mono leading-relaxed text-textSecondary whitespace-pre-wrap p-3 rounded-xl bg-black/20 border border-white/[0.03]">
            {data.best_scaffold || data.reasoning_tree?.slice(-1)?.[0]?.content || "No scaffold yet"}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

"use client";

import { GlassCard } from "../ui/GlassCard";
import { motion } from "framer-motion";

export function GenomeExplorer({ genomeHistory, currentGenome }: { genomeHistory: any[]; currentGenome: any }) {
  return (
    <div className="space-y-6">
      <GlassCard>
        <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Genome Explorer - Cognitive DNA</h3>
        {currentGenome ? (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-gradient-to-br from-primary/10 to-secondary/10 border border-primary/20">
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-mono font-bold text-textPrimary">Genome {currentGenome.id}</p>
                  <p className="text-xs text-textSecondary">Gen {currentGenome.generation} | Parent {currentGenome.parent_id || "root"} | Lineage {currentGenome.lineage?.length || 0}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-success">{(currentGenome.fitness * 100).toFixed(1)}%</p>
                  <p className="text-xs text-textMuted">Fitness</p>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-2 text-[11px]">
                {Object.entries(currentGenome)
                  .filter(([k]) => !["id", "lineage", "fitness_history", "benchmark_scores"].includes(k))
                  .slice(0, 18)
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between p-2 rounded-lg bg-black/20 border border-white/[0.03]">
                      <span className="text-textMuted">{k.replace(/_/g, " ")}</span>
                      <span className="font-mono text-textPrimary">{typeof v === "number" ? v.toFixed(2) : String(v).slice(0, 20)}</span>
                    </div>
                  ))}
              </div>
              <div className="mt-4 p-3 rounded-xl bg-black/30 border border-white/[0.05] font-mono text-[11px] text-textSecondary whitespace-pre-wrap">
                {currentGenome.id ? `${currentGenome.planning_depth} depth, ${currentGenome.verification_passes} verification, ${currentGenome.reasoning_order} order, ${currentGenome.decomposition_style} decomposition` : ""}
              </div>
            </div>

            <div>
              <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Prompt Fragment (Genome → LLM)</h4>
              <pre className="p-3 rounded-xl bg-black/40 border border-white/[0.05] text-[11px] text-textSecondary overflow-auto max-h-[240px] whitespace-pre-wrap">
                Cognitive Protocol [Genome:{currentGenome.id} Gen:{currentGenome.generation}]: {"\n"}
                - Planning Depth: {currentGenome.planning_depth} (horizon {currentGenome.planning_horizon} steps, style {currentGenome.decomposition_style}){"\n"}
                - Reasoning Order: {currentGenome.reasoning_order} with search width {currentGenome.search_width},{"\n"}
                - Verification: {currentGenome.verification_passes} passes, strictness {currentGenome.verification_strictness}...
              </pre>
            </div>
          </div>
        ) : (
          <p className="text-textMuted">No genome</p>
        )}
      </GlassCard>

      <GlassCard>
        <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Evolution History - Mutation Timeline ({genomeHistory?.length || 0} events)</h3>
        <div className="space-y-2 max-h-[400px] overflow-auto">
          {(genomeHistory || []).slice().reverse().map((ev, i) => (
            <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3 p-3 rounded-xl bg-white/[0.03] border border-white/[0.05] text-xs">
              <div className="font-mono text-primary">Gen {ev.generation}</div>
              <div className="flex-1">
                <div className="flex justify-between">
                  <span className="text-textPrimary">Winner {ev.winner_id?.slice(0, 6)} fitness {(ev.winner_fitness * 100).toFixed(1)}%</span>
                  <span className={`px-2 py-0.5 rounded-full text-[10px] ${ev.improvement ? "bg-success/20 text-success" : "bg-white/[0.05] text-textMuted"}`}>{ev.improvement ? "IMPROVED" : "stable"}</span>
                </div>
                <div className="text-textMuted mt-1">pop {ev.population_size} | avg {(ev.avg_fitness * 100).toFixed(1)}% | complexity {(ev.complexity * 100).toFixed(0)}% | {ev.latency_ms?.toFixed(0)}ms</div>
              </div>
            </motion.div>
          ))}
          {(!genomeHistory || genomeHistory.length === 0) && <p className="text-textMuted text-sm">No history yet</p>}
        </div>
      </GlassCard>
    </div>
  );
}

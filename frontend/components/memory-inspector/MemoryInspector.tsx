"use client";

import { GlassCard } from "../ui/GlassCard";

export function MemoryInspector({ memory }: { memory: any }) {
  if (!memory) return <GlassCard><p className="text-textMuted">No memory data</p></GlassCard>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <GlassCard>
          <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Working Memory</h4>
          <p className="text-2xl font-bold">{memory.working?.steps ?? 0}</p>
          <p className="text-xs text-textSecondary mt-1">{memory.working?.tokens ?? 0} tokens active</p>
          <p className="text-xs text-textMuted">Gen {memory.working?.generation}</p>
        </GlassCard>
        <GlassCard>
          <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Episodic</h4>
          <p className="text-2xl font-bold">{memory.episodic?.total_generations ?? 0}</p>
          <p className="text-xs text-textSecondary">best {(memory.episodic?.best_fitness * 100)?.toFixed(1) ?? 0}% gen {memory.episodic?.best_generation}</p>
        </GlassCard>
        <GlassCard>
          <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Semantic</h4>
          <p className="text-2xl font-bold">{memory.semantic?.patterns ?? 0}</p>
          <p className="text-xs text-textSecondary">{memory.semantic?.templates ?? 0} templates</p>
        </GlassCard>
        <GlassCard>
          <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Compressed</h4>
          <p className="text-2xl font-bold">{memory.compressed?.total_nodes ?? 0}</p>
          <p className="text-xs text-textSecondary">{(memory.compressed?.avg_compression_ratio * 100)?.toFixed(0) ?? 0}% ratio</p>
          <p className="text-xs text-textMuted">{memory.compressed?.root_nodes ?? 0} roots</p>
        </GlassCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GlassCard>
          <h3 className="text-sm uppercase tracking-widest text-textMuted mb-3">Top Patterns (Semantic Memory)</h3>
          <div className="space-y-2">
            {(memory.semantic?.top_patterns || []).map((p: any, i: number) => (
              <div key={i} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.05] text-xs">
                <div className="flex justify-between">
                  <span className="font-mono text-primary">{p.id?.slice(0, 8)}</span>
                  <span className="text-success">{(p.success_rate * 100).toFixed(0)}% success</span>
                </div>
                <p className="text-textSecondary mt-1">{p.desc}</p>
                <p className="text-textMuted text-[10px] mt-1">gain {p.gain?.toFixed(3)}</p>
              </div>
            ))}
            {(memory.semantic?.top_patterns?.length ?? 0) === 0 && <p className="text-textMuted text-sm">No patterns distilled yet — will emerge after reflections</p>}
          </div>
        </GlassCard>

        <GlassCard>
          <h3 className="text-sm uppercase tracking-widest text-textMuted mb-3">Compressed Memory Stats</h3>
          <div className="space-y-2 text-xs">
            <div className="grid grid-cols-4 gap-2">
              {Object.entries(memory.compressed?.levels || {}).map(([lvl, count]) => (
                <div key={lvl} className="p-2 rounded-lg bg-black/20 border border-white/[0.03] text-center">
                  <p className="font-bold text-textPrimary">L{lvl}</p>
                  <p className="text-textSecondary">{count as any}</p>
                </div>
              ))}
            </div>
            <div className="p-3 rounded-xl bg-black/20 border border-white/[0.03] font-mono text-[11px]">
              <p>Original tokens: {memory.compressed?.total_original_tokens}</p>
              <p>Compressed tokens: {memory.compressed?.total_compressed_tokens}</p>
              <p>Avg ratio: {(memory.compressed?.avg_compression_ratio * 100)?.toFixed(1)}% saved</p>
            </div>
            <details className="mt-2">
              <summary className="cursor-pointer text-textMuted">Compressed Context (token optimized)</summary>
              <pre className="mt-2 p-3 rounded-xl bg-black/30 border border-white/[0.05] text-[10px] whitespace-pre-wrap max-h-[200px] overflow-auto">
                {memory.compressed?.context || "No compressed context"}
              </pre>
            </details>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

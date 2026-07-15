"use client";

import { useState, useEffect } from "react";
import { GlassCard } from "../ui/GlassCard";
import { api } from "../../lib/api";

export function BenchmarkViewer({ benchmarkResults }: { benchmarkResults: any }) {
  const [families, setFamilies] = useState<string[]>([]);
  const [selectedFamily, setSelectedFamily] = useState<string>("");
  const [generatedTask, setGeneratedTask] = useState<any>(null);
  const [difficulty, setDifficulty] = useState(0.5);

  useEffect(() => {
    api.getBenchmarkFamilies().then((res) => setFamilies(res.families || [])).catch(() => {
      // fallback from local list
      setFamilies([
        "graph_algorithms","mathematics","formal_logic","constraint_satisfaction","optimization","planning","programming","debugging","compression","scientific_reasoning","pattern_recognition","information_reconstruction","scheduling","causal_inference","abstract_reasoning","counterfactual_reasoning","strategic_games","algorithm_design","multi_step_reasoning","knowledge_integration"
      ]);
    });
  }, []);

  const generate = async () => {
    try {
      const task = await api.generateBenchmark(selectedFamily || undefined, difficulty, 1);
      setGeneratedTask(Array.isArray(task) ? task[0] : task);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <GlassCard>
        <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">PIES - Procedural Intelligence Evaluation System</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Performance per Family</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-[320px] overflow-auto">
              {benchmarkResults?.per_family ? Object.entries(benchmarkResults.per_family).map(([fam, data]: any) => (
                <div key={fam} className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.05] text-xs">
                  <p className="font-bold text-textPrimary truncate">{fam}</p>
                  <p className="text-textSecondary mt-1">acc {(data.accuracy * 100).toFixed(0)}% | avg {(data.avg_score * 100).toFixed(0)}%</p>
                  <p className="text-textMuted text-[10px]">{data.total} evals</p>
                  <div className="mt-2 h-1 bg-black/30 rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: `${data.accuracy * 100}%` }} />
                  </div>
                </div>
              )) : <p className="text-textMuted text-sm">No evaluations yet — evaluations accumulate as evolution runs</p>}
            </div>
            {benchmarkResults && (
              <div className="mt-4 p-3 rounded-xl bg-black/20 border border-white/[0.03] text-xs flex gap-4">
                <span>Total: {benchmarkResults.total_evals}</span>
                <span>Accuracy: {(benchmarkResults.overall_accuracy * 100).toFixed(1)}%</span>
                <span>Avg Score: {(benchmarkResults.avg_score * 100).toFixed(1)}%</span>
              </div>
            )}
          </div>
          <div>
            <h4 className="text-xs uppercase tracking-widest text-textMuted mb-2">Adaptive Difficulty</h4>
            <div className="space-y-2 max-h-[320px] overflow-auto">
              {benchmarkResults?.current_difficulties ? Object.entries(benchmarkResults.current_difficulties).map(([fam, diff]: any) => (
                <div key={fam} className="flex justify-between text-xs p-2 rounded-lg bg-white/[0.03] border border-white/[0.03]">
                  <span className="text-textSecondary truncate mr-2">{fam}</span>
                  <span className="font-mono text-textPrimary">{(diff * 100).toFixed(0)}%</span>
                </div>
              )) : <p className="text-textMuted text-sm">Difficulty evolves based on performance — starts at 50%</p>}
            </div>
          </div>
        </div>
      </GlassCard>

      <GlassCard>
        <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Generate New Benchmark Task (Procedural, Infinite Unique)</h3>
        <div className="flex flex-wrap gap-3 mb-4">
          <select value={selectedFamily} onChange={(e) => setSelectedFamily(e.target.value)} className="px-3 py-2 rounded-xl bg-black/30 border border-white/[0.08] text-sm text-textPrimary">
            <option value="">Random Family</option>
            {families.map((f) => (
              <option key={f} value={f}>{f}</option>
            ))}
          </select>
          <div className="flex gap-2 items-center">
            <span className="text-xs text-textMuted">Difficulty</span>
            <input type="range" min={0.1} max={0.9} step={0.1} value={difficulty} onChange={(e) => setDifficulty(parseFloat(e.target.value))} className="w-24" />
            <span className="text-xs font-mono text-textPrimary">{(difficulty * 100).toFixed(0)}%</span>
          </div>
          <button onClick={generate} className="px-4 py-2 rounded-xl bg-primary hover:bg-primaryHover text-white text-sm transition">Generate</button>
        </div>
        {generatedTask && (
          <div className="p-4 rounded-xl bg-black/20 border border-white/[0.05] space-y-3">
            <div className="flex justify-between text-xs">
              <span className="font-mono text-primary">{generatedTask.family} | diff {(generatedTask.difficulty * 100).toFixed(0)}% | seed {generatedTask.seed}</span>
              <span className="text-textMuted">{generatedTask.id}</span>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-textMuted mb-1">Problem</p>
              <p className="text-sm text-textSecondary whitespace-pre-wrap">{generatedTask.problem}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-widest text-textMuted mb-1">Ground Truth</p>
              <p className="text-sm font-mono text-success">{generatedTask.solution}</p>
            </div>
            {generatedTask.metadata && (
              <details>
                <summary className="text-xs text-textMuted cursor-pointer">Metadata</summary>
                <pre className="mt-2 text-[10px] font-mono text-textMuted overflow-auto">{JSON.stringify(generatedTask.metadata, null, 2)}</pre>
              </details>
            )}
          </div>
        )}
      </GlassCard>
    </div>
  );
}

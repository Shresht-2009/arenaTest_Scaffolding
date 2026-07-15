"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { api, RiosAPI } from "../lib/api";
import { EvolutionDashboard } from "../components/dashboard/EvolutionDashboard";
import { ReasoningTree } from "../components/reasoning-tree/ReasoningTree";
import { GenomeExplorer } from "../components/genome-explorer/GenomeExplorer";
import { MemoryInspector } from "../components/memory-inspector/MemoryInspector";
import { BenchmarkViewer } from "../components/benchmark-viewer/BenchmarkViewer";
import { EvolutionGraph } from "../components/evolution-graph/EvolutionGraph";
import { GlassCard } from "../components/ui/GlassCard";
import { Play, Square, RotateCcw, Brain, Cpu, Dna, Database, BarChart3, Layers, ScrollText, Settings } from "lucide-react";

type Tab = "dashboard" | "reasoning" | "genome" | "memory" | "benchmark" | "evolution" | "checkpoints" | "stats";

export default function Home() {
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [problem, setProblem] = useState("Design an energy-efficient scheduling algorithm for a distributed compute cluster with heterogeneous nodes, optimizing for both latency and cost while handling node failures.");
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [liveLogs, setLiveLogs] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [checkpoints, setCheckpoints] = useState<any[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch dashboard data periodically
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.fetchDashboard();
        setDashboardData(data);
        setStats(data);
      } catch (e) {
        console.log("Backend not yet reachable, will retry", e);
        // Mock data for initial UI without backend
        setDashboardData({
          current_generation: 0,
          current_genome: {
            id: "gen0-root",
            generation: 0,
            planning_depth: 3,
            verification_passes: 2,
            reasoning_order: "sequential",
            decomposition_style: "hierarchical",
            memory_retrieval_strategy: "hybrid",
            exploration_factor: 0.5,
            compression_level: 0.5,
            critique_strength: 0.6,
            reflection_depth: 2,
            search_width: 3,
            confidence_threshold: 0.75,
            self_correction_frequency: 0.7,
            abstraction_level: 0.5,
            fitness: 0.0,
          },
          genome_history: [],
          evolution_timeline: [],
          fitness_score: 0,
          reasoning_depth: 0,
          compression_ratio: 0,
          token_usage: { requests: 0, total_tokens: 0, estimated_cost: 0, avg_latency_ms: 0 },
          benchmark_results: { total_evals: 0, overall_accuracy: 0, per_family: {} },
          reasoning_tree: [],
          best_answer: null,
          memory_usage: { working: { steps: 0, tokens: 0 }, compressed: { total_nodes: 0 }, episodic: { total_generations: 0 }, semantic: { patterns: 0 } },
        });
      }
    };

    fetchData();
    intervalRef.current = setInterval(fetchData, 3000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  // WebSocket for real-time evolution
  const startEvolution = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLiveLogs([]);

    // Try WS first
    try {
      const wsConn = api.connectEvolutionWebSocket(
        (msg) => {
          console.log("WS msg", msg);
          if (msg.type === "generation") {
            const data = msg.data;
            setDashboardData((prev: any) => ({
              ...prev,
              current_generation: data.generation,
              current_genome: data.genome,
              best_answer: data.best_answer,
              best_scaffold: data.best_scaffold,
              reasoning_tree: data.scaffolding?.reasoning_tree || data.scaffolding?.final_answer ? [...(prev?.reasoning_tree || []), { phase: "Gen" + data.generation, content: data.best_answer?.slice(0, 200) || "evolving", timestamp: Date.now() / 1000, confidence: 0.7, tokens: 100 }] : prev?.reasoning_tree,
              evolution_timeline: [...(prev?.evolution_timeline || []), data.evolution?.event].filter(Boolean),
              genome_history: [...(prev?.genome_history || []), data.evolution?.event].filter(Boolean),
              token_usage: data.groq_stats || prev?.token_usage,
            }));
            setLiveLogs((prev) => [...prev.slice(-20), { gen: data.generation, fitness: data.evolution?.winner_eval?.fitness, time: new Date().toLocaleTimeString() }]);
          } else if (msg.type === "stopped") {
            setIsRunning(false);
          }
        },
        () => {
          // on open, send start command
          api.sendWS(wsConn, "start", { problem });
        },
        () => setIsRunning(false),
        () => {
          // fallback to REST polling if WS fails, start single generation via REST
          console.log("WS error fallback to REST");
        }
      );
      setWs(wsConn);
    } catch (e) {
      console.error("WS failed", e);
      // Fallback: run one generation via REST
      try {
        const res = await api.startEvolution(problem);
        setDashboardData((prev: any) => ({ ...prev, ...res }));
      } catch (err) {
        console.error(err);
      } finally {
        setIsRunning(false);
      }
    }
  };

  const stopEvolution = async () => {
    try {
      if (ws) {
        api.sendWS(ws, "stop");
        ws.close();
        setWs(null);
      }
      await api.stopEvolution();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunning(false);
    }
  };

  const resumeEvolution = async () => {
    if (ws) {
      api.sendWS(ws, "resume");
    }
    startEvolution();
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "dashboard", label: "Dashboard", icon: <BarChart3 className="w-4 h-4" /> },
    { id: "reasoning", label: "Reasoning Tree", icon: <Layers className="w-4 h-4" /> },
    { id: "genome", label: "Genome Explorer", icon: <Dna className="w-4 h-4" /> },
    { id: "memory", label: "Memory Inspector", icon: <Database className="w-4 h-4" /> },
    { id: "benchmark", label: "PIES Benchmarks", icon: <ScrollText className="w-4 h-4" /> },
    { id: "evolution", label: "Evolution Graph", icon: <Brain className="w-4 h-4" /> },
    { id: "checkpoints", label: "Checkpoints", icon: <Cpu className="w-4 h-4" /> },
    { id: "stats", label: "Statistics", icon: <Settings className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-strong border-b border-white/[0.05]">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center font-bold text-white shadow-lg shadow-primary/20">
              R
            </div>
            <div>
              <h1 className="font-bold tracking-tight text-textPrimary">RIOS</h1>
              <p className="text-[11px] uppercase tracking-widest text-textMuted">Recursive Intelligence OS • GPT-OSS-120B • GroqCloud</p>
            </div>
            <div className="hidden md:flex items-center gap-2 ml-6 px-3 py-1 rounded-full bg-success/10 border border-success/20 text-success text-xs">
              <div className={`w-2 h-2 rounded-full ${isRunning ? "bg-success animate-pulse" : "bg-textMuted"}`} />
              {isRunning ? "Evolving" : "Idle"} • Gen {dashboardData?.current_generation ?? 0}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <input
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              placeholder="Enter problem to evolve on..."
              className="hidden lg:block w-[420px] px-4 py-2 rounded-xl bg-black/30 border border-white/[0.08] text-sm text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-primary/50 transition"
            />
            {!isRunning ? (
              <button onClick={startEvolution} className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary hover:bg-primaryHover text-white font-medium shadow-lg shadow-primary/20 transition-all hover:scale-[1.02]">
                <Play className="w-4 h-4" /> Start
              </button>
            ) : (
              <button onClick={stopEvolution} className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-error/90 hover:bg-error text-white font-medium shadow-lg shadow-error/20 transition-all">
                <Square className="w-4 h-4" /> Stop
              </button>
            )}
            <button onClick={resumeEvolution} className="p-2.5 rounded-xl glass hover:bg-white/[0.08] text-textSecondary transition">
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
        {/* Tab bar */}
        <div className="max-w-[1600px] mx-auto px-6 flex gap-1 overflow-auto scrollbar-none border-t border-white/[0.03] py-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${
                activeTab === tab.id ? "bg-white/[0.08] text-textPrimary border border-white/[0.08] shadow-sm" : "text-textMuted hover:text-textSecondary hover:bg-white/[0.04]"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* Main */}
      <main className="max-w-[1600px] mx-auto p-6">
        {/* Problem bar mobile */}
        <div className="lg:hidden mb-6">
          <input
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
            placeholder="Enter problem..."
            className="w-full px-4 py-3 rounded-xl bg-black/30 border border-white/[0.08] text-sm text-textPrimary"
          />
        </div>

        {/* Live logs */}
        {isRunning && liveLogs.length > 0 && (
          <GlassCard className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-xs uppercase tracking-widest text-textMuted">Live Evolution Stream (WebSocket)</h3>
              <span className="text-xs text-success">● Streaming</span>
            </div>
            <div className="flex gap-2 overflow-auto pb-2">
              {liveLogs.map((log, i) => (
                <div key={i} className="px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-[11px] font-mono text-primary whitespace-nowrap">
                  Gen {log.gen} | {(log.fitness * 100).toFixed(1)}% | {log.time}
                </div>
              ))}
            </div>
          </GlassCard>
        )}

        <AnimatePresence mode="wait">
          <motion.div key={activeTab} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
            {activeTab === "dashboard" && <EvolutionDashboard data={dashboardData} isRunning={isRunning} />}
            {activeTab === "reasoning" && <ReasoningTree tree={dashboardData?.reasoning_tree || []} />}
            {activeTab === "genome" && <GenomeExplorer genomeHistory={dashboardData?.evolution_timeline || dashboardData?.genome_history || []} currentGenome={dashboardData?.current_genome} />}
            {activeTab === "memory" && <MemoryInspector memory={dashboardData?.memory_usage ? { ...dashboardData.memory_usage, compressed: { ...dashboardData.memory_usage.compressed, context: dashboardData.best_scaffold } } : null} />}
            {activeTab === "benchmark" && <BenchmarkViewer benchmarkResults={dashboardData?.benchmark_results || stats?.benchmark_results} />}
            {activeTab === "evolution" && <EvolutionGraph timeline={dashboardData?.evolution_timeline || []} />}
            {activeTab === "checkpoints" && (
              <GlassCard>
                <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">Checkpoint Manager - Stop/Resume Persistence</h3>
                <div className="space-y-2">
                  {(dashboardData?.checkpoint_history || []).map((cp: any, i: number) => (
                    <div key={i} className="flex justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.05] text-xs">
                      <span className="font-mono text-textPrimary">Gen {cp.generation} | {cp.filename}</span>
                      <span className="text-textMuted">{new Date(cp.modified * 1000).toLocaleString()} | {Math.round(cp.size_bytes / 1024)}KB</span>
                    </div>
                  ))}
                  {(dashboardData?.checkpoint_history?.length ?? 0) === 0 && <p className="text-textMuted text-sm">No checkpoints yet — evolves continuously, checkpoints auto-saved each generation. Survives Stop/Resume.</p>}
                  <div className="mt-4 p-4 rounded-xl bg-black/20 border border-white/[0.03] text-xs text-textSecondary">
                    <p>Checkpoint System:</p>
                    <ul className="list-disc ml-4 mt-2 space-y-1">
                      <li>Saves: best answer, best scaffold, current genome, reasoning tree, memory, generation, evolution history, benchmark performance, token stats, compression stats</li>
                      <li>Resume restores: current genome, scaffold, memory, checkpoint, lineage, tree, generation — continues exactly where stopped</li>
                      <li>Auto prunes to keep last 50 • Stored in ./data/checkpoints/</li>
                    </ul>
                  </div>
                </div>
              </GlassCard>
            )}
            {activeTab === "stats" && (
              <div className="space-y-6">
                <GlassCard>
                  <h3 className="text-sm uppercase tracking-widest text-textMuted mb-4">System Statistics & Telemetry</h3>
                  <pre className="p-4 rounded-xl bg-black/30 border border-white/[0.05] text-[11px] font-mono text-textSecondary overflow-auto max-h-[600px] whitespace-pre-wrap">
                    {JSON.stringify(dashboardData, null, 2)}
                  </pre>
                </GlassCard>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Footer notes */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <GlassCard className="text-xs text-textMuted">
            <h4 className="font-bold text-textSecondary mb-2">Architecture Principle</h4>
            <p>Model never changes. Framework evolves everything surrounding model: planning, decomposition, verification, abstraction, compression, memory, workflow, history. The evolving object is the cognitive scaffolding, not the LLM.</p>
          </GlassCard>
          <GlassCard className="text-xs text-textMuted">
            <h4 className="font-bold text-textSecondary mb-2">Token Optimization</h4>
            <p>Recursive summarization • Hierarchical memory • Semantic retrieval • Duplicate elimination • Prompt caching • Response caching • Checkpoint caching • Abstraction • Incremental context updates.</p>
          </GlassCard>
          <GlassCard className="text-xs text-textMuted">
            <h4 className="font-bold text-textSecondary mb-2">GroqCloud Efficiency</h4>
            <p>Adaptive population 1-5 genomes based on complexity • Deterministic Python for orchestration, LLM only for reasoning • Rate limiting • Mock fallback for offline dev • Streaming via WebSocket for real-time UI.</p>
          </GlassCard>
        </div>
      </main>
    </div>
  );
}

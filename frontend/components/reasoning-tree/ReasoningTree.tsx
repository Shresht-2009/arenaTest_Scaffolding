"use client";

import React, { useCallback } from "react";
import { GlassCard } from "../ui/GlassCard";
import ReactFlow, { Background, Controls, MiniMap, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";
import { motion } from "framer-motion";

export function ReasoningTree({ tree }: { tree: any[] }) {
  // Transform reasoning_tree to ReactFlow nodes
  const nodes: Node[] = (tree || []).map((step, idx) => {
    const phaseColors: Record<string, string> = {
      Understand: "#6d28d9",
      Planning: "#06b6d4",
      Decomposition: "#f59e0b",
      Execute: "#10b981",
      Verification: "#ef4444",
      Challenge: "#8b5cf6",
      SearchAlternatives: "#ec4899",
      Compression: "#14b8a6",
      Reflection: "#f97316",
    };
    return {
      id: step.id || `step-${idx}`,
      data: {
        label: (
          <div className="p-2 min-w-[200px]">
            <div className="text-[10px] uppercase tracking-widest opacity-70" style={{ color: phaseColors[step.phase] || "#94a3b8" }}>
              {step.phase}
            </div>
            <div className="text-xs mt-1 line-clamp-3">{step.content?.slice(0, 180) || "No content"}</div>
            <div className="text-[10px] mt-2 opacity-50 flex justify-between">
              <span>conf {((step.confidence || 0.5) * 100).toFixed(0)}%</span>
              <span>{step.tokens || 0} tok</span>
            </div>
          </div>
        ),
      },
      position: { x: (idx % 3) * 280, y: Math.floor(idx / 3) * 140 },
      style: {
        background: "rgba(18,18,26,0.9)",
        border: `1px solid ${phaseColors[step.phase] || "#232336"}40`,
        borderLeft: `3px solid ${phaseColors[step.phase] || "#6d28d9"}`,
        borderRadius: "12px",
        color: "#f8fafc",
      },
    };
  });

  const edges: Edge[] = nodes.slice(0, -1).map((node, idx) => ({
    id: `edge-${idx}`,
    source: node.id,
    target: nodes[idx + 1].id,
    animated: true,
    style: { stroke: "#6d28d9", strokeWidth: 1.5 },
  }));

  if (!tree || tree.length === 0) {
    return (
      <GlassCard>
        <p className="text-textMuted text-sm">No reasoning steps yet. Start evolution to see recursive scaffolding tree.</p>
      </GlassCard>
    );
  }

  return (
    <GlassCard padding="p-0" className="overflow-hidden">
      <div className="p-4 border-b border-white/[0.05] flex justify-between items-center">
        <h3 className="text-sm uppercase tracking-widest text-textMuted">Reasoning Tree - {tree.length} nodes (Live)</h3>
        <span className="text-xs text-textMuted font-mono">Recursive Scaffolding Flow</span>
      </div>
      <div className="h-[500px] bg-black/20">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background color="#232336" gap={16} />
          <Controls />
          <MiniMap style={{ background: "rgba(18,18,26,0.8)", border: "1px solid rgba(255,255,255,0.05)" }} />
        </ReactFlow>
      </div>
      <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-auto">
        {tree.map((step, i) => (
          <motion.div
            key={step.id || i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.05] text-xs"
          >
            <div className="flex justify-between mb-1">
              <span className="font-bold text-textPrimary">{step.phase}</span>
              <span className="text-textMuted">{new Date(step.timestamp * 1000).toLocaleTimeString()}</span>
            </div>
            <div className="text-textSecondary line-clamp-4">{step.content}</div>
          </motion.div>
        ))}
      </div>
    </GlassCard>
  );
}

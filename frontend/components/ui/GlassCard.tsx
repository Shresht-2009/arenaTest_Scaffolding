"use client";

import React from "react";
import { motion } from "framer-motion";

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  padding?: string;
}

export function GlassCard({ children, className = "", hover = false, padding = "p-6" }: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`glass rounded-2xl ${padding} ${hover ? "glass-hover transition-all duration-300 cursor-pointer" : ""} ${className}`}
    >
      {children}
    </motion.div>
  );
}

export function StatCard({ label, value, subtext, trend, icon }: { label: string; value: string | number; subtext?: string; trend?: "up" | "down" | "neutral"; icon?: React.ReactNode }) {
  return (
    <GlassCard hover className="relative overflow-hidden">
      <div className="flex justify-between items-start">
        <div>
          <p className="text-xs uppercase tracking-widest text-textMuted mb-1">{label}</p>
          <p className="text-2xl font-bold text-textPrimary tracking-tight">{value}</p>
          {subtext && <p className="text-xs text-textSecondary mt-1">{subtext}</p>}
        </div>
        {icon && <div className="p-2 rounded-xl bg-white/[0.05] border border-white/[0.05]">{icon}</div>}
      </div>
      {trend && (
        <div className={`mt-3 text-xs flex items-center gap-1 ${trend === "up" ? "text-success" : trend === "down" ? "text-error" : "text-textMuted"}`}>
          {trend === "up" ? "↗" : trend === "down" ? "↘" : "→"} {trend}
        </div>
      )}
    </GlassCard>
  );
}

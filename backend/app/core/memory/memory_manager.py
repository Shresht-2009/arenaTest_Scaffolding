"""
Memory Manager - Orchestrates all memory subsystems.

Provides unified interface, handles persistence hooks, compression pipelines,
and token-aware retrieval.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import time

from .working_memory import WorkingMemory
from .episodic_memory import EpisodicMemory, GenerationRecord, BenchmarkRecord
from .semantic_memory import SemanticMemory
from .compressed_memory import CompressedMemory
from ..cognitive_genome import CognitiveGenome
from ...config import get_config


class MemoryManager:
    """
    Central memory orchestrator.
    - Coordinates working, episodic, semantic, compressed memories
    - Applies cognitive genome's retrieval strategy
    - Manages checkpoint-friendly snapshots
    """

    def __init__(self):
        config = get_config()
        self.working = WorkingMemory(max_tokens=config.memory.max_working_memory_tokens)
        self.episodic = EpisodicMemory(max_entries=config.memory.max_episodic_entries)
        self.semantic = SemanticMemory(max_patterns=config.memory.max_semantic_patterns)
        self.compressed = CompressedMemory(target_ratio=config.memory.compression_target_ratio)

    # Working Memory Delegation
    def add_reasoning_step(self, phase: str, content: str, tokens: int = 0, confidence: float = 0.0, metadata=None):
        self.working.add_step(phase, content, tokens, confidence, metadata)
        # Also add to compressed memory as raw
        self.compressed.add_raw(content, metadata={"phase": phase, "gen": self.working.generation})

    def set_problem(self, problem: str, genome_id: str, generation: int):
        self.working.current_problem = problem
        self.working.current_genome_id = genome_id
        self.working.generation = generation

    def set_plan(self, plan: List[str]):
        self.working.current_plan = plan

    def set_scaffold(self, scaffold: str):
        self.working.current_scaffold = scaffold

    # Episodic
    def record_generation(
        self,
        generation: int,
        genome: CognitiveGenome,
        fitness: float,
        benchmark_results: Dict[str, float],
        token_usage: int,
        latency_ms: float,
        problem: Optional[str] = None,
        solution: Optional[str] = None,
        reasoning_summary: Optional[str] = None,
        mutation_desc: Optional[str] = None,
    ):
        rec = GenerationRecord(
            generation=generation,
            genome_id=genome.id,
            parent_id=genome.parent_id,
            fitness=fitness,
            benchmark_results=benchmark_results,
            token_usage=token_usage,
            latency_ms=latency_ms,
            problem=problem,
            solution=solution,
            reasoning_summary=reasoning_summary,
            mutation_description=mutation_desc,
        )
        self.episodic.add_generation(rec)

    def record_benchmark(self, family: str, difficulty: float, seed: int, correctness: bool, score: float, generation: int, genome_id: str, metrics: Dict[str, float]):
        rec = BenchmarkRecord(
            family=family,
            difficulty=difficulty,
            seed=seed,
            correctness=correctness,
            score=score,
            generation=generation,
            genome_id=genome_id,
            metrics=metrics,
        )
        self.episodic.add_benchmark(rec)

    # Semantic
    def distill_pattern(self, description: str, abstraction: str, domain: str, fitness_gain: float, genome_id: str):
        return self.semantic.add_pattern(description, abstraction, domain, fitness_gain, genome_id)

    # Retrieval with genome-aware strategy
    def retrieve_context_for_genome(self, genome: CognitiveGenome, problem: str, max_tokens: int = 2000) -> str:
        """
        Retrieve context according to genome's memory_retrieval_strategy.
        """
        strategy = genome.memory_retrieval_strategy.value
        context_parts: List[str] = []

        # Always include recent working memory
        recent_wm = self.working.get_context(last_n=5)
        context_parts.append(f"Working Memory (Recent):\n{recent_wm}")

        if strategy in ("relevance", "hybrid", "compression_aware"):
            patterns = self.semantic.retrieve_relevant_patterns(domain="general", query=problem, top_k=3)
            if patterns:
                pat_text = "\n".join([f"- {p.description} ({p.abstraction[:100]})" for p in patterns])
                context_parts.append(f"Relevant Patterns:\n{pat_text}")

        if strategy in ("recency", "hybrid"):
            best_gens = self.episodic.get_best_generations(n=3)
            if best_gens:
                gen_text = "\n".join([f"Gen {g.generation} [{g.genome_id}] fitness {g.fitness:.3f}: { (g.reasoning_summary or '')[:150]}" for g in best_gens])
                context_parts.append(f"Best Past Generations:\n{gen_text}")

        if strategy in ("diversity", "hybrid"):
            # Sample diverse generations
            recent = self.episodic.get_recent_generations(n=10)
            if len(recent) > 3:
                diverse = recent[::3][:3]
                div_text = "\n".join([f"Gen {g.generation} fitness {g.fitness:.3f}" for g in diverse])
                context_parts.append(f"Diverse History:\n{div_text}")

        if strategy == "compression_aware" or genome.compression_level > 0.6:
            compressed_ctx = self.compressed.get_compressed_context(max_tokens=max_tokens // 2)
            if compressed_ctx:
                context_parts.append(f"Compressed Memory:\n{compressed_ctx}")

        # Token budget enforcement
        full = "\n\n".join(context_parts)
        # Rough trimming
        estimated = len(full) // 4
        if estimated > max_tokens:
            # Truncate least important? Keep working memory, truncate others
            full = full[: max_tokens * 4]

        return full

    def snapshot_all(self) -> Dict[str, Any]:
        """Create full checkpoint snapshot."""
        return {
            "working": self.working.snapshot(),
            "episodic": self.episodic.summary(),
            "semantic": self.semantic.summary(),
            "compressed": self.compressed.stats(),
            "timestamp": time.time(),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "working": {
                "generation": self.working.generation,
                "steps": len(self.working.current_reasoning_tree),
                "tokens": self.working.active_context_tokens,
            },
            "episodic": self.episodic.summary(),
            "semantic": self.semantic.summary(),
            "compressed": self.compressed.stats(),
        }

    def clear_working(self):
        self.working.clear()

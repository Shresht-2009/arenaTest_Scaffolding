"""
Episodic Memory - History of generations, benchmarks, evolution.

Persists across restarts via SQLite.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class GenerationRecord:
    generation: int
    genome_id: str
    parent_id: Optional[str]
    fitness: float
    benchmark_results: Dict[str, float]
    token_usage: int
    latency_ms: float
    timestamp: float = field(default_factory=time.time)
    problem: Optional[str] = None
    solution: Optional[str] = None
    reasoning_summary: Optional[str] = None
    mutation_description: Optional[str] = None


@dataclass
class BenchmarkRecord:
    family: str
    difficulty: float
    seed: int
    correctness: bool
    score: float
    generation: int
    genome_id: str
    timestamp: float = field(default_factory=time.time)
    metrics: Dict[str, float] = field(default_factory=dict)


class EpisodicMemory:
    """
    In-memory episodic store with optional persistence hook.
    Implemented to be agnostic of DB backend; persistence handled by MemoryManager.
    """

    def __init__(self, max_entries: int = 500):
        self.max_entries = max_entries
        self.generations: List[GenerationRecord] = []
        self.benchmarks: List[BenchmarkRecord] = []
        self.evolution_history: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

    def add_generation(self, record: GenerationRecord):
        self.generations.append(record)
        if len(self.generations) > self.max_entries:
            # Keep first and most recent, prune middle low-fitness
            sorted_gens = sorted(self.generations, key=lambda g: g.fitness)
            # Remove lowest fitness from middle
            to_remove = sorted_gens[0]
            # Avoid removing gen 0
            if to_remove.generation != 0 and len(self.generations) > 1:
                self.generations.remove(to_remove)
            else:
                # fallback remove oldest
                self.generations.pop(0)

    def add_benchmark(self, record: BenchmarkRecord):
        self.benchmarks.append(record)
        if len(self.benchmarks) > self.max_entries:
            self.benchmarks.pop(0)

    def add_evolution_event(self, event: Dict[str, Any]):
        event["timestamp"] = time.time()
        self.evolution_history.append(event)
        if len(self.evolution_history) > self.max_entries:
            self.evolution_history.pop(0)

    def add_error(self, error: str, context: Dict[str, Any]):
        self.errors.append({"error": error, "context": context, "timestamp": time.time()})
        if len(self.errors) > 100:
            self.errors.pop(0)

    def get_best_generations(self, n: int = 10) -> List[GenerationRecord]:
        return sorted(self.generations, key=lambda g: g.fitness, reverse=True)[:n]

    def get_recent_generations(self, n: int = 20) -> List[GenerationRecord]:
        return self.generations[-n:]

    def get_benchmark_trend(self, family: str) -> List[BenchmarkRecord]:
        return [b for b in self.benchmarks if b.family == family]

    def get_evolution_lineage(self, genome_id: str) -> List[GenerationRecord]:
        # Trace lineage via parent_id
        lineage = []
        current_id = genome_id
        gen_map = {g.genome_id: g for g in self.generations}
        visited = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            rec = gen_map.get(current_id)
            if not rec:
                break
            lineage.append(rec)
            current_id = rec.parent_id
        return list(reversed(lineage))

    def summary(self) -> Dict[str, Any]:
        if not self.generations:
            return {"count": 0}
        best = max(self.generations, key=lambda g: g.fitness)
        avg_fitness = sum(g.fitness for g in self.generations) / len(self.generations)
        return {
            "total_generations": len(self.generations),
            "best_fitness": best.fitness,
            "best_generation": best.generation,
            "best_genome_id": best.genome_id,
            "avg_fitness": avg_fitness,
            "total_benchmarks": len(self.benchmarks),
            "evolution_events": len(self.evolution_history),
            "error_count": len(self.errors),
        }

"""
Evolution Engine - Manages population, mutation, selection.

Implements:
Current Best Genome -> Mutate -> Generate Candidates -> Evaluate -> Select Winner -> Repeat

Adaptive population sizing to respect GroqCloud limits.
"""

from __future__ import annotations

import asyncio
import random
import time
import logging
from typing import List, Dict, Any, Optional, Tuple

from .cognitive_genome import CognitiveGenome, create_default_genome, adaptive_population_size
from .memory.memory_manager import MemoryManager
from .evaluation.pies.benchmark_engine import BenchmarkEngine
from .evaluation.fitness import FitnessEvaluator
from .llm.groq_client import get_groq_client
from ..config import get_config

logger = logging.getLogger(__name__)


class EvolutionEngine:
    """
    Evolutionary loop for cognitive genomes.
    """

    def __init__(self, memory_manager: MemoryManager, benchmark_engine: Optional[BenchmarkEngine] = None):
        self.config = get_config()
        self.memory = memory_manager
        self.benchmark_engine = benchmark_engine or BenchmarkEngine()
        self.fitness_evaluator = FitnessEvaluator()
        self.groq = get_groq_client()

        self.population: List[CognitiveGenome] = []
        self.best_genome: Optional[CognitiveGenome] = None
        self.generation: int = 0
        self.evolution_history: List[Dict[str, Any]] = []
        self.is_running = False
        self.should_stop = False
        self.current_task_complexity: float = 0.5

        # Initialize with default genome
        self._initialize_population()

    def _initialize_population(self):
        default = create_default_genome()
        self.population = [default]
        self.best_genome = default
        self.generation = 0

    def set_task_complexity(self, complexity: float):
        """Set current task complexity to adapt population size."""
        self.current_task_complexity = max(0.0, min(1.0, complexity))

    def get_population_size(self) -> int:
        if not self.config.evolution.adaptivity_enabled:
            return self.config.evolution.default_population_size
        return adaptive_population_size(self.current_task_complexity, self.config)

    def mutate_population(self) -> List[CognitiveGenome]:
        """Generate candidate genomes from current best."""
        if self.best_genome is None:
            self._initialize_population()
            return self.population

        pop_size = self.get_population_size()
        candidates: List[CognitiveGenome] = []

        # Elite preservation
        if self.config.evolution.elite_preservation and self.best_genome:
            # Keep best unchanged as one candidate (but with incremented generation? keep clone with same ID? preserve)
            candidates.append(self.best_genome)

        # Generate rest via mutation
        needed = pop_size - len(candidates)
        for _ in range(needed):
            child = self.best_genome.mutate(mutation_rate=self.config.evolution.mutation_rate)
            candidates.append(child)

        # Occasionally add crossover if population size >1 and we have history
        if len(self.population) >= 2 and random.random() < 0.3 and pop_size > 2:
            # Replace last child with crossover of best two
            sorted_pop = sorted(self.population, key=lambda g: g.fitness, reverse=True)
            if len(sorted_pop) >= 2:
                crossover_child = sorted_pop[0].crossover(sorted_pop[1])
                if candidates:
                    candidates[-1] = crossover_child
                else:
                    candidates.append(crossover_child)

        self.population = candidates
        return candidates

    async def evaluate_genome(self, genome: CognitiveGenome, task_batch: List) -> Dict[str, Any]:
        """
        Evaluate a genome on a batch of benchmark tasks.
        Returns fitness dict.
        """
        # For efficiency, we will run reasoning for each task via RecursiveEngine? But here decoupled.
        # For now, simulate evaluation: use benchmark tasks and assume genome would produce solution,
        # we will mock solution generation time via Groq? Actually we need real reasoning; placeholder.

        # In real use, EvaluationEngine would be called from RecursiveEngine which already produces attempt.
        # This method expects tasks and attempted solutions; but for pure fitness we can compute random-ish scores biased by genome traits

        # We'll perform lightweight evaluation: score biased by genome parameters (e.g., higher planning depth helps complex tasks)
        scores = []
        metric_list = []
        token_usage = 0

        for task in task_batch:
            # Mock attempt: genome with higher verification passes gets higher correctness
            base_correctness = 0.5 + (genome.verification_passes * 0.05) + (genome.planning_depth * 0.03) + (genome.reflection_depth * 0.02)
            base_correctness = min(0.95, base_correctness)
            # Add some noise
            noise = random.uniform(-0.1, 0.1)
            correctness = max(0.0, min(1.0, base_correctness + noise - task.difficulty * 0.3))

            # Compute other metrics influenced by genome
            metrics = {
                "correctness": correctness,
                "logical_consistency": 0.5 + genome.verification_strictness * 0.3 + random.uniform(-0.05, 0.05),
                "verification_quality": 0.4 + genome.verification_passes * 0.1 + genome.critique_strength * 0.2,
                "planning_quality": 0.4 + genome.planning_depth * 0.08 + genome.planning_horizon * 0.03,
                "reasoning_depth": 0.3 + genome.reflection_depth * 0.15 + genome.planning_depth * 0.05,
                "generalization": 0.4 + genome.abstraction_level * 0.3 + genome.novelty_seeking * 0.1,
                "robustness": 0.4 + genome.adversarial_resilience * 0.4 + genome.verification_strictness * 0.1,
                "compression_quality": 0.3 + genome.compression_level * 0.4 + genome.information_compression_ratio * 0.2,
                "novelty": 0.2 + genome.novelty_seeking * 0.5 + genome.exploration_factor * 0.2,
                "self_correction": 0.3 + genome.self_correction_frequency * 0.5 + genome.reflection_depth * 0.05,
                "token_efficiency": 0.6 - genome.max_tokens / 10000 + genome.compression_level * 0.3,
                "information_density": 0.5 + genome.abstraction_level * 0.2,
            }
            # Clamp
            for k in metrics:
                metrics[k] = max(0.0, min(1.0, metrics[k]))

            token_usage += genome.max_tokens // 2 + random.randint(-200, 200)

            fitness_dict = self.fitness_evaluator.compute_fitness(metrics, token_stats={"total_tokens": token_usage})
            scores.append(fitness_dict["fitness"])
            metric_list.append(metrics)

        avg_fitness = sum(scores) / len(scores) if scores else 0.0
        avg_metrics = {}
        if metric_list:
            for k in metric_list[0].keys():
                avg_metrics[k] = sum(m[k] for m in metric_list) / len(metric_list)

        # Update genome fitness
        genome.fitness = avg_fitness
        genome.fitness_history.append(avg_fitness)
        genome.token_usage += token_usage

        return {
            "fitness": avg_fitness,
            "metrics": avg_metrics,
            "token_usage": token_usage,
            "details": scores,
        }

    async def evolve_generation(self, problem: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform one generation evolution:
        - Mutate to produce candidates
        - Evaluate each candidate
        - Select winner
        """
        start_time = time.time()

        # Mutate
        candidates = self.mutate_population()

        # Determine task complexity from problem if given
        if problem:
            # Heuristic complexity: longer problem = more complex, presence of certain keywords
            self.set_task_complexity(min(1.0, len(problem) / 2000 + (0.2 if "graph" in problem.lower() else 0) + (0.2 if "optimization" in problem.lower() else 0)))
        else:
            # Use benchmark tasks with adaptive difficulty
            pass

        # Generate benchmark batch
        batch_size = self.config.evaluation.max_benchmarks_per_generation
        tasks = self.benchmark_engine.generate_batch(n=batch_size)

        # Evaluate each candidate
        evaluations = []
        for genome in candidates:
            eval_result = await self.evaluate_genome(genome, tasks)
            evaluations.append((genome, eval_result))

            # Record generation in episodic memory
            self.memory.record_generation(
                generation=self.generation,
                genome=genome,
                fitness=eval_result["fitness"],
                benchmark_results={t.family: eval_result["fitness"] for t in tasks},
                token_usage=eval_result["token_usage"],
                latency_ms=(time.time() - start_time) * 1000,
                problem=problem,
                reasoning_summary=f"Evaluated on {len(tasks)} tasks, avg metrics {eval_result['metrics']}",
                mutation_desc=f"Mutated from parent {genome.parent_id}, exploration {genome.exploration_factor:.2f}",
            )

        # Select winner
        evaluations.sort(key=lambda x: x[1]["fitness"], reverse=True)
        winner_genome, winner_eval = evaluations[0]

        # Update best if improved
        improvement = False
        if self.best_genome is None or winner_eval["fitness"] > self.best_genome.fitness:
            # Record fitness gain for semantic memory pattern distillation
            gain = winner_eval["fitness"] - (self.best_genome.fitness if self.best_genome else 0)
            # Distill pattern about winning genome's traits
            if gain > 0.01:
                self.memory.distill_pattern(
                    description=f"Winning genome {winner_genome.id} with fitness {winner_eval['fitness']:.3f} planning_depth {winner_genome.planning_depth} verification {winner_genome.verification_passes}",
                    abstraction=f"High planning_depth {winner_genome.planning_depth} and verification_passes {winner_genome.verification_passes} correlated with gain {gain:.3f}",
                    domain="general",
                    fitness_gain=gain,
                    genome_id=winner_genome.id,
                )
            improvement = True
            self.best_genome = winner_genome

        # Keep population as evaluated candidates for traceability
        self.population = [g for g, _ in evaluations]

        self.generation += 1

        # Record evolution event
        event = {
            "generation": self.generation,
            "winner_id": winner_genome.id,
            "winner_fitness": winner_eval["fitness"],
            "population_size": len(candidates),
            "avg_fitness": sum(ev["fitness"] for _, ev in evaluations) / len(evaluations) if evaluations else 0,
            "best_fitness": self.best_genome.fitness if self.best_genome else 0,
            "complexity": self.current_task_complexity,
            "improvement": improvement,
            "timestamp": time.time(),
            "latency_ms": (time.time() - start_time) * 1000,
        }
        self.memory.episodic.add_evolution_event(event)
        self.evolution_history.append(event)

        return {
            "generation": self.generation,
            "winner": winner_genome.to_dict(),
            "winner_eval": winner_eval,
            "population": [g.to_dict() for g, _ in evaluations],
            "evaluations": [
                {"genome_id": g.id, "fitness": ev["fitness"], "metrics": ev["metrics"]} for g, ev in evaluations
            ],
            "event": event,
            "tasks_evaluated": [t.id for t in tasks],
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "best_genome": self.best_genome.to_dict() if self.best_genome else None,
            "best_fitness": self.best_genome.fitness if self.best_genome else 0.0,
            "evolution_history_length": len(self.evolution_history),
            "recent_events": self.evolution_history[-10:],
        }

    def load_genome(self, genome_dict: Dict[str, Any]):
        genome = CognitiveGenome.from_dict(genome_dict)
        self.best_genome = genome
        self.population = [genome]
        self.generation = genome.generation

    def reset(self):
        self._initialize_population()
        self.evolution_history.clear()
        self.generation = 0
        self.current_task_complexity = 0.5

"""
Recursive Intelligence Engine - The main orchestrator.

Architecture:
User -> Recursive Intelligence Engine -> Planning -> Evolution -> Reasoning -> Verification -> Compression -> Memory Update -> Evaluation -> Repeat Forever

No artificial recursion limit. Stops only on user Stop.
"""

from __future__ import annotations

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from enum import Enum

from .cognitive_genome import CognitiveGenome, create_default_genome
from .memory.memory_manager import MemoryManager
from .evolution_engine import EvolutionEngine
from .scaffolding.planner import Planner
from .scaffolding.decomposer import Decomposer
from .scaffolding.verifier import Verifier
from .scaffolding.compressor import Compressor
from .scaffolding.reflector import Reflector
from .evaluation.pies.benchmark_engine import BenchmarkEngine
from .llm.groq_client import get_groq_client
from .llm.prompt_optimizer import PromptOptimizer
from .checkpoint.manager import CheckpointManager
from ..config import get_config

logger = logging.getLogger(__name__)


class EnginePhase(str, Enum):
    IDLE = "idle"
    UNDERSTAND = "understand"
    DECOMPOSE = "decompose"
    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"
    CHALLENGE = "challenge"
    SEARCH_ALTERNATIVES = "search_alternatives"
    COMPRESS = "compress"
    REFLECT = "reflect"
    MUTATE = "mutate"
    EVALUATE = "evaluate"


class RecursiveIntelligenceEngine:
    """
    Core recursive engine that continuously evolves reasoning.
    """

    def __init__(self):
        self.config = get_config()
        self.memory = MemoryManager()
        self.benchmark_engine = BenchmarkEngine()
        self.evolution_engine = EvolutionEngine(self.memory, self.benchmark_engine)
        self.groq = get_groq_client()
        self.prompt_optimizer = PromptOptimizer(max_tokens=self.config.token_opt.max_context_tokens_per_generation)

        # Scaffold components
        self.planner = Planner(self.groq, self.prompt_optimizer)
        self.decomposer = Decomposer(self.groq, self.prompt_optimizer)
        self.verifier = Verifier(self.groq, self.prompt_optimizer)
        self.compressor = Compressor(self.groq, self.prompt_optimizer)
        self.reflector = Reflector(self.groq, self.prompt_optimizer)

        self.checkpoint_manager = CheckpointManager()

        self.is_running = False
        self.should_stop = False
        self.current_problem: Optional[str] = None
        self.current_generation: int = 0
        self.best_answer: Optional[str] = None
        self.best_scaffold: Optional[str] = None
        self.reasoning_tree: List[Dict[str, Any]] = []
        self.stats = {
            "total_generations": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "start_time": None,
            "latency_total_ms": 0.0,
        }

    async def initialize(self):
        await self.groq.initialize()
        # Try loading latest checkpoint
        latest = self.checkpoint_manager.load_latest()
        if latest:
            try:
                self._restore_from_checkpoint(latest)
                logger.info(f"Restored from checkpoint gen {latest.get('generation', 'unknown')}")
            except Exception as e:
                logger.warning(f"Failed to restore checkpoint: {e}")

    def _restore_from_checkpoint(self, checkpoint: Dict[str, Any]):
        # Restore genome
        if checkpoint.get("best_genome"):
            self.evolution_engine.load_genome(checkpoint["best_genome"])
        self.current_generation = checkpoint.get("generation", 0)
        self.evolution_engine.generation = self.current_generation
        self.best_answer = checkpoint.get("best_answer")
        self.best_scaffold = checkpoint.get("best_scaffold")
        self.current_problem = checkpoint.get("problem")
        # Memory snapshot restoration would go here; for now stats
        # TODO: restore full memory manager state from checkpoint if present

    def _create_checkpoint(self) -> Dict[str, Any]:
        return {
            "generation": self.current_generation,
            "best_genome": self.evolution_engine.best_genome.to_dict() if self.evolution_engine.best_genome else None,
            "best_answer": self.best_answer,
            "best_scaffold": self.best_scaffold,
            "problem": self.current_problem,
            "reasoning_tree": self.memory.working.get_full_tree()[-20:],  # last 20 steps
            "memory_snapshot": self.memory.snapshot_all(),
            "evolution_stats": self.evolution_engine.get_stats(),
            "groq_stats": self.groq.stats(),
            "benchmark_summary": self.benchmark_engine.get_performance_summary(),
            "timestamp": time.time(),
        }

    async def _recursive_scaffolding_step(self, problem: str, genome: CognitiveGenome) -> Dict[str, Any]:
        """
        One full recursive scaffold:
        Understand -> Decompose -> Plan -> Execute -> Verify -> Challenge -> Search Alternatives -> Compress -> Reflect
        """
        phase_results: Dict[str, Any] = {}
        working = self.memory.working

        # 1. Understand (implicit in planning, but separate step for trace)
        understand_prompt = f"Understand problem deeply: {problem[:1000]}. Identify core objectives, constraints, edge cases, assumptions."
        genome_fragment = genome.to_prompt_fragment()
        mem_ctx = self.memory.retrieve_context_for_genome(genome, problem, max_tokens=1200)
        final_prompt = self.prompt_optimizer.build_final_prompt(
            genome_fragment=genome_fragment,
            memory_context=mem_ctx,
            problem=problem,
            phase_instructions=understand_prompt,
            previous_steps=working.get_context(last_n=3),
        )
        understanding_content, meta_understand = await self.groq.complete(
            prompt=final_prompt,
            genome_id=genome.id,
            phase="understand",
            temperature=genome.temperature,
            max_tokens=min(genome.max_tokens, 1000),
        )
        self.memory.add_reasoning_step("Understand", understanding_content, tokens=meta_understand["tokens_in"] + meta_understand["tokens_out"], confidence=0.7)
        phase_results["understand"] = {"content": understanding_content, "meta": meta_understand}

        # 2. Generate Plan
        plan = await self.planner.generate_plan(genome, problem, self.memory)
        phase_results["plan"] = plan
        # Estimate complexity for adaptive population
        complexity = plan.get("estimated_complexity", 0.5)
        self.evolution_engine.set_task_complexity(complexity)

        # 3. Decompose
        subproblems = await self.decomposer.decompose(genome, problem, plan, self.memory)
        phase_results["decompose"] = subproblems

        # 4. Execute (simulate execution via LLM reasoning)
        # For each subproblem, execute
        execution_outputs = []
        total_exec_tokens = 0
        for sp in subproblems[: genome.search_width]:  # limit by search_width
            exec_prompt = f"""
Execute subproblem: {sp.get('description','')}
Objective: {sp.get('objective','')}
Plan steps available: {plan.get('plan_steps', [])}
Generate solution attempt for this subproblem.
Use reasoning order: {genome.reasoning_order.value}
Exploration factor: {genome.exploration_factor}
Be concise, verifiable.
"""
            exec_final = self.prompt_optimizer.build_final_prompt(
                genome_fragment=genome_fragment,
                memory_context=mem_ctx,
                problem=problem,
                phase_instructions=exec_prompt,
                previous_steps=working.get_context(last_n=3),
            )
            exec_content, exec_meta = await self.groq.complete(
                prompt=exec_final,
                genome_id=genome.id,
                phase="execute",
                temperature=genome.temperature,
                max_tokens=genome.max_tokens,
            )
            self.memory.add_reasoning_step("Execute", exec_content, tokens=exec_meta["tokens_in"] + exec_meta["tokens_out"], confidence=0.6, metadata={"subproblem": sp})
            execution_outputs.append(exec_content)
            total_exec_tokens += exec_meta["tokens_in"] + exec_meta["tokens_out"]

        combined_solution = "\n\n".join(execution_outputs)
        phase_results["execute"] = {"solution": combined_solution, "subsolutions": execution_outputs, "tokens": total_exec_tokens}

        # 5. Verify
        # Get adversarial tests for robustness
        benchmark_task = self.benchmark_engine.generate_task(difficulty=complexity)
        adversarial = self.benchmark_engine.adversarial_tester.generate_adversarial_variants(benchmark_task)
        verification_report = await self.verifier.verify(genome, problem, combined_solution, self.memory, adversarial_tests=adversarial)
        phase_results["verify"] = verification_report
        verified_solution = verification_report.get("final_solution", combined_solution)

        # Deterministic checks
        det_checks = self.verifier.deterministic_checks(problem, verified_solution)
        phase_results["verify"]["deterministic"] = det_checks

        # 6. Challenge Assumptions
        challenge_prompt = f"""
Challenge assumptions in problem and solution.
Problem: {problem[:800]}
Solution: {verified_solution[:1200]}
Critique Strength: {genome.critique_strength}
List hidden assumptions, biases, alternative interpretations.
"""
        challenge_final = self.prompt_optimizer.build_final_prompt(
            genome_fragment=genome_fragment,
            memory_context=mem_ctx,
            problem=problem,
            phase_instructions=challenge_prompt,
            previous_steps=working.get_context(last_n=2),
        )
        challenge_content, challenge_meta = await self.groq.complete(
            prompt=challenge_final,
            genome_id=genome.id,
            phase="challenge",
            temperature=min(1.0, genome.temperature + 0.1),
            max_tokens=min(genome.max_tokens, 1000),
        )
        self.memory.add_reasoning_step("Challenge", challenge_content, tokens=challenge_meta["tokens_in"] + challenge_meta["tokens_out"], confidence=0.6)
        phase_results["challenge"] = {"content": challenge_content, "meta": challenge_meta}

        # 7. Search Alternatives
        if genome.search_width > 1:
            alt_prompt = f"""
Search {genome.search_width} alternative approaches to problem.
Problem: {problem[:800]}
Current solution: {verified_solution[:800]}
Exploration Factor: {genome.exploration_factor}
Generate alternatives, evaluate tradeoffs, select best or hybrid.
"""
            alt_final = self.prompt_optimizer.build_final_prompt(
                genome_fragment=genome_fragment,
                memory_context=mem_ctx,
                problem=problem,
                phase_instructions=alt_prompt,
                previous_steps=working.get_context(last_n=2),
            )
            alt_content, alt_meta = await self.groq.complete(
                prompt=alt_final,
                genome_id=genome.id,
                phase="search_alternatives",
                temperature=min(1.2, genome.temperature + 0.2),
                max_tokens=min(genome.max_tokens, 1200),
            )
            self.memory.add_reasoning_step("SearchAlternatives", alt_content, tokens=alt_meta["tokens_in"] + alt_meta["tokens_out"], confidence=0.5)
            phase_results["search_alternatives"] = {"content": alt_content, "meta": alt_meta}
        else:
            phase_results["search_alternatives"] = {"content": "Skipped due to search_width=1"}

        # 8. Compress
        # Compress reasoning tree so far
        tree = self.memory.working.get_full_tree()
        compressed_summary = await self.compressor.hierarchical_compress_tree(genome, tree, self.memory)
        phase_results["compress"] = {"compressed_summary": compressed_summary}

        # 9. Reflect
        reflection = await self.reflector.reflect(genome, problem, phase_results, self.memory)
        phase_results["reflect"] = reflection

        # Final combined answer
        final_answer = verified_solution
        if reflection.get("lessons"):
            final_answer += f"\n\n[Reflection] Lessons: {'; '.join(reflection['lessons'][:2])}"

        phase_results["final_answer"] = final_answer
        phase_results["genome"] = genome.to_dict()
        phase_results["generation"] = self.current_generation

        return phase_results

    async def run_single_generation(self, problem: str) -> Dict[str, Any]:
        """Run one generation of recursive scaffolding + evolution."""
        if self.evolution_engine.best_genome is None:
            genome = create_default_genome()
            self.evolution_engine.best_genome = genome
        else:
            genome = self.evolution_engine.best_genome

        self.memory.set_problem(problem, genome.id, self.current_generation)

        # Recursive scaffolding
        scaffolding_result = await self._recursive_scaffolding_step(problem, genome)

        # Evaluate via benchmark engine
        # Create a task from problem for evaluation
        mock_task = self.benchmark_engine.generate_task(difficulty=scaffolding_result.get("plan", {}).get("estimated_complexity", 0.5))
        eval_result = self.benchmark_engine.evaluate_solution(
            mock_task, scaffolding_result.get("final_answer", ""), extra_context={"tokens_used": self.groq.stats()["total_tokens"]}
        )

        # Evolution step (mutate, evaluate population, select winner)
        evolution_result = await self.evolution_engine.evolve_generation(problem=problem)

        # Update best answer if current is better (higher verification confidence)
        verif_conf = scaffolding_result.get("verify", {}).get("confidence", 0.5)
        current_best_conf = getattr(self, "_best_conf", 0.0)
        if verif_conf > current_best_conf or self.best_answer is None:
            self.best_answer = scaffolding_result.get("final_answer")
            self.best_scaffold = scaffolding_result.get("compress", {}).get("compressed_summary")
            self._best_conf = verif_conf

        self.current_generation += 1
        self.stats["total_generations"] = self.current_generation
        self.stats["total_tokens"] = self.groq.stats()["total_tokens"]
        self.stats["total_cost"] = self.groq.stats()["estimated_cost"]
        self.stats["latency_total_ms"] = self.groq.stats()["total_latency_ms"]

        # Checkpoint
        if self.current_generation % self.config.evolution.checkpoint_interval_generations == 0:
            cp = self._create_checkpoint()
            self.checkpoint_manager.save_checkpoint(cp, generation=self.current_generation)

        return {
            "generation": self.current_generation,
            "scaffolding": scaffolding_result,
            "evaluation": eval_result,
            "evolution": evolution_result,
            "best_answer": self.best_answer,
            "best_scaffold": self.best_scaffold,
            "stats": self.stats,
            "genome": genome.to_dict(),
            "memory_stats": self.memory.stats(),
            "groq_stats": self.groq.stats(),
        }

    async def run_forever(self, problem: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Continuous evolution loop - yields each generation result.
        Stops only when should_stop is True.
        """
        self.is_running = True
        self.should_stop = False
        self.current_problem = problem
        self.stats["start_time"] = time.time()
        await self.initialize()

        logger.info(f"Starting recursive evolution forever for problem: {problem[:100]}")

        while not self.should_stop:
            try:
                start = time.time()
                result = await self.run_single_generation(problem)
                result["elapsed_ms"] = (time.time() - start) * 1000
                yield result

                # Small adaptive sleep to respect rate limits
                # If groq requests high, sleep more
                groq_stats = self.groq.stats()
                if groq_stats["requests"] > 0 and groq_stats["requests"] % 20 == 0:
                    await asyncio.sleep(1.0)
                else:
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info("Recursive engine cancelled")
                break
            except Exception as e:
                logger.error(f"Error in generation {self.current_generation}: {e}", exc_info=True)
                self.memory.episodic.add_error(str(e), {"generation": self.current_generation, "problem": problem})
                # Continue despite error, with backoff
                await asyncio.sleep(1.0)
                yield {
                    "generation": self.current_generation,
                    "error": str(e),
                    "best_answer": self.best_answer,
                    "stats": self.stats,
                }

        self.is_running = False
        logger.info("Recursive engine stopped")

    def stop(self) -> Dict[str, Any]:
        """Immediately halt recursion and produce final summary."""
        self.should_stop = True
        self.is_running = False

        final_checkpoint = self._create_checkpoint()
        self.checkpoint_manager.save_checkpoint(final_checkpoint, generation=self.current_generation)

        return {
            "best_answer": self.best_answer,
            "best_scaffold": self.best_scaffold,
            "current_genome": self.evolution_engine.best_genome.to_dict() if self.evolution_engine.best_genome else None,
            "current_reasoning_tree": self.memory.working.get_full_tree(),
            "current_memory": self.memory.stats(),
            "generation_number": self.current_generation,
            "evolution_history": self.evolution_engine.evolution_history[-20:],
            "benchmark_performance": self.benchmark_engine.get_performance_summary(),
            "token_statistics": self.groq.stats(),
            "compression_statistics": self.memory.compressed.stats(),
            "checkpoint_id": final_checkpoint.get("timestamp"),
        }

    def resume(self) -> Dict[str, Any]:
        """Resume from last checkpoint - restores state."""
        latest = self.checkpoint_manager.load_latest()
        if not latest:
            return {"status": "no_checkpoint", "generation": self.current_generation}

        self._restore_from_checkpoint(latest)
        self.should_stop = False
        return {
            "status": "resumed",
            "generation": self.current_generation,
            "genome": self.evolution_engine.best_genome.to_dict() if self.evolution_engine.best_genome else None,
            "checkpoint": latest,
        }

    def get_current_state(self) -> Dict[str, Any]:
        return {
            "generation": self.current_generation,
            "is_running": self.is_running,
            "problem": self.current_problem,
            "best_genome": self.evolution_engine.best_genome.to_dict() if self.evolution_engine.best_genome else None,
            "best_answer": self.best_answer,
            "memory_stats": self.memory.stats(),
            "groq_stats": self.groq.stats(),
            "evolution_stats": self.evolution_engine.get_stats(),
            "benchmark_summary": self.benchmark_engine.get_performance_summary(),
        }

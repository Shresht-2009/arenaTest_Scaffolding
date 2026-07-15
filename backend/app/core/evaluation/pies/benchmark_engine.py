"""
Benchmark Engine - Orchestrates procedural generation, difficulty adaptation, evaluation.
"""

from __future__ import annotations

import random
import time
from typing import Dict, List, Any, Optional, Tuple

from .base import BenchmarkTask, BaseBenchmarkGenerator
from .generators import GENERATOR_REGISTRY
from .difficulty_manager import DifficultyManager
from .adversarial_tester import AdversarialTester
from .metrics import compute_metrics
from ....config import get_config


class BenchmarkEngine:
    """
    Generates tasks, evaluates solutions, manages difficulty.
    Operates deterministically for reproducibility but generates infinite uniqueness via seeds.
    """

    def __init__(self, families: Optional[List[str]] = None):
        config = get_config()
        self.families = families or config.evaluation.benchmark_families
        self.generators: Dict[str, BaseBenchmarkGenerator] = {}
        for fam in self.families:
            if fam in GENERATOR_REGISTRY:
                self.generators[fam] = GENERATOR_REGISTRY[fam]()
        self.difficulty_manager = DifficultyManager(default_difficulty=config.evaluation.default_difficulty)
        self.adversarial_tester = AdversarialTester()
        self.evaluation_history: List[Dict[str, Any]] = []
        self.seed_counter = 0

    def _next_seed(self) -> int:
        self.seed_counter += 1
        return int(time.time() * 1000) % 1000000 + self.seed_counter * 9973

    def generate_task(self, family: Optional[str] = None, difficulty: Optional[float] = None, seed: Optional[int] = None) -> BenchmarkTask:
        if family is None:
            family = random.choice(list(self.generators.keys()))
        if family not in self.generators:
            raise ValueError(f"Unknown family {family}")

        diff = difficulty if difficulty is not None else self.difficulty_manager.get_difficulty(family)
        s = seed if seed is not None else self._next_seed()
        task = self.generators[family].generate(seed=s, difficulty=diff)
        return task

    def generate_batch(self, n: int, families: Optional[List[str]] = None, difficulty: Optional[float] = None) -> List[BenchmarkTask]:
        fams = families or self.families
        tasks = []
        for _ in range(n):
            fam = random.choice(fams) if fams else None
            tasks.append(self.generate_task(family=fam, difficulty=difficulty))
        return tasks

    def evaluate_solution(self, task: BenchmarkTask, attempted_solution: str, extra_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate attempted solution with multi-dimensional metrics.
        """
        # Base correctness via task checker
        check_result = task.check(attempted_solution)

        # Adversarial robustness
        adversarial_results = self.adversarial_tester.test(task, attempted_solution)

        # Multi-dimensional metrics
        metrics = compute_metrics(task, attempted_solution, check_result, adversarial_results, extra_context)

        # Record difficulty adaptation
        self.difficulty_manager.update(task.family, check_result.get("correct", False), metrics.get("score", 0.0))

        eval_record = {
            "task_id": task.id,
            "family": task.family,
            "seed": task.seed,
            "difficulty": task.difficulty,
            "correct": check_result.get("correct", False),
            "score": check_result.get("score", 0.0),
            "metrics": metrics,
            "adversarial": adversarial_results,
            "check_feedback": check_result.get("feedback", ""),
            "timestamp": time.time(),
        }
        self.evaluation_history.append(eval_record)
        if len(self.evaluation_history) > 1000:
            self.evaluation_history.pop(0)

        return eval_record

    def get_performance_summary(self) -> Dict[str, Any]:
        if not self.evaluation_history:
            return {"total_evals": 0}

        total = len(self.evaluation_history)
        correct = sum(1 for e in self.evaluation_history if e["correct"])
        avg_score = sum(e["score"] for e in self.evaluation_history) / total

        per_family = {}
        for e in self.evaluation_history:
            fam = e["family"]
            per_family.setdefault(fam, {"total": 0, "correct": 0, "scores": []})
            per_family[fam]["total"] += 1
            per_family[fam]["correct"] += 1 if e["correct"] else 0
            per_family[fam]["scores"].append(e["score"])

        for fam, data in per_family.items():
            data["accuracy"] = data["correct"] / data["total"] if data["total"] > 0 else 0
            data["avg_score"] = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            del data["scores"]

        return {
            "total_evals": total,
            "overall_accuracy": correct / total if total > 0 else 0,
            "avg_score": avg_score,
            "per_family": per_family,
            "current_difficulties": self.difficulty_manager.get_all_difficulties(),
        }

    def suggest_next_task_family(self, weakest: bool = True) -> str:
        """
        Suggest next family to evaluate - focus on weakest or rotate.
        """
        summary = self.get_performance_summary()
        if not summary["per_family"] or not weakest:
            return random.choice(self.families)
        # Find lowest accuracy
        weakest_fam = min(summary["per_family"].items(), key=lambda kv: kv[1]["accuracy"])[0]
        return weakest_fam

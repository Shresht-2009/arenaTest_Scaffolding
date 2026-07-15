"""
PIES Base - Procedural benchmark generator interface.

Every generator must be:
- Deterministic given seed
- Infinite uniqueness (procedural)
- Self-checking (provides solution + checker)
- Difficulty scalable 0..1
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
import random
import time


@dataclass
class BenchmarkTask:
    """
    Generated benchmark instance.
    """

    family: str
    id: str
    difficulty: float  # 0..1
    seed: int
    problem: str
    solution: str  # ground truth or expected
    checker: Optional[Callable[[str], Dict[str, Any]]] = None  # function to verify attempted solution
    metadata: Dict[str, Any] = field(default_factory=dict)
    adversarial_variants: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def check(self, attempted_solution: str) -> Dict[str, Any]:
        """Run checker if available, else simple correctness."""
        if self.checker:
            try:
                return self.checker(attempted_solution)
            except Exception as e:
                return {"correct": False, "score": 0.0, "error": str(e), "feedback": f"Checker failed: {e}"}
        # Fallback: substring match
        correct = self.solution.lower() in attempted_solution.lower() or attempted_solution.lower() in self.solution.lower()
        return {
            "correct": correct,
            "score": 1.0 if correct else 0.0,
            "feedback": "Simple substring match" if correct else "Solution mismatch",
        }


class BaseBenchmarkGenerator(ABC):
    """Abstract base for all families."""

    def __init__(self, family_name: str):
        self.family_name = family_name

    @abstractmethod
    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        """Generate a task deterministically from seed and difficulty."""
        pass

    def generate_batch(self, seeds: List[int], difficulty: float = 0.5) -> List[BenchmarkTask]:
        return [self.generate(seed=s, difficulty=difficulty) for s in seeds]

    def _rng(self, seed: int) -> random.Random:
        return random.Random(seed)

    def _scale(self, difficulty: float, min_val: int, max_val: int) -> int:
        """Linear scale difficulty to int range."""
        return int(min_val + (max_val - min_val) * difficulty)

    def make_adversarial_variants(self, task: BenchmarkTask) -> List[Dict[str, Any]]:
        """
        Generate adversarial perturbations:
        - rephrase, rename variables, add constraints, inject noise, etc.
        Subclasses can override.
        """
        variants = []
        # Rephrase variant (simple word shuffle)
        variants.append(
            {
                "type": "rephrase",
                "problem": task.problem.replace("Find", "Determine").replace("Calculate", "Compute"),
                "description": "Rephrased problem statement",
            }
        )
        # Variable rename
        import re

        renamed = re.sub(r"\b([A-Z])\b", r"\1'", task.problem)
        variants.append({"type": "rename_vars", "problem": renamed, "description": "Renamed variables"})

        # Inject irrelevant info
        injected = task.problem + "\n\nNote: This problem was originally proposed in 2023. Irrelevant context should be ignored."
        variants.append({"type": "inject_noise", "problem": injected, "description": "Injected irrelevant info"})

        return variants

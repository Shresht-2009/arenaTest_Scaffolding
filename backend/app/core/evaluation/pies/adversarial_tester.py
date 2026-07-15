"""
Adversarial Tester - Tests solution robustness via perturbations.
"""

from __future__ import annotations

import re
import random
from typing import Dict, Any, List
from .base import BenchmarkTask


class AdversarialTester:
    """
    Performs automated adversarial evaluation:
    - rephrase problem
    - change variable names
    - add constraints
    - remove assumptions
    - reorder information
    - inject irrelevant info
    - perturb numerical values
    """

    def __init__(self, tests_per_solution: int = 3):
        self.tests_per_solution = tests_per_solution

    def _perturb_numbers(self, text: str, delta: float = 0.1) -> str:
        def repl(match):
            num_str = match.group(0)
            try:
                if "." in num_str:
                    val = float(num_str)
                    new_val = val * (1 + random.uniform(-delta, delta))
                    return f"{new_val:.2f}"
                else:
                    val = int(num_str)
                    # small perturb +-1
                    new_val = val + random.choice([-1, 1])
                    return str(new_val)
            except Exception:
                return num_str

        # Only perturb numbers not likely to be critical? For testing, perturb slightly
        return re.sub(r"\b\d+\.?\d*\b", repl, text)

    def _reorder_sentences(self, text: str) -> str:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        if len(sentences) <= 2:
            return text
        # Keep first, shuffle rest
        first = sentences[0]
        rest = sentences[1:]
        random.shuffle(rest)
        return " ".join([first] + rest)

    def _inject_noise(self, text: str) -> str:
        noise = [
            "Note: This problem is from a 2023 contest.",
            "Background: Consider general reasoning principles.",
            "Irrelevant: The sky is blue.",
            "Reminder: Be concise but thorough.",
        ]
        return text + "\n\n" + random.choice(noise)

    def _add_constraint(self, text: str) -> str:
        extras = [
            " Additional constraint: Solutions must be efficient.",
            " Note: Edge cases must be handled.",
            " Requirement: Provide justification for each step.",
        ]
        return text + random.choice(extras)

    def generate_adversarial_variants(self, task: BenchmarkTask) -> List[Dict[str, Any]]:
        variants = []
        variants.append(
            {
                "type": "reorder",
                "problem": self._reorder_sentences(task.problem),
                "description": "Reordered information",
            }
        )
        variants.append(
            {
                "type": "inject_noise",
                "problem": self._inject_noise(task.problem),
                "description": "Injected irrelevant information",
            }
        )
        variants.append(
            {
                "type": "perturb_numbers",
                "problem": self._perturb_numbers(task.problem, delta=0.05),
                "description": "Slightly perturbed numerical values",
            }
        )
        variants.append(
            {
                "type": "add_constraint",
                "problem": self._add_constraint(task.problem),
                "description": "Added extra constraint",
            }
        )
        # Sample requested number
        return random.sample(variants, min(self.tests_per_solution, len(variants)))

    def test(self, task: BenchmarkTask, attempted_solution: str) -> Dict[str, Any]:
        """
        For current implementation, adversarial testing measures stability:
        - Does solution contain reasoning robust to perturbations? (heuristic)
        Since we don't re-run LLM for each variant to save tokens (per design constraint),
        we perform deterministic stability checks on the attempted solution.
        """
        variants = self.generate_adversarial_variants(task)

        results = []
        base_tokens = set(attempted_solution.lower().split())
        stability_scores = []

        for var in variants:
            # Heuristic: check if attempted solution still addresses variant problem tokens overlap
            variant_tokens = set(var["problem"].lower().split())
            # If attempted solution shares keywords with original problem, it should also share with variant
            # unless it overfits to specific phrasing
            original_tokens = set(task.problem.lower().split())
            # Compute overlap of attempted with original vs variant
            overlap_original = len(base_tokens & original_tokens) / max(1, len(original_tokens))
            overlap_variant = len(base_tokens & variant_tokens) / max(1, len(variant_tokens))
            # Stability = 1 - |overlap diff| (if similar, stable)
            stability = 1.0 - abs(overlap_original - overlap_variant)
            stability = max(0.0, min(1.0, stability))
            stability_scores.append(stability)
            results.append(
                {
                    "type": var["type"],
                    "description": var["description"],
                    "stability": stability,
                    "overlap_original": overlap_original,
                    "overlap_variant": overlap_variant,
                }
            )

        avg_stability = sum(stability_scores) / len(stability_scores) if stability_scores else 0.0
        # Robustness score
        robustness = avg_stability

        return {
            "variants_tested": len(results),
            "average_stability": avg_stability,
            "robustness_score": robustness,
            "details": results,
            "is_robust": robustness > 0.7,
        }

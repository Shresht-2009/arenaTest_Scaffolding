"""
Evolutionary Fitness - Weighted fitness scoring.

Suggested weighting (normalized):
- Reasoning Quality 20%
- Correctness 20%
- Verification 15%
- Planning 10%
- Generalization 10%
- Robustness 10%
- Compression 5%
- Token Efficiency 5%
- Novelty 5% (actually 3% in config + 2% self-correction)
- Self-Correction 5%
"""

from __future__ import annotations

from typing import Dict, Any
from ...config import get_config


class FitnessEvaluator:
    def __init__(self):
        self.config = get_config()
        self.weights = self.config.fitness.normalized()

    def compute_fitness(self, metrics: Dict[str, float], token_stats: Dict[str, Any] = None, genome_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Compute weighted fitness score.
        metrics: from compute_metrics
        token_stats: e.g., tokens per generation, cost
        genome_stats: e.g., genome complexity
        Returns detailed breakdown and total fitness.
        """
        # Map metrics to fitness dimensions
        # Need to handle naming alignment
        mapping = {
            "reasoning_quality": metrics.get("reasoning_depth", 0.5) * 0.5 + metrics.get("logical_consistency", 0.5) * 0.5,
            "correctness": metrics.get("correctness", 0.0),
            "verification": metrics.get("verification_quality", 0.5),
            "planning": metrics.get("planning_quality", 0.5),
            "generalization": metrics.get("generalization", 0.5),
            "robustness": metrics.get("robustness", 0.5),
            "compression": metrics.get("compression_quality", 0.5),
            "token_efficiency": metrics.get("token_efficiency", 0.5),
            "novelty": metrics.get("novelty", 0.5),
            "self_correction": metrics.get("self_correction", 0.5),
        }

        total = 0.0
        breakdown = {}
        for dim, weight in self.weights.items():
            val = mapping.get(dim, 0.5)
            weighted = val * weight
            breakdown[dim] = {"value": val, "weight": weight, "weighted": weighted}
            total += weighted

        # Bonus / penalties based on token stats
        bonus = 0.0
        if token_stats:
            # If token efficiency high and total tokens low, bonus
            tokens = token_stats.get("total_tokens", 0)
            if tokens < 1000 and mapping["token_efficiency"] > 0.7:
                bonus += 0.02
            if tokens > 5000:
                bonus -= 0.02

        # Genome complexity penalty if too complex? Encourage simplicity if fitness same
        if genome_stats:
            # If planning_depth >5 and fitness low, penalize
            if genome_stats.get("planning_depth", 3) > 5 and total < 0.6:
                bonus -= 0.01

        total = max(0.0, min(1.0, total + bonus))

        return {
            "fitness": total,
            "breakdown": breakdown,
            "mapping": mapping,
            "bonus": bonus,
            "raw_metrics": metrics,
        }

    def rank_genomes(self, genome_fitness_list: list) -> list:
        """
        Rank list of (genome, fitness_dict) by fitness.
        Expected input: [{"genome_id":..., "fitness":...}, ...]
        """
        return sorted(genome_fitness_list, key=lambda x: x.get("fitness", {}).get("fitness", x.get("fitness", 0)) if isinstance(x.get("fitness"), dict) else x.get("fitness", 0), reverse=True)

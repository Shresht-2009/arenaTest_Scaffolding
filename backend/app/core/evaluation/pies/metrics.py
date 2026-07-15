"""
Multi-Dimensional Evaluation Metrics.

Metrics include:
- Correctness
- Logical consistency
- Verification quality
- Planning quality
- Reasoning depth
- Generalization
- Robustness
- Compression quality
- Novelty
- Self-correction
- Information density
- Token efficiency
- Stability under paraphrasing
- Resistance to adversarial modifications
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import re


def _count_reasoning_steps(solution: str) -> int:
    # Count lines that look like steps, or numbered, or contain reasoning keywords
    lines = solution.splitlines()
    count = 0
    for line in lines:
        if not line.strip():
            continue
        if re.match(r"^\s*\d+\.", line) or re.match(r"^\s*[-*]\s+", line):
            count += 1
        elif any(kw in line.lower() for kw in ["therefore", "because", "since", "step", "first", "next", "then"]):
            count += 1
    return max(1, count)


def _information_density(solution: str) -> float:
    # Ratio of unique words to total words
    words = solution.split()
    if not words:
        return 0.0
    unique = set(w.lower() for w in words)
    return len(unique) / len(words)


def _token_efficiency_score(tokens_used: int, content_len: int) -> float:
    # Lower tokens for same content is better
    # Heuristic: efficiency = content_chars / (tokens * 4)
    if tokens_used == 0:
        return 0.5
    # tokens *4 roughly chars
    ratio = content_len / (tokens_used * 4)
    # Ideal ratio ~1, higher means efficient (less tokens than chars)
    # Map to 0..1
    return min(1.0, ratio * 1.2)


def compute_metrics(
    task,
    attempted_solution: str,
    check_result: Dict[str, Any],
    adversarial_results: Dict[str, Any],
    extra_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """
    Compute multi-dimensional metrics for a solution.
    extra_context can contain: planning_quality, verification_quality, tokens_used, reasoning_depth, etc.
    """
    extra_context = extra_context or {}

    # Correctness from checker
    correctness = float(check_result.get("score", 1.0 if check_result.get("correct") else 0.0))

    # Logical consistency: look for contradictions, check for reasoning keywords
    lower = attempted_solution.lower()
    contradiction_indicators = lower.count("however") + lower.count("but") * 0.5
    has_logic_markers = sum(1 for kw in ["therefore", "thus", "hence", "because", "implies"] if kw in lower)
    logical_consistency = min(1.0, 0.5 + has_logic_markers * 0.1 - contradiction_indicators * 0.05)
    logical_consistency = max(0.0, logical_consistency)

    # Verification quality: from extra_context if provided, else heuristic
    verification_quality = extra_context.get("verification_quality")
    if verification_quality is None:
        # If solution contains verification-like phrases
        verification_keywords = ["verify", "check", "validate", "counterexample", "edge case", "tested"]
        matches = sum(1 for kw in verification_keywords if kw in lower)
        verification_quality = min(1.0, matches * 0.2 + 0.3)

    # Planning quality: does solution show plan?
    planning_quality = extra_context.get("planning_quality")
    if planning_quality is None:
        plan_indicators = ["plan", "step 1", "step 2", "first", "next", "then", "decompose"]
        matches = sum(1 for kw in plan_indicators if kw in lower)
        planning_quality = min(1.0, matches * 0.15 + 0.3)

    # Reasoning depth: number of steps
    depth_raw = _count_reasoning_steps(attempted_solution)
    # Normalize: 1-3 steps = 0.4, 4-6=0.7, 7+ = 0.9
    if depth_raw <= 2:
        reasoning_depth = 0.3
    elif depth_raw <= 4:
        reasoning_depth = 0.6
    elif depth_raw <= 7:
        reasoning_depth = 0.8
    else:
        reasoning_depth = 0.9

    # Generalization: from adversarial stability if available
    generalization = adversarial_results.get("average_stability", 0.6) if adversarial_results else 0.6

    # Robustness: from adversarial
    robustness = adversarial_results.get("robustness_score", 0.6) if adversarial_results else 0.6

    # Compression quality: information density as proxy
    info_density = _information_density(attempted_solution)
    compression_quality = min(1.0, info_density * 1.2 + 0.2)

    # Novelty: check unique phrases vs template? Simple heuristic based on uncommon words
    novelty = extra_context.get("novelty_score", 0.5)
    # Boost if contains creative phrasing
    if any(w in lower for w in ["alternatively", "novel", "innovative", "approach", "insight"]):
        novelty = min(1.0, novelty + 0.1)

    # Self-correction: mentions of correction
    self_correction = 0.3
    if any(kw in lower for kw in ["correction", "correction", "revise", "re-evaluate", "self-correct", "mistake", "error"]):
        self_correction = 0.8
    self_correction = extra_context.get("self_correction", self_correction)

    # Token efficiency
    tokens_used = extra_context.get("tokens_used", len(attempted_solution) // 4)
    token_efficiency = _token_efficiency_score(tokens_used, len(attempted_solution))

    # Stability under paraphrasing: same as robustness
    stability_paraphrase = adversarial_results.get("average_stability", 0.6) if adversarial_results else 0.6

    # Resistance to adversarial modifications: robustness
    resistance_adversarial = robustness

    # Overall score weighted? We'll compute weighted later in fitness, but provide aggregated score here
    overall = (
        correctness * 0.25
        + logical_consistency * 0.15
        + verification_quality * 0.1
        + planning_quality * 0.1
        + reasoning_depth * 0.1
        + generalization * 0.05
        + robustness * 0.05
        + compression_quality * 0.05
        + novelty * 0.05
        + self_correction * 0.05
        + token_efficiency * 0.05
    )

    return {
        "correctness": correctness,
        "logical_consistency": logical_consistency,
        "verification_quality": verification_quality,
        "planning_quality": planning_quality,
        "reasoning_depth": reasoning_depth,
        "generalization": generalization,
        "robustness": robustness,
        "compression_quality": compression_quality,
        "novelty": novelty,
        "self_correction": self_correction,
        "information_density": info_density,
        "token_efficiency": token_efficiency,
        "stability_paraphrasing": stability_paraphrase,
        "resistance_adversarial": resistance_adversarial,
        "score": overall,
        "overall": overall,
        "reasoning_steps_count": float(depth_raw),
    }

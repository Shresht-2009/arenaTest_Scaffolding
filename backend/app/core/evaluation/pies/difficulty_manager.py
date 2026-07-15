"""
Adaptive Difficulty Manager - Continuously estimates reasoning frontier.
"""

from __future__ import annotations

from typing import Dict
import time


class DifficultyManager:
    """
    Tracks per-family difficulty and adapts:
    - If consistently succeeding (e.g., 3 wins in a row), increase difficulty.
    - If performance drops, reduce slightly.
    - Bounded 0.1 .. 0.95 to avoid degenerate cases.
    """

    def __init__(self, default_difficulty: float = 0.5, adaptation_rate: float = 0.1, window_size: int = 10):
        self.default = default_difficulty
        self.rate = adaptation_rate
        self.window = window_size
        self.difficulties: Dict[str, float] = {}
        self.histories: Dict[str, list] = {}  # list of (correct, score)
        self.last_update: Dict[str, float] = {}

    def get_difficulty(self, family: str) -> float:
        return self.difficulties.get(family, self.default)

    def get_all_difficulties(self) -> Dict[str, float]:
        return dict(self.difficulties)

    def update(self, family: str, correct: bool, score: float):
        history = self.histories.setdefault(family, [])
        history.append((correct, score))
        if len(history) > self.window:
            history.pop(0)

        # Compute recent accuracy
        if len(history) < 2:
            return

        recent_correct = sum(1 for c, _ in history[-3:] if c)
        recent_avg_score = sum(s for _, s in history[-3:]) / min(3, len(history))

        curr = self.get_difficulty(family)

        # Adaptation logic
        if recent_correct >= 3 and recent_avg_score > 0.8:
            # Increase complexity
            curr = min(0.95, curr + self.rate)
        elif recent_correct <= 1 and recent_avg_score < 0.4:
            # Decrease slightly, but not too much
            curr = max(0.1, curr - self.rate * 0.7)
        elif recent_avg_score > 0.75:
            curr = min(0.95, curr + self.rate * 0.5)
        elif recent_avg_score < 0.35:
            curr = max(0.1, curr - self.rate * 0.5)

        self.difficulties[family] = curr
        self.last_update[family] = time.time()

    def should_increase_complexity(self, family: str) -> bool:
        hist = self.histories.get(family, [])
        if len(hist) < 3:
            return False
        return all(c for c, _ in hist[-3:])

    def estimate_frontier(self) -> Dict[str, float]:
        """
        Estimate reasoning frontier as difficulty where accuracy ~50%.
        """
        frontier = {}
        for fam, hist in self.histories.items():
            if len(hist) < 5:
                frontier[fam] = self.get_difficulty(fam)
                continue
            # Simple: if accuracy high at current difficulty, frontier higher
            acc = sum(1 for c, _ in hist if c) / len(hist)
            curr_diff = self.get_difficulty(fam)
            # Frontier roughly curr_diff + (acc - 0.5)
            frontier[fam] = max(0.1, min(0.95, curr_diff + (acc - 0.5) * 0.5))
        return frontier

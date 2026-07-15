"""
Working Memory - Current reasoning state.

Holds transient, high-frequency updated data for current generation.
Aggressively pruned and compressed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time


@dataclass
class ReasoningStep:
    """Single step in reasoning chain."""

    id: str
    phase: str  # Understand, Decompose, Plan, Execute, Verify, etc.
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkingMemory:
    """
    Working memory holds current generation's transient state.
    Implements token-aware pruning.
    """

    generation: int = 0
    current_problem: Optional[str] = None
    current_scaffold: Optional[str] = None
    current_plan: Optional[List[str]] = None
    current_reasoning_tree: List[ReasoningStep] = field(default_factory=list)
    current_genome_id: Optional[str] = None
    active_context_tokens: int = 0
    max_tokens: int = 4000

    # Scratchpad for intermediate artifacts
    scratchpad: Dict[str, Any] = field(default_factory=dict)
    # Verified artifacts
    verified_artifacts: List[Dict[str, Any]] = field(default_factory=list)

    def add_step(self, phase: str, content: str, tokens: int = 0, confidence: float = 0.0, metadata=None):
        step = ReasoningStep(
            id=f"{self.generation}-{len(self.current_reasoning_tree)}",
            phase=phase,
            content=content,
            tokens=tokens,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.current_reasoning_tree.append(step)
        self.active_context_tokens += tokens
        self._maybe_prune()

    def _maybe_prune(self):
        """Prune oldest low-confidence steps if over token budget."""
        if self.active_context_tokens <= self.max_tokens:
            return

        # Sort by confidence ascending, then timestamp ascending (old low-confidence first)
        # Keep at least 3 most recent
        if len(self.current_reasoning_tree) <= 3:
            return

        # Calculate excess
        excess = self.active_context_tokens - self.max_tokens
        # Remove low-confidence old steps
        candidates = sorted(
            self.current_reasoning_tree[:-3], key=lambda s: (s.confidence, s.timestamp)
        )
        removed_tokens = 0
        to_keep = []
        removed_ids = set()
        for c in candidates:
            if removed_tokens < excess:
                removed_tokens += c.tokens
                removed_ids.add(c.id)
            else:
                to_keep.append(c)
        # Reconstruct tree preserving order, keep recent 3
        recent = self.current_reasoning_tree[-3:]
        middle = [s for s in self.current_reasoning_tree[:-3] if s.id not in removed_ids]
        self.current_reasoning_tree = middle + recent
        self.active_context_tokens -= removed_tokens

    def get_context(self, last_n: int = 5) -> str:
        """Get compact context of last N steps."""
        steps = self.current_reasoning_tree[-last_n:]
        return "\n".join([f"[{s.phase}] {s.content[:300]}" for s in steps])

    def get_full_tree(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": s.id,
                "phase": s.phase,
                "content": s.content,
                "timestamp": s.timestamp,
                "confidence": s.confidence,
                "tokens": s.tokens,
            }
            for s in self.current_reasoning_tree
        ]

    def clear(self):
        self.current_reasoning_tree.clear()
        self.scratchpad.clear()
        self.verified_artifacts.clear()
        self.active_context_tokens = 0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "generation": self.generation,
            "current_problem": self.current_problem,
            "current_scaffold": self.current_scaffold,
            "current_plan": self.current_plan,
            "reasoning_tree": self.get_full_tree(),
            "genome_id": self.current_genome_id,
            "tokens": self.active_context_tokens,
            "scratchpad_keys": list(self.scratchpad.keys()),
        }

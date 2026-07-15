"""
Semantic Memory - Reusable patterns, abstractions, templates.

Stores successful reasoning patterns extracted from episodic memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time
import hashlib


@dataclass
class ReasoningPattern:
    id: str
    description: str
    abstraction: str  # compressed representation
    domain: str  # which benchmark family or general
    success_count: int = 1
    failure_count: int = 0
    avg_fitness_gain: float = 0.0
    first_seen: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    example_genome_ids: List[str] = field(default_factory=list)
    compressed_form: Optional[str] = None

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


@dataclass
class PlanningTemplate:
    id: str
    name: str
    steps: List[str]
    applicable_domains: List[str]
    fitness: float = 0.0
    usage_count: int = 0


class SemanticMemory:
    """Long-term semantic store of distilled knowledge."""

    def __init__(self, max_patterns: int = 200):
        self.max_patterns = max_patterns
        self.patterns: Dict[str, ReasoningPattern] = {}
        self.templates: Dict[str, PlanningTemplate] = {}
        self.abstractions: Dict[str, str] = {}  # hash -> abstraction
        self.compression_strategies: List[Dict] = []

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def add_pattern(self, description: str, abstraction: str, domain: str, fitness_gain: float, genome_id: str) -> str:
        pid = self._hash(description + abstraction + domain)
        if pid in self.patterns:
            p = self.patterns[pid]
            p.success_count += 1
            p.avg_fitness_gain = (p.avg_fitness_gain * (p.success_count - 1) + fitness_gain) / p.success_count
            p.last_used = time.time()
            if genome_id not in p.example_genome_ids:
                p.example_genome_ids.append(genome_id)
            return pid

        # Prune if over capacity: remove lowest success rate
        if len(self.patterns) >= self.max_patterns:
            worst = min(self.patterns.values(), key=lambda p: p.success_rate)
            del self.patterns[worst.id]

        pattern = ReasoningPattern(
            id=pid,
            description=description,
            abstraction=abstraction,
            domain=domain,
            success_count=1,
            avg_fitness_gain=fitness_gain,
            example_genome_ids=[genome_id],
            compressed_form=abstraction[:200],
        )
        self.patterns[pid] = pattern
        return pid

    def add_template(self, name: str, steps: List[str], domains: List[str], fitness: float) -> str:
        tid = self._hash(name + "".join(steps))
        if tid in self.templates:
            t = self.templates[tid]
            t.usage_count += 1
            t.fitness = max(t.fitness, fitness)
            return tid
        template = PlanningTemplate(id=tid, name=name, steps=steps, applicable_domains=domains, fitness=fitness, usage_count=1)
        self.templates[tid] = template
        return tid

    def retrieve_relevant_patterns(self, domain: str, query: str, top_k: int = 3) -> List[ReasoningPattern]:
        """Simple heuristic retrieval: domain match + keyword overlap."""
        candidates = []
        query_tokens = set(query.lower().split())
        for p in self.patterns.values():
            score = 0.0
            if p.domain == domain or p.domain == "general":
                score += 0.5
            # Overlap
            desc_tokens = set(p.description.lower().split())
            overlap = len(query_tokens & desc_tokens) / max(1, len(query_tokens))
            score += overlap * 0.5
            # Bias by success
            score += p.success_rate * 0.3
            score += min(p.avg_fitness_gain, 1.0) * 0.2
            candidates.append((score, p))

        candidates.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in candidates[:top_k]]

    def retrieve_templates(self, domain: str, top_k: int = 2) -> List[PlanningTemplate]:
        cands = [t for t in self.templates.values() if domain in t.applicable_domains or "general" in t.applicable_domains]
        cands.sort(key=lambda t: t.fitness, reverse=True)
        return cands[:top_k]

    def get_compression_strategy(self, content_type: str) -> Optional[Dict]:
        # Return best compression strategy for type
        filtered = [s for s in self.compression_strategies if s.get("type") == content_type]
        if not filtered:
            return self.compression_strategies[0] if self.compression_strategies else None
        return sorted(filtered, key=lambda s: s.get("ratio", 0), reverse=True)[0]

    def summary(self) -> Dict:
        return {
            "patterns": len(self.patterns),
            "templates": len(self.templates),
            "abstractions": len(self.abstractions),
            "top_patterns": [
                {"id": p.id, "desc": p.description[:100], "success_rate": p.success_rate, "gain": p.avg_fitness_gain}
                for p in sorted(self.patterns.values(), key=lambda x: x.success_rate, reverse=True)[:5]
            ],
        }

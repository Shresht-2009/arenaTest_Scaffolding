"""
Cognitive Genome - The Evolving Unit of Intelligence

NOT a persona. Defines HOW reasoning occurs.

Every parameter is documented, bounded, and mutable.
Evolution operates on this genome, not on prompts or model weights.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Tuple
import math


class ReasoningOrder(str, Enum):
    """Order of reasoning phases."""

    SEQUENTIAL = "sequential"  # Understand -> Plan -> Execute -> Verify
    ITERATIVE = "iterative"  # Loop until confidence
    TREE_OF_THOUGHT = "tree_of_thought"
    CHAIN_OF_VERIFICATION = "chain_of_verification"
    RECURSIVE_DECOMPOSITION = "recursive_decomposition"
    DIVERGE_CONVERGE = "diverge_converge"  # Generate many, then prune


class DecompositionStyle(str, Enum):
    """How problems are broken down."""

    FUNCTIONAL = "functional"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    HIERARCHICAL = "hierarchical"
    CONSTRAINT_BASED = "constraint_based"
    FIRST_PRINCIPLES = "first_principles"


class MemoryRetrievalStrategy(str, Enum):
    """How memory is queried."""

    RECENCY = "recency"
    RELEVANCE = "relevance"
    DIVERSITY = "diversity"
    COMPRESSION_AWARE = "compression_aware"
    HYBRID = "hybrid"


@dataclass
class CognitiveGenome:
    """
    A complete specification of reasoning strategy.
    All fields are continuous or categorical and subject to mutation.
    """

    # Identity & Lineage
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    generation: int = 0
    parent_id: str | None = None
    lineage: List[str] = field(default_factory=list)

    # Core Cognitive Parameters (bounded 0.0-1.0 or discrete)
    planning_depth: int = 3  # 1-6 depth of planning recursion
    verification_passes: int = 2  # 1-5 verification iterations
    reasoning_order: ReasoningOrder = ReasoningOrder.SEQUENTIAL
    exploration_factor: float = 0.5  # 0..1, breadth vs depth
    compression_level: float = 0.5  # 0..1, aggressiveness of compression
    memory_retrieval_strategy: MemoryRetrievalStrategy = MemoryRetrievalStrategy.HYBRID
    decomposition_style: DecompositionStyle = DecompositionStyle.HIERARCHICAL
    critique_strength: float = 0.6  # how harshly to challenge assumptions
    reflection_depth: int = 2  # 1-5 meta-reflection loops
    search_width: int = 3  # 1-7 number of alternative branches
    confidence_threshold: float = 0.75  # 0..1 threshold to stop iterating
    self_correction_frequency: float = 0.7  # 0..1 likelihood of self-correction
    abstraction_level: float = 0.5  # 0..1 concrete vs abstract
    information_compression_ratio: float = 0.4  # target compression 0..0.8

    # Additional Evolvable Dimensions
    temperature: float = 0.7  # LLM temperature 0..1.2
    top_p: float = 0.95
    max_tokens: int = 2048  # per call limit 512-4096
    context_pruning_aggressiveness: float = 0.3  # 0..1
    verification_strictness: float = 0.7  # 0..1
    planning_horizon: int = 5  # steps ahead 2-10
    memory_weight_recent: float = 0.4  # weighting for retrieval
    memory_weight_relevant: float = 0.4
    memory_weight_diverse: float = 0.2
    adversarial_resilience: float = 0.5  # effort spent on robustness
    novelty_seeking: float = 0.3  # reward for novel approaches

    # Performance Tracking (not evolvable, but part of genome state)
    fitness: float = 0.0
    fitness_history: List[float] = field(default_factory=list)
    benchmark_scores: Dict[str, float] = field(default_factory=dict)
    token_usage: int = 0
    success_count: int = 0
    failure_count: int = 0

    def __post_init__(self):
        self._clamp()

    def _clamp(self):
        """Ensure all values within valid bounds."""
        self.planning_depth = max(1, min(6, int(self.planning_depth)))
        self.verification_passes = max(1, min(5, int(self.verification_passes)))
        self.reflection_depth = max(1, min(5, int(self.reflection_depth)))
        self.search_width = max(1, min(7, int(self.search_width)))
        self.planning_horizon = max(2, min(10, int(self.planning_horizon)))
        self.max_tokens = max(512, min(4096, int(self.max_tokens)))

        for attr in [
            "exploration_factor",
            "compression_level",
            "critique_strength",
            "confidence_threshold",
            "self_correction_frequency",
            "abstraction_level",
            "information_compression_ratio",
            "temperature",
            "context_pruning_aggressiveness",
            "verification_strictness",
            "memory_weight_recent",
            "memory_weight_relevant",
            "memory_weight_diverse",
            "adversarial_resilience",
            "novelty_seeking",
        ]:
            v = getattr(self, attr)
            setattr(self, attr, max(0.0, min(1.0, float(v))))

        self.top_p = max(0.1, min(1.0, float(self.top_p)))
        self.temperature = max(0.0, min(1.2, float(self.temperature)))

        # Normalize memory weights to sum 1
        total = self.memory_weight_recent + self.memory_weight_relevant + self.memory_weight_diverse
        if total > 0:
            self.memory_weight_recent /= total
            self.memory_weight_relevant /= total
            self.memory_weight_diverse /= total

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Convert enums to values
        d["reasoning_order"] = self.reasoning_order.value if isinstance(self.reasoning_order, Enum) else self.reasoning_order
        d["decomposition_style"] = self.decomposition_style.value if isinstance(self.decomposition_style, Enum) else self.decomposition_style
        d["memory_retrieval_strategy"] = self.memory_retrieval_strategy.value if isinstance(self.memory_retrieval_strategy, Enum) else self.memory_retrieval_strategy
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveGenome":
        # Restore enums
        if "reasoning_order" in data and isinstance(data["reasoning_order"], str):
            data["reasoning_order"] = ReasoningOrder(data["reasoning_order"])
        if "decomposition_style" in data and isinstance(data["decomposition_style"], str):
            data["decomposition_style"] = DecompositionStyle(data["decomposition_style"])
        if "memory_retrieval_strategy" in data and isinstance(data["memory_retrieval_strategy"], str):
            data["memory_retrieval_strategy"] = MemoryRetrievalStrategy(data["memory_retrieval_strategy"])
        return cls(**data)

    def to_prompt_fragment(self) -> str:
        """
        Convert genome into a compact reasoning instruction.
        This is NOT a persona, but a procedural specification.
        """
        return f"""Cognitive Protocol [Genome:{self.id} Gen:{self.generation}]:
- Planning Depth: {self.planning_depth} (horizon {self.planning_horizon} steps, style {self.decomposition_style.value})
- Reasoning Order: {self.reasoning_order.value} with search width {self.search_width}, exploration {self.exploration_factor:.2f}
- Verification: {self.verification_passes} passes, strictness {self.verification_strictness:.2f}, critique {self.critique_strength:.2f}
- Reflection: depth {self.reflection_depth}, self-correction {self.self_correction_frequency:.2f}, confidence threshold {self.confidence_threshold:.2f}
- Abstraction: level {self.abstraction_level:.2f}, compression ratio target {self.information_compression_ratio:.2f}
- Memory: strategy {self.memory_retrieval_strategy.value} (recent {self.memory_weight_recent:.2f}, relevant {self.memory_weight_relevant:.2f}, diverse {self.memory_weight_diverse:.2f})
- Efficiency: context pruning {self.context_pruning_aggressiveness:.2f}, compression {self.compression_level:.2f}
- Resilience: adversarial {self.adversarial_resilience:.2f}, novelty {self.novelty_seeking:.2f}
Follow this protocol strictly. Reason in structured steps. Compress intermediate thoughts. Verify before finalizing."""

    def mutate(self, mutation_rate: float = 0.35) -> "CognitiveGenome":
        """
        Produce a mutated child genome.
        - With low probability, change categorical strategies.
        - With mutation_rate, perturb continuous parameters with Gaussian noise.
        - Discrete params with random walk.
        """
        child_data = self.to_dict()
        child_data["id"] = str(uuid.uuid4())[:8]
        child_data["parent_id"] = self.id
        child_data["generation"] = self.generation + 1
        child_data["lineage"] = self.lineage + [self.id]
        # Reset performance trackers for child (will be evaluated)
        child_data["fitness"] = 0.0
        child_data["fitness_history"] = []
        child_data["benchmark_scores"] = {}
        child_data["token_usage"] = 0
        child_data["success_count"] = 0
        child_data["failure_count"] = 0

        def maybe_mutate_continuous(key: str, sigma: float = 0.15):
            if random.random() < mutation_rate:
                current = child_data[key]
                # Gaussian perturbation, scaled by sigma
                noise = random.gauss(0, sigma)
                child_data[key] = current + noise

        def maybe_mutate_discrete(key: str, min_v: int, max_v: int):
            if random.random() < mutation_rate * 0.6:
                step = random.choice([-1, 1])
                child_data[key] = max(min_v, min(max_v, child_data[key] + step))

        def maybe_mutate_enum(key: str, enum_cls):
            if random.random() < mutation_rate * 0.3:
                child_data[key] = random.choice(list(enum_cls)).value

        # Continuous
        for k in [
            "exploration_factor",
            "compression_level",
            "critique_strength",
            "confidence_threshold",
            "self_correction_frequency",
            "abstraction_level",
            "information_compression_ratio",
            "temperature",
            "context_pruning_aggressiveness",
            "verification_strictness",
            "memory_weight_recent",
            "memory_weight_relevant",
            "memory_weight_diverse",
            "adversarial_resilience",
            "novelty_seeking",
            "top_p",
        ]:
            maybe_mutate_continuous(k, sigma=0.12)

        # Discrete
        maybe_mutate_discrete("planning_depth", 1, 6)
        maybe_mutate_discrete("verification_passes", 1, 5)
        maybe_mutate_discrete("reflection_depth", 1, 5)
        maybe_mutate_discrete("search_width", 1, 7)
        maybe_mutate_discrete("planning_horizon", 2, 10)
        maybe_mutate_discrete("max_tokens", 512, 4096)

        # Categorical
        maybe_mutate_enum("reasoning_order", ReasoningOrder)
        maybe_mutate_enum("decomposition_style", DecompositionStyle)
        maybe_mutate_enum("memory_retrieval_strategy", MemoryRetrievalStrategy)

        # Occasionally larger jump for exploration
        if random.random() < 0.1:
            for k in random.sample(
                ["planning_depth", "search_width", "exploration_factor", "abstraction_level"], k=2
            ):
                if isinstance(child_data[k], int):
                    child_data[k] = random.randint(1, 6) if k == "planning_depth" else random.randint(1, 7)
                else:
                    child_data[k] = random.random()

        child = CognitiveGenome.from_dict(child_data)
        child._clamp()
        return child

    def crossover(self, other: "CognitiveGenome") -> "CognitiveGenome":
        """Single-point crossover with another genome."""
        self_dict = self.to_dict()
        other_dict = other.to_dict()

        # New child
        child_dict: Dict[str, Any] = {}
        # Performance reset
        child_dict["id"] = str(uuid.uuid4())[:8]
        child_dict["parent_id"] = self.id
        child_dict["generation"] = max(self.generation, other.generation) + 1
        child_dict["lineage"] = self.lineage + [self.id, other.id]
        child_dict["fitness"] = 0.0
        child_dict["fitness_history"] = []
        child_dict["benchmark_scores"] = {}
        child_dict["token_usage"] = 0
        child_dict["success_count"] = 0
        child_dict["failure_count"] = 0

        # Crossover each gene
        all_keys = [k for k in self_dict.keys() if k not in child_dict]
        crossover_point = random.randint(0, len(all_keys))
        for i, k in enumerate(all_keys):
            source = self_dict if i < crossover_point else other_dict
            child_dict[k] = source[k]

        child = CognitiveGenome.from_dict(child_dict)
        child._clamp()
        # Slight mutation after crossover
        if random.random() < 0.5:
            child = child.mutate(mutation_rate=0.2)
        return child

    def distance_to(self, other: "CognitiveGenome") -> float:
        """Genetic distance metric for diversity maintenance."""
        d_self = self.to_dict()
        d_other = other.to_dict()
        cont_keys = [
            "exploration_factor",
            "compression_level",
            "critique_strength",
            "confidence_threshold",
            "self_correction_frequency",
            "abstraction_level",
            "information_compression_ratio",
        ]
        dist = 0.0
        for k in cont_keys:
            dist += (d_self[k] - d_other[k]) ** 2
        # Categorical penalty
        for k in ["reasoning_order", "decomposition_style", "memory_retrieval_strategy"]:
            if d_self[k] != d_other[k]:
                dist += 0.5
        return math.sqrt(dist)


def create_default_genome() -> CognitiveGenome:
    """Generation 0 default genome - balanced, conservative."""
    return CognitiveGenome(
        id="gen0-root",
        generation=0,
        parent_id=None,
        lineage=[],
        planning_depth=3,
        verification_passes=2,
        reasoning_order=ReasoningOrder.SEQUENTIAL,
        exploration_factor=0.5,
        compression_level=0.5,
        memory_retrieval_strategy=MemoryRetrievalStrategy.HYBRID,
        decomposition_style=DecompositionStyle.HIERARCHICAL,
        critique_strength=0.6,
        reflection_depth=2,
        search_width=3,
        confidence_threshold=0.75,
        self_correction_frequency=0.7,
        abstraction_level=0.5,
        information_compression_ratio=0.4,
    )


def adaptive_population_size(task_complexity: float, config) -> int:
    """
    Map task complexity 0..1 to population size 1..5.
    Avoids wasting Groq API calls.
    """
    if task_complexity < 0.2:
        return config.evolution.complexity_thresholds["easy"]
    elif task_complexity < 0.5:
        return config.evolution.complexity_thresholds["medium"]
    elif task_complexity < 0.8:
        return config.evolution.complexity_thresholds["complex"]
    else:
        return config.evolution.complexity_thresholds["extreme"]

"""
RIOS Configuration
Centralized, type-safe configuration with environment overrides.
Respects GroqCloud limitations through adaptive population and token budgeting.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


@dataclass
class GroqConfig:
    """GroqCloud API configuration."""

    api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
    base_url: str = field(default_factory=lambda: os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
    max_retries: int = 3
    timeout_seconds: int = 60
    max_tokens_per_request: int = 4096
    requests_per_minute_limit: int = 30  # adaptive throttling
    concurrent_requests_limit: int = 5


@dataclass
class EvolutionConfig:
    """Evolution engine tuning."""

    default_population_size: int = 1
    max_population_size: int = 5
    min_population_size: int = 1
    mutation_rate: float = 0.35
    elite_preservation: bool = True
    checkpoint_interval_generations: int = 1
    max_generations_before_pause: int = 10000  # effectively infinite; stop only via user
    adaptivity_enabled: bool = True
    # Task complexity heuristics -> population mapping
    complexity_thresholds: dict = field(
        default_factory=lambda: {
            "easy": 1,
            "medium": 2,
            "complex": 3,
            "extreme": 5,
        }
    )


@dataclass
class MemoryConfig:
    """Memory subsystem configuration."""

    max_working_memory_tokens: int = 4000
    max_episodic_entries: int = 500
    max_semantic_patterns: int = 200
    compression_target_ratio: float = 0.4
    summarization_trigger_tokens: int = 8000
    embedding_enabled: bool = False  # optional vector db
    vector_db_path: str = "./data/vectordb"


@dataclass
class TokenOptimizationConfig:
    """Aggressive token minimization."""

    enable_prompt_caching: bool = True
    enable_response_caching: bool = True
    enable_checkpoint_caching: bool = True
    enable_recursive_summarization: bool = True
    enable_duplicate_elimination: bool = True
    enable_incremental_context: bool = True
    max_context_tokens_per_generation: int = 6000
    summary_max_tokens: int = 512


@dataclass
class EvaluationConfig:
    """PIES evaluation tuning."""

    benchmark_families: List[str] = field(
        default_factory=lambda: [
            "graph_algorithms",
            "mathematics",
            "formal_logic",
            "constraint_satisfaction",
            "optimization",
            "planning",
            "programming",
            "debugging",
            "compression",
            "scientific_reasoning",
            "pattern_recognition",
            "information_reconstruction",
            "scheduling",
            "causal_inference",
            "abstract_reasoning",
            "counterfactual_reasoning",
            "strategic_games",
            "algorithm_design",
            "multi_step_reasoning",
            "knowledge_integration",
        ]
    )
    default_difficulty: float = 0.5  # 0..1
    difficulty_adaptation_rate: float = 0.1
    adversarial_tests_per_solution: int = 3
    max_benchmarks_per_generation: int = 2


@dataclass
class FitnessWeights:
    """Weighted fitness dimensions - must sum ~1.0 but normalized at runtime."""

    reasoning_quality: float = 0.20
    correctness: float = 0.20
    verification: float = 0.15
    planning: float = 0.10
    generalization: float = 0.10
    robustness: float = 0.10
    compression: float = 0.05
    token_efficiency: float = 0.05
    novelty: float = 0.03
    self_correction: float = 0.02

    def as_dict(self) -> dict:
        return {
            "reasoning_quality": self.reasoning_quality,
            "correctness": self.correctness,
            "verification": self.verification,
            "planning": self.planning,
            "generalization": self.generalization,
            "robustness": self.robustness,
            "compression": self.compression,
            "token_efficiency": self.token_efficiency,
            "novelty": self.novelty,
            "self_correction": self.self_correction,
        }

    def normalized(self) -> dict:
        d = self.as_dict()
        total = sum(d.values())
        return {k: v / total for k, v in d.items()}


@dataclass
class AppConfig:
    """Root application config composed of sub-configs."""

    app_name: str = "RIOS - Recursive Intelligence Operating System"
    version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/rios.db"))
    data_dir: str = "./data"
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    groq: GroqConfig = field(default_factory=GroqConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    token_opt: TokenOptimizationConfig = field(default_factory=TokenOptimizationConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)
    fitness: FitnessWeights = field(default_factory=FitnessWeights)

    # CORS and server
    cors_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"])
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Singleton cached config."""
    return AppConfig()

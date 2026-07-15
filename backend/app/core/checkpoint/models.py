"""
Checkpoint Models - Pydantic schemas for checkpoint data.
"""

from __future__ import annotations

from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import time


class CheckpointMetadata(BaseModel):
    generation: int
    timestamp: float = time.time()
    best_fitness: float = 0.0
    total_tokens: int = 0
    problem: Optional[str] = None


class CheckpointModel(BaseModel):
    generation: int
    best_genome: Optional[Dict[str, Any]] = None
    best_answer: Optional[str] = None
    best_scaffold: Optional[str] = None
    problem: Optional[str] = None
    reasoning_tree: List[Dict[str, Any]] = []
    memory_snapshot: Dict[str, Any] = {}
    evolution_stats: Dict[str, Any] = {}
    groq_stats: Dict[str, Any] = {}
    benchmark_summary: Dict[str, Any] = {}
    timestamp: float = time.time()

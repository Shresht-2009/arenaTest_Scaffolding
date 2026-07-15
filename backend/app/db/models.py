"""
DB Models - Dataclass representations (not ORM heavy).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationModel:
    generation: int
    genome_id: str
    parent_id: Optional[str]
    fitness: float
    token_usage: int
    problem: Optional[str]
    solution: Optional[str]
    reasoning_summary: Optional[str]
    timestamp: float

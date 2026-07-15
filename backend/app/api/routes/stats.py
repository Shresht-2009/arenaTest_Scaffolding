"""
Stats API
"""

from fastapi import APIRouter
from .evolution import get_engine
from ...core.telemetry.stats import get_stats_collector

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/")
async def get_all_stats():
    engine = get_engine()
    telemetry = get_stats_collector()
    return {
        "engine": engine.get_current_state(),
        "telemetry": telemetry.get_stats(),
        "groq": engine.groq.stats(),
        "evolution": engine.evolution_engine.get_stats(),
        "benchmarks": engine.benchmark_engine.get_performance_summary(),
        "memory": engine.memory.stats(),
    }


@router.get("/tokens")
async def get_token_stats():
    engine = get_engine()
    return engine.groq.stats()

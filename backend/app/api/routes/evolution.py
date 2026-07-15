"""
Evolution API Routes
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio

from ...core.recursive_engine import RecursiveIntelligenceEngine

router = APIRouter(prefix="/api/evolution", tags=["evolution"])

# Global engine singleton (in production use dependency injection)
_engine_instance: Optional[RecursiveIntelligenceEngine] = None


def get_engine() -> RecursiveIntelligenceEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = RecursiveIntelligenceEngine()
        # Set to websocket manager
        try:
            from ..websockets.evolution_ws import get_ws_manager

            get_ws_manager().set_engine(_engine_instance)
        except Exception:
            pass
    return _engine_instance


class StartRequest(BaseModel):
    problem: str
    resume: bool = False


class StopResponse(BaseModel):
    best_answer: Optional[str] = None
    generation_number: int
    current_genome: Optional[Dict[str, Any]] = None


@router.get("/state")
async def get_state():
    engine = get_engine()
    return engine.get_current_state()


@router.post("/start")
async def start_evolution(req: StartRequest):
    engine = get_engine()
    if engine.is_running:
        raise HTTPException(status_code=400, detail="Evolution already running")
    # Initialize but don't block; client should use WS for streaming
    # For REST, run one generation as demo
    await engine.initialize()
    if req.resume:
        engine.resume()
    result = await engine.run_single_generation(req.problem)
    return result


@router.post("/stop")
async def stop_evolution():
    engine = get_engine()
    if not engine.is_running:
        # Still produce summary even if not running
        result = engine.stop()
        return result
    result = engine.stop()
    return result


@router.post("/resume")
async def resume_evolution():
    engine = get_engine()
    res = engine.resume()
    return res


@router.get("/genome")
async def get_best_genome():
    engine = get_engine()
    if engine.evolution_engine.best_genome:
        return engine.evolution_engine.best_genome.to_dict()
    return {"message": "No genome yet"}


@router.get("/genome/history")
async def get_genome_history():
    engine = get_engine()
    return {"history": engine.evolution_engine.evolution_history[-50:], "generation": engine.current_generation}


@router.get("/memory")
async def get_memory_stats():
    engine = get_engine()
    return engine.memory.stats()


@router.get("/stats")
async def get_stats():
    engine = get_engine()
    return {
        "engine_stats": engine.stats,
        "groq_stats": engine.groq.stats(),
        "evolution_stats": engine.evolution_engine.get_stats(),
        "benchmark_summary": engine.benchmark_engine.get_performance_summary(),
    }

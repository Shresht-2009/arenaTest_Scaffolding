"""
Memory Inspector API
"""

from fastapi import APIRouter

from .evolution import get_engine

router = APIRouter(prefix="/api/memory", tags=["memory"])


@router.get("/")
async def get_memory():
    engine = get_engine()
    return engine.memory.stats()


@router.get("/working")
async def get_working_memory():
    engine = get_engine()
    return {
        "working": engine.memory.working.snapshot(),
        "tree": engine.memory.working.get_full_tree()[-20:],
    }


@router.get("/episodic")
async def get_episodic():
    engine = get_engine()
    return {
        "summary": engine.memory.episodic.summary(),
        "best_generations": [g.__dict__ for g in engine.memory.episodic.get_best_generations(10)],
        "recent": [g.__dict__ for g in engine.memory.episodic.get_recent_generations(20)],
    }


@router.get("/semantic")
async def get_semantic():
    engine = get_engine()
    return engine.memory.semantic.summary()


@router.get("/compressed")
async def get_compressed():
    engine = get_engine()
    return {
        "stats": engine.memory.compressed.stats(),
        "tree": engine.memory.compressed.export_tree(max_depth=2),
        "context": engine.memory.compressed.get_compressed_context(max_tokens=500),
    }


@router.post("/clear_working")
async def clear_working():
    engine = get_engine()
    engine.memory.clear_working()
    return {"status": "cleared"}

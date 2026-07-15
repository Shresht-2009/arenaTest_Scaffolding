"""
RIOS - Recursive Intelligence Operating System
FastAPI main entry point.

Production-quality, modular, observable.
"""

from __future__ import annotations

import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config import get_config
from .core.telemetry.logger import setup_logging
from .db.database import init_db
from .api.routes import evolution, benchmark, memory, checkpoints, stats
from .api.websockets.evolution_ws import get_ws_manager, manager

config = get_config()
setup_logging(log_level=config.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {config.app_name} v{config.version}")
    init_db()
    Path = __import__("pathlib").Path
    Path(config.data_dir).mkdir(parents=True, exist_ok=True)
    Path(f"{config.data_dir}/checkpoints").mkdir(parents=True, exist_ok=True)

    # Initialize engine
    try:
        from .api.routes.evolution import get_engine

        engine = get_engine()
        await engine.initialize()
        get_ws_manager().set_engine(engine)
        logger.info("Recursive Intelligence Engine initialized")
    except Exception as e:
        logger.warning(f"Engine init failed (will retry on first request): {e}")

    yield
    # Shutdown
    logger.info("Shutting down RIOS")


app = FastAPI(
    title=config.app_name,
    version=config.version,
    description="""
Recursive Intelligence Operating System (RIOS)

An evolving reasoning system around GPT-OSS-120B (GroqCloud).

- Recursive scaffolding with no artificial limit
- Cognitive genome evolution
- Hierarchical memory with aggressive compression
- Procedural Intelligence Evaluation System (PIES)
- Adaptive population to respect GroqCloud limits
- Real-time evolution streaming via WebSockets

The model never changes - the framework evolves.
    """,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(evolution.router)
app.include_router(benchmark.router)
app.include_router(memory.router)
app.include_router(checkpoints.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    return {
        "name": config.app_name,
        "version": config.version,
        "status": "running",
        "model": config.groq.model,
        "description": "Recursive Intelligence Operating System - evolving reasoning around GPT-OSS-120B",
        "endpoints": {
            "rest": ["/api/evolution/state", "/api/benchmark/families", "/api/memory", "/api/checkpoints", "/api/stats"],
            "websocket": "/ws/evolution",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health():
    from .api.routes.evolution import get_engine

    try:
        engine = get_engine()
        state = engine.get_current_state()
        return {"status": "healthy", "engine_running": state.get("is_running", False), "generation": state.get("generation", 0)}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.websocket("/ws/evolution")
async def websocket_evolution(websocket: WebSocket):
    ws_manager = get_ws_manager()
    await ws_manager.handle_client(websocket)


@app.get("/api/engine/dashboard")
async def dashboard_data():
    """
    Aggregated dashboard data for frontend - single call to get everything.
    """
    from .api.routes.evolution import get_engine

    engine = get_engine()
    return {
        "current_generation": engine.current_generation,
        "current_genome": engine.evolution_engine.best_genome.to_dict() if engine.evolution_engine.best_genome else None,
        "genome_history": engine.evolution_engine.evolution_history[-30:],
        "fitness_score": engine.evolution_engine.best_genome.fitness if engine.evolution_engine.best_genome else 0.0,
        "reasoning_depth": engine.memory.stats()["working"]["steps"],
        "compression_ratio": engine.memory.compressed.stats().get("avg_compression_ratio", 0.0),
        "memory_usage": engine.memory.stats(),
        "token_usage": engine.groq.stats(),
        "api_requests": engine.groq.stats().get("requests", 0),
        "latency": engine.groq.stats().get("avg_latency_ms", 0),
        "cost_estimate": engine.groq.stats().get("estimated_cost", 0.0),
        "recursive_depth": engine.evolution_engine.best_genome.planning_depth if engine.evolution_engine.best_genome else 0,
        "benchmark_results": engine.benchmark_engine.get_performance_summary(),
        "evolution_timeline": engine.evolution_engine.evolution_history[-50:],
        "checkpoint_history": engine.checkpoint_manager.get_checkpoint_history()[:10],
        "best_answer": engine.best_answer,
        "best_scaffold": engine.best_scaffold,
        "reasoning_tree": engine.memory.working.get_full_tree()[-20:],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=config.host, port=config.port, reload=config.debug)

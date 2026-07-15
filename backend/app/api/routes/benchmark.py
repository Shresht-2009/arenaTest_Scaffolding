"""
Benchmark API Routes - PIES
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List

from ...core.evaluation.pies.benchmark_engine import BenchmarkEngine

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

_engine: Optional[BenchmarkEngine] = None


def get_benchmark_engine() -> BenchmarkEngine:
    global _engine
    if _engine is None:
        _engine = BenchmarkEngine()
    return _engine


class GenerateRequest(BaseModel):
    family: Optional[str] = None
    difficulty: float = 0.5
    seed: Optional[int] = None
    count: int = 1


@router.post("/generate")
async def generate_task(req: GenerateRequest):
    eng = get_benchmark_engine()
    if req.count == 1:
        task = eng.generate_task(family=req.family, difficulty=req.difficulty, seed=req.seed)
        return {
            "id": task.id,
            "family": task.family,
            "difficulty": task.difficulty,
            "seed": task.seed,
            "problem": task.problem,
            "solution": task.solution,
            "metadata": task.metadata,
            "adversarial_variants": task.adversarial_variants[:2],
        }
    else:
        tasks = eng.generate_batch(n=req.count, families=[req.family] if req.family else None, difficulty=req.difficulty)
        return [
            {
                "id": t.id,
                "family": t.family,
                "difficulty": t.difficulty,
                "seed": t.seed,
                "problem": t.problem,
                "solution": t.solution,
                "metadata": t.metadata,
            }
            for t in tasks
        ]


@router.get("/families")
async def list_families():
    eng = get_benchmark_engine()
    return {"families": list(eng.generators.keys())}


@router.get("/summary")
async def summary():
    eng = get_benchmark_engine()
    return eng.get_performance_summary()


@router.post("/evaluate")
async def evaluate_solution(payload: dict):
    # payload: task_id or problem+family, attempted_solution
    eng = get_benchmark_engine()
    task_data = payload.get("task")
    attempted = payload.get("attempted_solution", "")
    # If task_data provided as simple, generate task
    from ...core.evaluation.pies.base import BenchmarkTask

    if task_data and "problem" in task_data:
        task = BenchmarkTask(
            family=task_data.get("family", "general"),
            id=task_data.get("id", "custom"),
            difficulty=task_data.get("difficulty", 0.5),
            seed=task_data.get("seed", 0),
            problem=task_data["problem"],
            solution=task_data.get("solution", ""),
            checker=None,
        )
    else:
        # Generate random task for evaluation
        task = eng.generate_task()

    result = eng.evaluate_solution(task, attempted)
    return result

"""
Checkpoint Manager API
"""

from fastapi import APIRouter
from ...core.checkpoint.manager import CheckpointManager

router = APIRouter(prefix="/api/checkpoints", tags=["checkpoints"])

manager = CheckpointManager()


@router.get("/")
async def list_checkpoints():
    history = manager.get_checkpoint_history()
    return {"checkpoints": history, "count": len(history)}


@router.get("/latest")
async def get_latest():
    cp = manager.load_latest()
    if not cp:
        return {"message": "No checkpoints"}
    return cp


@router.get("/{checkpoint_file}")
async def get_checkpoint(checkpoint_file: str):
    # checkpoint_file is filename
    path = manager.checkpoint_dir / checkpoint_file
    if not path.exists():
        return {"error": "Not found"}
    data = manager.load_checkpoint(str(path))
    return data or {"error": "Failed to load"}


@router.delete("/{checkpoint_file}")
async def delete_checkpoint(checkpoint_file: str):
    path = manager.checkpoint_dir / checkpoint_file
    success = manager.delete_checkpoint(str(path))
    return {"deleted": success, "file": checkpoint_file}

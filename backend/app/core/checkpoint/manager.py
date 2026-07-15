"""
Checkpoint Manager - Persistence for Stop/Resume.

Handles saving/loading checkpoints to disk (JSON) and optionally SQLite.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages checkpoint persistence.
    - Saves to ./data/checkpoints/
    - Keeps last N checkpoints
    - Provides load_latest and list
    """

    def __init__(self, checkpoint_dir: str = "./data/checkpoints", max_checkpoints: int = 50):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.max_checkpoints = max_checkpoints

    def _checkpoint_path(self, generation: int, timestamp: Optional[float] = None) -> Path:
        ts = int((timestamp or time.time()) * 1000)
        return self.checkpoint_dir / f"checkpoint_gen{generation}_{ts}.json"

    def save_checkpoint(self, data: Dict[str, Any], generation: int) -> str:
        path = self._checkpoint_path(generation, data.get("timestamp"))
        try:
            # Ensure serializable
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved checkpoint gen {generation} to {path}")
            self._prune_old()
            return str(path)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return ""

    def load_checkpoint(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load checkpoint {path}: {e}")
            return None

    def load_latest(self) -> Optional[Dict[str, Any]]:
        checkpoints = self.list_checkpoints()
        if not checkpoints:
            return None
        latest_path = max(checkpoints, key=lambda p: p.stat().st_mtime)
        return self.load_checkpoint(str(latest_path))

    def list_checkpoints(self) -> List[Path]:
        if not self.checkpoint_dir.exists():
            return []
        return sorted(self.checkpoint_dir.glob("checkpoint_gen*.json"), key=lambda p: p.stat().st_mtime)

    def get_checkpoint_history(self) -> List[Dict[str, Any]]:
        result = []
        for p in self.list_checkpoints():
            try:
                stat = p.stat()
                # Quick metadata without loading full file
                result.append(
                    {
                        "path": str(p),
                        "generation": self._extract_generation(p.name),
                        "size_bytes": stat.st_size,
                        "modified": stat.st_mtime,
                        "filename": p.name,
                    }
                )
            except Exception:
                continue
        # Sort newest first
        result.sort(key=lambda x: x["modified"], reverse=True)
        return result

    def _extract_generation(self, filename: str) -> int:
        import re
        m = re.search(r"gen(\d+)", filename)
        return int(m.group(1)) if m else 0

    def _prune_old(self):
        checkpoints = self.list_checkpoints()
        if len(checkpoints) <= self.max_checkpoints:
            return
        # Remove oldest
        checkpoints_sorted = sorted(checkpoints, key=lambda p: p.stat().st_mtime)
        to_remove = checkpoints_sorted[: len(checkpoints) - self.max_checkpoints]
        for p in to_remove:
            try:
                p.unlink()
                logger.info(f"Pruned old checkpoint {p}")
            except Exception as e:
                logger.warning(f"Failed to prune {p}: {e}")

    def delete_checkpoint(self, path: str) -> bool:
        try:
            Path(path).unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {path}: {e}")
            return False

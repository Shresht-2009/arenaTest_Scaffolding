"""
LLM Cache - Response, prompt, checkpoint caching for token efficiency.

Implements:
- LRU response cache keyed by (genome_id + problem + prompt hash)
- Prompt fragment caching
- Dedup via fingerprint
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, Optional
import hashlib
import time
import json


def _hash_key(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()[:16]


class LRUCache:
    def __init__(self, max_size: int = 200):
        self.max_size = max_size
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            self.misses += 1
            return None
        self.hits += 1
        self.cache.move_to_end(key)
        entry = self.cache[key]
        # Check expiry if present
        if isinstance(entry, dict) and "expiry" in entry:
            if time.time() > entry["expiry"]:
                del self.cache[key]
                self.misses += 1
                return None
            return entry["value"]
        return entry

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = {"value": value, "expiry": time.time() + ttl_seconds} if ttl_seconds else value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def stats(self):
        total = self.hits + self.misses
        return {
            "size": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0.0,
        }

    def clear(self):
        self.cache.clear()
        self.hits = 0
        self.misses = 0


class PromptCache:
    """Cache for prompt fragments (genome prompts, memory context)."""

    def __init__(self):
        self.fragments: Dict[str, str] = {}
        self.usage_counts: Dict[str, int] = {}

    def get_fragment(self, key: str) -> Optional[str]:
        if key in self.fragments:
            self.usage_counts[key] = self.usage_counts.get(key, 0) + 1
            return self.fragments[key]
        return None

    def set_fragment(self, key: str, fragment: str):
        self.fragments[key] = fragment
        self.usage_counts[key] = self.usage_counts.get(key, 0) + 1

    def stats(self):
        return {
            "fragments": len(self.fragments),
            "total_usages": sum(self.usage_counts.values()),
            "top_fragments": sorted(self.usage_counts.items(), key=lambda x: x[1], reverse=True)[:5],
        }


class ResponseCache:
    """LLM response cache."""

    def __init__(self, max_size: int = 300):
        self.lru = LRUCache(max_size=max_size)

    def make_key(self, genome_id: str, problem: str, phase: str, prompt: str) -> str:
        composite = f"{genome_id}|{phase}|{problem[:200]}|{prompt[:500]}"
        return _hash_key(composite)

    def get(self, key: str) -> Optional[str]:
        return self.lru.get(key)

    def set(self, key: str, response: str, ttl_seconds: int = 3600):
        self.lru.set(key, response, ttl_seconds=ttl_seconds)

    def stats(self):
        return self.lru.stats()


class CheckpointCache:
    """Cache for checkpoint embeddings / snapshots to avoid re-computation."""

    def __init__(self):
        self.checkpoints: Dict[str, Any] = {}

    def set(self, gen: int, data: Any):
        self.checkpoints[str(gen)] = data

    def get(self, gen: int) -> Optional[Any]:
        return self.checkpoints.get(str(gen))

    def latest(self) -> Optional[Any]:
        if not self.checkpoints:
            return None
        latest_gen = max(int(k) for k in self.checkpoints.keys())
        return self.checkpoints[str(latest_gen)]

    def stats(self):
        return {"count": len(self.checkpoints)}

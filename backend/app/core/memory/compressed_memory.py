"""
Compressed Memory - Recursive summaries, fingerprints, abstraction trees.

Implements aggressive compression to reduce token usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import hashlib
import json


@dataclass
class CompressedNode:
    id: str
    level: int  # 0 = raw, 1 = summarized, 2 = abstracted, 3 = fingerprint
    content: str
    original_tokens: int
    compressed_tokens: int
    fingerprint: str  # hash
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def compression_ratio(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return 1.0 - (self.compressed_tokens / self.original_tokens)


class CompressedMemory:
    """
    Hierarchical compression tree.
    Level 0: raw reasoning steps
    Level 1: summarized clusters
    Level 2: abstracted principles
    Level 3: fingerprints / embeddings-like hashes
    """

    def __init__(self, target_ratio: float = 0.4):
        self.target_ratio = target_ratio
        self.nodes: Dict[str, CompressedNode] = {}
        self.root_ids: List[str] = []
        self.fingerprint_index: Dict[str, str] = {}  # fingerprint -> node_id

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _estimate_tokens(self, text: str) -> int:
        # Rough: 1 token ~ 0.75 words ~ 4 chars
        return max(1, len(text) // 4)

    def add_raw(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add raw content as level 0 node."""
        fp = self._hash_content(content)
        # Deduplication
        if fp in self.fingerprint_index:
            return self.fingerprint_index[fp]

        node_id = f"n-{fp[:8]}-{int(time.time()*1000)%10000}"
        tokens = self._estimate_tokens(content)
        node = CompressedNode(
            id=node_id,
            level=0,
            content=content,
            original_tokens=tokens,
            compressed_tokens=tokens,
            fingerprint=fp,
            metadata=metadata or {},
        )
        self.nodes[node_id] = node
        self.root_ids.append(node_id)
        self.fingerprint_index[fp] = node_id
        return node_id

    def compress_node(self, node_id: str, compressed_content: str, level: int) -> Optional[str]:
        """Create compressed parent of a node."""
        if node_id not in self.nodes:
            return None
        parent = self.nodes[node_id]
        fp = self._hash_content(compressed_content)

        new_id = f"n-{fp[:8]}-L{level}-{int(time.time()*1000)%10000}"
        new_node = CompressedNode(
            id=new_id,
            level=level,
            content=compressed_content,
            original_tokens=parent.original_tokens,
            compressed_tokens=self._estimate_tokens(compressed_content),
            fingerprint=fp,
            children_ids=[node_id],
            metadata={"compressed_from": node_id},
        )
        self.nodes[new_id] = new_node
        parent.parent_id = new_id
        # Replace root if needed
        if node_id in self.root_ids:
            self.root_ids.remove(node_id)
            self.root_ids.append(new_id)
        self.fingerprint_index[fp] = new_id
        return new_id

    def hierarchical_compress(self, node_ids: List[str], summary_fn) -> Optional[str]:
        """
        Compress multiple nodes into one summary node.
        summary_fn: callable that takes list of contents and returns summary string
                     (in production this would be LLM call; here deterministic placeholder)
        """
        if not node_ids:
            return None
        contents = [self.nodes[nid].content for nid in node_ids if nid in self.nodes]
        if not contents:
            return None

        # Simple deterministic summarization if no LLM provided
        if summary_fn is None:
            # Take first 100 chars of each, concatenate, then abstract
            summary = " | ".join([c[:150] for c in contents[:5]])
            summary = f"Summary({len(contents)} nodes): {summary[:500]}"
        else:
            try:
                summary = summary_fn(contents)
            except Exception:
                summary = " | ".join([c[:100] for c in contents])[:500]

        fp = self._hash_content(summary)
        if fp in self.fingerprint_index:
            return self.fingerprint_index[fp]

        total_original = sum(self.nodes[nid].original_tokens for nid in node_ids if nid in self.nodes)
        new_id = f"n-{fp[:8]}-H-{int(time.time()*1000)%10000}"
        new_node = CompressedNode(
            id=new_id,
            level=2,
            content=summary,
            original_tokens=total_original,
            compressed_tokens=self._estimate_tokens(summary),
            fingerprint=fp,
            children_ids=node_ids,
            metadata={"hierarchical": True, "child_count": len(node_ids)},
        )
        self.nodes[new_id] = new_node
        for nid in node_ids:
            if nid in self.nodes:
                self.nodes[nid].parent_id = new_id
                if nid in self.root_ids:
                    self.root_ids.remove(nid)
        self.root_ids.append(new_id)
        self.fingerprint_index[fp] = new_id
        return new_id

    def get_compressed_context(self, max_tokens: int = 1000) -> str:
        """Retrieve compressed context to fit token budget."""
        # Prefer higher-level nodes for efficiency
        sorted_nodes = sorted(
            [self.nodes[nid] for nid in self.root_ids if nid in self.nodes],
            key=lambda n: (n.level, -n.timestamp),
            reverse=True,
        )
        budget = max_tokens
        parts = []
        for node in sorted_nodes:
            if budget <= 0:
                break
            if node.compressed_tokens <= budget:
                parts.append(f"[L{node.level}:{node.fingerprint[:6]}] {node.content}")
                budget -= node.compressed_tokens
        return "\n".join(parts)

    def get_fingerprint(self, content: str) -> str:
        return self._hash_content(content)

    def stats(self) -> Dict[str, Any]:
        total_original = sum(n.original_tokens for n in self.nodes.values())
        total_compressed = sum(n.compressed_tokens for n in self.nodes.values() if n.id in self.root_ids)
        avg_ratio = 1.0 - (total_compressed / total_original) if total_original > 0 else 0.0
        return {
            "total_nodes": len(self.nodes),
            "root_nodes": len(self.root_ids),
            "total_original_tokens": total_original,
            "total_compressed_tokens": total_compressed,
            "avg_compression_ratio": avg_ratio,
            "levels": {
                level: len([n for n in self.nodes.values() if n.level == level]) for level in range(4)
            },
        }

    def export_tree(self, max_depth: int = 3) -> Dict[str, Any]:
        """Export tree for visualization."""

        def node_to_dict(nid: str, depth: int) -> Dict[str, Any]:
            if depth > max_depth or nid not in self.nodes:
                return {}
            node = self.nodes[nid]
            return {
                "id": node.id,
                "level": node.level,
                "content": node.content[:200],
                "ratio": node.compression_ratio,
                "tokens": node.compressed_tokens,
                "children": [node_to_dict(cid, depth + 1) for cid in node.children_ids[:5]],
            }

        return {"roots": [node_to_dict(rid, 0) for rid in self.root_ids[:10]], "stats": self.stats()}

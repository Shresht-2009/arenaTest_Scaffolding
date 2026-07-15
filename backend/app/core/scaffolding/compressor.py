"""
Compressor - Information compression engine.

Implements recursive summarization, hierarchical abstraction,
information fingerprints, duplicate elimination.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from ..cognitive_genome import CognitiveGenome
from ..memory.memory_manager import MemoryManager
from ..llm.groq_client import GroqClient, get_groq_client
from ..llm.prompt_optimizer import PromptOptimizer
import hashlib


class Compressor:
    """Compression scaffold with both deterministic and LLM-assisted modes."""

    def __init__(self, groq_client: Optional[GroqClient] = None, prompt_optimizer: Optional[PromptOptimizer] = None):
        self.groq = groq_client or get_groq_client()
        self.optimizer = prompt_optimizer or PromptOptimizer()

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def deterministic_compress(self, text: str, target_ratio: float = 0.4) -> str:
        """
        Deterministic compression without LLM:
        - Remove filler phrases
        - Keep first sentence of each paragraph
        - Remove redundant whitespaces
        """
        import re

        # Remove common filler
        filler_pattern = r"\b(in other words|it is important to note|as mentioned|basically|essentially|quite|very|really)\b"
        text = re.sub(filler_pattern, "", text, flags=re.IGNORECASE)

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return text[: int(len(text) * (1 - target_ratio))]

        # Keep structure
        compressed_paras = []
        target_len = int(len(text) * (1 - target_ratio))
        current_len = 0
        for para in paragraphs:
            if current_len >= target_len:
                break
            sentences = re.split(r"(?<=[.!?])\s+", para)
            # Keep first and last if many
            if len(sentences) <= 2:
                kept = para
            else:
                kept = sentences[0] + " " + sentences[-1]
            compressed_paras.append(kept[:300])
            current_len += len(kept)

        return "\n\n".join(compressed_paras)

    def fingerprint(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    async def compress(
        self,
        genome: CognitiveGenome,
        content: str,
        memory_manager: MemoryManager,
        level: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Compress content according to genome's compression_level.
        Uses LLM for high-quality compression if needed, but prefers deterministic for efficiency.
        """
        target_ratio = level if level is not None else genome.compression_level
        original_tokens = self.estimate_tokens(content)

        # For low compression or small content, use deterministic
        if target_ratio < 0.3 or original_tokens < 200:
            compressed = self.deterministic_compress(content, target_ratio)
            compressed_tokens = self.estimate_tokens(compressed)
            result = {
                "compressed": compressed,
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "ratio": 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0,
                "fingerprint": self.fingerprint(compressed),
                "method": "deterministic",
            }
            # Store in compressed memory
            memory_manager.compressed.add_raw(content)
            memory_manager.compressed.compress_node(
                list(memory_manager.compressed.nodes.keys())[-1] if memory_manager.compressed.nodes else "",
                compressed,
                level=1,
            )
            return result

        # LLM-assisted compression for higher ratios
        genome_fragment = genome.to_prompt_fragment()
        memory_context = ""  # minimal for compression to save tokens
        phase_instructions = f"""
You are in COMPRESSION phase.
Compression Level: {genome.compression_level:.2f}
Target Ratio: {target_ratio:.2f} (remove {target_ratio*100:.0f}% tokens)
Abstraction Level: {genome.abstraction_level:.2f}

Task: Compress the following reasoning/content while preserving:
- Core logic
- Key insights
- Verification results
- Information essential for future reasoning

Remove:
- Redundancy
- Verbose phrasing
- Low-information filler
- Duplicate reasoning

If abstraction_level > 0.6, convert to higher-level abstractions and principles.
If abstraction_level <= 0.6, keep concrete but concise.

Content to compress:
{content[:3000]}

Output ONLY the compressed version, no explanation. Max {int(original_tokens * (1 - target_ratio * 0.8))} tokens.

Compressed version:
"""

        prompt = self.optimizer.build_final_prompt(
            genome_fragment=genome_fragment,
            memory_context=memory_context,
            problem="Compress reasoning",
            phase_instructions=phase_instructions,
            previous_steps="",
        )

        llm_content, meta = await self.groq.complete(
            prompt=prompt,
            genome_id=genome.id,
            phase="compress",
            temperature=0.3,  # low temp for compression
            max_tokens=min(genome.max_tokens, int(original_tokens * (1 - target_ratio) + 200)),
            top_p=0.9,
        )

        compressed = llm_content.strip()
        compressed_tokens = self.estimate_tokens(compressed)
        actual_ratio = 1 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0

        # Record
        memory_manager.add_reasoning_step(
            phase="Compression",
            content=f"Original {original_tokens} -> Compressed {compressed_tokens} ratio {actual_ratio:.2f}",
            tokens=meta.get("tokens_in", 0) + meta.get("tokens_out", 0),
            confidence=0.8,
            metadata={"ratio": actual_ratio, "method": "llm"},
        )

        return {
            "compressed": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ratio": actual_ratio,
            "fingerprint": self.fingerprint(compressed),
            "method": "llm",
            "llm_meta": meta,
        }

    async def hierarchical_compress_tree(self, genome: CognitiveGenome, reasoning_tree: List[Dict[str, Any]], memory_manager: MemoryManager) -> str:
        """
        Compress entire reasoning tree hierarchically.
        """
        import json

        # Group by phase
        phases: Dict[str, List[str]] = {}
        for step in reasoning_tree:
            phase = step.get("phase", "unknown")
            phases.setdefault(phase, []).append(step.get("content", "")[:500])

        summaries = []
        for phase, contents in phases.items():
            combined = "\n".join(contents)
            comp = self.deterministic_compress(combined, target_ratio=genome.information_compression_ratio)
            summaries.append(f"[{phase}]: {comp[:300]}")

        # Second-level compression via LLM if needed
        if genome.compression_level > 0.5 and len(summaries) > 3:
            second_level_input = "\n\n".join(summaries)
            result = await self.compress(genome, second_level_input, memory_manager, level=genome.compression_level)
            return result["compressed"]

        return "\n\n".join(summaries)

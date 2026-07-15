"""
Reflector - Meta-reflection and self-correction.

Performs reflection_depth iterations of meta-analysis.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from ..cognitive_genome import CognitiveGenome
from ..memory.memory_manager import MemoryManager
from ..llm.groq_client import GroqClient, get_groq_client
from ..llm.prompt_optimizer import PromptOptimizer


class Reflector:
    """Meta-reflection scaffold."""

    def __init__(self, groq_client: Optional[GroqClient] = None, prompt_optimizer: Optional[PromptOptimizer] = None):
        self.groq = groq_client or get_groq_client()
        self.optimizer = prompt_optimizer or PromptOptimizer()

    async def reflect(
        self, genome: CognitiveGenome, problem: str, execution_result: Dict[str, Any], memory_manager: MemoryManager
    ) -> Dict[str, Any]:
        """
        Perform reflection_depth meta-reflections.
        Output insights for semantic memory.
        """
        genome_fragment = genome.to_prompt_fragment()
        previous = memory_manager.working.get_context(last_n=4)
        memory_context = memory_manager.retrieve_context_for_genome(genome, problem, max_tokens=1000)

        reflections = []
        current_context = f"""
Problem: {problem[:800]}
Execution Result: {str(execution_result)[:1000]}
Current Genome: {genome.id} Gen {genome.generation}
Fitness if available: {genome.fitness}
"""

        for depth in range(genome.reflection_depth):
            phase_instructions = f"""
You are in REFLECTION phase - Depth {depth+1}/{genome.reflection_depth}
Self-Correction Frequency: {genome.self_correction_frequency:.2f}
Abstraction Level: {genome.abstraction_level:.2f}
Novelty Seeking: {genome.novelty_seeking:.2f}

Context:
{current_context}

Tasks:
1. What worked well in this reasoning? Why?
2. What failed or was inefficient?
3. What would you do differently next generation?
4. Extract reusable pattern/abstraction.
5. Suggest genome mutation direction (increase/decrease specific parameters).

Output JSON:
{{
  "what_worked": "...",
  "what_failed": "...",
  "lesson": "...",
  "reusable_pattern": {{"description": "...", "abstraction": "...", "domain": "general"}},
  "genome_suggestions": {{"parameter": "increase/decrease", ...}},
  "confidence": 0.0-1.0,
  "novelty_score": 0.0-1.0
}}

Be honest, concise, actionable.
"""

            # Convert previous reflections dicts to strings for context
            refl_str = "\n".join([str(r.get("lesson", ""))[:200] for r in reflections[-2:]]) if reflections else ""
            prompt = self.optimizer.build_final_prompt(
                genome_fragment=genome_fragment,
                memory_context=memory_context,
                problem=problem,
                phase_instructions=phase_instructions,
                previous_steps=previous + "\n" + refl_str,
            )

            content, meta = await self.groq.complete(
                prompt=prompt,
                genome_id=genome.id,
                phase="reflect",
                temperature=genome.temperature * 0.9,
                max_tokens=min(genome.max_tokens, 1200),
                top_p=genome.top_p,
            )

            parsed = self._parse_reflection(content)
            parsed["_meta"] = meta
            parsed["depth"] = depth + 1
            reflections.append(parsed)

            memory_manager.add_reasoning_step(
                phase=f"Reflection-Depth-{depth+1}",
                content=content,
                tokens=meta.get("tokens_in", 0) + meta.get("tokens_out", 0),
                confidence=parsed.get("confidence", 0.5),
                metadata={"reflection": parsed},
            )

            # Update current context for next depth
            current_context += f"\nReflection {depth+1}: {parsed.get('lesson','')[:200]}"

            # Distill pattern to semantic memory if high confidence
            if parsed.get("reusable_pattern") and parsed.get("confidence", 0) > 0.6:
                pat = parsed["reusable_pattern"]
                memory_manager.distill_pattern(
                    description=pat.get("description", parsed.get("lesson", ""))[:300],
                    abstraction=pat.get("abstraction", "")[:300],
                    domain=pat.get("domain", "general"),
                    fitness_gain=genome.fitness if genome.fitness > 0 else 0.1,
                    genome_id=genome.id,
                )

        # Aggregate final reflection
        final = self._aggregate_reflections(reflections)
        return final

    def _parse_reflection(self, content: str) -> Dict[str, Any]:
        import json, re

        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                data = json.loads(m.group(0))
                data.setdefault("what_worked", content[:200])
                data.setdefault("what_failed", "")
                data.setdefault("lesson", content[:300])
                data.setdefault("reusable_pattern", {"description": content[:200], "abstraction": "", "domain": "general"})
                data.setdefault("confidence", 0.6)
                data.setdefault("novelty_score", 0.5)
                return data
            except Exception:
                pass

        return {
            "what_worked": content[:200],
            "what_failed": "",
            "lesson": content[:300],
            "reusable_pattern": {"description": content[:200], "abstraction": "", "domain": "general"},
            "confidence": 0.5,
            "novelty_score": 0.4,
        }

    def _aggregate_reflections(self, reflections: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not reflections:
            return {"lesson": "no reflection", "patterns": []}

        lessons = [r.get("lesson", "") for r in reflections]
        patterns = [r.get("reusable_pattern") for r in reflections if r.get("reusable_pattern")]
        avg_conf = sum(r.get("confidence", 0) for r in reflections) / len(reflections)
        avg_novelty = sum(r.get("novelty_score", 0) for r in reflections) / len(reflections)

        return {
            "lessons": lessons,
            "patterns": patterns,
            "avg_confidence": avg_conf,
            "avg_novelty": avg_novelty,
            "depths": len(reflections),
            "individual": reflections,
        }

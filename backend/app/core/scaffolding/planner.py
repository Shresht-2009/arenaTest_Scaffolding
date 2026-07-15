"""
Planner - Generates structured plans according to cognitive genome.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from ..cognitive_genome import CognitiveGenome
from ..memory.memory_manager import MemoryManager
from ..llm.groq_client import GroqClient, get_groq_client
from ..llm.prompt_optimizer import PromptOptimizer


class Planner:
    """Generates execution plans conditioned on genome."""

    def __init__(self, groq_client: Optional[GroqClient] = None, prompt_optimizer: Optional[PromptOptimizer] = None):
        self.groq = groq_client or get_groq_client()
        self.optimizer = prompt_optimizer or PromptOptimizer()

    def _build_phase_prompt(self, genome: CognitiveGenome, problem: str, memory_context: str, previous_steps: str) -> str:
        genome_fragment = genome.to_prompt_fragment()

        phase_instructions = f"""
You are in PLANNING phase.
Planning Depth: {genome.planning_depth}
Planning Horizon: {genome.planning_horizon}
Decomposition Style: {genome.decomposition_style.value}
Abstraction Level: {genome.abstraction_level:.2f}
Search Width: {genome.search_width}

Tasks:
1. Understand problem deeply - identify constraints, goals, edge cases.
2. Decompose using {genome.decomposition_style.value} style into {genome.planning_depth} levels.
3. Generate executable plan with {genome.planning_horizon} steps ahead.
4. Consider {genome.search_width} alternative approaches, then select best.
5. Output plan as numbered steps, each with objective, method, verification criterion.

Be concise, information-dense, actionable. Avoid verbosity.
Problem complexity: infer and state.

Return JSON with fields:
{{
  "understanding": "brief problem understanding",
  "decomposition": ["subproblem1", "subproblem2", ...],
  "plan_steps": ["step1", "step2", ...],
  "alternatives": ["alt1", "alt2"],
  "selected_approach": "why selected",
  "confidence": 0.0-1.0,
  "estimated_complexity": 0.0-1.0
}}
"""

        return self.optimizer.build_final_prompt(
            genome_fragment=genome_fragment,
            memory_context=memory_context,
            problem=problem,
            phase_instructions=phase_instructions,
            previous_steps=previous_steps,
        )

    async def generate_plan(
        self, genome: CognitiveGenome, problem: str, memory_manager: MemoryManager
    ) -> Dict[str, Any]:
        memory_context = memory_manager.retrieve_context_for_genome(genome, problem, max_tokens=1500)
        previous = memory_manager.working.get_context(last_n=3)

        prompt = self._build_phase_prompt(genome, problem, memory_context, previous)

        content, meta = await self.groq.complete(
            prompt=prompt,
            genome_id=genome.id,
            phase="plan",
            temperature=genome.temperature * 0.8,  # slightly more deterministic for planning
            max_tokens=min(genome.max_tokens, 1500),
            top_p=genome.top_p,
        )

        # Try to parse JSON, fallback to heuristic
        plan_data = self._parse_plan(content, problem)

        # Record in working memory
        memory_manager.add_reasoning_step(
            phase="Planning",
            content=content,
            tokens=meta.get("tokens_in", 0) + meta.get("tokens_out", 0),
            confidence=plan_data.get("confidence", 0.5),
            metadata={"meta": meta, "parsed": plan_data},
        )
        if plan_data.get("plan_steps"):
            memory_manager.set_plan(plan_data["plan_steps"])

        plan_data["_llm_meta"] = meta
        return plan_data

    def _parse_plan(self, content: str, problem: str) -> Dict[str, Any]:
        import json, re

        # Attempt JSON extraction
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                # Ensure required fields
                data.setdefault("understanding", content[:300])
                data.setdefault("decomposition", [problem])
                data.setdefault("plan_steps", [content])
                data.setdefault("alternatives", [])
                data.setdefault("confidence", 0.6)
                data.setdefault("estimated_complexity", 0.5)
                return data
            except Exception:
                pass

        # Fallback heuristic
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        steps = [l for l in lines if l[0].isdigit() or l.startswith("-")]
        if not steps:
            steps = lines[:5]

        return {
            "understanding": content[:400],
            "decomposition": [problem],
            "plan_steps": steps[:10],
            "alternatives": [],
            "selected_approach": steps[0] if steps else "direct",
            "confidence": 0.6,
            "estimated_complexity": 0.5,
        }

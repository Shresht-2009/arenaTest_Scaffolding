"""
Decomposer - Problem decomposition engine.
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from ..cognitive_genome import CognitiveGenome, DecompositionStyle
from ..memory.memory_manager import MemoryManager
from ..llm.groq_client import GroqClient, get_groq_client
from ..llm.prompt_optimizer import PromptOptimizer


class Decomposer:
    """Decomposes problems according to genome's decomposition style."""

    STYLE_PROMPTS = {
        DecompositionStyle.FUNCTIONAL: "Decompose by function: each subproblem is a distinct functional unit with clear I/O.",
        DecompositionStyle.TEMPORAL: "Decompose temporally: sequence of steps over time, dependencies in chronological order.",
        DecompositionStyle.CAUSAL: "Decompose causally: identify cause-effect chains, root causes, propagating effects.",
        DecompositionStyle.HIERARCHICAL: "Decompose hierarchically: high-level goal into mid-level objectives into low-level tasks.",
        DecompositionStyle.CONSTRAINT_BASED: "Decompose by constraints: each subproblem addresses a specific constraint cluster.",
        DecompositionStyle.FIRST_PRINCIPLES: "Decompose via first principles: reduce to fundamental axioms, then rebuild.",
    }

    def __init__(self, groq_client: Optional[GroqClient] = None, prompt_optimizer: Optional[PromptOptimizer] = None):
        self.groq = groq_client or get_groq_client()
        self.optimizer = prompt_optimizer or PromptOptimizer()

    async def decompose(
        self, genome: CognitiveGenome, problem: str, plan: Dict[str, Any], memory_manager: MemoryManager
    ) -> List[Dict[str, Any]]:
        memory_context = memory_manager.retrieve_context_for_genome(genome, problem, max_tokens=1000)
        previous = memory_manager.working.get_context(last_n=2)

        style_instruction = self.STYLE_PROMPTS.get(genome.decomposition_style, self.STYLE_PROMPTS[DecompositionStyle.HIERARCHICAL])

        genome_fragment = genome.to_prompt_fragment()

        phase_instructions = f"""
You are in DECOMPOSITION phase.
{style_instruction}
Planning Depth: {genome.planning_depth}
Search Width: {genome.search_width}
Exploration Factor: {genome.exploration_factor}

Given problem and existing plan, produce refined subproblems.

Existing plan steps:
{plan.get('plan_steps', [])}

Output JSON:
{{
  "subproblems": [
    {{"id": "sp1", "description": "...", "objective": "...", "dependencies": [], "estimated_tokens": 100, "complexity": 0.5}},
    ...
  ],
  "dependency_graph": [["sp1", "sp2"], ...],
  "critical_path": ["sp1", "sp2"],
  "confidence": 0.8
}}

Be precise and minimal. Each subproblem should be independently verifiable.
"""

        prompt = self.optimizer.build_final_prompt(
            genome_fragment=genome_fragment,
            memory_context=memory_context,
            problem=problem,
            phase_instructions=phase_instructions,
            previous_steps=previous,
        )

        content, meta = await self.groq.complete(
            prompt=prompt,
            genome_id=genome.id,
            phase="decompose",
            temperature=genome.temperature * 0.7,
            max_tokens=min(genome.max_tokens, 1200),
            top_p=genome.top_p,
        )

        subproblems = self._parse_decomposition(content, problem)

        memory_manager.add_reasoning_step(
            phase="Decomposition",
            content=content,
            tokens=meta.get("tokens_in", 0) + meta.get("tokens_out", 0),
            confidence=0.7,
            metadata={"subproblems": subproblems, "meta": meta},
        )

        return subproblems

    def _parse_decomposition(self, content: str, problem: str) -> List[Dict[str, Any]]:
        import json, re

        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                data = json.loads(m.group(0))
                if "subproblems" in data and isinstance(data["subproblems"], list):
                    return data["subproblems"][:10]
            except Exception:
                pass

        # Fallback: split problem into 2-3 heuristically
        sentences = re.split(r"[.!?]\s+", problem)
        if len(sentences) >= 3:
            return [
                {"id": f"sp{i+1}", "description": s.strip(), "objective": s.strip(), "dependencies": [], "complexity": 0.5}
                for i, s in enumerate(sentences[:3])
            ]
        return [
            {"id": "sp1", "description": problem, "objective": "Solve main problem", "dependencies": [], "complexity": 0.6}
        ]

"""
Prompt Optimizer - Token efficiency layer.

Implements:
- Recursive summarization
- Incremental context updates (diff-based)
- Duplicate elimination
- Abstraction
"""

from __future__ import annotations

from typing import List, Dict, Optional
import re


class PromptOptimizer:
    """
    Optimizes prompts before sending to Groq.
    Pure Python, no LLM calls.
    """

    def __init__(self, max_tokens: int = 6000):
        self.max_tokens = max_tokens
        self._last_context_hashes: Dict[str, int] = {}

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def deduplicate(self, text: str) -> str:
        """Remove duplicate lines / paragraphs."""
        lines = text.splitlines()
        seen = set()
        deduped = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                deduped.append(line)
                continue
            if stripped.lower() not in seen:
                seen.add(stripped.lower())
                deduped.append(line)
        return "\n".join(deduped)

    def recursive_summarize(self, text: str, target_tokens: int = 512) -> str:
        """
        Deterministic summarization without LLM:
        - Keep headings, first sentences of paragraphs, key bullet points
        - This is a fast approximation; LLM summarization is done separately when needed
        """
        if self.estimate_tokens(text) <= target_tokens:
            return text

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        kept = []
        tokens = 0
        for para in paragraphs:
            # Keep first sentence + keywords
            sentences = re.split(r"[.!?]\s+", para)
            if sentences:
                first = sentences[0][:200]
                kept.append(first)
                tokens += self.estimate_tokens(first)
                if tokens >= target_tokens:
                    break

        summary = "\n".join(kept)[: target_tokens * 4]
        return f"[SUMMARIZED to {target_tokens} tokens]\n{summary}"

    def incremental_update(self, old_context: str, new_context: str) -> str:
        """
        Compute diff-like update: only send changed parts.
        For simplicity, if overlap > 70%, send only new lines.
        """
        old_lines = set(old_context.splitlines())
        new_lines = new_context.splitlines()
        added = [l for l in new_lines if l not in old_lines]
        if len(added) / max(1, len(new_lines)) < 0.3:
            # Highly overlapping, send incremental
            return "[INCREMENTAL UPDATE]\n" + "\n".join(added)
        return new_context

    def abstract_reasoning(self, reasoning_steps: List[str]) -> str:
        """
        Abstract reasoning into higher-level pattern:
        - Replace specific numbers with <NUM>, variables with <VAR>
        - Extract structure
        """
        abstracted = []
        for step in reasoning_steps:
            # Simple abstraction rules
            s = re.sub(r"\b\d+\.?\d*\b", "<NUM>", step)
            s = re.sub(r"\b[A-Z][a-z]?\b", "<VAR>", s)
            # Keep if contains reasoning keywords
            if any(kw in s.lower() for kw in ["therefore", "because", "if", "then", "since", "implies", "hence"]):
                abstracted.append(s[:150])
        return "\n".join(abstracted[:10])

    def optimize(self, prompt: str, context: Optional[str] = None, genome_compression: float = 0.5) -> str:
        """
        Full optimization pipeline.
        """
        # Deduplicate
        optimized = self.deduplicate(prompt)

        # If context provided, merge with incremental logic
        if context:
            optimized = context + "\n\n" + optimized

        # If genome prefers high compression, apply summarization
        est = self.estimate_tokens(optimized)
        if est > self.max_tokens:
            target = int(self.max_tokens * (1.0 - genome_compression * 0.5))
            optimized = self.recursive_summarize(optimized, target_tokens=target)

        return optimized

    def build_final_prompt(
        self,
        genome_fragment: str,
        memory_context: str,
        problem: str,
        phase_instructions: str,
        previous_steps: str = "",
    ) -> str:
        """
        Compose final prompt from components with token budgeting.
        Priority: problem > genome > phase > memory > previous
        """
        # Budget allocation
        total_budget = self.max_tokens
        # Fixed allocation roughly: problem 20%, genome 15%, phase 25%, memory 25%, history 15%
        problem_budget = int(total_budget * 0.2)
        genome_budget = int(total_budget * 0.15)
        phase_budget = int(total_budget * 0.25)
        memory_budget = int(total_budget * 0.25)
        history_budget = total_budget - (problem_budget + genome_budget + phase_budget + memory_budget)

        def truncate(text: str, budget: int) -> str:
            if self.estimate_tokens(text) <= budget:
                return text
            return self.recursive_summarize(text, target_tokens=budget)

        parts = [
            f"## COGNITIVE GENOME\n{truncate(genome_fragment, genome_budget)}",
            f"## MEMORY CONTEXT\n{truncate(memory_context, memory_budget)}" if memory_context else "",
            f"## PROBLEM\n{truncate(problem, problem_budget)}",
            f"## PHASE: {phase_instructions[:50]}\n{truncate(phase_instructions, phase_budget)}",
            f"## PREVIOUS REASONING (compressed)\n{truncate(previous_steps, history_budget)}" if previous_steps else "",
        ]
        # Filter empty
        parts = [p for p in parts if p.strip()]
        final = "\n\n".join(parts)
        # Final deduplicate
        final = self.deduplicate(final)
        return final

"""
Verifier - Rigorous verification engine.

Performs multiple verification passes as dictated by genome.
Includes logical consistency, counterexample search, adversarial perturbation.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
from ..cognitive_genome import CognitiveGenome
from ..memory.memory_manager import MemoryManager
from ..llm.groq_client import GroqClient, get_groq_client
from ..llm.prompt_optimizer import PromptOptimizer
import re


class Verifier:
    """Verification scaffold."""

    def __init__(self, groq_client: Optional[GroqClient] = None, prompt_optimizer: Optional[PromptOptimizer] = None):
        self.groq = groq_client or get_groq_client()
        self.optimizer = prompt_optimizer or PromptOptimizer()

    async def verify(
        self,
        genome: CognitiveGenome,
        problem: str,
        solution: str,
        memory_manager: MemoryManager,
        adversarial_tests: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Perform verification_passes iterations of critique.
        Returns verification report with scores.
        """
        memory_context = memory_manager.retrieve_context_for_genome(genome, problem, max_tokens=1000)
        previous = memory_manager.working.get_context(last_n=2)

        genome_fragment = genome.to_prompt_fragment()

        all_reports = []
        current_solution = solution

        for pass_idx in range(genome.verification_passes):
            phase_instruction = f"""
You are in VERIFICATION phase - Pass {pass_idx+1}/{genome.verification_passes}
Verification Strictness: {genome.verification_strictness:.2f}
Critique Strength: {genome.critique_strength:.2f}
Confidence Threshold: {genome.confidence_threshold:.2f}

Problem: {problem[:800]}

Solution to verify:
{current_solution[:2000]}

Tasks:
1. Check logical consistency - are steps coherent?
2. Search for counterexamples or edge cases.
3. Validate against problem constraints.
4. Challenge hidden assumptions.
5. If adversarial tests provided, test robustness.

Adversarial context: {str(adversarial_tests)[:500] if adversarial_tests else "None"}

Output JSON:
{{
  "is_valid": true/false,
  "confidence": 0.0-1.0,
  "issues_found": ["issue1", ...],
  "counterexamples": ["example1", ...],
  "suggested_fixes": ["fix1", ...],
  "corrected_solution": "improved solution if needed, else original",
  "logical_consistency_score": 0.0-1.0,
  "robustness_score": 0.0-1.0
}}

Be ruthless but fair. High critique strength means find subtle flaws.
"""

            prompt = self.optimizer.build_final_prompt(
                genome_fragment=genome_fragment,
                memory_context=memory_context,
                problem=problem,
                phase_instructions=phase_instruction,
                previous_steps=previous,
            )

            content, meta = await self.groq.complete(
                prompt=prompt,
                genome_id=genome.id,
                phase="verify",
                temperature=genome.temperature * 0.5,  # more deterministic for verification
                max_tokens=min(genome.max_tokens, 1500),
                top_p=genome.top_p,
            )

            report = self._parse_verification(content, solution)
            report["_meta"] = meta
            report["pass"] = pass_idx + 1
            all_reports.append(report)

            # If solution corrected, use corrected for next pass
            if report.get("corrected_solution") and report["corrected_solution"] != current_solution:
                current_solution = report["corrected_solution"]

            # Early exit if high confidence and valid
            if report.get("is_valid") and report.get("confidence", 0) >= genome.confidence_threshold and pass_idx > 0:
                break

            memory_manager.add_reasoning_step(
                phase=f"Verification-Pass-{pass_idx+1}",
                content=content,
                tokens=meta.get("tokens_in", 0) + meta.get("tokens_out", 0),
                confidence=report.get("confidence", 0.5),
                metadata={"report": report},
            )

        # Aggregate
        final = self._aggregate_reports(all_reports, solution)
        return final

    def _parse_verification(self, content: str, original_solution: str) -> Dict[str, Any]:
        import json, re

        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                data = json.loads(m.group(0))
                data.setdefault("is_valid", True)
                data.setdefault("confidence", 0.6)
                data.setdefault("issues_found", [])
                data.setdefault("counterexamples", [])
                data.setdefault("suggested_fixes", [])
                data.setdefault("corrected_solution", original_solution)
                data.setdefault("logical_consistency_score", 0.7)
                data.setdefault("robustness_score", 0.6)
                return data
            except Exception:
                pass

        # Fallback heuristic: look for keywords
        lower = content.lower()
        is_valid = "invalid" not in lower and ("valid" in lower or "correct" in lower)
        confidence = 0.7 if is_valid else 0.4
        issues = []
        if "counterexample" in lower:
            # extract lines containing counterexample
            issues = [l for l in content.splitlines() if "counter" in l.lower()][:3]

        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "issues_found": issues,
            "counterexamples": [],
            "suggested_fixes": [],
            "corrected_solution": original_solution,
            "logical_consistency_score": 0.7 if is_valid else 0.4,
            "robustness_score": 0.6,
        }

    def _aggregate_reports(self, reports: List[Dict[str, Any]], original_solution: str) -> Dict[str, Any]:
        if not reports:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "issues_found": ["no verification performed"],
                "final_solution": original_solution,
                "avg_logical_consistency": 0.0,
                "avg_robustness": 0.0,
                "passes": 0,
            }

        # Average scores
        avg_conf = sum(r.get("confidence", 0) for r in reports) / len(reports)
        avg_logic = sum(r.get("logical_consistency_score", 0) for r in reports) / len(reports)
        avg_robust = sum(r.get("robustness_score", 0) for r in reports) / len(reports)
        all_valid = all(r.get("is_valid", False) for r in reports)
        all_issues = []
        for r in reports:
            all_issues.extend(r.get("issues_found", []))
        # Final solution is last corrected
        final_solution = reports[-1].get("corrected_solution", original_solution)

        return {
            "is_valid": all_valid,
            "confidence": avg_conf,
            "issues_found": list(set(all_issues))[:10],
            "final_solution": final_solution,
            "avg_logical_consistency": avg_logic,
            "avg_robustness": avg_robust,
            "passes": len(reports),
            "individual_reports": reports,
        }

    def deterministic_checks(self, problem: str, solution: str) -> Dict[str, float]:
        """
        Pure Python deterministic verifications that don't need LLM.
        - Checks for empty solution, length, basic sanity
        """
        scores = {}
        scores["non_empty"] = 1.0 if solution and len(solution.strip()) > 20 else 0.0
        scores["contains_reasoning"] = 1.0 if any(kw in solution.lower() for kw in ["therefore", "because", "since", "thus", "hence"]) else 0.3
        # Check if solution addresses problem keywords (simple overlap)
        prob_tokens = set(problem.lower().split())
        sol_tokens = set(solution.lower().split())
        overlap = len(prob_tokens & sol_tokens) / max(1, len(prob_tokens))
        scores["keyword_overlap"] = min(1.0, overlap * 2)
        scores["overall_deterministic"] = sum(scores.values()) / len(scores)
        return scores

"""
Full PIES Generators - Implements all 20 benchmark families.

Each generator is deterministic via seed and scales with difficulty 0..1.

For brevity, implementations use procedural generation with verifiers.
"""

from __future__ import annotations

import random
import math
import itertools
import re
import string
from typing import Dict, Any, List, Tuple, Callable

from .base import BaseBenchmarkGenerator, BenchmarkTask


# --- Utility helpers ---


def _check_exact_match(expected: str):
    def checker(attempted: str) -> Dict[str, Any]:
        exp_norm = expected.strip().lower()
        att_norm = attempted.strip().lower()
        correct = exp_norm in att_norm or att_norm in exp_norm
        return {
            "correct": correct,
            "score": 1.0 if correct else 0.0,
            "feedback": "Exact match found" if correct else f"Expected containing '{expected}'",
        }

    return checker


# --- 1. Graph Algorithms ---
class GraphAlgorithmsGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("graph_algorithms")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        n = self._scale(difficulty, 4, 12)
        p = 0.3 + difficulty * 0.4
        # Generate adjacency list
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    edges.append((i, j, rng.randint(1, 10)))

        problem_type = rng.choice(["shortest_path", "mst_weight", "connected_components", "cycle_detection"])

        if problem_type == "shortest_path":
            src, dst = 0, n - 1
            problem = f"Given undirected weighted graph with {n} nodes (0..{n-1}) and edges: {edges}. Find shortest path distance from {src} to {dst}. If no path, return -1."
            # Compute shortest path via Dijkstra (deterministic)
            solution = str(self._dijkstra(n, edges, src, dst))
            def checker(att):
                # Extract first integer from attempted
                import re
                m = re.search(r"-?\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number found"}
                try:
                    val = int(m.group(0))
                    correct = val == int(solution)
                    return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback": f"Expected {solution}, got {val}"}
                except Exception as e:
                    return {"correct": False, "score": 0.0, "feedback": str(e)}

        elif problem_type == "mst_weight":
            problem = f"Graph with {n} nodes and edges {edges}. Compute total weight of Minimum Spanning Tree (or MST forest if disconnected). Use Kruskal."
            sol = self._mst_weight(n, edges)
            solution = str(sol)

            def checker(att):
                import re
                m = re.search(r"-?\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                val = int(m.group(0))
                return {"correct": val == sol, "score": 1.0 if val == sol else 0.0, "feedback": f"Expected {sol}, got {val}"}

        elif problem_type == "connected_components":
            problem = f"Graph with {n} nodes edges {edges}. Count connected components."
            sol = self._connected_components(n, edges)
            solution = str(sol)

            def checker(att):
                import re
                m = re.search(r"\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                val = int(m.group(0))
                return {"correct": val == sol, "score": 1.0 if val == sol else 0.0, "feedback": f"Expected {sol}"}

        else:  # cycle_detection
            problem = f"Graph with {n} nodes edges {edges} (undirected). Does it contain a cycle? Answer YES/NO."
            sol = "YES" if self._has_cycle(n, edges) else "NO"
            solution = sol

            def checker(att):
                norm = att.strip().upper()
                correct = sol in norm
                return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback": f"Expected {sol}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"n": n, "edges": edges, "type": problem_type},
        )
        task.adversarial_variants = self.make_adversarial_variants(task)
        return task

    def _dijkstra(self, n, edges, src, dst):
        import heapq
        adj = {i: [] for i in range(n)}
        for u, v, w in edges:
            adj[u].append((v, w))
            adj[v].append((u, w))
        dist = [math.inf] * n
        dist[src] = 0
        pq = [(0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d != dist[u]:
                continue
            if u == dst:
                break
            for v, w in adj[u]:
                if dist[v] > d + w:
                    dist[v] = d + w
                    heapq.heappush(pq, (dist[v], v))
        return -1 if dist[dst] == math.inf else dist[dst]

    def _mst_weight(self, n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            parent[rb] = ra
            return True

        edges_sorted = sorted(edges, key=lambda e: e[2])
        total = 0
        for u, v, w in edges_sorted:
            if union(u, v):
                total += w
        return total

    def _connected_components(self, n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for u, v, _ in edges:
            union(u, v)
        roots = set(find(i) for i in range(n))
        return len(roots)

    def _has_cycle(self, n, edges):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return True
            parent[rb] = ra
            return False

        for u, v, _ in edges:
            if union(u, v):
                return True
        return False


# --- 2. Mathematics ---
class MathematicsGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("mathematics")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        kind = rng.choice(["linear", "quadratic", "sequence", "number_theory", "combinatorics"])

        if kind == "linear":
            a = rng.randint(2, 10)
            b = rng.randint(1, 20)
            c = rng.randint(1, 50)
            problem = f"Solve for x: {a}x + {b} = {c}. Provide integer or float."
            sol_val = (c - b) / a
            solution = str(sol_val)
            def checker(att):
                import re
                nums = re.findall(r"-?\d+\.?\d*", att)
                if not nums:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                try:
                    val = float(nums[0])
                    correct = abs(val - sol_val) < 1e-6
                    return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback": f"Expected {sol_val}"}
                except Exception as e:
                    return {"correct": False, "score": 0.0, "feedback": str(e)}

        elif kind == "quadratic":
            # (x - r1)(x - r2) = 0
            r1 = rng.randint(-5, 5)
            r2 = rng.randint(-5, 5)
            # expand: x^2 - (r1+r2)x + r1*r2
            s = r1 + r2
            p = r1 * r2
            problem = f"Solve quadratic: x^2 - {s}x + {p} = 0. List roots separated by comma."
            solution = f"{r1}, {r2}"
            def checker(att):
                import re
                nums = [int(x) for x in re.findall(r"-?\d+", att)]
                correct = set(nums) == {r1, r2} or sorted(nums) == sorted([r1, r2])
                return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback": f"Expected {r1}, {r2}"}

        elif kind == "sequence":
            start = rng.randint(1, 5)
            diff = rng.randint(2, 6)
            length = self._scale(difficulty, 4, 8)
            seq = [start + i * diff for i in range(length)]
            problem = f"Arithmetic sequence: {seq}. What is next term?"
            sol = seq[-1] + diff
            solution = str(sol)
            def checker(att):
                import re
                m = re.search(r"\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                return {"correct": int(m.group(0)) == sol, "score": 1.0 if int(m.group(0)) == sol else 0.0, "feedback": f"Expected {sol}"}

        elif kind == "number_theory":
            n = rng.randint(20, 100 + int(difficulty * 200))
            problem = f"Find number of divisors of {n} (including 1 and itself)."
            # count divisors
            cnt = sum(1 for i in range(1, int(math.sqrt(n)) + 1) if n % i == 0)
            # Adjust for squares
            # Actually recount properly
            cnt = 0
            for i in range(1, int(math.sqrt(n)) + 1):
                if n % i == 0:
                    cnt += 1
                    if i != n // i:
                        cnt += 1
            sol = cnt
            solution = str(sol)
            def checker(att):
                import re
                m = re.search(r"\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                return {"correct": int(m.group(0)) == sol, "score": 1.0 if int(m.group(0)) == sol else 0.0, "feedback": f"Expected {sol}"}

        else:  # combinatorics
            n = rng.randint(5, 7 + int(difficulty * 5))
            k = rng.randint(2, min(4, n - 1))
            problem = f"Compute C({n},{k}) = number of ways to choose {k} from {n}."
            sol = math.comb(n, k)
            solution = str(sol)
            def checker(att):
                import re
                m = re.search(r"\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                return {"correct": int(m.group(0)) == sol, "score": 1.0 if int(m.group(0)) == sol else 0.0, "feedback": f"Expected {sol}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"kind": kind},
        )
        task.adversarial_variants = self.make_adversarial_variants(task)
        return task


# --- 3. Formal Logic ---
class FormalLogicGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("formal_logic")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Generate syllogism or propositional logic
        propositions = ["P", "Q", "R", "S"]
        # Random formula
        # e.g., (P -> Q) and P therefore Q
        templates = [
            (["P -> Q", "P"], "Q", "Modus Ponens"),
            (["P -> Q", "not Q"], "not P", "Modus Tollens"),
            (["P or Q", "not P"], "Q", "Disjunctive Syllogism"),
            (["P and Q"], "P", "Conjunction Elimination"),
            (["not (P and Q)", "P"], "not Q", "De Morgan"),
        ]
        premise, conclusion, rule = rng.choice(templates)
        # Add difficulty: more premises
        extra = self._scale(difficulty, 0, 2)
        extra_premises = []
        for _ in range(extra):
            a, b = rng.sample(propositions, 2)
            extra_premises.append(f"{a} -> {b}")

        all_premises = premise + extra_premises
        problem = f"Given premises: {', '.join(all_premises)}. Does '{conclusion}' logically follow? Answer YES/NO and justify.\nRule hint: {rule}"
        solution = "YES"
        # Checker: look for YES
        def checker(att):
            norm = att.upper()
            # If premises are valid, answer YES; check if att contains YES and not NO as main answer
            # Simple
            if "YES" in norm[:100]:  # first 100 chars
                return {"correct": True, "score": 1.0, "feedback": "Valid inference recognized"}
            if "NO" in norm[:100]:
                return {"correct": False, "score": 0.0, "feedback": "Should be YES"}
            return {"correct": "YES" in norm, "score": 1.0 if "YES" in norm else 0.0, "feedback": "Look for YES"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"rule": rule, "premises": all_premises},
        )
        return task


# --- 4. Constraint Satisfaction ---
class ConstraintSatisfactionGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("constraint_satisfaction")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Generate simple CSP: e.g., map coloring or N-queens tiny or assignment
        n_vars = self._scale(difficulty, 3, 6)
        domain_size = self._scale(difficulty, 2, 4)
        vars = [f"X{i}" for i in range(n_vars)]
        # Random binary constraints: Xi != Xj or Xi < Xj etc.
        constraints = []
        for _ in range(rng.randint(n_vars - 1, n_vars * 2)):
            a, b = rng.sample(vars, 2)
            op = rng.choice(["!=", "<", ">"])
            constraints.append(f"{a} {op} {b}")

        problem = f"CSP: Variables {vars} each domain 0..{domain_size-1}. Constraints: {', '.join(constraints)}. Find assignment satisfying all or state UNSAT. Output assignment dict or UNSAT."
        # Brute force solve to get ground truth
        solution_dict = self._solve_csp(vars, domain_size, constraints)
        solution = str(solution_dict) if solution_dict else "UNSAT"

        def checker(att):
            att_upper = att.strip().upper()
            if solution_dict is None:
                return {"correct": "UNSAT" in att_upper, "score": 1.0 if "UNSAT" in att_upper else 0.0, "feedback": "Expected UNSAT"}
            # Try to parse assignment
            # Check if all constraints satisfied by attempted assignment extraction
            # Simplistic: look for numbers
            import re
            # Try eval if looks like dict
            try:
                # Find dict-like
                m = re.search(r"\{[^}]+\}", att)
                if m:
                    # crude parse
                    d = {}
                    pairs = re.findall(r"X(\d+)\s*[:=]\s*(\d+)", att)
                    for var_idx, val in pairs:
                        d[f"X{var_idx}"] = int(val)
                    if len(d) == n_vars and self._check_assignment(d, constraints):
                        return {"correct": True, "score": 1.0, "feedback": "Valid assignment"}
                    # also attempt to evaluate directly if matches vars
                    # fallback check token count overlap
            except Exception:
                pass
            # Check if attempted contains valid numbers
            return {"correct": False, "score": 0.2, "feedback": f"Expected {solution}, could not verify attempted, checking manually"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"vars": vars, "domain": domain_size, "constraints": constraints},
        )
        return task

    def _solve_csp(self, vars, domain_size, constraints):
        # Brute force
        for values in itertools.product(range(domain_size), repeat=len(vars)):
            assignment = dict(zip(vars, values))
            if self._check_assignment(assignment, constraints):
                return assignment
        return None

    def _check_assignment(self, assign, constraints):
        for c in constraints:
            # c like "X0 != X1" or "X0 < X1"
            parts = c.split()
            if len(parts) != 3:
                continue
            var_a, op, var_b = parts
            if var_a not in assign or var_b not in assign:
                continue
            a, b = assign[var_a], assign[var_b]
            if op == "!=" and not (a != b):
                return False
            if op == "<" and not (a < b):
                return False
            if op == ">" and not (a > b):
                return False
        return True


# --- 5. Optimization ---
class OptimizationGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("optimization")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        n = self._scale(difficulty, 4, 10)
        # Knapsack-like problem
        items = [(f"item{i}", rng.randint(1, 10), rng.randint(1, 20)) for i in range(n)]  # name, weight, value
        capacity = self._scale(difficulty, 10, 30)
        problem = f"Knapsack: capacity {capacity}. Items (name, weight, value): {items}. Maximize value. Return max value and selection."
        # Solve via DP
        max_val, selection = self._knapsack(items, capacity)
        solution = f"Max value {max_val}, selection {selection}"

        def checker(att):
            import re
            m = re.search(r"\d+", att)
            if not m:
                return {"correct": False, "score": 0.0, "feedback": "No number"}
            # Find all numbers, assume first large is max value? Heuristic
            nums = [int(x) for x in re.findall(r"\d+", att)]
            # Check if max_val in nums
            if max_val in nums:
                return {"correct": True, "score": 1.0, "feedback": f"Correct max value {max_val}"}
            # Partial credit: if close
            closest = min(nums, key=lambda x: abs(x - max_val)) if nums else None
            if closest and abs(closest - max_val) <= 2:
                return {"correct": False, "score": 0.5, "feedback": f"Close to {max_val}, got {closest}"}
            return {"correct": False, "score": 0.0, "feedback": f"Expected {max_val}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"items": items, "capacity": capacity, "max_val": max_val},
        )
        return task

    def _knapsack(self, items, capacity):
        n = len(items)
        dp = [[0] * (capacity + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            _, w, v = items[i - 1]
            for c in range(capacity + 1):
                if w <= c:
                    dp[i][c] = max(dp[i - 1][c], dp[i - 1][c - w] + v)
                else:
                    dp[i][c] = dp[i - 1][c]
        # backtrack
        c = capacity
        sel = []
        for i in range(n, 0, -1):
            if dp[i][c] != dp[i - 1][c]:
                sel.append(items[i - 1][0])
                c -= items[i - 1][1]
        return dp[n][capacity], sel


# --- 6. Planning ---
class PlanningGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("planning")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Blocks world / simple logistics
        num_blocks = self._scale(difficulty, 3, 6)
        blocks = [f"Block{chr(65+i)}" for i in range(num_blocks)]
        # Initial random stacks
        rng.shuffle(blocks)
        # Generate initial state: random stacking
        initial = []
        # Create 1-3 stacks
        num_stacks = rng.randint(1, 3)
        per_stack = [[] for _ in range(num_stacks)]
        for b in blocks:
            per_stack[rng.randint(0, num_stacks - 1)].append(b)
        for stack in per_stack:
            if stack:
                initial.append(" -> ".join(stack) + " (bottom->top)")

        goal_stack = blocks.copy()
        rng.shuffle(goal_stack)
        goal = " -> ".join(goal_stack)
        problem = f"Blocks world planning: Initial stacks: {initial}. Goal: stack all blocks as {goal} (bottom->top). Actions: pickup, putdown, stack, unstack. Find minimal plan steps. Output plan as list."
        # Solution: naive plan length estimate
        solution = f"Plan requires at least {num_blocks*2} moves. Example plan: unstack all to table then restack to {goal}"
        def checker(att):
            # Check if att contains enough steps and mentions blocks
            has_blocks = all(b in att for b in blocks[:2])
            steps = att.lower().count("stack") + att.lower().count("pick") + att.lower().count("move")
            correct = has_blocks and steps >= num_blocks
            return {"correct": correct, "score": 1.0 if correct else 0.3, "feedback": "Checks for block mentions and actions"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"blocks": blocks, "initial": initial, "goal": goal},
        )
        return task


# --- 7. Programming ---
class ProgrammingGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("programming")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        probs = [
            ("Write a function to reverse a string.", "def reverse(s): return s[::-1]", "reverse"),
            ("Write a function to check if a number is prime.", "def is_prime(n): return all(n%i!=0 for i in range(2,int(n**0.5)+1)) and n>1", "prime"),
            ("Write function to sum list.", "def sum_list(lst): return sum(lst)", "sum"),
            ("Write function to find max in list.", "def find_max(lst): return max(lst)", "max"),
            ("Write function factorial.", "def fact(n): return 1 if n<=1 else n*fact(n-1)", "factorial"),
        ]
        if difficulty > 0.6:
            probs.extend(
                [
                    ("Write function to merge two sorted lists.", "def merge(a,b):...", "merge"),
                    ("Write function to compute Fibonacci n-th.", "def fib(n):...", "fib"),
                    ("Write function to binary search.", "def bsearch(arr, x):...", "binary"),
                ]
            )
        problem_desc, sol_code, keyword = rng.choice(probs)
        problem = f"{problem_desc} Input/Output example should be included. Language: Python. Output only code."
        solution = sol_code

        def checker(att):
            # Check if attempt contains function def and keyword
            has_def = "def " in att
            has_keyword = keyword.lower() in att.lower()
            correct = has_def and has_keyword
            return {"correct": correct, "score": 1.0 if correct else 0.2, "feedback": f"Contains def and keyword {keyword}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"keyword": keyword},
        )
        return task


# --- 8. Debugging ---
class DebuggingGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("debugging")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        buggy_codes = [
            ("def sum_list(lst):\n    total = 0\n    for i in range(len(lst)):\n        total += lst[i+1]\n    return total", "Off-by-one, should be lst[i]", "IndexError"),
            ("def is_even(n):\n    if n % 2 = 0:\n        return True", "Use == not =", "Syntax"),
            ("def factorial(n):\n    if n == 0:\n        return 0\n    else:\n        return n * factorial(n-1)", "Base case should return 1", "Logic"),
            ("def find_max(lst):\n    max_val = 0\n    for x in lst:\n        if x > max_val:\n            max_val = x\n    return max_val", "Fails for negative list, should start with lst[0]", "Edge case"),
        ]
        code, explanation, err_type = rng.choice(buggy_codes)
        problem = f"Debug this Python code:\n```python\n{code}\n```\nIdentify bug type ({err_type}) and provide corrected code."
        solution = explanation

        def checker(att):
            # Check if explanation mentions key fix words
            has_fix = any(w in att.lower() for w in ["index", "==", "1", "lst[0]", "off-by-one", "base"])
            return {"correct": has_fix, "score": 1.0 if has_fix else 0.3, "feedback": f"Expected fix related to {explanation}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"error_type": err_type},
        )
        return task


# --- 9. Compression ---
class CompressionGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("compression")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Generate repetitive text to be compressed
        vocab = ["reason", "plan", "verify", "execute", "reflect", "genome", "evolution", "memory"]
        length = self._scale(difficulty, 20, 80)
        text = " ".join(rng.choice(vocab) for _ in range(length))
        # Add redundancy
        redundant = text + " " + text[: len(text) // 2]
        problem = f"Compress the following text preserving meaning, target 50% size. Text: '{redundant}'. Output compressed version then compression ratio."
        # Solution: deterministic compressed version (unique words)
        unique = []
        seen = set()
        for w in redundant.split():
            if w not in seen:
                seen.add(w)
                unique.append(w)
        compressed = " ".join(unique)
        solution = compressed

        def checker(att):
            # Check ratio and coverage
            words_in = set(redundant.split())
            words_out = set(att.split())
            coverage = len(words_in & words_out) / len(words_in) if words_in else 0
            # Compressed should be shorter
            shorter = len(att) < len(redundant)
            score = coverage * 0.7 + (0.3 if shorter else 0)
            return {"correct": score > 0.7, "score": min(1.0, score), "feedback": f"Coverage {coverage:.2f}, shorter {shorter}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"original_len": len(redundant)},
        )
        return task


# --- 10. Scientific Reasoning ---
class ScientificReasoningGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("scientific_reasoning")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        scenarios = [
            ("A plant grows faster in sunlight vs darkness. Design experiment to test light effect, control variables.", "Controlled experiment with light as independent variable, growth as dependent, control water, soil, etc.", "biology"),
            ("Temperature affects reaction rate. How to test?", "Vary temperature, measure rate, keep concentration constant.", "chemistry"),
            ("Object falls: does mass affect fall time in vacuum? Form hypothesis and test.", "Hypothesis: mass independent in vacuum. Test in vacuum chamber.", "physics"),
        ]
        scenario, sol, domain = rng.choice(scenarios)
        problem = f"Scientific reasoning ({domain}): {scenario} Provide hypothesis, independent/dependent variables, controls, procedure."
        solution = sol

        def checker(att):
            has_hyp = "hypothesis" in att.lower() or "hypoth" in att.lower()
            has_iv = "independent" in att.lower() or "variable" in att.lower()
            has_control = "control" in att.lower()
            score = (has_hyp + has_iv + has_control) / 3
            return {"correct": score >= 0.66, "score": score, "feedback": "Checks for hypothesis, variables, controls"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"domain": domain},
        )
        return task


# --- 11. Pattern Recognition ---
class PatternRecognitionGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("pattern_recognition")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        pattern_type = rng.choice(["arithmetic", "geometric", "alternating", "prime"])
        if pattern_type == "arithmetic":
            start = rng.randint(1, 10)
            diff = rng.randint(2, 5)
            seq = [start + i * diff for i in range(5)]
            next_val = seq[-1] + diff
            problem = f"Find next in pattern: {seq} -> ?"
            solution = str(next_val)
        elif pattern_type == "geometric":
            start = rng.randint(2, 4)
            ratio = rng.randint(2, 3)
            seq = [start * (ratio**i) for i in range(5)]
            next_val = seq[-1] * ratio
            problem = f"Find next in geometric pattern: {seq}"
            solution = str(next_val)
        elif pattern_type == "alternating":
            seq = []
            for i in range(5):
                seq.append(rng.randint(1, 10) if i % 2 == 0 else rng.randint(20, 30))
            # Pattern: low, high, low, high...
            next_val = rng.randint(1, 10)  # low
            problem = f"Pattern with alternating low(1-10) high(20-30): {seq}. Next?"
            solution = f"Low number 1-10, e.g. {next_val}"
            def checker(att):
                import re
                m = re.search(r"\d+", att)
                if not m:
                    return {"correct": False, "score": 0.0, "feedback": "No number"}
                val = int(m.group(0))
                correct = 1 <= val <= 10
                return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback": "Expected low 1-10"}
            task = BenchmarkTask(
                family=self.family_name,
                id=f"{self.family_name}-{seed}-{difficulty:.2f}",
                difficulty=difficulty,
                seed=seed,
                problem=problem,
                solution=solution,
                checker=checker,
                metadata={"pattern": pattern_type, "seq": seq},
            )
            return task
        else:  # prime
            primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
            idx = rng.randint(0, 5)
            seq = primes[idx : idx + 4]
            next_val = primes[idx + 4]
            problem = f"Prime pattern: {seq}. Next prime?"
            solution = str(next_val)

        def checker(att):
            import re
            m = re.search(r"\d+", att)
            if not m:
                return {"correct": False, "score": 0.0, "feedback": "No number"}
            try:
                return {"correct": int(m.group(0)) == int(next_val) if isinstance(next_val, int) else True, "score": 1.0 if int(m.group(0)) == next_val else 0.0, "feedback": f"Expected {next_val}"}
            except Exception:
                return {"correct": False, "score": 0.0, "feedback": f"Expected {next_val}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"pattern": pattern_type, "seq": seq},
        )
        return task


# --- 12. Information Reconstruction ---
class InformationReconstructionGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("information_reconstruction")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        original = "".join(rng.choice(string.ascii_lowercase) for _ in range(self._scale(difficulty, 20, 50)))
        # Create fragments with overlaps (like genome assembly)
        fragments = []
        fragment_len = 10
        step = 5
        for i in range(0, len(original) - fragment_len + 1, step):
            fragments.append(original[i : i + fragment_len])
        rng.shuffle(fragments)
        problem = f"Reconstruct original string from overlapping fragments (overlap >=5): {fragments}. Original length {len(original)}. Reconstruct."
        solution = original

        def checker(att):
            # Check if att contains original or close
            att_clean = "".join(c for c in att.lower() if c.isalpha())
            # For reconstruction task, check if original substring present or edit distance low?
            # Simplified: if original equals att after cleaning and stripping
            if original in att or att_clean == original:
                return {"correct": True, "score": 1.0, "feedback": "Exact reconstruction"}
            # Compute longest common substring length heuristic
            # Check if most fragments covered
            coverage = sum(1 for f in fragments if f in att) / len(fragments) if fragments else 0
            return {"correct": coverage > 0.8, "score": coverage, "feedback": f"Coverage {coverage:.2f}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"fragments": fragments, "original_len": len(original)},
        )
        return task


# --- 13. Scheduling ---
class SchedulingGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("scheduling")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        n_tasks = self._scale(difficulty, 4, 8)
        tasks = []
        for i in range(n_tasks):
            duration = rng.randint(1, 5)
            deadline = rng.randint(duration, duration + 10 + int(difficulty * 10))
            tasks.append((f"T{i}", duration, deadline))
        problem = f"Scheduling: tasks (name, duration, deadline): {tasks}. Single machine. Minimize max lateness? Provide schedule order and max lateness. Use EDF (Earliest Deadline First) is optimal for minimizing max lateness."
        # EDF schedule
        sorted_tasks = sorted(tasks, key=lambda x: x[2])
        time = 0
        max_lateness = 0
        for name, dur, dead in sorted_tasks:
            time += dur
            lateness = max(0, time - dead)
            max_lateness = max(max_lateness, lateness)
        solution = f"Order { [t[0] for t in sorted_tasks] }, max lateness {max_lateness}"

        def checker(att):
            import re
            # Check if order mentions tasks and max lateness close
            has_tasks = all(t[0] in att for t in tasks[:2])
            nums = [int(x) for x in re.findall(r"\d+", att)]
            contains_lateness = max_lateness in nums if nums else False
            score = (0.5 if has_tasks else 0) + (0.5 if contains_lateness else 0)
            return {"correct": score >= 0.8, "score": score, "feedback": f"Expected lateness {max_lateness}, order {sorted_tasks}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"tasks": tasks, "max_lateness": max_lateness},
        )
        return task


# --- 14. Causal Inference ---
class CausalInferenceGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("causal_inference")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Simple causal graph
        variables = ["A", "B", "C", "D"]
        # Random DAG
        edges = []
        for i in range(len(variables)):
            for j in range(i + 1, len(variables)):
                if rng.random() < 0.5:
                    edges.append((variables[i], variables[j]))
        problem = f"Causal graph DAG with variables {variables} and edges {edges} (A->B means A causes B). Question: If we intervene on {variables[0]}, which variables are affected? Use do-calculus, consider causal paths."
        # Affected = descendants
        # Compute descendants via BFS
        adj = {v: [] for v in variables}
        for u, v in edges:
            adj[u].append(v)
        # BFS from first var
        start = variables[0]
        visited = set()
        stack = [start]
        while stack:
            cur = stack.pop()
            for nb in adj[cur]:
                if nb not in visited and nb != start:
                    visited.add(nb)
                    stack.append(nb)
        solution = f"Affected: {visited} via causal paths from {start}"

        def checker(att):
            # Check if att mentions affected vars
            correct_vars = visited
            # score based on overlap
            mentioned = sum(1 for v in correct_vars if v in att)
            score = mentioned / len(correct_vars) if correct_vars else (1.0 if "none" in att.lower() else 0.0)
            return {"correct": score >= 0.7, "score": score, "feedback": f"Expected affected {correct_vars}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"edges": edges, "affected": list(visited)},
        )
        return task


# --- 15. Abstract Reasoning ---
class AbstractReasoningGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("abstract_reasoning")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Raven-like matrices but symbolic
        # Pattern: shape, color, size transformations
        shapes = ["circle", "square", "triangle"]
        colors = ["red", "blue", "green"]
        sizes = ["small", "medium", "large"]
        # Generate 2x2 matrix with pattern
        # Row-wise: shape constant, color changes
        r1 = f"{rng.choice(shapes)} {colors[0]} {sizes[0]}"
        r2 = f"{rng.choice(shapes)} {colors[1]} {sizes[0]}"
        r3 = f"{rng.choice(shapes)} {colors[0]} {sizes[1]}"
        # Pattern: row col influences? Expect second color for row2?
        # Simplified: missing should be color[1] size[1] with new shape
        missing_color = colors[1]
        missing_size = sizes[1]
        missing_shape = rng.choice(shapes)
        problem = f"Abstract matrix: Row1: {r1} | {r2} \nRow2: {r3} | ?. Rule: Row1 color progresses {colors[0]}->{colors[1]}, Row2 size? Determine missing element (shape color size). Explain rule."
        solution = f"{missing_shape} {missing_color} {missing_size}"

        def checker(att):
            has_color = missing_color in att.lower()
            has_size = missing_size in att.lower()
            score = (1 if has_color else 0) * 0.5 + (1 if has_size else 0) * 0.5
            return {"correct": score >= 0.5, "score": score, "feedback": f"Expected {missing_color} {missing_size}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"missing": solution},
        )
        return task


# --- 16. Counterfactual Reasoning ---
class CounterfactualReasoningGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("counterfactual_reasoning")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        base_facts = [
            "If it rains, the ground gets wet. It rained, so ground is wet.",
            "If you study hard, you pass. John studied hard and passed.",
            "If temperature >100C, water boils. Water did not boil, so temperature <=100C.",
        ]
        fact = rng.choice(base_facts)
        counterfactuals = [
            "What if it had not rained?",
            "What if John had not studied?",
            "What if water had boiled?",
        ]
        q = rng.choice(counterfactuals)
        problem = f"Given: {fact}. Counterfactual: {q} Evaluate counterfactual truth and provide reasoning using possible worlds."
        solution = f"Counterfactual analysis: In nearest possible world where antecedent false, consequent might be false, etc."

        def checker(att):
            has_counter = "possible world" in att.lower() or "counterfactual" in att.lower() or "if" in att.lower()
            length_ok = len(att) > 50
            score = (1 if has_counter else 0.5) * (1 if length_ok else 0.5)
            return {"correct": score >= 0.5, "score": min(1.0, score + 0.2), "feedback": "Checks for counterfactual reasoning terms"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"fact": fact},
        )
        return task


# --- 17. Strategic Games ---
class StrategicGamesGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("strategic_games")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        game_type = rng.choice(["prisoner", "nim", "tic_tac_toe"])
        if game_type == "prisoner":
            problem = "Prisoner's Dilemma: Payoff matrix: Cooperate/Cooperate = (3,3), Cooperate/Defect = (0,5), Defect/Cooperate = (5,0), Defect/Defect=(1,1). What is Nash Equilibrium? What is optimal strategy in iterated version with Tit-for-Tat?"
            solution = "Nash Equilibrium is Defect/Defect (1,1). Iterated optimal is Tit-for-Tat cooperation."
            def checker(att):
                has_nash = "defect" in att.lower() and "nash" in att.lower()
                return {"correct": has_nash, "score": 0.8 if has_nash else 0.3, "feedback": "Check Nash" }
        elif game_type == "nim":
            piles = [rng.randint(1, 5) for _ in range(self._scale(difficulty, 2, 4))]
            xor = 0
            for p in piles:
                xor ^= p
            problem = f"Nim game piles {piles}. Is this N-position (winning for next player) or P-position? If winning, give winning move."
            winning = xor != 0
            solution = f"{'N-position winning' if winning else 'P-position losing'} xor={xor}"
            def checker(att):
                has_xor = str(xor) in att or ("winning" in att.lower() if winning else "losing" in att.lower())
                return {"correct": bool(has_xor), "score": 1.0 if has_xor else 0.4, "feedback": f"xor {xor}" }
        else:
            problem = "Tic-Tac-Toe board: X|O| \n X| | \n  | |O. It's X's turn. Find optimal move using minimax to win or draw."
            solution = "X should play middle-right or optimal blocking."
            def checker(att):
                return {"correct": len(att) > 20, "score": 0.7, "feedback": "Checks reasoning"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"game": game_type},
        )
        return task


# --- 18. Algorithm Design ---
class AlgorithmDesignGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("algorithm_design")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        problems = [
            ("Design O(n log n) algorithm to find closest pair of points in 2D.", "Divide and conquer.", "closest_pair"),
            ("Design O(n) algorithm to find majority element if exists.", "Boyer-Moore voting.", "majority"),
            ("Design algorithm to detect cycle in linked list O(1) space.", "Floyd's cycle detection.", "cycle"),
            ("Design O(n) algorithm to find max subarray sum.", "Kadane's algorithm.", "max_subarray"),
        ]
        prob_desc, sol_hint, keyword = rng.choice(problems)
        problem = f"{prob_desc} Provide pseudocode, time/space complexity analysis, correctness proof sketch."
        solution = sol_hint

        def checker(att):
            has_complexity = "o(" in att.lower() and ("n log n" in att.lower() or "n)" in att.lower() or "log" in att.lower())
            has_keyword = keyword in att.lower() or any(k in att.lower() for k in ["divide", "conquer", "voting", "floyd", "kadane"])
            score = (0.5 if has_complexity else 0) + (0.5 if has_keyword else 0)
            return {"correct": score >= 0.5, "score": score, "feedback": f"Expected {sol_hint}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"keyword": keyword},
        )
        return task


# --- 19. Multi-step Reasoning ---
class MultiStepReasoningGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("multi_step_reasoning")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        steps = self._scale(difficulty, 3, 6)
        # Chain of logic
        facts = []
        current = rng.randint(1, 10)
        facts.append(f"Initial value A={current}")
        ops = []
        for i in range(steps):
            op = rng.choice(["+", "-", "*"])
            val = rng.randint(1, 5)
            ops.append((op, val))
            if op == "+":
                current += val
                facts.append(f"After step {i+1}: Add {val}, now {current}")
            elif op == "-":
                current -= val
                facts.append(f"After step {i+1}: Subtract {val}, now {current}")
            else:
                current *= val
                facts.append(f"After step {i+1}: Multiply by {val}, now {current}")

        problem = f"Multi-step reasoning chain: {'; '.join(facts[:2])}. Steps: {ops}. What is final value? Show each step."
        solution = str(current)

        def checker(att):
            import re
            nums = [int(x) for x in re.findall(r"-?\d+", att)]
            correct = current in nums
            return {"correct": correct, "score": 1.0 if correct else 0.0, "feedback": f"Expected {current}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"final": current, "steps": ops},
        )
        return task


# --- 20. Knowledge Integration ---
class KnowledgeIntegrationGenerator(BaseBenchmarkGenerator):
    def __init__(self):
        super().__init__("knowledge_integration")

    def generate(self, seed: int, difficulty: float = 0.5) -> BenchmarkTask:
        rng = self._rng(seed)
        # Require integrating two domains
        combos = [
            ("Use graph theory to model social network and apply logic to infer influence.", "Model as directed graph, influence spreads via BFS.", "graph+logic"),
            ("Combine probability and optimization: maximize expected value.", "Expected value = sum p_i * v_i, optimize via DP.", "prob+optim"),
            ("Integrate scheduling and constraint satisfaction for resource allocation.", "CSP with scheduling constraints solved via backtracking.", "sched+csp"),
        ]
        desc, sol, combo = rng.choice(combos)
        problem = f"Knowledge integration ({combo}): {desc} Provide integrated solution explaining how concepts from both domains interact."
        solution = sol

        def checker(att):
            # Check if mentions both domains
            words = att.lower()
            has_both = sum(1 for k in combo.split("+") if k.lower()[:4] in words) >= 1 or len(att) > 100
            return {"correct": len(att) > 80, "score": 0.7 if has_both else 0.4, "feedback": f"Expected integration of {combo}"}

        task = BenchmarkTask(
            family=self.family_name,
            id=f"{self.family_name}-{seed}-{difficulty:.2f}",
            difficulty=difficulty,
            seed=seed,
            problem=problem,
            solution=solution,
            checker=checker,
            metadata={"combo": combo},
        )
        return task


# Registry for easy lookup
GENERATOR_REGISTRY = {
    "graph_algorithms": GraphAlgorithmsGenerator,
    "mathematics": MathematicsGenerator,
    "formal_logic": FormalLogicGenerator,
    "constraint_satisfaction": ConstraintSatisfactionGenerator,
    "optimization": OptimizationGenerator,
    "planning": PlanningGenerator,
    "programming": ProgrammingGenerator,
    "debugging": DebuggingGenerator,
    "compression": CompressionGenerator,
    "scientific_reasoning": ScientificReasoningGenerator,
    "pattern_recognition": PatternRecognitionGenerator,
    "information_reconstruction": InformationReconstructionGenerator,
    "scheduling": SchedulingGenerator,
    "causal_inference": CausalInferenceGenerator,
    "abstract_reasoning": AbstractReasoningGenerator,
    "counterfactual_reasoning": CounterfactualReasoningGenerator,
    "strategic_games": StrategicGamesGenerator,
    "algorithm_design": AlgorithmDesignGenerator,
    "multi_step_reasoning": MultiStepReasoningGenerator,
    "knowledge_integration": KnowledgeIntegrationGenerator,
}

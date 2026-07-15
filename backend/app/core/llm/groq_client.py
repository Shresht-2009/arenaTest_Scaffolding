"""
GroqCloud Client - Wrapper for GPT-OSS-120B.

Handles:
- Async requests with retries, backoff
- Token counting, cost estimation
- Request throttling respecting Groq limits
- Caching integration
- Streaming support for real-time dashboard

Uses Groq SDK (openai-compatible). If SDK not available, fallback to httpx.
"""

from __future__ import annotations

import asyncio
import time
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
import json
import os

from ...config import get_config
from .cache import ResponseCache, PromptCache

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq  # type: ignore

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    AsyncGroq = None  # type: ignore

# Fallback mock client for offline development / testing
class MockResponse:
    def __init__(self, content: str, tokens: int = 100):
        self.content = content
        self.tokens = tokens


class GroqClient:
    """
    Async Groq client for GPT-OSS-120B.
    Single instance should be reused.
    """

    def __init__(self):
        self.config = get_config().groq
        self.token_config = get_config().token_opt
        self.client: Optional[Any] = None
        self.response_cache = ResponseCache(max_size=300)
        self.prompt_cache = PromptCache()
        self.request_count = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.total_latency_ms = 0.0
        self._semaphore = asyncio.Semaphore(self.config.concurrent_requests_limit)
        self._last_request_times: List[float] = []
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if GROQ_AVAILABLE and self.config.api_key:
            try:
                self.client = AsyncGroq(api_key=self.config.api_key)
                logger.info(f"Initialized Groq client with model {self.config.model}")
            except Exception as e:
                logger.warning(f"Failed to init Groq client: {e}, using mock")
                self.client = None
        else:
            if not GROQ_AVAILABLE:
                logger.warning("groq package not installed, using mock client")
            if not self.config.api_key:
                logger.warning("GROQ_API_KEY not set, using mock client for development")
            self.client = None
        self._initialized = True

    def _check_rate_limit(self):
        """Simple sliding window rate limiting."""
        now = time.time()
        # Keep only requests in last 60s
        self._last_request_times = [t for t in self._last_request_times if now - t < 60]
        if len(self._last_request_times) >= self.config.requests_per_minute_limit:
            sleep_time = 60 - (now - self._last_request_times[0])
            return max(0, sleep_time)
        return 0

    def _record_request(self):
        self._last_request_times.append(time.time())
        self.request_count += 1

    def estimate_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)

    def estimate_cost(self, tokens_in: int, tokens_out: int) -> float:
        # Approximate Groq pricing for 120B - placeholder $0.15 / 1M input, $0.75 / 1M output
        return (tokens_in * 0.15 + tokens_out * 0.75) / 1_000_000

    async def _mock_completion(self, prompt: str, genome_id: str = "mock", phase: str = "general") -> Tuple[str, Dict[str, Any]]:
        """Deterministic mock for offline testing - simulates reasoning."""
        await asyncio.sleep(0.3)  # simulate latency
        # Generate mock reasoning based on phase
        mock_templates = {
            "understand": f"[MOCK Understand] Problem analyzed. Key constraints identified. Genome {genome_id} applied hierarchical decomposition.",
            "decompose": f"[MOCK Decompose] Problem split into 3 subproblems: (1) core logic, (2) edge cases, (3) verification. Using search width 3.",
            "plan": f"[MOCK Plan] Plan: Step1 Understand, Step2 Decompose, Step3 Execute with verification passes. Confidence 0.78.",
            "execute": f"[MOCK Execute] Executing plan. Intermediate result computed. Tokens used ~ {len(prompt)//4}. Solution draft produced.",
            "verify": f"[MOCK Verify] Verification passed: logical consistency checked, counterexample search completed, no flaws found.",
            "challenge": f"[MOCK Challenge] Assumptions challenged: alternative interpretation considered, robustness tested.",
            "compress": f"[MOCK Compress] Reasoning compressed from {len(prompt)} chars to {len(prompt)//2} chars. Ratio 0.5.",
            "reflect": f"[MOCK Reflect] Reflection: planning depth adequate, verification strictness effective, exploration balanced.",
        }
        content = mock_templates.get(phase.lower(), f"[MOCK {phase}] Reasoning completed for genome {genome_id}. Problem length {len(prompt)}")
        tokens_in = self.estimate_tokens(prompt)
        tokens_out = self.estimate_tokens(content)
        return content, {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": 300,
            "mock": True,
        }

    async def complete(
        self,
        prompt: str,
        genome_id: str = "default",
        phase: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        use_cache: bool = True,
        stream: bool = False,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Main completion method.
        Returns (content, metadata).
        """
        await self.initialize()

        # Cache check
        if use_cache and self.token_config.enable_response_caching:
            cache_key = self.response_cache.make_key(genome_id, prompt[:200], phase, prompt)
            cached = self.response_cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for genome {genome_id} phase {phase}")
                tokens_in = self.estimate_tokens(prompt)
                tokens_out = self.estimate_tokens(cached)
                return cached, {
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "latency_ms": 0,
                    "cached": True,
                    "cost": self.estimate_cost(tokens_in, tokens_out),
                }

        # Rate limit check
        wait = self._check_rate_limit()
        if wait > 0:
            logger.info(f"Rate limit hit, waiting {wait:.1f}s")
            await asyncio.sleep(wait)

        async with self._semaphore:
            start = time.time()
            self._record_request()

            # Mock path
            if self.client is None:
                content, meta = await self._mock_completion(prompt, genome_id, phase)
                latency = (time.time() - start) * 1000
                meta["latency_ms"] = latency
                self.total_tokens_in += meta["tokens_in"]
                self.total_tokens_out += meta["tokens_out"]
                self.total_latency_ms += latency
                if use_cache:
                    cache_key = self.response_cache.make_key(genome_id, prompt[:200], phase, prompt)
                    self.response_cache.set(cache_key, content)
                return content, meta

            # Real Groq path with retries
            last_error = None
            for attempt in range(self.config.max_retries):
                try:
                    response = await self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                    )
                    content = response.choices[0].message.content or ""
                    tokens_in = getattr(response.usage, "prompt_tokens", self.estimate_tokens(prompt)) if hasattr(response, "usage") else self.estimate_tokens(prompt)
                    tokens_out = getattr(response.usage, "completion_tokens", self.estimate_tokens(content)) if hasattr(response, "usage") else self.estimate_tokens(content)
                    latency = (time.time() - start) * 1000

                    self.total_tokens_in += tokens_in
                    self.total_tokens_out += tokens_out
                    self.total_latency_ms += latency

                    meta = {
                        "tokens_in": tokens_in,
                        "tokens_out": tokens_out,
                        "latency_ms": latency,
                        "cached": False,
                        "cost": self.estimate_cost(tokens_in, tokens_out),
                        "model": self.config.model,
                        "attempt": attempt + 1,
                    }

                    if use_cache:
                        cache_key = self.response_cache.make_key(genome_id, prompt[:200], phase, prompt)
                        self.response_cache.set(cache_key, content)

                    return content, meta

                except Exception as e:
                    last_error = e
                    logger.warning(f"Groq call failed attempt {attempt+1}: {e}")
                    if attempt < self.config.max_retries - 1:
                        backoff = (2**attempt) + 0.5
                        await asyncio.sleep(backoff)
                    else:
                        break

            # After retries failed, fallback to mock to keep system alive
            logger.error(f"All retries failed, fallback to mock. Last error: {last_error}")
            content, meta = await self._mock_completion(prompt, genome_id, phase)
            meta["error"] = str(last_error)
            meta["fallback_mock"] = True
            return content, meta

    async def stream_complete(
        self,
        prompt: str,
        genome_id: str = "default",
        phase: str = "general",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[Tuple[str, bool], None]:
        """
        Streaming completion, yields chunks.
        Last yield has bool True indicating done.
        """
        await self.initialize()

        if self.client is None:
            # Mock streaming
            content, _ = await self._mock_completion(prompt, genome_id, phase)
            # Stream word by word
            words = content.split()
            for i, w in enumerate(words):
                await asyncio.sleep(0.05)
                yield w + " ", (i == len(words) - 1)
            return

        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield delta, False
            yield "", True
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            # Fallback: single complete then stream mock-wise
            content, _ = await self.complete(prompt, genome_id, phase, temperature, max_tokens, use_cache=False)
            for w in content.split():
                await asyncio.sleep(0.02)
                yield w + " ", False
            yield "", True

    def stats(self) -> Dict[str, Any]:
        total_tokens = self.total_tokens_in + self.total_tokens_out
        return {
            "requests": self.request_count,
            "tokens_in": self.total_tokens_in,
            "tokens_out": self.total_tokens_out,
            "total_tokens": total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.total_latency_ms / self.request_count if self.request_count > 0 else 0,
            "estimated_cost": self.estimate_cost(self.total_tokens_in, self.total_tokens_out),
            "cache": self.response_cache.stats(),
            "prompt_cache": self.prompt_cache.stats(),
        }

    def reset_stats(self):
        self.request_count = 0
        self.total_tokens_in = 0
        self.total_tokens_out = 0
        self.total_latency_ms = 0


# Global singleton
_client_instance: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GroqClient()
    return _client_instance

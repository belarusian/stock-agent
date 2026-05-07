"""
Chart analyzer - sends screenshots to LLM and returns free-form text analysis.

Uses the local vision-capable LLM (qwen3 at :8080) or any OpenAI-compatible
endpoint to analyze stock charts from screenshots.

No JSON parsing — just clean free-form text output with the LLM's reasoning.
"""

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import Optional

import httpx

from .config import LLMConfig

logger = logging.getLogger(__name__)


class ChartAnalyzer:
    """Send chart screenshots to LLM and return analysis as text."""

    SINGLE_STOCK_PROMPT = """You are a senior technical analyst. Analyze this stock chart.

Read the ticker, price, and all visible indicators. Cover:
- Trend direction and strength
- RSI level and what it signals
- Bollinger Band position (is it overbought/oversold?)
- Volume patterns
- Support/resistance levels
- Any catalysts (earnings dates, news, patterns)
- Risk assessment (low/medium/high)

Be specific with numbers you can read from the chart. Keep it concise — bullet points are fine."""

    MULTI_STOCK_PROMPT = """You are a senior portfolio manager. I'm showing you {n_stocks} stock charts.

For each one, give a quick read: trend, key indicators, risk level.

Then rank them and recommend how to allocate $100K across them. Mention which to buy, hold, skip, or reduce. Explain your reasoning for each."""

    POSITION_REVIEW_PROMPT = """You are a senior portfolio manager. I'm showing you my current positions and charts.

Review each position:
- Is the chart setup still good?
- Should I add, hold, reduce, or close?
- Any traps (overbought, declining momentum)?

Then give me a summary of what I should do."""

    def __init__(self, config: LLMConfig, verbose: bool = True):
        self.config = config
        self.verbose = verbose
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=180.0,
            headers={"Authorization": f"Bearer {config.api_key}"} if config.api_key else {},
        )

    def _log(self, msg: str):
        if self.verbose:
            print(f"[stock_agent] {msg}")

    def _image_to_base64(self, image_path: str, max_size: int = 1024) -> str:
        """Resize image if needed, then convert to base64 data URI."""
        try:
            from PIL import Image
        except ImportError:
            return self._image_to_base64_raw(image_path)

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            img = Image.open(path)
            if img.mode == "RGBA":
                img = img.convert("RGB")

            orig_w, orig_h = img.size
            if max(orig_w, orig_h) > max_size:
                ratio = max_size / max(orig_w, orig_h)
                new_w = int(orig_w * ratio)
                new_h = int(orig_h * ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
                self._log(f"Resized image: {orig_w}x{orig_h} -> {new_w}x{new_h}")

            import io
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            self._log(f"Image compressed: {buf.tell():,} bytes (JPEG q85)")
            data = buf.getvalue()

        except Exception:
            return self._image_to_base64_raw(image_path)

        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"

    def _image_to_base64_raw(self, image_path: str) -> str:
        """Fallback: send raw image without resize."""
        path = Path(image_path)
        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        suffix = path.suffix.lower()
        mime = "image/png" if suffix == ".png" else "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
        return f"data:{mime};base64,{b64}"

    async def _call_llm(
        self,
        image_path: str,
        user_prompt: str,
        system_prompt: str = "You are a precise technical analyst.",
    ) -> str:
        """Send image + prompt to LLM and return the response as free-form text."""
        self._log(f"Loading image: {image_path}")
        image_b64 = self._image_to_base64(image_path)
        self._log(f"Base64 payload: {len(image_b64):,} chars")

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_b64}},
                    {"type": "text", "text": user_prompt},
                ],
            },
        ]

        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        self._log("Sending request to LLM...")
        start_time = time.time()
        response = await self._client.post("/chat/completions", json=payload)
        elapsed = time.time() - start_time
        self._log(f"Response received in {elapsed:.1f}s")

        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:300]}")

        data = response.json()

        if "error" in data:
            raise RuntimeError(f"LLM error: {data['error']}")

        content = data["choices"][0]["message"]["content"]
        reasoning = data["choices"][0]["message"].get("reasoning_content", "")

        # Qwen3-style models put everything in reasoning_content and leave content empty.
        # If content is empty, use reasoning as the actual response.
        if not content or not content.strip():
            if reasoning and reasoning.strip():
                self._log(f"\n--- LLM Analysis ({len(reasoning):,} chars) ---")
                display = reasoning[:3000] if len(reasoning) > 3000 else reasoning
                print(display)
                if len(reasoning) > 3000:
                    print(f"... ({len(reasoning) - 3000:,} more chars)")
                print("--- End of analysis ---\n")
                return reasoning
            else:
                raise RuntimeError("LLM returned empty response (no content, no reasoning)")

        # Model used content normally — still show reasoning if present
        if reasoning and reasoning.strip():
            self._log(f"\n--- LLM Analysis ({len(reasoning):,} chars) ---")
            display = reasoning[:3000] if len(reasoning) > 3000 else reasoning
            print(display)
            if len(reasoning) > 3000:
                print(f"... ({len(reasoning) - 3000:,} more chars)")
            print("--- End of analysis ---\n")

        return content

    async def analyze(self, image_path: str) -> str:
        """Analyze a single stock chart screenshot."""
        self._log(f"Analyzing chart: {image_path}")
        result = await self._call_llm(
            image_path=image_path,
            system_prompt="You are a precise technical analyst. Be concise and specific with numbers.",
            user_prompt=self.SINGLE_STOCK_PROMPT,
        )
        return result

    async def analyze_multiple(self, image_paths: list[str]) -> str:
        """Analyze multiple stock charts and return combined analysis."""
        self._log(f"Analyzing {len(image_paths)} charts...")

        individual_results = []
        for i, path in enumerate(image_paths, 1):
            self._log(f"[{i}/{len(image_paths)}] Analyzing...")
            result = await self.analyze(path)
            individual_results.append(result)

        # Now get the ranking + allocation
        combined = "\n\n".join(individual_results)
        self._log("Generating ranking and allocation...")
        result = await self._call_llm(
            image_path=image_paths[0],
            system_prompt="You are a portfolio manager allocating capital based on technical analysis.",
            user_prompt=self.MULTI_STOCK_PROMPT.format(n_stocks=len(image_paths)) + "\n\n--- Individual analyses above ---\n\nNow rank them and allocate $100K.",
        )
        return result

    async def review_positions(self, image_path: str) -> str:
        """Review current positions against chart analysis."""
        self._log("Reviewing positions...")
        result = await self._call_llm(
            image_path=image_path,
            system_prompt="You are a senior portfolio manager reviewing positions.",
            user_prompt=self.POSITION_REVIEW_PROMPT,
        )
        return result

    async def close(self):
        await self._client.aclose()

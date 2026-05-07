"""
Stock Agent - Automated stock chart analysis via screenshots.

Uses macOS screencapture + local LLM (vision-capable) to analyze
stock charts and recommend allocations.

CLI:
    python -m compass.stock_agent screenshot.png
    python -m compass.stock_agent --capture
    python -m compass.stock_agent --clipboard
    python -m compass.stock_agent --review screenshot.png

Library:
    from compass.stock_agent import StockAgent
    agent = StockAgent()
    result = await agent.analyze_screenshot("chart.png")
"""

from .config import LLMConfig
from .capture import CaptureManager
from .analyzer import ChartAnalyzer
from .engine import StockEngine

# Default config (points to local qwen3 vision endpoint)
config = LLMConfig()

__all__ = ["StockAgent", "config", "LLMConfig", "CaptureManager", "ChartAnalyzer", "StockEngine"]


class StockAgent:
    """High-level interface for automated stock chart analysis."""

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or config
        self.capture = CaptureManager()
        self.analyzer = ChartAnalyzer(self.config)
        self.engine = StockEngine(self.capture, self.analyzer)

    async def analyze_screenshot(self, image_path: str) -> str:
        """Analyze a single chart screenshot and return text analysis."""
        return await self.analyzer.analyze(image_path)

    async def analyze_multiple(self, image_paths: list[str]) -> str:
        """Analyze multiple charts and return ranking + allocation."""
        return await self.analyzer.analyze_multiple(image_paths)

    async def run(self, total_capital: float = 100_000) -> str:
        """Full agent loop: capture → analyze → display."""
        return await self.engine.run(total_capital=total_capital)

    async def review_positions(self, screenshot_path: str) -> str:
        """Compare current portfolio against chart analysis."""
        return await self.engine.review_positions(screenshot_path)

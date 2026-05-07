"""
Stock engine - orchestrates the agent loop.

Capture → analyze → display results.
"""

import asyncio
from typing import Optional

from .capture import CaptureManager
from .analyzer import ChartAnalyzer


class StockEngine:
    """Orchestrates the stock analysis agent loop."""

    def __init__(self, capture: CaptureManager, analyzer: ChartAnalyzer, verbose: bool = True):
        self.capture = capture
        self.analyzer = analyzer
        self.verbose = verbose

    async def run(self, total_capital: float = 100_000, capture_delay: int = 2) -> str:
        """Full agent loop: capture → analyze → display."""
        print(f"[stock_agent] Capturing portfolio charts ({total_capital:,} to allocate)...")
        print("[stock_agent] Switch to your trading platform and press Enter when ready...")
        input()

        path = self.capture.capture_full(delay=capture_delay)
        print(f"[stock_agent] Screenshot saved: {path}")

        result = await self.analyzer.analyze_multiple([path])
        self._print_result(result, total_capital)
        return result

    async def review_positions(self, screenshot_path: str) -> str:
        """Review current positions against chart analysis."""
        print(f"[stock_agent] Reviewing positions...")
        result = await self.analyzer.review_positions(screenshot_path)
        self._print_result(result, 0, label="POSITION REVIEW")
        return result

    async def single_stock(self, screenshot_path: str) -> str:
        """Analyze a single stock chart."""
        print(f"[stock_agent] Analyzing chart: {screenshot_path}")
        result = await self.analyzer.analyze(screenshot_path)
        self._print_result(result, 0, label="SINGLE CHART ANALYSIS")
        return result

    async def continuous_monitor(
        self,
        interval_seconds: int = 300,
        total_capital: float = 100_000,
        max_iterations: int = 10,
    ):
        """Periodically capture and analyze."""
        print(f"[stock_agent] Monitoring (interval={interval_seconds}s, max={max_iterations})")
        print("[stock_agent] Press Ctrl+C to stop\n")

        for i in range(max_iterations):
            try:
                print(f"\n{'='*60}")
                print(f"[stock_agent] Cycle {i+1}/{max_iterations}")
                print(f"{'='*60}\n")

                path = self.capture.capture_full(delay=2)
                result = await self.analyzer.analyze_multiple([path])
                self._print_result(result, total_capital)

                if i < max_iterations - 1:
                    print(f"\n[stock_agent] Next cycle in {interval_seconds}s (Ctrl+C to stop)")
                    await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n[stock_agent] Monitoring stopped")
                break
            except Exception as e:
                print(f"[stock_agent] Error: {e}")
                await asyncio.sleep(10)

    @staticmethod
    def _print_result(result: str, total_capital: float, label: str = "ANALYSIS"):
        print(f"\n{'='*60}")
        print(f"[stock_agent] {label}")
        print(f"{'='*60}")
        print(result)
        print(f"{'='*60}\n")

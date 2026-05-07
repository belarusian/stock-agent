"""
macOS screencapture wrapper for the stock agent.

Handles taking screenshots of trading screens, either full screen,
specific displays, or with a delay for window switching.
"""

import os
import tempfile
import time
import subprocess
from pathlib import Path
from typing import Optional


class CaptureManager:
    """Manage screenshot capture for chart analysis."""

    def __init__(self, output_dir: Optional[str] = None):
        self._output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / "stock_agent"
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._cleanup_old()

    def _cleanup_old(self):
        """Remove screenshots older than 1 hour."""
        cutoff = time.time() - 3600
        for f in self._output_dir.glob("*.png"):
            if f.stat().st_mtime < cutoff:
                f.unlink()

    def _next_path(self, prefix: str) -> Path:
        """Generate a unique file path using timestamp."""
        ts = time.time()
        suffix = f"{ts:.6f}".replace(".", "")  # 14 digits
        return self._output_dir / f"{prefix}_{suffix}.png"

    def capture_full(self, delay: int = 0) -> str:
        """
        Capture full screen.

        Args:
            delay: Seconds to wait before capturing (for window switching)

        Returns:
            Path to the saved PNG file
        """
        if delay > 0:
            import time
            time.sleep(delay)

        output_path = self._next_path("screenshot")
        subprocess.run(["screencapture", str(output_path)], check=True)
        return str(output_path)

    def capture_display(self, display_id: int = 0, delay: int = 0) -> str:
        """
        Capture a specific display.

        Args:
            display_id: Display ID (0 = all displays, 1 = primary, etc.)
            delay: Seconds to wait before capturing

        Returns:
            Path to the saved PNG file
        """
        if delay > 0:
            import time
            time.sleep(delay)

        output_path = self._next_path(f"display_{display_id}")

        if display_id == 0:
            subprocess.run(["screencapture", "-x", str(output_path)], check=True)
        else:
            subprocess.run(["screencapture", "-x", f"-D{display_id}", str(output_path)], check=True)

        return str(output_path)

    def capture_selection(self) -> Optional[str]:
        """
        Let user select a region to capture.
        Returns None if user cancels.

        Returns:
            Path to saved PNG, or None
        """
        output_path = self._next_path("selection")
        result = subprocess.run(["screencapture", "-s", str(output_path)], capture_output=True)

        # -s returns non-zero if user cancels (escapes)
        if result.returncode != 0:
            # File might still be created as empty
            if output_path.exists() and output_path.stat().st_size > 1000:
                return str(output_path)
            return None

        return str(output_path) if output_path.exists() else None

    def capture_window(self, window_id: Optional[int] = None, delay: int = 0) -> str:
        """
        Capture a specific window.

        If window_id is not provided, prompts user to click a window.

        Args:
            window_id: Specific window ID (from macOS API)
            delay: Seconds to wait before capturing

        Returns:
            Path to the saved PNG file
        """
        if delay > 0:
            import time
            time.sleep(delay)

        output_path = self._next_path("window")

        if window_id:
            subprocess.run(["screencapture", "-x", f"-W{window_id}", str(output_path)], check=True)
        else:
            # User clicks on the window they want to capture
            subprocess.run(["screencapture", "-x", "-l", "0", str(output_path)], check=True)

        return str(output_path)

    def list_displays(self) -> list[dict]:
        """
        List available displays.

        Returns:
            List of display info dicts with id, name, dimensions
        """
        result = subprocess.run(
            ["system_profiler", "SPDisplaysDataType"],
            capture_output=True, text=True
        )
        return result.stdout

    def cleanup(self, older_than_seconds: int = 3600):
        """Remove old screenshots to save disk space."""
        import time
        cutoff = time.time() - older_than_seconds
        for f in self._output_dir.glob("screenshot_*.png"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
        for f in self._output_dir.glob("display_*.png"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
        for f in self._output_dir.glob("selection_*.png"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
        for f in self._output_dir.glob("window_*.png"):
            if f.stat().st_mtime < cutoff:
                f.unlink()

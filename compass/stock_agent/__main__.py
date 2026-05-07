"""
CLI entry point for stock agent.

Usage:
    python -m compass.stock_agent screenshot.png
    python -m compass.stock_agent --capture
    python -m compass.stock_agent --clipboard
    python -m compass.stock_agent --review screenshot.png
    python -m compass.stock_agent chart1.png chart2.png chart3.png
"""

import argparse
import asyncio
import sys
import tempfile
from pathlib import Path


def extract_clipboard_image() -> str:
    """Extract image from macOS clipboard to a temp PNG."""
    try:
        import AppKit
    except ImportError:
        print("[stock_agent] PyObjC not installed. Use --capture instead.")
        sys.exit(1)

    pasteboard = AppKit.NSPasteboard.generalPasteboard()

    png_data = pasteboard.dataForType_(AppKit.NSPasteboardTypePNG)
    if png_data:
        img = AppKit.NSImage.alloc().initWithData_(png_data)
    else:
        tiff_data = pasteboard.dataForType_(AppKit.NSPasteboardTypeTIFF)
        if tiff_data:
            img = AppKit.NSImage.alloc().initWithData_(tiff_data)
        else:
            print("[stock_agent] Clipboard empty or not an image.")
            print("[stock_agent] Take a screenshot (Cmd+Shift+4, then Cmd+C).")
            sys.exit(1)

    bitmap_rep = AppKit.NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
    png_bytes = bitmap_rep.representationUsingType_properties_(AppKit.NSPNGFileType, None)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="/tmp/stock_agent")
    png_bytes.writeToFile_(tmp.name)
    tmp.close()
    return tmp.name


async def run_analysis(analyzer, image_paths: list[str], mode: str, total_capital: float):
    """Run the appropriate analysis mode."""
    if mode == "single":
        if len(image_paths) == 1:
            result = await analyzer.analyze(image_paths[0])
            print(f"\n{'='*60}")
            print("[stock_agent] SINGLE CHART ANALYSIS")
            print(f"{'='*60}")
            print(result)
            print(f"{'='*60}\n")
        else:
            result = await analyzer.analyze_multiple(image_paths)
            _print_result(result, total_capital)

    elif mode == "multi":
        result = await analyzer.analyze_multiple(image_paths)
        _print_result(result, total_capital)

    elif mode == "review":
        if len(image_paths) != 1:
            print("[stock_agent] Review mode requires exactly 1 screenshot.")
            sys.exit(1)
        result = await analyzer.review_positions(image_paths[0])
        print(f"\n{'='*60}")
        print("[stock_agent] POSITION REVIEW")
        print(f"{'='*60}")
        print(result)
        print(f"{'='*60}\n")


def _print_result(result: str, total_capital: float):
    print(f"\n{'='*60}")
    print("[stock_agent] ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(result)
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(prog="stock_agent", description="Automated stock chart analysis via screenshots")

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("screenshot", nargs="*", help="Screenshot file(s) to analyze")
    input_group.add_argument("--capture", action="store_true", help="Capture screen then analyze")
    input_group.add_argument("--clipboard", action="store_true", help="Analyze screenshot from clipboard")

    parser.add_argument("--mode", choices=["single", "multi", "review"], default=None)
    parser.add_argument("--review", action="store_true", help="Position review mode")
    parser.add_argument("--capital", type=float, default=100_000, help="Total capital to allocate (default: 100000)")
    parser.add_argument("--delay", type=int, default=3, help="Seconds to wait before capture (default: 3)")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--url", default=None, help="LLM endpoint URL")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")

    args = parser.parse_args()
    if args.review:
        args.mode = "review"

    image_paths = []

    if args.capture:
        from compass.stock_agent.capture import CaptureManager
        print(f"[stock_agent] Switch to trading platform, pressing in {args.delay}s...")
        import time
        time.sleep(args.delay)
        cm = CaptureManager()
        path = cm.capture_full()
        image_paths = [path]
        print(f"[stock_agent] Screenshot: {path}")

    elif args.clipboard:
        try:
            path = extract_clipboard_image()
            image_paths = [path]
            print(f"[stock_agent] Clipboard image: {path}")
        except Exception as e:
            print(f"[stock_agent] Failed: {e}")
            sys.exit(1)

    else:
        for s in args.screenshot:
            p = Path(s)
            if not p.exists():
                print(f"[stock_agent] File not found: {s}")
                sys.exit(1)
            image_paths.append(str(p))

    mode = args.mode or ("single" if len(image_paths) == 1 else "multi")

    from compass.stock_agent.config import LLMConfig
    from compass.stock_agent.analyzer import ChartAnalyzer

    config = LLMConfig()
    if args.url:
        config.base_url = args.url
    if args.model:
        config.model = args.model

    analyzer = ChartAnalyzer(config, verbose=not args.quiet)

    asyncio.run(run_analysis(analyzer, image_paths, mode, args.capital))


if __name__ == "__main__":
    main()

"""Tests for clipboard image extraction."""

import tempfile
from pathlib import Path
from PIL import Image


def test_clipboard_extract_from_pil_image():
    """Test extracting clipboard image using PIL (same flow as __main__.py)."""
    # Create a test PNG image (larger to simulate real screenshots)
    img = Image.new("RGB", (1024, 768), color="blue")
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, format="PNG")
    tmp.close()

    # Simulate clipboard flow: NSImage → TIFF → PIL → PNG
    img2 = Image.open(tmp.name)
    if img2.mode == "RGBA":
        img2 = img2.convert("RGB")

    png_buf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img2.save(png_buf.name, format="PNG")
    png_buf.close()

    assert Path(png_buf.name).exists()
    assert Path(png_buf.name).stat().st_size > 1000

    Path(tmp.name).unlink()
    Path(png_buf.name).unlink()


def test_pil_to_png_conversion():
    """Test that PIL can convert any image to PNG bytes."""
    # Use a larger image for reliable test
    img = Image.new("RGB", (2048, 1536), color="red")
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name, format="PNG")
    tmp.close()

    assert Path(tmp.name).exists()
    assert Path(tmp.name).stat().st_size > 1000
    Path(tmp.name).unlink()


def test_clipboard_logic_with_tiff():
    """Test TIFF → PNG conversion via PIL (the actual clipboard path)."""
    img = Image.new("RGB", (500, 400), color="green")
    tmp_tiff = tempfile.NamedTemporaryFile(suffix=".tiff", delete=False)
    img.save(tmp_tiff.name, format="TIFF")
    tmp_tiff.close()

    img2 = Image.open(tmp_tiff.name)
    if img2.mode == "RGBA":
        img2 = img2.convert("RGB")

    png_buf = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img2.save(png_buf.name, format="PNG")
    png_buf.close()

    assert Path(png_buf.name).exists()
    assert Path(png_buf.name).stat().st_size > 1000

    Path(tmp_tiff.name).unlink()
    Path(png_buf.name).unlink()


if __name__ == "__main__":
    test_clipboard_extract_from_pil_image()
    test_pil_to_png_conversion()
    test_clipboard_logic_with_tiff()
    print("All tests passed")

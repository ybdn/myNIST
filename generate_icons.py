#!/usr/bin/env python3
"""
Generate icon files in various formats from SVG source.

This script converts the SVG icon to PNG and ICO formats
required for the application and PyInstaller.
"""

import sys
from pathlib import Path

try:
    from PIL import Image
    import cairosvg
except ImportError:
    print("Required libraries not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "cairosvg"])
    from PIL import Image
    import cairosvg


def generate_png_from_svg(svg_path: Path, png_path: Path, size: int):
    """
    Generate PNG from SVG at specified size.

    Args:
        svg_path: Path to SVG file
        png_path: Path to output PNG file
        size: Size in pixels (square)
    """
    print(f"  Generating {png_path.name} ({size}x{size})...")
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=size,
        output_height=size
    )


def generate_ico_from_pngs(png_paths: list, ico_path: Path):
    """
    Generate ICO file from multiple PNG files.

    Args:
        png_paths: List of PNG file paths (different sizes)
        ico_path: Path to output ICO file
    """
    print(f"  Generating {ico_path.name}...")

    # Load all PNG images
    images = [Image.open(png) for png in png_paths]

    # Save as ICO with multiple sizes
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images]
    )


def main():
    """Main icon generation function."""
    print("=" * 60)
    print("myNIST Icon Generator")
    print("=" * 60)
    print()

    # Paths
    project_root = Path(__file__).parent
    icons_dir = project_root / "mynist" / "resources" / "icons"
    svg_path = icons_dir / "mynist.svg"

    # Verify SVG exists
    if not svg_path.exists():
        print(f"ERROR: SVG file not found: {svg_path}")
        sys.exit(1)

    print(f"Source SVG: {svg_path}")
    print(f"Output directory: {icons_dir}")
    print()

    # Generate PNG files at various sizes
    print("Generating PNG files...")
    sizes = [512, 256, 128, 64, 48, 32, 16]
    png_paths = []

    for size in sizes:
        png_path = icons_dir / f"mynist_{size}.png"
        generate_png_from_svg(svg_path, png_path, size)
        png_paths.append(png_path)

    # Create primary 512x512 PNG
    primary_png = icons_dir / "mynist.png"
    print(f"  Copying mynist_512.png to mynist.png...")
    import shutil
    shutil.copy(png_paths[0], primary_png)

    print()

    # Generate ICO file (Windows/PyInstaller)
    print("Generating ICO file...")
    ico_path = icons_dir / "mynist.ico"

    # Use multiple sizes for ICO (Windows best practice)
    ico_sizes = [256, 128, 64, 48, 32, 16]
    ico_pngs = [icons_dir / f"mynist_{s}.png" for s in ico_sizes]

    generate_ico_from_pngs(ico_pngs, ico_path)

    print()
    print("=" * 60)
    print("Icon Generation Complete!")
    print("=" * 60)
    print()
    print("Generated files:")
    print(f"  - mynist.svg (source)")
    print(f"  - mynist.png (512x512, primary)")
    print(f"  - mynist.ico (multi-size, for PyInstaller)")
    for size in sizes:
        print(f"  - mynist_{size}.png")
    print()
    print("You can now build with PyInstaller to include the icon.")
    print()


if __name__ == "__main__":
    main()

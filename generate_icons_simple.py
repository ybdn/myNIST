#!/usr/bin/env python3
"""
Simple icon generator using only Pillow (no SVG dependencies).

Creates a fingerprint-style icon directly with PIL/Pillow.
"""

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image, ImageDraw, ImageFont


def create_fingerprint_icon(size=512):
    """
    Create a fingerprint icon using Pillow.

    Args:
        size: Size of the icon in pixels (square)

    Returns:
        PIL Image object
    """
    # Create image with dark blue background
    img = Image.new('RGBA', (size, size), (44, 62, 80, 255))  # #2c3e50
    draw = ImageDraw.Draw(img)

    center_x = size // 2
    center_y = size // 2

    # Draw fingerprint-style arcs
    blue = (52, 152, 219, 255)  # #3498db
    line_width = max(size // 40, 2)

    # Calculate positions based on size
    scale = size / 512

    # Draw concentric arcs to simulate fingerprint
    curves = [
        # (start_angle, end_angle, bbox_offset, opacity)
        (160, 280, int(50 * scale), 230),
        (160, 280, int(60 * scale), 210),
        (150, 290, int(75 * scale), 230),
        (150, 290, int(85 * scale), 210),
        (140, 300, int(100 * scale), 230),
        (140, 300, int(110 * scale), 210),
        (130, 310, int(125 * scale), 230),
        (130, 310, int(135 * scale), 210),
        (120, 320, int(150 * scale), 210),
        (120, 320, int(160 * scale), 190),
        (110, 330, int(175 * scale), 190),
        (110, 330, int(185 * scale), 170),
    ]

    for start, end, offset, opacity in curves:
        bbox = [
            center_x - offset,
            center_y - offset,
            center_x + offset,
            center_y + offset
        ]
        arc_color = (blue[0], blue[1], blue[2], opacity)
        draw.arc(bbox, start, end, fill=arc_color, width=line_width)

    # Add some detail dots
    dot_size = max(size // 80, 2)
    dots = [
        (center_x, center_y - int(90 * scale), 200),
        (center_x - int(10 * scale), center_y - int(83 * scale), 180),
        (center_x + int(10 * scale), center_y - int(83 * scale), 180),
        (center_x - int(18 * scale), center_y - int(70 * scale), 160),
        (center_x + int(18 * scale), center_y - int(70 * scale), 160),
    ]

    for x, y, opacity in dots:
        dot_color = (blue[0], blue[1], blue[2], opacity)
        draw.ellipse([x - dot_size, y - dot_size, x + dot_size, y + dot_size], fill=dot_color)

    # Add "myNIST" text
    try:
        font_size = max(size // 12, 20)
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

        text = "myNIST"
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = center_x - text_width // 2
        text_y = size - int(90 * scale)

        draw.text((text_x, text_y), text, fill=(236, 240, 241, 255), font=font)
    except Exception as e:
        print(f"Warning: Could not add text: {e}")

    return img


def main():
    """Main function to generate all icon sizes."""
    print("=" * 60)
    print("myNIST Simple Icon Generator")
    print("=" * 60)
    print()

    # Paths
    project_root = Path(__file__).parent
    icons_dir = project_root / "mynist" / "resources" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {icons_dir}")
    print()

    # Generate PNG files at various sizes
    print("Generating PNG files...")
    sizes = [512, 256, 128, 64, 48, 32, 16]

    images = []
    for size in sizes:
        print(f"  Creating {size}x{size} icon...")
        img = create_fingerprint_icon(size)

        # Save PNG
        png_path = icons_dir / f"mynist_{size}.png"
        img.save(png_path, 'PNG')
        images.append((size, img))

        # Save primary 512x512 as mynist.png
        if size == 512:
            primary_path = icons_dir / "mynist.png"
            img.save(primary_path, 'PNG')
            print(f"    Saved as {png_path.name} and mynist.png")
        else:
            print(f"    Saved as {png_path.name}")

    print()

    # Generate ICO file
    print("Generating ICO file...")
    ico_path = icons_dir / "mynist.ico"

    # Load images for ICO (use sizes that work well in ICO format)
    ico_sizes = [(img[1], (img[0], img[0])) for img in images if img[0] in [256, 128, 64, 48, 32, 16]]

    # Save as ICO
    if ico_sizes:
        primary_img = images[0][1]  # Use 512x512 as base
        primary_img.save(
            ico_path,
            format='ICO',
            sizes=[size[1] for size in ico_sizes]
        )
        print(f"  Saved as {ico_path.name}")

    print()
    print("=" * 60)
    print("Icon Generation Complete!")
    print("=" * 60)
    print()
    print("Generated files:")
    print(f"  ✓ mynist.svg (manual vector source)")
    print(f"  ✓ mynist.png (512x512, primary)")
    print(f"  ✓ mynist.ico (multi-size, for PyInstaller)")
    for size in sizes:
        print(f"  ✓ mynist_{size}.png")
    print()
    print("Next steps:")
    print("  1. Build with: ./build.sh")
    print("  2. Icon will appear in the application window and executable")
    print()


if __name__ == "__main__":
    main()

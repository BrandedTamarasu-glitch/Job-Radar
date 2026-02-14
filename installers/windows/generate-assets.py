#!/usr/bin/env python3
"""Generate NSIS branding assets from icon.png.

Creates:
  - header.bmp (150x57) - Wizard header image
  - sidebar.bmp (164x314) - Welcome/Finish page sidebar
  - icon.ico - Windows icon file converted from icon.png

Usage:
  python installers/windows/generate-assets.py
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
ICON_PATH = PROJECT_ROOT / "icon.png"
OUTPUT_DIR = Path(__file__).parent

# Brand colors
NAVY = "#1a1a2e"
WHITE = "#ffffff"
CYAN = "#00d4ff"

def create_header_bmp():
    """Create 150x57px header.bmp with dark navy background and right-aligned text."""
    img = Image.new('RGB', (150, 57), NAVY)
    draw = ImageDraw.Draw(img)

    # Try to load a font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()

    # Draw "Job Radar" text right-aligned
    text = "Job Radar"
    # For basic positioning without getbbox (PIL compatibility)
    # Approximate text width: ~80px for "Job Radar" at size 16
    text_x = 150 - 85  # Right margin ~5px
    text_y = 20
    draw.text((text_x, text_y), text, fill=WHITE, font=font)

    # Draw small target/radar circle icon on left
    draw.ellipse([10, 15, 35, 40], outline=CYAN, width=2)
    draw.ellipse([18, 23, 27, 32], fill=CYAN)

    output_path = OUTPUT_DIR / "header.bmp"
    img.save(output_path, "BMP")
    print(f"✓ Created {output_path.name} (150x57)")

def create_sidebar_bmp():
    """Create 164x314px sidebar.bmp with dark navy gradient and centered logo."""
    img = Image.new('RGB', (164, 314), NAVY)
    draw = ImageDraw.Draw(img)

    # Draw gradient (simple top-to-bottom darkening)
    for y in range(314):
        # Darken slightly toward bottom
        darkness = int(26 - (y / 314) * 10)  # 26 -> 16
        color = f"#{darkness:02x}{darkness:02x}{darkness + 14:02x}"
        draw.line([(0, y), (164, y)], fill=color, width=1)

    # Try to load a font
    try:
        font_large = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw "Job Radar" centered vertically
    text = "Job Radar"
    # Approximate positioning
    text_x = 25
    text_y = 130
    draw.text((text_x, text_y), text, fill=WHITE, font=font_large)

    # Draw target/radar icon above text
    center_x = 82
    icon_y = 90
    draw.ellipse([center_x - 20, icon_y - 20, center_x + 20, icon_y + 20], outline=CYAN, width=3)
    draw.ellipse([center_x - 8, icon_y - 8, center_x + 8, icon_y + 8], fill=CYAN)
    draw.line([(center_x, icon_y - 20), (center_x, icon_y + 20)], fill=CYAN, width=2)
    draw.line([(center_x - 20, icon_y), (center_x + 20, icon_y)], fill=CYAN, width=2)

    # Version text at bottom
    version_text = "v2.1.0"
    draw.text((55, 280), version_text, fill="#999999", font=font_small)

    output_path = OUTPUT_DIR / "sidebar.bmp"
    img.save(output_path, "BMP")
    print(f"✓ Created {output_path.name} (164x314)")

def create_icon_ico():
    """Convert icon.png to icon.ico with multiple sizes."""
    if not ICON_PATH.exists():
        print(f"⚠ Warning: {ICON_PATH} not found, generating placeholder icon")
        # Create a simple placeholder icon if source doesn't exist
        img = Image.new('RGBA', (256, 256), (26, 26, 46, 255))
        draw = ImageDraw.Draw(img)

        # Draw target/radar icon
        center = 128
        draw.ellipse([28, 28, 228, 228], outline=(0, 212, 255, 255), width=10)
        draw.ellipse([78, 78, 178, 178], outline=(0, 212, 255, 255), width=8)
        draw.ellipse([108, 108, 148, 148], fill=(0, 212, 255, 255))
        draw.line([(center, 28), (center, 228)], fill=(0, 212, 255, 255), width=6)
        draw.line([(28, center), (228, center)], fill=(0, 212, 255, 255), width=6)
    else:
        img = Image.open(ICON_PATH)

    # Convert to RGBA if needed
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create multiple sizes for ICO format
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    icon_images = []
    for size in sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        icon_images.append(resized)

    output_path = OUTPUT_DIR / "icon.ico"
    icon_images[0].save(
        output_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in icon_images],
        append_images=icon_images[1:]
    )
    print(f"✓ Created {output_path.name} (multi-size ICO: 16, 32, 48, 256)")

if __name__ == "__main__":
    print("Generating NSIS branding assets...")
    create_header_bmp()
    create_sidebar_bmp()
    create_icon_ico()
    print("\nAll assets created successfully!")

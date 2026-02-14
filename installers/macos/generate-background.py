#!/usr/bin/env python3
"""Generate DMG background image for Job Radar installer.

Creates an 800x500 branded background with drag arrow and installation instructions.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def generate_background():
    """Generate DMG background image."""
    # Canvas size
    width = 800
    height = 500

    # Colors
    bg_color = "#1a1a2e"  # Dark navy background
    text_color = "#ffffff"  # White text
    arrow_color = "#ffffff"  # White arrow
    subtitle_color = "#c8c8d2"  # Light gray for tagline

    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to use system fonts, fallback to PIL defaults
    try:
        # macOS system fonts (Helvetica Neue or San Francisco)
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
        tagline_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        version_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except OSError:
        # Fallback to default fonts
        title_font = ImageFont.load_default()
        tagline_font = ImageFont.load_default()
        version_font = ImageFont.load_default()

    # Title: "Job Radar"
    title = "Job Radar"
    # Use textbbox to get text dimensions
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = 60
    draw.text((title_x, title_y), title, fill=text_color, font=title_font)

    # Tagline: "Drag to Applications to install"
    tagline = "Drag to Applications to install"
    tagline_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = tagline_bbox[2] - tagline_bbox[0]
    tagline_x = (width - tagline_width) // 2
    tagline_y = 120
    draw.text((tagline_x, tagline_y), tagline, fill=subtitle_color, font=tagline_font)

    # Draw arrow between app icon (x=200, y=190) and Applications folder (x=600, y=190)
    # Arrow positioned in center between icons at y=190 (vertically aligned with icons)
    # Icon size is 128px, so center is at y=190+64=254
    arrow_y = 254
    arrow_start_x = 200 + 128 + 30  # Icon width (128) + padding
    arrow_end_x = 600 - 30  # Applications folder x - padding

    # Draw arrow shaft (thick line)
    draw.line([(arrow_start_x, arrow_y), (arrow_end_x, arrow_y)],
              fill=arrow_color, width=6)

    # Draw arrowhead (triangle)
    arrowhead_size = 20
    arrowhead_points = [
        (arrow_end_x, arrow_y),  # tip
        (arrow_end_x - arrowhead_size, arrow_y - arrowhead_size//2),  # top
        (arrow_end_x - arrowhead_size, arrow_y + arrowhead_size//2),  # bottom
    ]
    draw.polygon(arrowhead_points, fill=arrow_color)

    # Version and branding at bottom
    version_text = "v2.1.0 | Accurate Job-Candidate Scoring"
    version_bbox = draw.textbbox((0, 0), version_text, font=version_font)
    version_width = version_bbox[2] - version_bbox[0]
    version_x = (width - version_width) // 2
    version_y = height - 40
    draw.text((version_x, version_y), version_text, fill=subtitle_color, font=version_font)

    # Save image
    script_dir = Path(__file__).parent
    output_path = script_dir / 'dmg-background.png'
    img.save(output_path, 'PNG')
    print(f"Background generated: {output_path}")
    print(f"  Size: {width}x{height}")
    print(f"  App icon position: x=200, y=190")
    print(f"  Applications position: x=600, y=190")


if __name__ == '__main__':
    generate_background()

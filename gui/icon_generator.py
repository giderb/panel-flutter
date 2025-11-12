"""
Generate application icon for Panel Flutter Analysis
Creates a professional modern geometric icon
"""

from PIL import Image, ImageDraw
import os
import math

def create_panel_flutter_icon(size=256):
    """
    Create a professional icon representing advanced analysis.
    Modern geometric design with diamond shape and analytical elements.
    """
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Define colors - professional blue gradient
    primary_blue = (0, 102, 204, 255)  # #0066CC
    light_blue = (0, 168, 255, 255)    # #00A8FF
    dark_blue = (0, 51, 102, 255)      # #003366
    accent_blue = (51, 153, 255, 255)  # #3399FF
    white = (255, 255, 255, 200)

    center_x = size // 2
    center_y = size // 2

    # Background circle (subtle)
    circle_radius = int(size * 0.42)
    draw.ellipse(
        [(center_x - circle_radius, center_y - circle_radius),
         (center_x + circle_radius, center_y + circle_radius)],
        fill=(primary_blue[0], primary_blue[1], primary_blue[2], 30)
    )

    # Draw large diamond shape (main icon element)
    diamond_size = int(size * 0.35)
    diamond_points = [
        (center_x, center_y - diamond_size),           # Top
        (center_x + diamond_size, center_y),           # Right
        (center_x, center_y + diamond_size),           # Bottom
        (center_x - diamond_size, center_y)            # Left
    ]

    # Draw diamond with gradient effect (multiple layers)
    for i in range(4):
        scale = 1 - i * 0.12
        layer_size = int(diamond_size * scale)
        layer_points = [
            (center_x, center_y - layer_size),
            (center_x + layer_size, center_y),
            (center_x, center_y + layer_size),
            (center_x - layer_size, center_y)
        ]

        # Color gradient from light to dark
        if i == 0:
            color = light_blue
        elif i == 1:
            color = accent_blue
        elif i == 2:
            color = primary_blue
        else:
            color = dark_blue

        draw.polygon(layer_points, fill=color, outline=None)

    # Add outer diamond outline
    draw.polygon(diamond_points, fill=None, outline=dark_blue, width=3)

    # Draw analytical grid lines (representing analysis/data)
    grid_size = int(diamond_size * 0.85)
    num_lines = 5

    for i in range(num_lines):
        offset = -grid_size + i * (2 * grid_size / (num_lines - 1))

        # Horizontal lines
        y = center_y + offset
        x_span = grid_size * (1 - abs(offset) / grid_size) * 0.7
        if x_span > 10:
            draw.line(
                [(center_x - x_span, y), (center_x + x_span, y)],
                fill=white, width=1
            )

        # Vertical lines
        x = center_x + offset
        y_span = grid_size * (1 - abs(offset) / grid_size) * 0.7
        if y_span > 10:
            draw.line(
                [(x, center_y - y_span), (x, center_y + y_span)],
                fill=white, width=1
            )

    # Add corner accents (representing advanced features)
    accent_size = int(size * 0.08)
    accent_positions = [
        (size * 0.15, size * 0.15),    # Top-left
        (size * 0.85, size * 0.15),    # Top-right
        (size * 0.85, size * 0.85),    # Bottom-right
        (size * 0.15, size * 0.85),    # Bottom-left
    ]

    for x, y in accent_positions:
        # Small diamond accents
        accent_points = [
            (x, y - accent_size * 0.5),
            (x + accent_size * 0.5, y),
            (x, y + accent_size * 0.5),
            (x - accent_size * 0.5, y)
        ]
        draw.polygon(accent_points, fill=light_blue, outline=None)

    # Add central highlight (depth effect)
    highlight_size = int(diamond_size * 0.15)
    highlight_points = [
        (center_x, center_y - highlight_size),
        (center_x + highlight_size, center_y),
        (center_x, center_y + highlight_size),
        (center_x - highlight_size, center_y)
    ]
    draw.polygon(highlight_points, fill=(255, 255, 255, 150), outline=None)

    return img

def save_icon(output_dir='gui/assets'):
    """Generate and save icon in multiple sizes"""
    os.makedirs(output_dir, exist_ok=True)

    # Generate high-resolution icon
    icon_256 = create_panel_flutter_icon(256)

    # Save PNG for use in application
    icon_256.save(os.path.join(output_dir, 'app_icon.png'))

    # Create ICO file with multiple sizes for Windows
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = [icon_256.resize(size, Image.Resampling.LANCZOS) for size in icon_sizes]

    ico_path = os.path.join(output_dir, 'app_icon.ico')
    icons[0].save(ico_path, format='ICO', sizes=icon_sizes)

    print(f"Icons generated successfully:")
    print(f"  - PNG: {os.path.join(output_dir, 'app_icon.png')}")
    print(f"  - ICO: {ico_path}")

    return ico_path

if __name__ == '__main__':
    save_icon()

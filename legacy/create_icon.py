"""
Create a simple stock alert icon for notifications
Requires: pip install pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 256x256 image with transparent background
size = 256
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Draw a circle background (blue gradient effect)
circle_color = (33, 150, 243, 255)  # Material Blue
draw.ellipse([20, 20, size-20, size-20], fill=circle_color)

# Draw an upward trending arrow/chart symbol
arrow_color = (255, 255, 255, 255)  # White
line_width = 20

# Draw chart line (upward trend)
points = [
    (60, 180),
    (100, 140),
    (140, 100),
    (180, 60)
]

for i in range(len(points) - 1):
    draw.line([points[i], points[i+1]], fill=arrow_color, width=line_width)

# Draw arrow head at the end
arrow_head = [
    (180, 60),
    (160, 80),
    (180, 90),
    (180, 60)
]
draw.polygon(arrow_head, fill=arrow_color)

# Save as ICO file
icon_path = os.path.join(os.path.dirname(__file__), 'stock_alert.ico')
img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

print(f"✅ Icon created: {icon_path}")

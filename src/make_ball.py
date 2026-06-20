"""Generates assets/yarn_ball.png — a small cartoon ball of yarn."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

OUT = Path(__file__).parent.parent / "assets" / "yarn_ball.png"
S = 64   # canvas size

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d   = ImageDraw.Draw(img)

cx, cy, r = S // 2, S // 2, S // 2 - 4

# Base ball (warm orange-red yarn)
d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=(220, 80, 40, 255))

# Yarn strands — curved lines across the ball
strand = (240, 110, 60, 200)
for angle_deg in range(0, 180, 22):
    a = math.radians(angle_deg)
    # chord across the circle at this angle
    x1 = int(cx + r * math.cos(a + math.pi / 2))
    y1 = int(cy + r * math.sin(a + math.pi / 2))
    x2 = int(cx + r * math.cos(a - math.pi / 2))
    y2 = int(cy + r * math.sin(a - math.pi / 2))
    # slight curve via midpoint offset
    mid_x = cx + int(10 * math.cos(a))
    mid_y = cy + int(10 * math.sin(a))
    d.line([(x1, y1), (mid_x, mid_y), (x2, y2)], fill=strand, width=2)

# Cross strands (perpendicular set)
strand2 = (200, 60, 20, 180)
for angle_deg in range(10, 180, 28):
    a = math.radians(angle_deg + 90)
    x1 = int(cx + r * math.cos(a + math.pi / 2))
    y1 = int(cy + r * math.sin(a + math.pi / 2))
    x2 = int(cx + r * math.cos(a - math.pi / 2))
    y2 = int(cy + r * math.sin(a - math.pi / 2))
    mid_x = cx + int(8 * math.cos(a))
    mid_y = cy + int(8 * math.sin(a))
    d.line([(x1, y1), (mid_x, mid_y), (x2, y2)], fill=strand2, width=2)

# Highlight (top-left)
d.ellipse([(cx - r + 6, cy - r + 5), (cx - r + 18, cy - r + 14)],
          fill=(255, 160, 120, 160))

# Loose tail of yarn
d.line([(cx + r - 4, cy - 6), (cx + r + 6, cy - 14), (cx + r + 10, cy - 8)],
       fill=(220, 80, 40, 200), width=2)

# Soft drop shadow
shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ImageDraw.Draw(shadow).ellipse(
    [(cx - r + 4, cy + r - 4), (cx + r - 4, cy + r + 6)],
    fill=(0, 0, 0, 70))
shadow = shadow.filter(ImageFilter.GaussianBlur(3))
base = Image.new("RGBA", (S, S + 8), (0, 0, 0, 0))
base.paste(shadow, (0, 8), mask=shadow)
base.paste(img,    (0, 0), mask=img)

base.save(OUT)
print(f"Saved {OUT}  ({base.width}×{base.height}px)")

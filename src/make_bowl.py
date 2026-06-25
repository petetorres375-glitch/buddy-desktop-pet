"""Generates assets/bowl.png — a cartoon cat food bowl with kibble."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math, random

OUT = Path(__file__).parent.parent / "assets" / "bowl.png"
W, H = 100, 68

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Outer rim — steel gray ellipse viewed slightly from above
RIM = (155, 155, 162, 255)
d.ellipse([(6, 16), (W - 6, H - 6)], fill=RIM)

# Inner bowl floor — slightly darker to suggest depth
FLOOR = (118, 118, 126, 255)
pad = 8
d.ellipse([(6 + pad, 16 + pad // 2), (W - 6 - pad, H - 6 - pad // 2)], fill=FLOOR)

# Kibble pieces — small rounded pellets scattered inside
random.seed(7)
KIBBLE = [
    (185, 118, 52, 255),   # warm brown
    (208, 146, 68, 255),   # golden tan
    (158, 95,  42, 255),   # dark brown
    (195, 130, 58, 255),   # medium
]
cx = W // 2
cy = (16 + H - 6) // 2
rx = (W - 6 - (6 + pad)) // 2 - 3
ry = (H - 6 - (16 + pad // 2)) // 2 - 3
for _ in range(20):
    angle = random.uniform(0, 2 * math.pi)
    r = math.sqrt(random.uniform(0, 0.85))
    kx = int(cx + r * rx * math.cos(angle))
    ky = int(cy + r * ry * math.sin(angle))
    kw = random.randint(5, 9)
    kh = random.randint(3, 6)
    col = random.choice(KIBBLE)
    d.ellipse([(kx - kw // 2, ky - kh // 2),
               (kx + kw // 2, ky + kh // 2)], fill=col)

# Rim highlight — small arc top-left for metallic sheen
HIGH = (220, 220, 228, 160)
d.arc([(8, 18), (38, 32)], start=195, end=315, fill=HIGH, width=2)

# Drop shadow below bowl
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shadow).ellipse(
    [(10, H - 10), (W - 10, H + 4)], fill=(0, 0, 0, 55))
shadow = shadow.filter(ImageFilter.GaussianBlur(3))
base = Image.new("RGBA", (W, H + 8), (0, 0, 0, 0))
base.paste(shadow, (0, 8), mask=shadow)
base.paste(img, (0, 0), mask=img)

base.save(OUT)
print(f"Saved {OUT}  ({base.width}×{base.height}px)")

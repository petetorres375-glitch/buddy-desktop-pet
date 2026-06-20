"""
Generates assets/bed.png — a small cartoon cat bed/cushion.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).parent.parent / "assets" / "bed.png"
W, H = 120, 80

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# ── outer rim (dark warm brown) ──────────────────────────────────────────────
rim_color  = (139, 90, 43, 255)
d.ellipse([(0, 10), (W - 1, H - 1)], fill=rim_color)

# ── inner cushion (soft beige) ───────────────────────────────────────────────
pad = 8
cushion_color = (245, 220, 180, 255)
d.ellipse([(pad, 10 + pad), (W - 1 - pad, H - 1 - pad // 2)], fill=cushion_color)

# ── pillow on the left side (slightly lighter) ───────────────────────────────
pillow_color = (255, 235, 200, 255)
d.ellipse([(12, 18), (52, H - 14)], fill=pillow_color)

# ── subtle stitching lines on pillow ─────────────────────────────────────────
stitch = (210, 175, 130, 180)
d.line([(32, 20), (32, H - 16)], fill=stitch, width=1)
d.line([(14, 36), (50, 36)], fill=stitch, width=1)

# ── soft shadow under the whole bed ─────────────────────────────────────────
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.ellipse([(4, H - 14), (W - 4, H + 4)], fill=(0, 0, 0, 60))
shadow = shadow.filter(ImageFilter.GaussianBlur(3))
# composite shadow below bed
base = Image.new("RGBA", (W, H + 8), (0, 0, 0, 0))
base.paste(shadow, (0, 8), mask=shadow)
base.paste(img, (0, 0), mask=img)

base.save(OUT)
print(f"Saved {OUT}  ({base.width}×{base.height}px)")

"""
Slices cat_sheet_raw.png into individual transparent frames.

Frame boundaries were measured pixel-by-pixel from the raw image
(content-detection scan rather than assuming a uniform grid).

Output:
  assets/frames/{anim}_{n}.png  — individual RGBA frames, background removed
  assets/cat_sheet.png           — uniform 180×180 grid for the animation inspector
"""

from pathlib import Path
from PIL import Image
import numpy as np

SRC        = Path(__file__).parent.parent / "assets" / "cat_sheet_raw.png"
OUT_DIR    = Path(__file__).parent.parent / "assets" / "frames"
SHEET_OUT  = Path(__file__).parent.parent / "assets" / "cat_sheet.png"
CELL_SIZE  = 180   # px per cell in the uniform output grid

OUT_DIR.mkdir(exist_ok=True)

# Per-frame crop rectangles (x1, y1, x2, y2) measured from cat_sheet_raw.png (896×1195)
FRAMES = {
    "idle": [
        ( 82, 205, 178, 372),   # F1
        (289, 205, 415, 372),   # F2
        (470, 205, 603, 372),   # F3
        (687, 205, 810, 372),   # F4
    ],
    "walk": [
        ( 35, 438, 182, 568),   # F1
        (168, 438, 308, 568),   # F2
        (300, 438, 448, 568),   # F3
        (440, 438, 584, 568),   # F4
        (575, 438, 730, 568),   # F5
        (720, 438, 854, 568),   # F6
    ],
    "sleep": [
        (447, 582, 550, 688),   # F1
        (548, 582, 650, 688),   # F2
        (649, 582, 751, 688),   # F3
        (750, 582, 852, 688),   # F4
    ],
    "jump": [
        ( 35, 688, 194, 848),   # F1
        (187, 688, 365, 848),   # F2
        (356, 688, 490, 848),   # F3
        (483, 688, 610, 848),   # F4
    ],
    "sit": [
        ( 40, 863, 143, 978),   # F1
        (143, 863, 246, 978),   # F2
        (247, 863, 349, 978),   # F3
        (351, 863, 454, 978),   # F4
    ],
    "play": [
        (500, 863, 615, 978),   # F1
        (615, 863, 733, 978),   # F2
        (732, 863, 850, 978),   # F3
    ],
    "meow": [
        ( 40, 1028, 163, 1148), # F1
        (166, 1028, 285, 1148), # F2
    ],
    "stretch": [
        (342, 1028, 471, 1148), # F1
        (469, 1028, 591, 1148), # F2
        (595, 1028, 725, 1148), # F3
    ],
}

ANIM_ORDER = ["idle", "walk", "sleep", "jump", "sit", "play", "meow", "stretch"]


def remove_background(img: Image.Image) -> Image.Image:
    """Replace light-blue and dark-blue grid colors with transparency."""
    arr = np.array(img.convert("RGBA"), dtype=float)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    light_blue  = (b > r + 25) & (b > g + 8) & (g > 120) & (b > 170)
    dark_blue   = (r < 100) & (g < 150) & (b > 100) & (b > r + 40)
    # bright cyan cell-border highlights (r~220, g=255, b=255) where b≈g so b>g+8 fails
    cell_border = (g > 240) & (b > 240) & (b >= g.astype(int) - 5) & (r < 240)
    arr[:, :, 3] = np.where(light_blue | dark_blue | cell_border, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def tight_crop(img: Image.Image, pad: int = 4) -> Image.Image:
    bbox = img.getbbox()
    if bbox is None:
        return img
    x1 = max(0, bbox[0] - pad)
    y1 = max(0, bbox[1] - pad)
    x2 = min(img.width,  bbox[2] + pad)
    y2 = min(img.height, bbox[3] + pad)
    return img.crop((x1, y1, x2, y2))


def fit_to_cell(img: Image.Image, size: int) -> Image.Image:
    img.thumbnail((size, size), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ox = (size - img.width)  // 2
    oy = (size - img.height) // 2
    canvas.paste(img, (ox, oy), mask=img)
    return canvas


src = Image.open(SRC)
extracted = {}

for anim in ANIM_ORDER:
    extracted[anim] = []
    for i, (x1, y1, x2, y2) in enumerate(FRAMES[anim]):
        cell = src.crop((x1, y1, x2, y2))
        cell = remove_background(cell)
        cell = tight_crop(cell)
        cell = fit_to_cell(cell, CELL_SIZE)
        out  = OUT_DIR / f"{anim}_{i}.png"
        cell.save(out)
        extracted[anim].append(cell)
        print(f"  {out.name}")

# Build uniform grid sheet (one animation per row, padded to max frame count)
max_cols = max(len(extracted[a]) for a in ANIM_ORDER)
n_rows   = len(ANIM_ORDER)
sheet    = Image.new("RGBA", (max_cols * CELL_SIZE, n_rows * CELL_SIZE), (0, 0, 0, 0))

for row, anim in enumerate(ANIM_ORDER):
    for col, frame in enumerate(extracted[anim]):
        sheet.paste(frame, (col * CELL_SIZE, row * CELL_SIZE), mask=frame)

sheet.save(SHEET_OUT)
print(f"\nSaved: {SHEET_OUT}")
print(f"Grid: {max_cols} cols × {n_rows} rows @ {CELL_SIZE}px/cell")
print(f"\nFor anim_inspector.py:")
print(f"  FRAME_WIDTH = FRAME_HEIGHT = {CELL_SIZE}")
for i, a in enumerate(ANIM_ORDER):
    print(f"  '{a}' → row {i}  ({len(extracted[a])} frames)")

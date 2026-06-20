"""
cartoonize_sprite.py
Applies the cartoon effect (bold edges + flattened colors) to Buddy's
cropped, transparent cutout - this time preserving the alpha channel
instead of running on the full photo with background.
"""

import cv2
import numpy as np


def cartoonize_rgba(img, num_colors=6, edge_thickness=7):
    """
    img: RGBA numpy array (with transparency)
    Returns: RGBA cartoonized image, transparency untouched
    """
    bgr = img[:, :, :3]
    alpha = img[:, :, 3]

    # --- Edges ---
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.medianBlur(gray, 5)
    edges = cv2.adaptiveThreshold(
        gray_blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,
        blockSize=edge_thickness, C=5
    )

    # --- Direct color classification instead of automatic correction ---
    # Automatic white-balance and K-means clustering kept guessing wrong
    # (too brown, then too cool/blue) because the warm indoor lighting
    # confuses general-purpose color math. Buddy has exactly 3 real colors
    # (white fur, orange/ginger patches, dark brown accents), so instead
    # we classify each pixel directly using brightness + hue and assign
    # clean, true cartoon colors - no guessing.
    hsv_orig = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hue = hsv_orig[:, :, 0].astype(np.float32)        # 0-179 in OpenCV
    sat = hsv_orig[:, :, 1].astype(np.float32)
    val = hsv_orig[:, :, 2].astype(np.float32)

    # Orange/ginger fur: hue around 8-28, with meaningfully higher
    # saturation than his white fur (sampled: white chest ~sat 51,
    # orange ear ~sat 73 - threshold sits between the two)
    is_orange = (hue >= 8) & (hue <= 28) & (sat > 62)
    # Dark brown/shadow patches: low brightness
    is_dark = (val < 90) & (~is_orange)
    # Everything else (his white fur): low saturation, bright
    is_white = (~is_orange) & (~is_dark)

    flattened = np.zeros_like(bgr)
    flattened[is_white] = (235, 240, 245)   # clean off-white, BGR order
    flattened[is_orange] = (60, 140, 225)   # warm ginger orange, BGR order
    flattened[is_dark] = (55, 75, 95)       # warm brown shadow, BGR order

    flattened = cv2.medianBlur(flattened, 5)  # smooth small speckle between regions

    # --- Combine edges + flattened colors ---
    edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon_bgr = cv2.bitwise_and(flattened, edges_3ch)

    # Reassemble with original alpha (transparency) untouched
    cartoon_rgba = cv2.merge([cartoon_bgr[:, :, 0], cartoon_bgr[:, :, 1], cartoon_bgr[:, :, 2], alpha])
    return cartoon_rgba


if __name__ == "__main__":
    img = cv2.imread("/home/claude/buddy_pet/assets/buddy_cropped.png", cv2.IMREAD_UNCHANGED)
    cartoon = cartoonize_rgba(img)
    cv2.imwrite("/home/claude/buddy_pet/assets/buddy_cartoon_sprite_test.png", cartoon)
    print("Saved cartoonized sprite")

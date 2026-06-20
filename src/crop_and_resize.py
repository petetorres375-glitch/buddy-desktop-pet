"""
crop_and_resize.py
Takes the transparent cutout and:
1. Crops tightly to Buddy's actual bounding box (no wasted empty space)
2. Resizes down to sprite size for the desktop pet
"""

import cv2
import numpy as np


def crop_to_content(img):
    """Crop an RGBA image tightly to the non-transparent pixels."""
    alpha = img[:, :, 3]
    ys, xs = np.where(alpha > 10)  # any pixel with a little visibility
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    print(f"Content bounding box: x[{x0}:{x1}] y[{y0}:{y1}]")
    return img[y0:y1 + 1, x0:x1 + 1]


def resize_sprite(img, target_height=120):
    """Resize keeping aspect ratio, targeting a given pixel height for the sprite."""
    h, w = img.shape[:2]
    scale = target_height / h
    new_w = int(w * scale)
    resized = cv2.resize(img, (new_w, target_height), interpolation=cv2.INTER_AREA)
    print(f"Resized sprite to: {new_w}x{target_height}")
    return resized


if __name__ == "__main__":
    img = cv2.imread("/home/claude/buddy_pet/assets/buddy_cutout_test.png", cv2.IMREAD_UNCHANGED)
    cropped = crop_to_content(img)
    cv2.imwrite("/home/claude/buddy_pet/assets/buddy_cropped.png", cropped)

    sprite = resize_sprite(cropped, target_height=120)
    cv2.imwrite("/home/claude/buddy_pet/assets/buddy_idle.png", sprite)

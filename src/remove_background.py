"""
remove_background.py
Isolates Buddy from the photo background using GrabCut segmentation,
producing a transparent PNG cutout.

GrabCut works like this:
1. We give it a rough rectangle saying "the subject is roughly in here"
2. It looks at color/texture differences and iteratively decides,
   pixel by pixel, "this is foreground (Buddy)" vs "background (wall/floor)"
3. We get back a mask (a black & white "stencil") we can use to cut Buddy out
"""

import cv2
import numpy as np


def remove_background(input_path, output_path, rect=None, iterations=5, max_dim=800):
    img = cv2.imread(input_path)
    h, w = img.shape[:2]
    print(f"Original image size: {w}x{h}")

    # Downscale first - GrabCut is slow and we don't need 4000px for a
    # small desktop sprite. max_dim caps the longest side.
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
        print(f"Resized to: {w}x{h}")

    # GrabCut needs two small internal "scratchpad" arrays to do its math.
    # We don't use these directly, they're just required by the function.
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    # Buddy's white fur against the light wall/door has very low color
    # contrast, which makes automatic rectangle/seed-based guessing
    # unreliable (it kept including the door, hinge, and floor). Instead,
    # we manually mark the known background regions for THIS photo
    # (door frame, hinge, wall, dark cabinet, floor), based on its
    # 600x800 working resolution. Everything else is left "uncertain"
    # for GrabCut to resolve - a much smaller, easier judgment call.
    mask = np.full((h, w), cv2.GC_PR_FGD, np.uint8)  # default: probably foreground

    def bg_region(x0, x1, y0, y1):
        mask[int(y0 * h / 800):int(y1 * h / 800), int(x0 * w / 600):int(x1 * w / 600)] = cv2.GC_BGD

    bg_region(0, 95, 0, 800)       # door frame, full height, left strip
    bg_region(95, 170, 130, 245)   # door hinge area
    bg_region(95, 345, 0, 75)      # cream wall, top middle, above his head
    bg_region(155, 235, 60, 245)   # leftover wall sliver between hinge and head/tail
    bg_region(470, 600, 0, 520)    # dark cabinet/shelf, right side
    bg_region(430, 600, 470, 700)  # floor wedge, lower right
    bg_region(0, 600, 700, 800)    # floor, bottom strip full width

    # Confident core of Buddy's body as definite foreground (well inside
    # his actual silhouette bounding box of roughly x:100-460, y:75-700)
    mask[110:660, 150:430] = cv2.GC_FGD

    cv2.grabCut(img, mask, None, bgd_model, fgd_model, iterations, cv2.GC_INIT_WITH_MASK)

    # Collapse the 4 possible labels down to a simple binary mask:
    # "probably or definitely foreground" -> 1 (keep), everything else -> 0 (cut)
    binary_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype("uint8")

    # Clean up the mask: remove small stray specks, smooth jagged edges
    kernel = np.ones((7, 7), np.uint8)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
    binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel)

    # Keep only the single LARGEST connected shape in the mask.
    # This drops disconnected stray fragments (like a door hinge that
    # happened to touch Buddy's silhouette) while keeping all of Buddy,
    # since his body/tail/ears are one connected blob.
    num_labels, labels_im, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)
    if num_labels > 1:  # label 0 is always the background
        # stats[:, 4] is the pixel area of each component; skip index 0 (background)
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        binary_mask = np.where(labels_im == largest_label, 1, 0).astype("uint8")

    # Soften the mask edges slightly so the cutout doesn't look jagged/pixelated
    binary_mask_float = binary_mask.astype(np.float32)
    binary_mask_float = cv2.GaussianBlur(binary_mask_float, (5, 5), 0)

    # GrabCut kept treating one small wall patch next to Buddy's ear as
    # foreground because it's adjacent to confidently-foreground fur.
    # Force-clear it directly (after blurring) rather than continuing to
    # fight GrabCut's color reasoning over one small known spot.
    binary_mask_float[60:230, 150:240] = 0

    # Build the output: BGR color channels + our mask as the Alpha (transparency) channel
    b, g, r = cv2.split(img)
    alpha = (binary_mask_float * 255).astype(np.uint8)
    cutout = cv2.merge([b, g, r, alpha])  # BGRA = color + transparency

    cv2.imwrite(output_path, cutout)
    print(f"Saved cutout to {output_path}")

    return cutout, binary_mask


if __name__ == "__main__":
    remove_background(
        "/home/claude/buddy_pet/assets/buddy_original.jpg",
        "/home/claude/buddy_pet/assets/buddy_cutout_test.png"
    )

"""
cartoonize.py
Turns Buddy's real photo into a flat chibi-cartoon style image.

The classic "cartoonizer" technique has 2 ingredients:
1. EDGES  - find Buddy's outlines (whiskers, ears, body shape) and draw
            them as bold black lines.
2. COLORS - "flatten" the smooth gradient of fur color into a small
            number of solid color blocks (this is called posterizing).

Then we combine: solid color blocks UNDER bold black edges = cartoon look.
"""

import cv2
import numpy as np

def cartoonize(input_path, output_path, num_colors=8, edge_thickness=9):
    # --- Load the photo ---
    img = cv2.imread(input_path)  # OpenCV loads as BGR (not RGB!) by default
    print(f"Loaded image: {img.shape[1]}x{img.shape[0]} pixels")

    # --- STEP 1: Find edges ---
    # Convert to grayscale first - edge detection works on brightness, not color
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur slightly to remove noise/fuzz from the photo before edge detection,
    # otherwise we get thousands of tiny jagged edges from fur texture
    gray_blur = cv2.medianBlur(gray, 5)

    # adaptiveThreshold finds edges and outputs pure black/white.
    # Pixels that are "different enough" from their neighborhood become black lines.
    edges = cv2.adaptiveThreshold(
        gray_blur,
        255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        blockSize=edge_thickness,  # bigger = thicker/bolder lines
        C=5
    )

    # --- STEP 2: Flatten the colors (posterize) ---
    # We use K-means clustering: tell it "group all these colors into
    # just 8 buckets" and it picks the best 8 colors to represent the photo.
    data = img.reshape((-1, 3))  # flatten image into a list of [B,G,R] pixels
    data = np.float32(data)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        data, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )

    centers = np.uint8(centers)  # back to normal 0-255 color values
    flattened = centers[labels.flatten()]
    flattened = flattened.reshape(img.shape)

    # Smooth the flattened color regions a bit for a cleaner cartoon feel
    flattened = cv2.bilateralFilter(flattened, d=9, sigmaColor=200, sigmaSpace=200)

    # --- STEP 3: Combine colors + edges ---
    # Convert edges to 3-channel so we can combine with the color image
    edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cartoon = cv2.bitwise_and(flattened, edges_3ch)

    cv2.imwrite(output_path, cartoon)
    print(f"Saved cartoonized image to {output_path}")
    return cartoon


if __name__ == "__main__":
    cartoonize(
        "/home/claude/buddy_pet/assets/buddy_original.jpg",
        "/home/claude/buddy_pet/assets/buddy_cartoon_test.jpg"
    )

import cv2
import numpy as np
from skimage.morphology import skeletonize
import matplotlib.pyplot as plt

# === 1. Load and preprocess image ===
img = cv2.imread('test.png')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# === 2. Threshold and invert (black lines become white) ===
_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

# === 3. Skeletonize to thin the lines ===
binary_bool = binary > 0
skeleton = skeletonize(binary_bool).astype(np.uint8) * 255

# === 4. Find all contours, including shapes inside shapes ===
contours, hierarchy = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

# === 5. Extract and print coordinates ===
all_coords = []
for i, contour in enumerate(contours):
    coords = contour.reshape(-1, 2)
    all_coords.append(coords)
    
    #print(f"\nContour {i}: {len(coords)} points")
    #print(coords)

# === 6. Plot all contours ===
plt.figure(figsize=(8, 8))
for coords in all_coords:
    xs, ys = zip(*coords)
    plt.plot(xs, ys, marker='.', linestyle='-', linewidth=0.5)

plt.title("All Contour Coordinates (Including Nested Shapes)")
plt.gca().invert_yaxis()
plt.axis('equal')
plt.grid(True)
plt.show()

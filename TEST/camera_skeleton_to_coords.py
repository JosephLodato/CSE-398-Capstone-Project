# camera_skeleton_to_coords.py

import cv2
import numpy as np
from skimage.morphology import skeletonize

def get_skeleton_coords(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    binary_bool = binary > 0
    skeleton = skeletonize(binary_bool).astype(np.uint8) * 255

    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    all_coords = []
    for contour in contours:
        coords = contour.reshape(-1, 2)
        if len(coords) > 1:
            all_coords.append(coords.tolist())

    return all_coords

def capture_skeleton_from_camera(display_size=480):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera not available")

    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError("Failed to capture frame")

    h, w = frame.shape[:2]
    min_dim = min(h, w)
    cx, cy = w // 2, h // 2
    square_frame = frame[cy - min_dim//2:cy + min_dim//2, cx - min_dim//2:cx + min_dim//2]
    square_frame = cv2.resize(square_frame, (display_size, display_size))

    return get_skeleton_coords(square_frame)

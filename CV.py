import cv2
import numpy as np
from skimage.morphology import skeletonize
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from PIL import Image

# --- Camera Setup ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not available")
    exit()

# --- UI Settings ---
BUTTON_WIDTH = 150
DISPLAY_SIZE = 480  # Square display (480x480)
WINDOW_NAME = "Skeleton Camera"

# --- Button Area (x1, y1, x2, y2) ---
button_coords = (DISPLAY_SIZE + 10, 200, DISPLAY_SIZE + BUTTON_WIDTH - 10, 280)
button_clicked = False

# --- Mouse Callback ---
def mouse_callback(event, x, y, flags, param):
    global button_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        x1, y1, x2, y2 = button_coords
        if x1 <= x <= x2 and y1 <= y <= y2:
            button_clicked = True

cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback(WINDOW_NAME, mouse_callback)

# --- Skeleton Plot Helper ---
def generate_skeleton_plot(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    binary_bool = binary > 0
    skeleton = skeletonize(binary_bool).astype(np.uint8) * 255

    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(1, 1, 1)

    for contour in contours:
        coords = contour.reshape(-1, 2)
        if len(coords) > 1:
            xs, ys = zip(*coords)
            ax.plot(xs, ys, marker='.', linestyle='-', linewidth=0.5)

    ax.set_title("Skeleton Contours")
    ax.invert_yaxis()
    ax.axis('equal')
    ax.grid(True)

    canvas = FigureCanvas(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    buf.seek(0)
    img_pil = Image.open(buf).convert('RGB')
    img_np = np.array(img_pil)
    return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

# --- Main Loop ---
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    # Crop center square
    h, w = frame.shape[:2]
    min_dim = min(h, w)
    cx, cy = w // 2, h // 2
    square_frame = frame[cy - min_dim//2:cy + min_dim//2, cx - min_dim//2:cx + min_dim//2]
    square_frame = cv2.resize(square_frame, (DISPLAY_SIZE, DISPLAY_SIZE))

    # Create canvas: square display + button
    canvas_width = DISPLAY_SIZE + BUTTON_WIDTH
    canvas = np.ones((DISPLAY_SIZE, canvas_width, 3), dtype=np.uint8) * 50
    canvas[:, :DISPLAY_SIZE] = square_frame

    # Draw button
    x1, y1, x2, y2 = button_coords
    cv2.rectangle(canvas, (x1, y1), (x2, y2), (200, 200, 200), -1)
    cv2.putText(canvas, "Snapshot", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 0, 0), 2)

    cv2.imshow(WINDOW_NAME, canvas)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

    if button_clicked:
        plot_img = generate_skeleton_plot(square_frame)

        # Just show the result, no saving
        cv2.imshow("Skeleton Plot", plot_img)
        cv2.waitKey(3000)
        cv2.destroyWindow("Skeleton Plot")

        button_clicked = False

cap.release()
cv2.destroyAllWindows()
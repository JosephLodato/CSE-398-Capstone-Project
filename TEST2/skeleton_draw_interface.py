import cv2
import numpy as np
from skimage.morphology import skeletonize
import gpiod
import time
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from PIL import Image

# --- Motor Setup ---
MICROSTEPPING_MODE = "FULL"
MICROSTEP_CONFIG = {
    "FULL": [0, 0],
    "HALF": [1, 0],
    "1/4": [0, 1],
    "1/8": [1, 1],
}

class StepperMotor:
    def __init__(self, chip_name, dir_pin, step_pin, ms1_pin, ms2_pin, enable_pin, name="Motor"):
        self.chip = gpiod.Chip(chip_name)
        self.pins = [dir_pin, step_pin, ms1_pin, ms2_pin, enable_pin]
        self.lines = self.chip.get_lines(self.pins)
        self.lines.request(consumer="mp6500", type=gpiod.LINE_REQ_DIR_OUT)
        self.name = name
        self._set_microstepping(MICROSTEPPING_MODE)
        self.enable()

    def _set_microstepping(self, mode):
        ms_values = MICROSTEP_CONFIG[mode]
        self.microstep_values = ms_values

    def enable(self):
        self.lines.set_values([0, 0, *self.microstep_values, 0])

    def disable(self):
        self.lines.set_values([0, 0, 0, 0, 1])

    def set_direction(self, direction):
        values = self.lines.get_values()
        values[0] = direction
        self.lines.set_values(values)

    def pulse(self, delay=0.001):
        values = self.lines.get_values()
        values[1] = 1
        self.lines.set_values(values)
        time.sleep(delay)
        values[1] = 0
        self.lines.set_values(values)
        time.sleep(delay)

    def cleanup(self):
        self.disable()
        self.lines.release()
        self.chip.close()

motorX1 = StepperMotor("gpiochip4", 20, 21, 22, 23, 24, name="X1")
motorX2 = StepperMotor("gpiochip4", 25, 26, 27, 28, 29, name="X2")
motorY  = StepperMotor("gpiochip4", 5, 6, 7, 8, 9, name="Y")

def moveXY(x_steps, x_dir, y_steps, y_dir, delay=0.001):
    motorX1.set_direction(x_dir)
    motorX2.set_direction(x_dir)
    motorY.set_direction(y_dir)

    max_steps = max(x_steps, y_steps)
    x_ratio = x_steps / max_steps if x_steps else 0
    y_ratio = y_steps / max_steps if y_steps else 0

    x_progress = 0.0
    y_progress = 0.0

    for _ in range(max_steps):
        if x_progress < 1.0:
            motorX1.pulse(delay)
            motorX2.pulse(delay)
            x_progress += x_ratio
        if y_progress < 1.0:
            motorY.pulse(delay)
            y_progress += y_ratio

def cleanup_motors():
    motorX1.cleanup()
    motorX2.cleanup()
    motorY.cleanup()

# --- Skeleton Processing and Plotting ---
def generate_skeleton_plot(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    binary_bool = binary > 0
    skeleton = skeletonize(binary_bool).astype(np.uint8) * 255

    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(1, 1, 1)

    all_coords = []
    for contour in contours:
        coords = contour.reshape(-1, 2)
        if len(coords) > 1:
            all_coords.append(coords.tolist())
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
    plot_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

    return plot_img, all_coords

STEPS_PER_PIXEL = 1  # Change this for scaling output

def draw_contours_with_motors(contours):
    for contour in contours:
        last_x, last_y = contour[0]
        for x, y in contour[1:]:
            dx = x - last_x
            dy = y - last_y

            steps_x = int(abs(dx) * STEPS_PER_PIXEL)
            steps_y = int(abs(dy) * STEPS_PER_PIXEL)

            dir_x = 1 if dx > 0 else 0
            dir_y = 1 if dy > 0 else 0

            moveXY(steps_x, dir_x, steps_y, dir_y)

            last_x, last_y = x, y

# --- Camera Interface with Button ---
BUTTON_WIDTH = 150
DISPLAY_SIZE = 480
WINDOW_NAME = "Skeleton Camera"
button_coords = (DISPLAY_SIZE + 10, 200, DISPLAY_SIZE + BUTTON_WIDTH - 10, 280)
button_clicked = False

def mouse_callback(event, x, y, flags, param):
    global button_clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        x1, y1, x2, y2 = button_coords
        if x1 <= x <= x2 and y1 <= y <= y2:
            button_clicked = True

cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setMouseCallback(WINDOW_NAME, mouse_callback)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not available")
    exit()

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        h, w = frame.shape[:2]
        min_dim = min(h, w)
        cx, cy = w // 2, h // 2
        square_frame = frame[cy - min_dim//2:cy + min_dim//2, cx - min_dim//2:cx + min_dim//2]
        square_frame = cv2.resize(square_frame, (DISPLAY_SIZE, DISPLAY_SIZE))

        canvas_width = DISPLAY_SIZE + BUTTON_WIDTH
        canvas = np.ones((DISPLAY_SIZE, canvas_width, 3), dtype=np.uint8) * 50
        canvas[:, :DISPLAY_SIZE] = square_frame

        x1, y1, x2, y2 = button_coords
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (200, 200, 200), -1)
        cv2.putText(canvas, "Snapshot", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 0, 0), 2)

        cv2.imshow(WINDOW_NAME, canvas)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if button_clicked:
            plot_img, contours = generate_skeleton_plot(square_frame)

            # Show the contour plot
            cv2.imshow("Skeleton Plot", plot_img)
            cv2.waitKey(3000)
            cv2.destroyWindow("Skeleton Plot")

            # Print coordinates
            print("\n--- Contour Coordinates ---")
            for i, contour in enumerate(contours):
                print(f"Contour {i+1}: {len(contour)} points")
                for pt in contour:
                    print(f"  ({pt[0]}, {pt[1]})")
            print("--- End of Coordinates ---\n")

            # Move motors
            draw_contours_with_motors(contours)

            button_clicked = False

finally:
    cap.release()
    cv2.destroyAllWindows()
    cleanup_motors()

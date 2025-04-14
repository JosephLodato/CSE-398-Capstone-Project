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

# --- Skeleton Processing ---
def process_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    skeleton = skeletonize(binary > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    return contours

# --- Motion Execution ---
STEPS_PER_PIXEL = 1

def execute_path(contours):
    for contour in contours:
        last_x, last_y = contour[0][0]
        for point in contour[1:]:
            x, y = point[0]
            dx = x - last_x
            dy = y - last_y
            steps_x = int(abs(dx) * STEPS_PER_PIXEL)
            steps_y = int(abs(dy) * STEPS_PER_PIXEL)
            dir_x = 1 if dx > 0 else 0
            dir_y = 1 if dy > 0 else 0
            moveXY(steps_x, dir_x, steps_y, dir_y)
            last_x, last_y = x, y

# --- Camera and UI ---
BUTTON_WIDTH = 150
DISPLAY_SIZE = 480
WINDOW_NAME = "XY Control"
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
        cv2.putText(canvas, "Snapshot", (x1 + 10, y1 + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        cv2.imshow(WINDOW_NAME, canvas)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if button_clicked:
            contours = process_image(square_frame)
            execute_path(contours)
            button_clicked = False

finally:
    cap.release()
    cv2.destroyAllWindows()
    cleanup_motors()

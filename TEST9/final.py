import cv2
import numpy as np
from skimage.morphology import skeletonize
import gpiod
import time
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io
from PIL import Image
import RPi.GPIO as GPIO

# --- Motor Setup ---
GPIO.setmode(GPIO.BCM)  # Use BCM numbering

class StepperMotor:
    def __init__(self, dir_pin, step_pin, name="Motor"):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.name = name

        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)

        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)

    def set_direction(self, direction):
        GPIO.output(self.dir_pin, GPIO.HIGH if direction else GPIO.LOW)

    def pulse(self, delay=0.001):
        GPIO.output(self.step_pin, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(self.step_pin, GPIO.LOW)
        time.sleep(delay)

    def pulse(self, delay=0.001, steps=100):
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)
            
    def cleanup(self):
        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)

motorX = StepperMotor(12, 16, name="X")
motorY = StepperMotor(13, 6, name="Y")
motorZ = StepperMotor(18, 19, name="Z")  

def z_down():
    motorZ.set_direction(1)  # Down
    motorZ.pulse(delay=0.007, steps=100)

def z_up():
    motorZ.set_direction(0)  # Up
    motorZ.pulse(delay=0.007, steps=100)

def moveXY(x_steps, x_dir, y_steps, y_dir, delay=0.001):
    motorX.set_direction(x_dir)
    motorY.set_direction(y_dir)

    x = 0
    y = 0
    dx = x_steps
    dy = y_steps
    sx = 1
    sy = 1

    if dx > dy:
        err = dx / 2.0
        for _ in range(dx):
            motorX.pulse(delay)
            x += sx
            err -= dy
            if err < 0:
                motorY.pulse(delay)
                y += sy
                err += dx
    else:
        err = dy / 2.0
        for _ in range(dy):
            motorY.pulse(delay)
            y += sy
            err -= dx
            if err < 0:
                motorX.pulse(delay)
                x += sx
                err += dy

def cleanup_all():
    motorX.cleanup()
    motorY.cleanup()
    motorZ.cleanup()
    GPIO.cleanup()

# --- Skeleton Processing ---
def process_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)
    skeleton = skeletonize(binary > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    return skeleton, contours

# --- Motion Execution ---
STEPS_PER_PIXEL = 1

def wait_for_key_prompt(window_name, message):
    prompt_canvas = np.ones((100, 480 + BUTTON_WIDTH, 3), dtype=np.uint8) * 30
    cv2.putText(prompt_canvas, message, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.imshow(window_name, prompt_canvas)
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('n'):
            break

def execute_path(contours):
    #z_down()
    #time.sleep(0.5)
    current_x = 0
    current_y = 0

    for i, contour in enumerate(contours):
        if len(contour) < 2:
            continue

        first_x, first_y = contour[0][0]
        dx = first_x - current_x
        dy = first_y - current_y
        steps_x = int(abs(dx) * STEPS_PER_PIXEL)
        steps_y = int(abs(dy) * STEPS_PER_PIXEL)
        dir_x = 1 if dx > 0 else 0
        dir_y = 1 if dy > 0 else 0
        moveXY(steps_x, dir_x, steps_y, dir_y)

        current_x, current_y = first_x, first_y

        #wait_for_key_prompt(WINDOW_NAME, f"Lower pen for contour {i+1}, then press 'n' to continue")
        z_up()
        time.sleep(0.5)  # small delay to let marker settle


        for point in contour[1:]:
            x, y = point[0]
            dx = x - current_x
            dy = y - current_y
            steps_x = int(abs(dx) * STEPS_PER_PIXEL)
            steps_y = int(abs(dy) * STEPS_PER_PIXEL)
            dir_x = 1 if dx > 0 else 0
            dir_y = 1 if dy > 0 else 0
            moveXY(steps_x, dir_x, steps_y, dir_y)
            current_x, current_y = x, y

        #wait_for_key_prompt(WINDOW_NAME, f"Lift pen after contour {i+1}, then press 'n' to continue")
        z_down()
        time.sleep(0.5)  # small delay to let marker settle

    # Return to origin
    dx = 0 - current_x
    dy = 0 - current_y
    steps_x = int(abs(dx) * STEPS_PER_PIXEL)
    steps_y = int(abs(dy) * STEPS_PER_PIXEL)
    dir_x = 1 if dx > 0 else 0
    dir_y = 1 if dy > 0 else 0
    moveXY(steps_x, dir_x, steps_y, dir_y)


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
            skeleton, contours = process_image(square_frame)

            # Show contour overlay
            fig = Figure(figsize=(5, 5), dpi=100)
            ax = fig.add_subplot(1, 1, 1)
            for contour in contours:
                coords = contour.reshape(-1, 2)
                xs, ys = zip(*coords)
                ax.plot(xs, ys, marker='.', linestyle='-', linewidth=0.5)
            ax.set_title("Skeleton Contours")
            ax.invert_yaxis()
            ax.axis('equal')
            ax.grid(True)
            canvas_plot = FigureCanvas(fig)
            buf = io.BytesIO()
            canvas_plot.print_png(buf)
            buf.seek(0)
            img_pil = Image.open(buf).convert('RGB')
            img_np = np.array(img_pil)
            plot_img = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            cv2.imshow("Skeleton Plot", plot_img)
            cv2.waitKey(3000)
            cv2.destroyWindow("Skeleton Plot")

            # Execute motor movement
            execute_path(contours)
            button_clicked = False

finally:
    cap.release()
    cv2.destroyAllWindows()
    cleanup_all()

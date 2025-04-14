import numpy as np
import gpiod
import time

# --- Motor Setup ---
class StepperMotor:
    def __init__(self, chip_name, dir_pin, step_pin, name="Motor"):
        self.chip = gpiod.Chip(chip_name)
        self.pins = [dir_pin, step_pin]
        self.lines = self.chip.get_lines(self.pins)
        self.lines.request(consumer="mp6500", type=gpiod.LINE_REQ_DIR_OUT)
        self.name = name

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
        self.lines.release()
        self.chip.close()

motorX = StepperMotor("gpiochip4", 12, 16, name="X")
motorY = StepperMotor("gpiochip4", 13, 6, name="Y")

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

# --- Motion Execution ---
STEPS_PER_PIXEL = 1

def execute_path(contours):
    for contour in contours:
        time.sleep(2)  # Manual Z adjustment pause
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

# --- Shape Generators ---
def simulate_contour(points):
    return [np.array(points, dtype=np.int32).reshape(-1, 1, 2)]

def generate_circle(cx, cy, r, num_points=120):
    return [(int(cx + r * np.cos(t)), int(cy + r * np.sin(t))) for t in np.linspace(0, 2*np.pi, num_points)]

def generate_triangle():
    return [
        (100, 50),   # Top
        (50, 150),   # Bottom Left
        (150, 150),  # Bottom Right
        (100, 50)    # Back to Top
    ]

# --- Main ---
if __name__ == "__main__":
    try:
        shape = input("Enter shape to draw (circle/triangle): ").strip().lower()
        if shape == "circle":
            points = generate_circle(100, 100, 50)
        elif shape == "triangle":
            points = generate_triangle()
        else:
            print("Invalid shape.")
            exit()

        contours = simulate_contour(points)
        print("Drawing:", shape)
        time.sleep(2)
        execute_path(contours)

    finally:
        cleanup_all()
        print("Motors cleaned up.")

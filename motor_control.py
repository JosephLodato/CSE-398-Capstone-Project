from motorDriverTest import moveXY

# Virtual position tracking
current_x = 0
current_y = 0

# Scale pixel to steps if needed
PIXEL_TO_STEP = 1  # 1 pixel = 1 step (adjust for real-world scale)

def move_to_coordinate(x_target, y_target):
    global current_x, current_y

    dx = int((x_target - current_x) * PIXEL_TO_STEP)
    dy = int((y_target - current_y) * PIXEL_TO_STEP)

    x_dir = 1 if dx > 0 else 0
    y_dir = 1 if dy > 0 else 0

    print(f"Moving to ({x_target}, {y_target}) → Steps: X={abs(dx)}, Y={abs(dy)}")
    moveXY(abs(dx), x_dir, abs(dy), y_dir)

    current_x = x_target
    current_y = y_target

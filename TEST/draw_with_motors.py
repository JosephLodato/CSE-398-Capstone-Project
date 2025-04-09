# draw_with_motors.py

from camera_skeleton_to_coords import capture_skeleton_from_camera
from motor_control import moveXY, cleanup_motors

STEPS_PER_PIXEL = 1  # Tune this based on your motor steps-per-mm
X_ORIGIN, Y_ORIGIN = 0, 0

def draw_contours_with_motors(contours):
    global X_ORIGIN, Y_ORIGIN

    for contour in contours:
        last_x, last_y = X_ORIGIN, Y_ORIGIN

        for x, y in contour:
            dx = x - last_x
            dy = y - last_y

            steps_x = int(abs(dx) * STEPS_PER_PIXEL)
            steps_y = int(abs(dy) * STEPS_PER_PIXEL)

            dir_x = 1 if dx > 0 else 0
            dir_y = 1 if dy > 0 else 0

            moveXY(steps_x, dir_x, steps_y, dir_y)

            last_x, last_y = x, y

        # You can insert Z-axis lift here later

def main():
    print("Capturing skeleton image...")
    contours = capture_skeleton_from_camera()
    print(f"Drawing {len(contours)} contour paths...")
    try:
        draw_contours_with_motors(contours)
    except KeyboardInterrupt:
        print("User interrupted.")
    finally:
        cleanup_motors()

if __name__ == "__main__":
    main()

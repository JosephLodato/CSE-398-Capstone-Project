def simulate_contour(points):
    contour = np.array(points, dtype=np.int32).reshape(-1, 1, 2)
    return [contour]

import numpy as np
import time

# Assume StepperMotor class, moveX, moveY, moveXY, and execute_path are already defined
# Include simulate_contour() helper here

# Define triangle coordinates
triangle_points = [
    (100, 50),  # Top
    (50, 150),  # Bottom Left
    (150, 150), # Bottom Right
    (100, 50)   # Back to Top
]

contours = simulate_contour(triangle_points)

time.sleep(2)
execute_path(contours)

import time
"""
This script controls stepper motors using the gpiod library. It defines a `StepperMotor` class for motor control
and provides functions to move motors along the X and Y axes, as well as combined XY movement.
Classes:
    StepperMotor: Represents a stepper motor and provides methods for setting direction, pulsing, and cleanup.
Functions:
    moveX(steps, direction, delay=0.001):
        Moves the X-axis motors (motorX1 and motorX2) a specified number of steps in a given direction.
        Parameters:
            steps (int): Number of steps to move.
            direction (int): Direction of movement (0 or 1).
            delay (float): Delay between pulses in seconds (default is 0.001).
    moveY(steps, direction, delay=0.001):
        Moves the Y-axis motor (motorY) a specified number of steps in a given direction.
        Parameters:
            steps (int): Number of steps to move.
            direction (int): Direction of movement (0 or 1).
            delay (float): Delay between pulses in seconds (default is 0.001).
    moveXY(x_steps, x_dir, y_steps, y_dir, delay=0.001):
        Moves the motors along both X and Y axes simultaneously.
    cleanup_all():
        Releases all GPIO lines and closes the chip for all motors.
Usage:
    - Initialize the motors with the specified GPIO chip and pins.
    - Use `moveX`, `moveY`, or `moveXY` to move the motors as needed.
    - Call `cleanup_all` to release resources when done.
"""
import gpiod

class StepperMotor:
    def __init__(self, chip_name, dir_pin, step_pin, name="Motor"):
        self.chip = gpiod.Chip(chip_name)
        self.pins = [dir_pin, step_pin]
        self.lines = self.chip.get_lines(self.pins)
        self.lines.request(consumer="mp6500", type=gpiod.LINE_REQ_DIR_OUT)
        self.name = name

    def set_direction(self, direction):
        values = self.lines.get_values()
        values[0] = direction  # DIR
        self.lines.set_values(values)

    def pulse(self, delay=0.001):
        values = self.lines.get_values()
        values[1] = 1  # STEP High
        self.lines.set_values(values)
        time.sleep(delay)
        values[1] = 0  # STEP Low
        self.lines.set_values(values)
        time.sleep(delay)

    def cleanup(self):
        self.lines.release()
        self.chip.close()


# Initialize motors with NEW GPIOs
motorX1 = StepperMotor("gpiochip4", 19, 26, name="X1")  # GPIO17, GPIO18
motorX2 = StepperMotor("gpiochip4", 12, 16, name="X2")  # GPIO22, GPIO23
motorY  = StepperMotor("gpiochip4", 24, 25, name="Y")   # GPIO24, GPIO25

def moveX(steps, direction, delay=0.001):
    motorX1.set_direction(direction)
    motorX2.set_direction(1 - direction)  # Correctly invert (needs to be either 0 or 1, NOT -1 or 1)
    for _ in range(steps):
        motorX1.pulse(delay)
        motorX2.pulse(delay)

def moveY(steps, direction, delay=0.001):
    motorY.set_direction(direction)
    for _ in range(steps):
        motorY.pulse(delay)

def moveXY(x_steps, x_dir, y_steps, y_dir, delay=0.001):
    motorX1.set_direction(x_dir)
    motorX2.set_direction(1 - x_dir)  # Invert here too
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

def cleanup_all():
    motorX1.cleanup()
    motorX2.cleanup()
    motorY.cleanup()


moveX(200, 1)
time.sleep(2.0)
moveY(400, 1)
time.sleep(0.5)
moveY(400, 1)
time.sleep(2.0)
moveX(200, 0)

cleanup_all()
# motor_control.py

import time
import gpiod

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

# Initialize motors
motorX1 = StepperMotor("gpiochip4", 20, 21, 22, 23, 24, name="X1")
motorX2 = StepperMotor("gpiochip4", 25, 26, 27, 28, 29, name="X2")
motorY  = StepperMotor("gpiochip4", 5, 6, 7, 8, 9, name="Y")

def moveX(steps, direction, delay=0.001):
    motorX1.set_direction(direction)
    motorX2.set_direction(direction)
    for _ in range(steps):
        motorX1.pulse(delay)
        motorX2.pulse(delay)

def moveY(steps, direction, delay=0.001):
    motorY.set_direction(direction)
    for _ in range(steps):
        motorY.pulse(delay)

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

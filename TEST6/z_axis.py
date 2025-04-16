import gpiod
import time

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

    def pulse(self, delay=0.001, steps=100):
        for _ in range(steps):
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

# Initialize Z axis motor (update with correct GPIOs)
motorZ = StepperMotor("gpiochip4", 18, 19, name="Z")

try:
    print("Raising Z axis...")
    motorZ.set_direction(1)  # Up
    motorZ.pulse(delay=0.001, steps=200)

    time.sleep(2)

    print("Lowering Z axis...")
    motorZ.set_direction(0)  # Down
    motorZ.pulse(delay=0.001, steps=200)

finally:
    motorZ.cleanup()
    print("Z axis test completed.")

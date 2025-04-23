import RPi.GPIO as GPIO
import time

class StepperMotor:
    def __init__(self, dir_pin, step_pin, name="Motor"):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.name = name

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)

        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)

    def set_direction(self, direction):
        GPIO.output(self.dir_pin, GPIO.HIGH if direction else GPIO.LOW)

    def pulse(self, delay=0.001, steps=100):
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(delay)

    def cleanup(self):
        GPIO.output(self.dir_pin, GPIO.LOW)
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.cleanup([self.dir_pin, self.step_pin])  # Only clean up used pins

# Initialize Z axis motor (update with correct GPIOs)
motorZ = StepperMotor(18, 19, name="Z")

try:
    print("Raising Z axis...")
    motorZ.set_direction(1)  # Down
    motorZ.pulse(delay=0.007, steps=100)

    time.sleep(2)

    print("Lowering Z axis...")
    motorZ.set_direction(0)  # up
    motorZ.pulse(delay=0.007, steps=100)

finally:
    motorZ.cleanup()
    print("Z axis test completed.")

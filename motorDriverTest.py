
import time
import gpiod

# Define GPIO chip and lines for Raspberry Pi 5
chip = gpiod.Chip("gpiochip4")  # Check with `gpioinfo` to confirm
DIR_PIN = 20
STEP_PIN = 21
MS1_PIN = 22  # Optional (Microstepping)
MS2_PIN = 23  # Optional (Microstepping)
ENABLE_PIN = 24  # Optional (Enable, active LOW)

# Open GPIO lines
lines = chip.get_lines([DIR_PIN, STEP_PIN, MS1_PIN, MS2_PIN, ENABLE_PIN])
lines.request(consumer="mp6500", type=gpiod.LINE_REQ_DIR_OUT)

# Set Microstepping Mode (Change this based on your requirement)
MICROSTEPPING_MODE = "FULL"  # Options: FULL, HALF, 1/4, 1/8
MICROSTEP_CONFIG = {
    "FULL": [0, 0],  # Full step
    "HALF": [1, 0],  # Half step
    "1/4": [0, 1],  # Quarter step
    "1/8": [1, 1],  # Eighth step
}

# Set microstepping pins
lines.set_values([0, 0, *MICROSTEP_CONFIG[MICROSTEPPING_MODE], 0])  # Enable LOW

def step_motor(steps, direction, delay=0.001):
    #Function to move stepper motor using MP6500 driver
    lines.set_values([direction, 0, *MICROSTEP_CONFIG[MICROSTEPPING_MODE], 0])  # Set direction
    time.sleep(0.0001)

    for _ in range(steps):
        lines.set_values([direction, 1, *MICROSTEP_CONFIG[MICROSTEPPING_MODE], 0])  # Step High
        time.sleep(delay)
        lines.set_values([direction, 0, *MICROSTEP_CONFIG[MICROSTEPPING_MODE], 0])  # Step Low
        time.sleep(delay)

try:
    print("Rotating motor 200 steps (1 full rotation for 1.8° step)")
    step_motor(200, direction=1)
    time.sleep(1)
    
    print("Rotating motor back")
    step_motor(200, direction=0)

except KeyboardInterrupt:
    print("Stopping motor")

finally:
    lines.set_values([0, 0, 0, 0, 1])  # Disable driver (ENABLE HIGH)
    lines.release()


def moveXAxis():
    print("placeholder")

# X cords: [0, ]
# Y cords: [0, ]
# make funct to move X Motors n steps in xy
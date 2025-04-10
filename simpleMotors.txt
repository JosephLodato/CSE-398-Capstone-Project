import time
import gpiod

chip = gpiod.Chip("gpiochip4")
lines = chip.get_lines([17, 18])  # Example DIR=17, STEP=18
lines.request(consumer="test", type=gpiod.LINE_REQ_DIR_OUT)

print("Setting DIR forward")
lines.set_values([1, 0])
time.sleep(1)

print("Stepping motor slowly...")
for _ in range(200):
    lines.set_values([1, 1])  # STEP High
    time.sleep(0.01)          # 10 ms high
    lines.set_values([1, 0])  # STEP Low
    time.sleep(0.01)          # 10 ms low

print("Done stepping.")
lines.release()
chip.close()

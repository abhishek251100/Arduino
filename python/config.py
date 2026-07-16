"""
config.py  -  all the knobs in one place.

Beginners: you usually only ever touch SERIAL_PORT and CAM_INDEX.
"""

# --- Serial / Arduino -------------------------------------------------------
# Leave as "auto" and the app hunts for your Arduino automatically.
# Or hard-code it, e.g.  "COM5"  on Windows  /  "/dev/ttyUSB0" on Linux
#                        "/dev/tty.usbmodem14101" on a Mac.
SERIAL_PORT = "auto"
BAUD_RATE   = 115200

# If no Arduino is found the app still runs in MOCK mode: it PRINTS every
# command it would have sent, and draws them on screen. Perfect for coding
# and demos when you don't have the hardware plugged in yet.
ALLOW_MOCK = True

# --- Camera -----------------------------------------------------------------
CAM_INDEX = 0          # 0 = default webcam. Try 1, 2.. if you have several.
CAM_WIDTH = 1280
CAM_HEIGHT = 720
FLIP_CAMERA = True     # mirror image so moving right = moving right on screen

# --- Hand detection ---------------------------------------------------------
MAX_HANDS = 2          # 2 = enables two-hand gestures (zoom / twist / explode)
DETECTION_CONFIDENCE = 0.75

# --- Hardware layout (must match the Arduino sketch) ------------------------
NUM_LEDS = 5

# --- Look & feel ------------------------------------------------------------
SHOW_FPS = True

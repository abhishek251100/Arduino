"""
modes.py  -  every "game / feature" lives here as a small class.

Each mode gets the current HandData + the ArduinoLink + the camera image,
draws its own overlay, and sends commands to the board. Switch modes at run
time with the number keys (see main.py). Add your own by copying any class
and appending it to build_modes().

Design so students can read ONE class and understand the whole feature.
"""

import time
import random

import cv2
import config

# ---- musical notes (Hz) for the buzzer -------------------------------------
NOTES = {
    "C4": 262, "D4": 294, "E4": 330, "F4": 349,
    "G4": 392, "A4": 440, "B4": 494, "C5": 523,
}
SCALE = ["C4", "D4", "E4", "F4", "G4", "B4"]      # index by finger count

# ---- tiny drawing helpers --------------------------------------------------
WHITE = (255, 255, 255)
GREEN = (80, 230, 120)
CYAN  = (230, 220, 90)
RED   = (80, 80, 240)
GREY  = (60, 60, 60)


def _panel(img, lines, x=30, y=120):
    for i, (txt, col) in enumerate(lines):
        cv2.putText(img, txt, (x, y + i * 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, col, 2)


def _bar(img, value, maxv, x=30, y=650, w=420, h=34, col=GREEN):
    cv2.rectangle(img, (x, y), (x + w, y + h), GREY, 2)
    frac = 0 if maxv == 0 else max(0.0, min(1.0, value / maxv))
    cv2.rectangle(img, (x, y), (x + int(w * frac), y + h), col, -1)


def _leds(img, states, x=30, y=560, r=22):
    """draw a row of virtual LEDs so you SEE the output without hardware."""
    for i, on in enumerate(states):
        c = (60, 240, 120) if on else (50, 50, 50)
        cx = x + i * (r * 2 + 14)
        cv2.circle(img, (cx, y), r, c, -1)
        cv2.circle(img, (cx, y), r, WHITE, 2)


# ============================================================================
class Mode:
    name = "base"
    help = ""

    def enter(self, link):
        link.send("ALLOFF")

    def update(self, data, link, img):
        ...


# 1) ------------------------------------------------------------- FINGER BAR
class FingerBarMode(Mode):
    """The classic reel: fingers up = that many LEDs light up."""
    name = "Finger LED Bar"
    help = "Hold up 0-5 fingers. That many LEDs turn on."

    def update(self, data, link, img):
        n = data.count if data.found else 0
        link.send_if_changed(f"BAR:{n}")
        _leds(img, [i < n for i in range(config.NUM_LEDS)])
        _panel(img, [(f"Fingers up: {n}", GREEN),
                     (f"Gesture: {data.gesture}", CYAN)])


# 2) --------------------------------------------------------- BINARY COUNTER
class BinaryCounterMode(Mode):
    """Each finger is a bit -> count 0..31 on 5 LEDs. Teaches binary!"""
    name = "Binary Counter"
    help = "Fingers become bits. Count from 0 to 31 with one hand."

    def update(self, data, link, img):
        f = data.fingers if data.found else [0, 0, 0, 0, 0]
        value = sum(bit << i for i, bit in enumerate(f))
        link.send_if_changed(f"MASK:{value}")
        _leds(img, [bool(b) for b in f])
        bits = "".join(str(b) for b in reversed(f))
        _panel(img, [(f"Binary: {bits}", GREEN),
                     (f"Decimal: {value}", CYAN)])


# 3) ------------------------------------------------------ BRIGHTNESS (PINCH)
class BrightnessMode(Mode):
    """Pinch thumb+index: far apart = bright, together = dim (PWM)."""
    name = "Pinch Dimmer"
    help = "Pinch thumb & index. Spread = brighter, close = dimmer."

    def update(self, data, link, img):
        if data.found:
            v = int(max(0, min(255, (data.pinch - 20) / 180 * 255)))
        else:
            v = 0
        link.send_if_changed(f"BRIGHT:{v}")
        _bar(img, v, 255)
        _panel(img, [(f"Brightness: {v}/255", GREEN),
                     (f"Pinch dist: {int(data.pinch)} px", CYAN)])


# 4) ------------------------------------------------------------- RGB MIXER
class RGBMixerMode(Mode):
    """Move your hand to mix colour: X=Red, Y=Green, pinch=Blue."""
    name = "RGB Colour Mixer"
    help = "Move hand: left/right = Red, up/down = Green, pinch = Blue."

    def update(self, data, link, img):
        if data.found:
            r = int(data.nx * 255)
            g = int((1 - data.ny) * 255)
            b = int(max(0, min(255, (data.pinch - 20) / 180 * 255)))
        else:
            r = g = b = 0
        link.send_if_changed(f"RGB:{r},{g},{b}")
        cv2.rectangle(img, (960, 540), (1240, 690), (b, g, r), -1)
        cv2.rectangle(img, (960, 540), (1240, 690), WHITE, 2)
        _panel(img, [(f"R {r}", (80, 80, 240)),
                     (f"G {g}", (80, 240, 80)),
                     (f"B {b}", (240, 160, 80))])


# 5) ------------------------------------------------------------ SERVO STEER
class ServoMode(Mode):
    """Hand left/right steers a servo motor 0..180 degrees."""
    name = "Servo Steering"
    help = "Move hand left/right to sweep the servo motor."

    def update(self, data, link, img):
        angle = int(data.nx * 180) if data.found else 90
        link.send_if_changed(f"SERVO:{angle}")
        # draw a virtual dial
        cx, cy, R = 1100, 600, 90
        import math
        a = math.radians(180 - angle)
        ex, ey = int(cx + R * math.cos(a)), int(cy - R * math.sin(a))
        cv2.ellipse(img, (cx, cy), (R, R), 0, 180, 360, GREY, 3)
        cv2.line(img, (cx, cy), (ex, ey), GREEN, 5)
        _panel(img, [(f"Servo angle: {angle} deg", GREEN)])


# 6) -------------------------------------------------------------- THEREMIN
class ThereminMode(Mode):
    """Hand height controls a continuous tone, like a theremin."""
    name = "Theremin"
    help = "Raise/lower your hand to change the pitch. Fist = silence."

    def update(self, data, link, img):
        if data.found and data.gesture != "fist":
            freq = int(200 + (1 - data.ny) * 1000)      # 200..1200 Hz
        else:
            freq = 0
        link.send_if_changed(f"TONE:{freq}")
        _bar(img, freq, 1200, col=CYAN)
        _panel(img, [(f"Pitch: {freq} Hz", GREEN),
                     ("Fist to mute", CYAN)])


# 7) ----------------------------------------------------------- FINGER PIANO
class PianoMode(Mode):
    """Number of fingers picks a musical note. A tiny playable instrument."""
    name = "Finger Piano"
    help = "1-6 fingers each play a different note on the buzzer."

    def __init__(self):
        self._last = -1

    def update(self, data, link, img):
        n = data.count if data.found else 0
        if n != self._last:
            self._last = n
            if 1 <= n <= len(SCALE):
                note = SCALE[n - 1]
                link.send(f"TONE:{NOTES[note]}")
                self._note = note
            else:
                link.send("TONE:0")
                self._note = "-"
        _panel(img, [(f"Fingers: {n}", GREEN),
                     (f"Note: {getattr(self, '_note', '-')}", CYAN)])


# 8) --------------------------------------------------------- REACTION GAME
class ReactionGameMode(Mode):
    """A random LED lights up; OPEN your hand fast to catch it. Beats time."""
    name = "Reaction Game"
    help = "Wait for the LED, then open your hand ASAP. Lower time = better."

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = "wait"         # wait -> lit -> done
        self.target = 0
        self.t_next = time.time() + random.uniform(1.5, 4.0)
        self.t_lit = 0
        self.best = None
        self.score = None

    def enter(self, link):
        link.send("ALLOFF")
        self.reset()

    def update(self, data, link, img):
        now = time.time()
        if self.state == "wait":
            if now >= self.t_next:
                self.target = random.randint(0, config.NUM_LEDS - 1)
                link.send(f"LED:{self.target},1")
                self.t_lit = now
                self.state = "lit"
        elif self.state == "lit":
            if data.found and data.count >= 4:      # open hand = caught
                self.score = round((now - self.t_lit) * 1000)
                self.best = self.score if self.best is None else min(self.best, self.score)
                link.send("ALLOFF")
                self.state = "done"
                self.t_next = now + 1.5
        elif self.state == "done":
            if now >= self.t_next:
                self.state = "wait"
                self.t_next = now + random.uniform(1.5, 4.0)

        leds = [i == self.target and self.state == "lit" for i in range(config.NUM_LEDS)]
        _leds(img, leds)
        lines = [(f"State: {self.state.upper()}", GREEN)]
        if self.score is not None:
            lines.append((f"Last: {self.score} ms", CYAN))
        if self.best is not None:
            lines.append((f"Best: {self.best} ms", GREEN))
        _panel(img, lines)


# 9) ------------------------------------------------------------ SIMON SAYS
class SimonSaysMode(Mode):
    """Memory game: watch the LED flash sequence, repeat it with finger counts."""
    name = "Simon Says"
    help = "Watch the flashes, then show that LED number with your fingers."

    def __init__(self):
        self.reset()

    def reset(self):
        self.seq = []
        self.phase = "show"
        self.idx = 0
        self.t = 0
        self.input_idx = 0
        self.level = 0
        self._prev_count = -1

    def enter(self, link):
        link.send("ALLOFF")
        self.reset()
        self._grow(link)

    def _grow(self, link):
        self.seq.append(random.randint(1, config.NUM_LEDS))
        self.level = len(self.seq)
        self.phase = "show"
        self.idx = 0
        self.t = time.time()

    def update(self, data, link, img):
        now = time.time()
        leds = [False] * config.NUM_LEDS

        if self.phase == "show":
            step = int((now - self.t) / 0.6)
            if step >= len(self.seq):
                self.phase = "input"
                self.input_idx = 0
                self._prev_count = -1
                link.send("ALLOFF")
            else:
                lit = (now - self.t - step * 0.6) < 0.35
                val = self.seq[step]
                if lit:
                    for i in range(val):
                        leds[i] = True
                    link.send_if_changed(f"BAR:{val}")
                else:
                    link.send_if_changed("BAR:0")

        elif self.phase == "input":
            n = data.count if data.found else 0
            for i in range(n):
                leds[i] = True
            # accept a value when the count is steady and the hand shows a fist->N
            if data.found and n >= 1 and n != self._prev_count:
                expected = self.seq[self.input_idx]
                if n == expected:
                    self.input_idx += 1
                    link.send(f"BAR:{n}")
                    if self.input_idx >= len(self.seq):
                        self.phase = "win"
                        self.t = now
                else:
                    self.phase = "lose"
                    self.t = now
            self._prev_count = n if data.found else -1

        elif self.phase == "win":
            link.send_if_changed("BAR:5")
            if now - self.t > 1.0:
                self._grow(link)

        elif self.phase == "lose":
            link.send_if_changed("ALLOFF")
            if now - self.t > 1.5:
                self.enter(link)

        _leds(img, leds)
        _panel(img, [(f"Level: {self.level}", GREEN),
                     (f"Phase: {self.phase.upper()}", CYAN)])


# 10) ---------------------------------------------------------- ULTRA RADAR
class RadarMode(Mode):
    """Uses the ultrasonic sensor: closer object = more LEDs + faster beep."""
    name = "Distance Radar"
    help = "Move an object near the ultrasonic sensor. Closer = more LEDs."

    def enter(self, link):
        link.send("ALLOFF")
        link.enable_stream(True)

    def update(self, data, link, img):
        dist = link.sensors.get("dist", -1)
        if dist is None or dist < 0:
            n = 0
            txt = "no echo (mock? or out of range)"
        else:
            # 0 cm -> full bar, 40 cm+ -> empty
            n = max(0, min(config.NUM_LEDS,
                           config.NUM_LEDS - int(dist / (40 / config.NUM_LEDS))))
            txt = f"{dist:.0f} cm"
        link.send_if_changed(f"BAR:{n}")
        _leds(img, [i < n for i in range(config.NUM_LEDS)])
        _panel(img, [(f"Distance: {txt}", GREEN),
                     (f"Bar: {n}/{config.NUM_LEDS}", CYAN)])


# 11) --------------------------------------------------------- LDR NIGHTLIGHT
class NightLightMode(Mode):
    """Uses the light sensor: dark room -> RGB glows; bright room -> off."""
    name = "Auto Night Light"
    help = "Cover the light sensor (LDR). Dark = light turns on automatically."

    def enter(self, link):
        link.send("ALLOFF")
        link.enable_stream(True)

    def update(self, data, link, img):
        ldr = link.sensors.get("ldr", -1)
        if ldr is None or ldr < 0:
            level = 0
            txt = "no reading (mock?)"
        else:
            # assume 0..1023: darker -> lower value -> brighter light
            level = int(max(0, min(255, (600 - ldr) / 600 * 255)))
            txt = f"{ldr:.0f}"
        link.send_if_changed(f"RGB:{level},{level},{level}")
        _bar(img, level, 255, col=CYAN)
        _panel(img, [(f"Light sensor: {txt}", GREEN),
                     (f"Lamp: {level}/255", CYAN)])


# 12) ------------------------------------------------------------- POT KNOB
class PotKnobMode(Mode):
    """Uses the potentiometer knob to drive the LED bar + servo. No hand needed."""
    name = "Knob Control"
    help = "Turn the potentiometer knob to move the LED bar and servo."

    def enter(self, link):
        link.send("ALLOFF")
        link.enable_stream(True)

    def update(self, data, link, img):
        pot = link.sensors.get("pot", -1)
        if pot is None or pot < 0:
            frac = 0
            txt = "no reading (mock?)"
        else:
            frac = max(0.0, min(1.0, pot / 1023))
            txt = f"{pot:.0f}"
        n = round(frac * config.NUM_LEDS)
        link.send_if_changed(f"BAR:{n}")
        link.send(f"SERVO:{int(frac * 180)}")
        _leds(img, [i < n for i in range(config.NUM_LEDS)])
        _panel(img, [(f"Knob: {txt}", GREEN),
                     (f"Bar: {n}  Servo: {int(frac*180)} deg", CYAN)])


def build_modes():
    """Order here = the number keys 1..9,0 in the app."""
    return [
        FingerBarMode(),      # 1
        BinaryCounterMode(),  # 2
        BrightnessMode(),     # 3
        RGBMixerMode(),       # 4
        ServoMode(),          # 5
        ThereminMode(),       # 6
        PianoMode(),          # 7
        ReactionGameMode(),   # 8
        SimonSaysMode(),      # 9
        RadarMode(),          # 0
        NightLightMode(),     # -
        PotKnobMode(),        # =
    ]

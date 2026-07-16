"""
gesture_engine.py  -  turns raw hand data into HIGH-LEVEL actions.

The tracker tells you "the hand is here, fingers are up". This engine watches
those over time and produces the verbs you actually want for 3D:

    events (fire once):        continuous state (every frame):
      grab / release             .rotate = (dx, dy)   spin while grabbing
      swipe_left / _right          .zoom   = factor    >1 zoom in, <1 out
      swipe_up / _down             .twist  = degrees   two-hand rotation
      slice  (scalpel cut)         .grabbing = bool
      select (point + hold)        .explode = 0..1     two-hand spread amount

Feed it the list of HandData from the tracker plus a timestamp:
    events = engine.update(tracker.hands, now)

It is deliberately framework-agnostic: the 3D lab, the games and even the
LED modes can all read the same verbs.
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict

import config


@dataclass
class GestureEvent:
    name: str
    data: dict = field(default_factory=dict)


# tuning knobs (in normalised 0..1 screen units unless noted)
SWIPE_SPEED = 1.4          # screen-widths per second to count as a swipe
SWIPE_COOLDOWN = 0.5       # seconds between swipes
GRAB_OPEN = 4              # fingers >= this = "open hand"
PINCH_PX = 45              # thumb-index gap below this = "pinching"
SLICE_MIN_TRAVEL = 0.25    # how far a pinch must travel to count as a cut


class GestureEngine:
    def __init__(self):
        self._prev: Dict[str, dict] = {}     # per hand-role history
        self.grabbing = False
        self.rotate = (0.0, 0.0)
        self.zoom = 1.0
        self.twist = 0.0
        self.explode = 0.0
        self._two_prev_dist = None
        self._two_prev_angle = None
        self._last_swipe_t = -999.0     # so the very first swipe isn't blocked
        self._slice_start = None            # (nx, ny) where a pinch-drag began
        self._select_since = None

    # -----------------------------------------------------------------
    def update(self, hands: List, now: float) -> List[GestureEvent]:
        events: List[GestureEvent] = []
        # reset per-frame continuous values
        self.rotate = (0.0, 0.0)
        self.zoom = 1.0
        self.twist = 0.0

        present = [h for h in hands if h.found]

        if len(present) >= 2:
            self._two_hand(present[0], present[1], now, events)
        else:
            self._two_prev_dist = None
            self._two_prev_angle = None

        if len(present) == 1:
            self._one_hand(present[0], now, events)
        elif len(present) == 0:
            self._reset_one_hand(now)

        return events

    # ---- ONE-HAND interactions -------------------------------------
    def _one_hand(self, h, now, events):
        role = "primary"
        prev = self._prev.get(role)
        vx = vy = 0.0
        if prev:
            dt = max(now - prev["t"], 1e-3)
            vx = (h.nx - prev["nx"]) / dt
            vy = (h.ny - prev["ny"]) / dt

        # --- grab / release (open <-> fist) ---
        was_grab = self.grabbing
        if h.count == 0:
            self.grabbing = True
        elif h.count >= GRAB_OPEN:
            self.grabbing = False
        if self.grabbing and not was_grab:
            events.append(GestureEvent("grab", {"nx": h.nx, "ny": h.ny}))
        elif was_grab and not self.grabbing:
            events.append(GestureEvent("release"))

        # --- rotate while grabbing (drag the fist) ---
        if self.grabbing and prev:
            self.rotate = ((h.nx - prev["nx"]), (h.ny - prev["ny"]))

        # --- pinch-zoom (one hand): closer pinch = zoom out ---
        if h.pinch < 200 and prev and "pinch" in prev and prev["pinch"] < 200:
            delta = h.pinch - prev["pinch"]
            self.zoom = 1.0 + delta / 400.0

        # --- scalpel slice: pinch, then drag across, then open ---
        pinching = h.pinch < PINCH_PX
        if pinching and self._slice_start is None:
            self._slice_start = (h.nx, h.ny)
        elif not pinching and self._slice_start is not None:
            sx, sy = self._slice_start
            if math.hypot(h.nx - sx, h.ny - sy) >= SLICE_MIN_TRAVEL:
                events.append(GestureEvent("slice", {
                    "start": (sx, sy), "end": (h.nx, h.ny)}))
            self._slice_start = None

        # --- swipe (fast open-hand flick, only when not grabbing) ---
        if not self.grabbing and (now - self._last_swipe_t) > SWIPE_COOLDOWN:
            if abs(vx) > SWIPE_SPEED and abs(vx) > abs(vy):
                events.append(GestureEvent("swipe_right" if vx > 0 else "swipe_left"))
                self._last_swipe_t = now
            elif abs(vy) > SWIPE_SPEED and abs(vy) > abs(vx):
                events.append(GestureEvent("swipe_down" if vy > 0 else "swipe_up"))
                self._last_swipe_t = now

        # --- point + hold = select ---
        if h.gesture == "point":
            if self._select_since is None:
                self._select_since = now
            elif now - self._select_since > 0.6:
                events.append(GestureEvent("select", {"nx": h.nx, "ny": h.ny}))
                self._select_since = now + 0.6   # re-arm
        else:
            self._select_since = None

        self._prev[role] = {"nx": h.nx, "ny": h.ny, "pinch": h.pinch, "t": now}

    def _reset_one_hand(self, now):
        self._prev.pop("primary", None)
        self._slice_start = None
        self._select_since = None
        if self.grabbing:
            self.grabbing = False

    # ---- TWO-HAND interactions -------------------------------------
    def _two_hand(self, a, b, now, events):
        dist = math.hypot(a.nx - b.nx, a.ny - b.ny)
        angle = math.degrees(math.atan2(b.ny - a.ny, b.nx - a.nx))

        if self._two_prev_dist is not None and self._two_prev_dist > 1e-3:
            self.zoom = dist / self._two_prev_dist
        if self._two_prev_angle is not None:
            d = angle - self._two_prev_angle
            # keep it in -180..180
            self.twist = (d + 180) % 360 - 180

        self.explode = min(1.0, dist / 0.8)     # hands wide apart = fully exploded
        self._two_prev_dist = dist
        self._two_prev_angle = angle


# quick self-check
if __name__ == "__main__":
    from hand_tracker import HandData
    eng = GestureEngine()
    t = 0.0
    # simulate: open hand -> fist (grab) -> drag right (rotate)
    seq = [HandData(found=True, count=5, nx=0.5, ny=0.5, pinch=300),
           HandData(found=True, count=0, nx=0.5, ny=0.5, pinch=300),
           HandData(found=True, count=0, nx=0.7, ny=0.5, pinch=300)]
    for hd in seq:
        evs = eng.update([hd], t)
        print(f"t={t:.1f}", [e.name for e in evs], "rotate=", eng.rotate)
        t += 0.1

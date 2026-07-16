"""
game.py  -  "SLICE SURGEON", a gesture game.   Run:  python game.py

Each round shows a 3D specimen and a target CUT LINE at some angle. Perform the
scalpel gesture (pinch thumb+index, drag across, release) so your cut matches the
target angle before time runs out. Accurate cuts score big; each level tightens
the tolerance and shortens the clock. Three misses and it's over.

The scoring logic (SliceSurgeon) is pure Python -> unit-tested in test_game.py
with no camera or monitor.
"""

import math
import random
import sys
import time

import cv2

import config
from hand_tracker import HandTracker
from gesture_engine import GestureEngine
from object_lab import Scene3D

SPECIMENS = ["cell", "atom", "earth"]


def line_angle(x1, y1, x2, y2):
    """Angle of a stroke as a 0..180 orientation (a line, not a direction)."""
    a = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return a % 180


def angle_diff(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


class SliceSurgeon:
    def __init__(self, seed_angle=None):
        self._seed = seed_angle
        self.reset()

    def reset(self, now=0.0):
        self.score = 0
        self.level = 1
        self.lives = 3
        self.over = False
        self.flash = ""            # "HIT!" / "MISS" feedback
        self.flash_until = 0.0
        self._new_round(now)

    def _new_round(self, now):
        self.target = self._seed if self._seed is not None else random.uniform(0, 180)
        self.tolerance = max(7.0, 24.0 - self.level * 2.0)     # degrees
        self.time_limit = max(3.0, 8.0 - self.level * 0.4)     # seconds
        self.deadline = now + self.time_limit
        self.specimen = SPECIMENS[(self.level - 1) % len(SPECIMENS)]

    def _feedback(self, text, now):
        self.flash = text
        self.flash_until = now + 0.9

    # returns a dict describing what happened this frame (for the UI/tests)
    def update(self, events, now):
        result = {"event": None}
        if self.over:
            return result

        if now > self.deadline:
            self.lives -= 1
            self._feedback("TIME!", now)
            result["event"] = "timeout"
            if self.lives <= 0:
                self.over = True
            else:
                self._new_round(now)
            return result

        for e in events:
            if e.name == "slice":
                s, en = e.data["start"], e.data["end"]
                cut = line_angle(s[0], s[1], en[0], en[1])
                diff = angle_diff(cut, self.target)
                if diff <= self.tolerance:
                    gained = int(100 + max(0, (self.tolerance - diff)) * 10)
                    self.score += gained
                    self.level += 1
                    self._feedback(f"HIT +{gained}", now)
                    result.update(event="hit", gained=gained, cut=cut)
                    self._new_round(now)
                else:
                    self.lives -= 1
                    self._feedback("MISS", now)
                    result.update(event="miss", cut=cut, diff=diff)
                    if self.lives <= 0:
                        self.over = True
                    else:
                        self._new_round(now)
                break
        return result


# ---------------------------------------------------------------- drawing
def draw_overlay(img, game, now):
    H, W = img.shape[:2]
    cx, cy = W // 2, H // 2

    if not game.over:
        # target cut line through the centre at the required angle
        rad = math.radians(game.target)
        dx, dy = math.cos(rad), math.sin(rad)
        L = max(W, H)
        p1 = (int(cx - dx * L), int(cy - dy * L))
        p2 = (int(cx + dx * L), int(cy + dy * L))
        cv2.line(img, p1, p2, (0, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(img, f"CUT AT {int(game.target)} deg  (+/-{int(game.tolerance)})",
                    (18, H - 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 220, 255), 2)
        tleft = max(0.0, game.deadline - now)
        cv2.putText(img, f"{tleft:4.1f}s", (W - 130, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                    (60, 60, 240) if tleft < 2 else (235, 235, 235), 2)

    hud = f"Score {game.score}   Level {game.level}   Lives {'#' * game.lives}"
    cv2.putText(img, hud, (18, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (235, 235, 235), 2)

    if game.flash and now < game.flash_until:
        col = (90, 240, 130) if game.flash.startswith("HIT") else (60, 60, 240)
        cv2.putText(img, game.flash, (cx - 90, cy - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, col, 4)

    if game.over:
        cv2.putText(img, "GAME OVER", (cx - 180, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.8, (60, 60, 240), 4)
        cv2.putText(img, f"Final score: {game.score}   press R to retry",
                    (cx - 230, cy + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (235, 235, 235), 2)
    return img


def run():
    print("=" * 56)
    print(" AYUS  |  SLICE SURGEON")
    print("=" * 56)
    game = SliceSurgeon()
    game.reset(time.time())
    scene = Scene3D(game.specimen)
    engine = GestureEngine()

    cap = cv2.VideoCapture(config.CAM_INDEX,
                           cv2.CAP_DSHOW if sys.platform == "win32" else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)
    if not cap.isOpened():
        print("[ERROR] Camera not found. Check CAM_INDEX in config.py.")
        return
    tracker = HandTracker(config.CAM_WIDTH, config.CAM_HEIGHT)

    last_specimen = game.specimen
    print("Ready. Match the yellow line with a scalpel slice (pinch + drag).\n")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if config.FLIP_CAMERA:
            frame = cv2.flip(frame, 1)

        _, frame = tracker.process(frame)
        now = time.time()
        events = engine.update(tracker.hands, now)
        res = game.update(events, now)

        if game.specimen != last_specimen:
            scene.load(game.specimen)
            last_specimen = game.specimen
        scene.rotate(0.004, 0.0)          # gentle idle spin
        if res["event"] == "hit":
            scene.slice(0, 0.5, 1, 0.5)   # show the cut briefly
        elif res["event"] in ("miss", "timeout", None):
            pass

        scene_img = cv2.cvtColor(scene.render(), cv2.COLOR_RGB2BGR)
        # camera picture-in-picture
        pip_w = scene_img.shape[1] // 4
        pip = cv2.resize(frame, (pip_w, int(pip_w * frame.shape[0] / frame.shape[1])))
        ph, pw = pip.shape[:2]
        scene_img[10:10 + ph, scene_img.shape[1] - pw - 10:scene_img.shape[1] - 10] = pip

        draw_overlay(scene_img, game, now)
        cv2.imshow("AYUS - Slice Surgeon", scene_img)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key == ord('r'):
            game.reset(time.time())
            scene.unslice()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()

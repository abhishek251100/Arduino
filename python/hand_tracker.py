"""
hand_tracker.py  -  the "eyes" of the project.

Wraps cvzone / mediapipe so the rest of the code gets clean, friendly data
about the hand(s) in front of the camera. Now supports UP TO TWO hands, which
unlocks two-hand gestures (zoom, twist, explode) used by the 3D features.

Per hand you get:
    .found      True if this hand is visible
    .fingers    [thumb, index, middle, ring, pinky]  each 0/1
    .count      how many fingers are up (0..5)
    .gesture    "fist" / "open" / "point" / "peace" / "thumbs_up" ...
    .pinch      pixels between thumb-tip and index-tip (small = pinching)
    .center     (x, y) middle of the hand
    .nx, .ny    position as 0..1  (0 = left/top, 1 = right/bottom)
    .size       hand bounding-box diagonal in px (a rough "how close" value)
    .hand_type  "Left" / "Right"
    .lm         raw 21 landmark points

process() returns (primary_hand, annotated_img) for backward compatibility
(the old LED modes only ever use one hand). All detected hands are also kept
in tracker.hands  -> a list you can pass to the GestureEngine.
"""

import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

import config

try:
    from cvzone.HandTrackingModule import HandDetector
    HAVE_CVZONE = True
except Exception:                       # pragma: no cover
    HAVE_CVZONE = False


@dataclass
class HandData:
    found: bool = False
    fingers: List[int] = field(default_factory=lambda: [0, 0, 0, 0, 0])
    count: int = 0
    gesture: str = "none"
    pinch: float = 999.0
    center: Tuple[int, int] = (0, 0)
    nx: float = 0.5
    ny: float = 0.5
    size: float = 0.0
    hand_type: str = ""
    lm: Optional[list] = None


_GESTURES = {
    (0, 0, 0, 0, 0): "fist",
    (1, 1, 1, 1, 1): "open",
    (0, 1, 0, 0, 0): "point",
    (0, 1, 1, 0, 0): "peace",
    (1, 0, 0, 0, 0): "thumbs_up",
    (0, 0, 0, 0, 1): "pinky",
    (0, 1, 0, 0, 1): "rock",
    (1, 1, 0, 0, 1): "spiderman",
    (1, 0, 0, 0, 1): "call_me",
    (1, 1, 1, 0, 0): "three",
}


class HandTracker:
    def __init__(self, frame_w=None, frame_h=None):
        if not HAVE_CVZONE:
            raise RuntimeError(
                "cvzone/mediapipe not installed. Run:  pip install -r requirements.txt"
            )
        self.detector = HandDetector(
            maxHands=config.MAX_HANDS,
            detectionCon=config.DETECTION_CONFIDENCE,
        )
        self.frame_w = frame_w or config.CAM_WIDTH
        self.frame_h = frame_h or config.CAM_HEIGHT
        self.hands: List[HandData] = []          # all hands this frame

    def _to_handdata(self, hand, img) -> HandData:
        lm = hand["lmList"]
        d = HandData(found=True, lm=lm)
        d.hand_type = hand.get("type", "")
        d.center = tuple(hand.get("center", (0, 0)))

        bx, by, bw, bh = hand.get("bbox", (0, 0, 0, 0))
        d.size = math.hypot(bw, bh)

        try:
            d.fingers = self.detector.fingersUp(hand)
        except Exception:
            d.fingers = [0, 0, 0, 0, 0]
        d.count = int(sum(d.fingers))
        d.gesture = _GESTURES.get(tuple(d.fingers), f"{d.count}-fingers")

        try:
            res = self.detector.findDistance(lm[4][:2], lm[8][:2], img)
            d.pinch = float(res[0])
        except Exception:
            d.pinch = 999.0

        cx, cy = d.center
        d.nx = min(max(cx / max(self.frame_w, 1), 0.0), 1.0)
        d.ny = min(max(cy / max(self.frame_h, 1), 0.0), 1.0)
        return d

    def process(self, img):
        """Run detection on a BGR frame; returns (primary_hand, annotated_img).
        Also fills self.hands with EVERY detected hand."""
        try:
            hands, img = self.detector.findHands(img, draw=True, flipType=False)
        except TypeError:
            hands = self.detector.findHands(img, draw=True)
            if isinstance(hands, tuple):
                hands, img = hands

        self.hands = [self._to_handdata(h, img) for h in (hands or [])]
        primary = self.hands[0] if self.hands else HandData()
        return primary, img

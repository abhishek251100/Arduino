"""
studio.py  -  the LIVE 3D experience.   Run:  python studio.py

Your hands drive a real 3D model on screen:
    open hand -> fist (GRAB) then move   = rotate the object
    pinch thumb+index and change the gap  = zoom
    TWO hands, move them apart / together = explode the model into its parts
    pinch + drag across (SCALPEL)         = slice it open (cross-section)
    swipe left / right                    = previous / next model
    point + hold                          = un-slice / reset the cut
    keys:  1 cell   2 atom   3 earth   r reset   q quit

The per-frame logic lives in drive_scene() so it can be unit-tested with no
camera or monitor (see test_studio.py).
"""

import sys
import time

import cv2
import numpy as np

import config
from hand_tracker import HandTracker
from gesture_engine import GestureEngine
from object_lab import Scene3D

MODELS = ["cell", "atom", "earth"]


def cycle_model(scene, state, step):
    state["idx"] = (state["idx"] + step) % len(MODELS)
    scene.load(MODELS[state["idx"]])


def drive_scene(scene, engine, events, state):
    """Apply gesture state + events to the 3D scene. Pure logic -> testable."""
    if engine.grabbing:
        dx, dy = engine.rotate
        scene.rotate(dx, dy)

    if abs(engine.zoom - 1.0) > 1e-3:
        scene.zoom(engine.zoom)

    if engine.explode > 0.02:
        scene.set_explode(engine.explode)

    for e in events:
        if e.name == "slice":
            s, en = e.data["start"], e.data["end"]
            scene.slice(s[0], s[1], en[0], en[1])
        elif e.name == "swipe_right":
            cycle_model(scene, state, +1)
        elif e.name == "swipe_left":
            cycle_model(scene, state, -1)
        elif e.name == "select":
            scene.unslice()


# ------------------------------------------------------------- compositing
def compose(scene_img, cam_img, hud_lines):
    """3D render as the main view, camera as a picture-in-picture, + HUD text."""
    out = cv2.cvtColor(scene_img, cv2.COLOR_RGB2BGR)
    H, W = out.shape[:2]

    pip_w = W // 4
    pip = cv2.resize(cam_img, (pip_w, int(pip_w * cam_img.shape[0] / cam_img.shape[1])))
    ph, pw = pip.shape[:2]
    out[10:10 + ph, W - pw - 10:W - 10] = pip
    cv2.rectangle(out, (W - pw - 10, 10), (W - 10, 10 + ph), (90, 90, 90), 1)

    for i, txt in enumerate(hud_lines):
        cv2.putText(out, txt, (18, 34 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (235, 235, 235), 2)
    return out


def main():
    print("=" * 56)
    print(" AYUS  |  3D GESTURE STUDIO")
    print("=" * 56)

    scene = Scene3D(MODELS[0])
    engine = GestureEngine()
    state = {"idx": 0}

    cap = cv2.VideoCapture(config.CAM_INDEX,
                           cv2.CAP_DSHOW if sys.platform == "win32" else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)
    if not cap.isOpened():
        print("[ERROR] Camera not found. Check CAM_INDEX in config.py.")
        return
    tracker = HandTracker(config.CAM_WIDTH, config.CAM_HEIGHT)

    print("Ready. Grab & drag to rotate, two hands to explode, pinch-drag to slice.\n")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if config.FLIP_CAMERA:
            frame = cv2.flip(frame, 1)

        _, frame = tracker.process(frame)
        events = engine.update(tracker.hands, time.time())
        drive_scene(scene, engine, events, state)

        scene_img = scene.render()
        hands_n = sum(1 for h in tracker.hands if h.found)
        hud = [
            f"Model: {scene.title}   ({state['idx']+1}/{len(MODELS)})",
            f"Hands: {hands_n}   Grab: {'YES' if engine.grabbing else 'no'}"
            f"   Explode: {scene.explode_amt:.2f}",
            "1/2/3 model   r reset   q quit",
        ]
        cv2.imshow("AYUS - 3D Gesture Studio", compose(scene_img, frame, hud))

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):
            break
        elif key == ord('r'):
            scene.reset_view()
        elif key in (ord('1'), ord('2'), ord('3')):
            state["idx"] = key - ord('1')
            scene.load(MODELS[state["idx"]])

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

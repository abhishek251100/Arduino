"""
test_studio.py  -  drive the 3D studio logic with simulated gestures, no camera
or monitor. Confirms grab-rotate, two-hand-explode, slice and swipe-change-model
all reach the 3D scene without errors and actually change its state.

    python test_studio.py
"""

from hand_tracker import HandData
from gesture_engine import GestureEngine
from object_lab import Scene3D
from studio import drive_scene, MODELS


def H(**kw):
    base = dict(found=True, count=5, nx=0.5, ny=0.5, pinch=300)
    base.update(kw)
    return HandData(**base)


def check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    return cond


def main():
    ok = True
    scene = Scene3D(MODELS[0])
    engine = GestureEngine()
    state = {"idx": 0}
    t = 0.0

    def frame(hands):
        nonlocal t
        ev = engine.update(hands, t)
        drive_scene(scene, engine, ev, state)
        t += 0.1
        return ev

    # grab + drag -> rotation changes
    az0 = scene.azim
    frame([H(count=5)])                       # open
    frame([H(count=0, nx=0.4)])               # fist (grab)
    frame([H(count=0, nx=0.7)])               # drag right
    ok &= check("grab + drag rotates the model", scene.azim != az0)

    # two hands apart -> explode grows
    frame([H(nx=0.45), H(nx=0.55)])
    frame([H(nx=0.15), H(nx=0.85)])
    ok &= check("two-hand spread explodes the model", scene.explode_amt > 0.2)

    # scalpel slice -> a clip plane is set
    frame([H(count=2, pinch=20, nx=0.2, ny=0.5)])
    frame([H(count=2, pinch=20, nx=0.7, ny=0.5)])
    frame([H(count=2, pinch=300, nx=0.75, ny=0.5)])
    ok &= check("pinch-drag sets a slice plane", scene.clip is not None)

    # swipe right -> next model
    idx0 = state["idx"]
    frame([H(nx=0.15)])
    frame([H(nx=0.9)])
    ok &= check("swipe changes the model", state["idx"] != idx0)

    # render still works after all that
    img = scene.render()
    ok &= check("scene still renders a valid frame", img.shape[2] == 3)

    print("\nRESULT:", "3D STUDIO OK" if ok else "SOMETHING WRONG")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

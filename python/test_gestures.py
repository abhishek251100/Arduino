"""
test_gestures.py  -  prove the gesture engine detects every high-level verb,
without a camera. Simulates hand sequences and checks the right event fires.

    python test_gestures.py
"""

from hand_tracker import HandData
from gesture_engine import GestureEngine


def run(seq, dt=0.1):
    """Feed a list of (hands_list) frames; return all events + final engine."""
    eng = GestureEngine()
    t, all_events = 0.0, []
    for hands in seq:
        for e in eng.update(hands, t):
            all_events.append(e.name)
        t += dt
    return all_events, eng


def H(**kw):
    base = dict(found=True, count=5, nx=0.5, ny=0.5, pinch=300)
    base.update(kw)
    return HandData(**base)


def check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    return cond


def main():
    ok = True

    # grab + release
    ev, eng = run([[H(count=5)], [H(count=0)], [H(count=5)]])
    ok &= check("grab fires on open->fist", "grab" in ev)
    ok &= check("release fires on fist->open", "release" in ev)

    # rotate while grabbing (drag the fist sideways)
    ev, eng = run([[H(count=0, nx=0.4)], [H(count=0, nx=0.6)]])
    ok &= check("rotate delta produced while grabbing", eng.rotate[0] > 0.1)

    # swipe right: fast open-hand move across screen
    ev, eng = run([[H(nx=0.2)], [H(nx=0.85)]], dt=0.1)
    ok &= check("swipe_right on fast rightward flick", "swipe_right" in ev)

    # swipe up
    ev, eng = run([[H(ny=0.85)], [H(ny=0.2)]], dt=0.1)
    ok &= check("swipe_up on fast upward flick", "swipe_up" in ev)

    # scalpel slice: pinch, drag across, open
    ev, eng = run([[H(count=2, pinch=20, nx=0.2, ny=0.5)],
                   [H(count=2, pinch=20, nx=0.6, ny=0.5)],
                   [H(count=2, pinch=300, nx=0.7, ny=0.5)]])
    ok &= check("slice fires on pinch-drag-release", "slice" in ev)

    # select: point and hold
    ev, eng = run([[H(count=1, fingers=[0, 1, 0, 0, 0], gesture="point")]] * 10)
    ok &= check("select fires on point + hold", "select" in ev)

    # two-hand zoom: hands moving apart -> zoom > 1
    ev, eng = run([[H(nx=0.45), H(nx=0.55)], [H(nx=0.2), H(nx=0.8)]])
    ok &= check("two-hand spread produces zoom>1", eng.zoom > 1.0)
    ok &= check("two-hand spread raises explode", eng.explode > 0.3)

    # two-hand twist: rotate the pair
    ev, eng = run([[H(nx=0.4, ny=0.5), H(nx=0.6, ny=0.5)],
                   [H(nx=0.5, ny=0.4), H(nx=0.5, ny=0.6)]])
    ok &= check("two-hand twist produces rotation", abs(eng.twist) > 5)

    print("\nRESULT:", "ALL GESTURES OK" if ok else "SOME FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

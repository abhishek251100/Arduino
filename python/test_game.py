"""
test_game.py  -  unit-test the Slice Surgeon scoring with no camera/monitor.

    python test_game.py
"""

from gesture_engine import GestureEvent
from game import SliceSurgeon, line_angle, angle_diff


def slice_event(x1, y1, x2, y2):
    return [GestureEvent("slice", {"start": (x1, y1), "end": (x2, y2)})]


def check(label, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    return cond


def main():
    ok = True

    # angle helpers
    ok &= check("line_angle 45deg", abs(line_angle(0, 0, 1, 1) - 45) < 1e-6)
    ok &= check("angle_diff wraps at 180", angle_diff(10, 170) == 20)

    # accurate cut -> score up, level up
    g = SliceSurgeon(seed_angle=45)
    g.reset(now=0.0)
    s0, lvl0 = g.score, g.level
    res = g.update(slice_event(0, 0, 1, 1), now=0.5)     # 45deg = target
    ok &= check("accurate cut registers HIT", res["event"] == "hit")
    ok &= check("score increased", g.score > s0)
    ok &= check("level increased", g.level == lvl0 + 1)

    # bad cut -> miss, lose a life
    g = SliceSurgeon(seed_angle=45)
    g.reset(now=0.0)
    lives0 = g.lives
    res = g.update(slice_event(0, 0, 1, 0), now=0.5)     # 0deg, far from 45
    ok &= check("wrong cut registers MISS", res["event"] == "miss")
    ok &= check("miss costs a life", g.lives == lives0 - 1)

    # timeout -> lose a life
    g = SliceSurgeon(seed_angle=45)
    g.reset(now=0.0)
    lives1 = g.lives
    res = g.update([], now=999.0)                          # way past deadline
    ok &= check("timeout costs a life", g.lives == lives1 - 1 and res["event"] == "timeout")

    # three misses -> game over
    g = SliceSurgeon(seed_angle=45)
    g.reset(now=0.0)
    for _ in range(3):
        g.update(slice_event(0, 0, 1, 0), now=0.1)
    ok &= check("three misses ends the game", g.over is True)

    print("\nRESULT:", "GAME OK" if ok else "SOMETHING WRONG")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

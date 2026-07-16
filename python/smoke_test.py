"""
smoke_test.py  -  prove everything works WITHOUT a camera or an Arduino.

Runs the real hand-tracker on a blank frame, then drives all 12 modes with a
simulated hand + fake sensor values, catching any error. Green = good.

    python smoke_test.py
"""

import traceback
import numpy as np

import config
from serial_comm import ArduinoLink
from hand_tracker import HandTracker, HandData
from modes import build_modes


def fake_hand(count=3, pinch=120.0, nx=0.5, ny=0.5):
    fingers = [1] * count + [0] * (5 - count)
    return HandData(
        found=True, fingers=fingers, count=count,
        gesture="open" if count == 5 else f"{count}-fingers",
        pinch=pinch, center=(int(nx * config.CAM_WIDTH), int(ny * config.CAM_HEIGHT)),
        nx=nx, ny=ny, hand_type="Right",
        lm=[[0, 0, 0]] * 21,
    )


def main():
    ok = True
    print("=" * 56)
    print(" SMOKE TEST  (no camera / no Arduino needed)")
    print("=" * 56)

    # 1) serial link in mock mode
    link = ArduinoLink()
    print(f"[1] ArduinoLink        -> mock={link.mock}  OK")

    # 2) real mediapipe hand tracker on a blank frame
    blank = np.zeros((config.CAM_HEIGHT, config.CAM_WIDTH, 3), dtype=np.uint8)
    tracker = HandTracker()
    data, out = tracker.process(blank)
    assert out.shape == blank.shape
    print(f"[2] HandTracker init   -> found_on_blank={data.found} (expected False)  OK")

    # 3) drive every mode with several simulated hands + sensor values
    link.sensors.update({"dist": 15, "ldr": 300, "pot": 512, "temp": 25, "hum": 40})
    modes = build_modes()
    frame = np.zeros((config.CAM_HEIGHT, config.CAM_WIDTH, 3), dtype=np.uint8)

    for i, m in enumerate(modes):
        try:
            m.enter(link)
            for c in (0, 1, 3, 5):
                m.update(fake_hand(count=c, pinch=30 + c * 40, nx=c / 5, ny=c / 5),
                         link, frame)
            m.update(HandData(found=False), link, frame)   # no-hand case
            print(f"[3.{i:02d}] {m.name:<20} OK")
        except Exception:
            ok = False
            print(f"[3.{i:02d}] {m.name:<20} FAILED")
            traceback.print_exc()

    link.close()
    print("=" * 56)
    print(" RESULT:", "ALL GOOD" if ok else "SOME FAILURES (see above)")
    print("=" * 56)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

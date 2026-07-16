"""
main.py  -  run this!    python main.py

The camera loop: grab a frame, read the hand, hand it to the current mode,
draw the HUD, repeat. Switch modes with the number keys, quit with Q.

Works with OR without an Arduino plugged in (mock mode).
"""

import time
import sys

import cv2

import config
from serial_comm import ArduinoLink
from hand_tracker import HandTracker
from modes import build_modes

# number keys -> mode index (1..0, then '-' and '=')
KEYMAP = {ord(str((i + 1) % 10)): i for i in range(10)}
KEYMAP[ord('-')] = 10
KEYMAP[ord('=')] = 11


def draw_header(img, mode, link, fps):
    cv2.rectangle(img, (0, 0), (config.CAM_WIDTH, 90), (25, 25, 25), -1)
    live = "MOCK (no board)" if link.mock else f"LIVE {link.board[:22]}"
    col = (80, 200, 255) if link.mock else (90, 240, 130)
    cv2.putText(img, f"[{'*' if not link.mock else 'o'}] {mode.name}",
                (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
    cv2.putText(img, live, (20, 74), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
    if config.SHOW_FPS:
        cv2.putText(img, f"{fps:4.1f} fps", (config.CAM_WIDTH - 190, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    cv2.putText(img, "keys 1-0 -=  switch mode   |   H help   |   Q quit",
                (config.CAM_WIDTH - 620, 74),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 170, 170), 1)


def draw_help(img, modes):
    overlay = img.copy()
    cv2.rectangle(overlay, (120, 110), (config.CAM_WIDTH - 120, 650),
                  (15, 15, 15), -1)
    img[:] = cv2.addWeighted(overlay, 0.85, img, 0.15, 0)
    cv2.putText(img, "GESTURE UNIVERSE  -  modes", (160, 165),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (90, 240, 130), 2)
    labels = "1234567890-="
    for i, m in enumerate(modes):
        y = 215 + i * 36
        cv2.putText(img, f"[{labels[i]}] {m.name}", (170, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, m.help, (560, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 200, 230), 1)


def main():
    print("=" * 60)
    print(" AYUS  |  GESTURE UNIVERSE")
    print("=" * 60)

    link = ArduinoLink()

    cap = cv2.VideoCapture(config.CAM_INDEX, cv2.CAP_DSHOW if sys.platform == "win32" else 0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)
    if not cap.isOpened():
        print("[ERROR] Could not open the camera. Check CAM_INDEX in config.py.")
        link.close()
        return

    tracker = HandTracker(config.CAM_WIDTH, config.CAM_HEIGHT)
    modes = build_modes()
    current = 0
    modes[current].enter(link)

    show_help = False
    prev_t = time.time()
    fps = 0.0

    print("Ready. A window should open. Press H for help, Q to quit.\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if config.FLIP_CAMERA:
            frame = cv2.flip(frame, 1)

        data, frame = tracker.process(frame)
        modes[current].update(data, link, frame)

        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - prev_t, 1e-3))
        prev_t = now

        draw_header(frame, modes[current], link, fps)
        if show_help:
            draw_help(frame, modes)

        cv2.imshow("AYUS - Gesture Universe", frame)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), 27):           # q or Esc
            break
        elif key in (ord('h'), ord('H')):
            show_help = not show_help
        elif key in KEYMAP and KEYMAP[key] < len(modes):
            link.send("STREAM:0")           # stop streaming from old mode
            current = KEYMAP[key]
            modes[current].enter(link)
            print(f"-> mode: {modes[current].name}")

    print("\nShutting down...")
    link.close()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

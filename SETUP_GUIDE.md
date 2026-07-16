# AYUS — Full Setup Guide (fresh machine, from zero) 🧭

This is the **complete, standalone** guide. Follow it top-to-bottom on any new
computer and you'll have everything running. No prior context needed — if you're
handing this to someone (or a fresh AI session) on another PC, this file + the
repo is all they need.

- **Repo:** https://github.com/abhishek251100/Arduino
- **What it is:** control electronics and 3D objects with **hand gestures** seen
  by your webcam. Python (OpenCV + MediaPipe) reads your hand; an Arduino drives
  LEDs/sensors; a 3D engine (PyVista) lets you rotate/explode/slice models and
  turn photos into 3D. Three apps, one gesture engine, all headless-testable.

---

## 0) The 60-second mental model

```
 Webcam ─► MediaPipe hand tracking ─► Gesture Engine ─► one of 3 apps:
                                          (grab, rotate,   1. LED/sensor modes  → Arduino (USB)
                                           zoom, swipe,    2. 3D dissection lab → screen
                                           slice, ...)     3. Slice Surgeon game→ screen
```

Everything runs **with or without an Arduino** (a built-in "mock mode" prints
what it would send). The 3D parts run **with or without a monitor** for testing
(they can render to image files).

---

## 1) Install the base tools

### 1a. Python (3.10 – 3.14 all work)
- Download: https://www.python.org/downloads/
- During install, **tick "Add Python to PATH"**.
- Verify in a terminal (PowerShell on Windows):
  ```powershell
  python --version
  ```
  > Note: MediaPipe installs most smoothly on **Python 3.10–3.12**. It also works
  > on 3.13/3.14 (tested), but if `pip install` ever fails on a very new Python,
  > install Python 3.11 alongside and use that.

### 1b. Git
- Download: https://git-scm.com/downloads  → verify: `git --version`

### 1c. Arduino IDE (only if you'll use real hardware)
- Download: https://www.arduino.cc/en/software

---

## 2) Get the code

```powershell
cd Desktop            # or wherever you want it
git clone https://github.com/abhishek251100/Arduino.git AYUS
cd AYUS
```

---

## 3) Install the Python libraries

```powershell
cd AYUS/python
pip install -r requirements.txt
```
This installs: `opencv-python`, `mediapipe`, `cvzone`, `numpy`, `pyserial`
(hardware link), and `pyvista` (3D engine). ~5–10 min the first time.

**Optional — real AI depth for photo→3D** (big download, GPU recommended):
```powershell
pip install torch timm
```
Then in [python/object_lab.py](python/object_lab.py) set:
`IMAGE_DEPTH_PROVIDER = "midas"` (default is `"auto"`, which uses MiDaS if it's
installed and otherwise the no-dependency luminance depth).

---

## 4) Prove it works — run the tests (no camera, no Arduino)

```powershell
cd AYUS/python
python run_all_tests.py
```
You should see a wall of `[PASS]` lines ending in **`ALL TESTS PASSED`**. This
verifies the gesture engine, all 12 LED modes, the 3D lab, the studio, the game,
and photo→3D — all on this machine. **If this passes, the project is healthy.**

---

## 5) Run the three apps

> Every app opens a window using your **webcam**. Quit any app with **`Q`** or **Esc**.
> If the window is black or uses the wrong camera, edit
> [python/config.py](python/config.py) and change `CAM_INDEX = 0` to `1`, then `2`.

### App 1 — LED / sensor modes  ·  `python main.py`
The classic gesture→electronics app. Top bar shows **MOCK** (no Arduino) or
**LIVE**. Press **`H`** for the menu. Number keys switch 12 modes:

`1` Finger LED Bar · `2` Binary Counter · `3` Pinch Dimmer · `4` RGB Mixer ·
`5` Servo Steering · `6` Theremin · `7` Finger Piano · `8` Reaction Game ·
`9` Simon Says · `0` Ultrasonic Radar · `-` Auto Night Light · `=` Knob Control

### App 2 — 3D Gesture Studio  ·  `python studio.py`
Manipulate 3D models with your hands (cell / atom / earth + any photos you add):

| Hand action | Result |
|---|---|
| open hand → **fist**, then move | rotate |
| **pinch** thumb+index, change gap | zoom |
| **two hands** apart / together | explode into parts |
| **pinch + drag** across (scalpel) | slice (cross-section) |
| **swipe** left / right | previous / next model |
| **point + hold** | un-slice / reset |
| keys `1` `2` `3` | jump to cell / atom / earth |

**Add your own photos:** drop `.png` / `.jpg` files into **`assets/images/`** and
restart the studio — each becomes a tiltable 3D relief. Swipe to reach them.

### App 3 — Slice Surgeon game  ·  `python game.py`
Match the yellow **cut line** with a scalpel gesture (pinch + drag) before time
runs out. Score points, level up, three misses = game over. Press **`R`** to retry.

---

## 6) The Arduino (only for App 1's real LEDs/sensors)

Full plain-English wiring is in **[WIRING.md](WIRING.md)**. Short version:

1. Open **[arduino/gesture_control/gesture_control.ino](arduino/gesture_control/gesture_control.ino)** in the Arduino IDE.
2. At the top, set the `ENABLE_*` switches to `1` for the parts you have
   (start with just `ENABLE_LEDS 1`).
3. **Tools → Board** = your board (Uno/Nano/Mega/ESP32), **Tools → Port** = its port.
4. Click **Upload**. On boot the LEDs do a little sweep = success.
5. Wire 5 LEDs to pins **D2–D6** (each LED: long leg → resistor → pin, short leg
   → GND). See WIRING.md "Level 1".
6. Run `python main.py` — the top bar flips to **LIVE**. Hold up fingers on mode `1`.

**Port note:** if App 1 stays on MOCK with the board plugged in, close the Arduino
IDE's Serial Monitor (it locks the port), or set `SERIAL_PORT` in `config.py`
manually (Windows `COM5`, Mac `/dev/tty.usbmodem...`, Linux `/dev/ttyUSB0`).

---

## 7) Project map (what each file is)

```
AYUS/
├─ arduino/gesture_control/gesture_control.ino   universal firmware (all boards)
├─ assets/images/                                 drop photos here → 3D reliefs
├─ python/
│  ├─ config.py          camera index + serial port + settings  ← you edit this
│  ├─ hand_tracker.py    webcam → hand landmarks (up to 2 hands)
│  ├─ gesture_engine.py  landmarks → grab/rotate/zoom/swipe/slice verbs
│  ├─ serial_comm.py     talks to Arduino; auto-detect + MOCK fallback
│  ├─ modes.py           the 12 LED/sensor modes
│  ├─ object_lab.py      3D dissection engine (rotate/explode/slice; PyVista)
│  ├─ image3d.py         photo → 3D relief (luminance default, MiDaS optional)
│  ├─ main.py            APP 1: LED/sensor modes
│  ├─ studio.py          APP 2: 3D dissection studio
│  ├─ game.py            APP 3: Slice Surgeon
│  ├─ run_all_tests.py   runs every test below
│  ├─ smoke_test.py / test_gestures.py / test_object_lab.py /
│  │   test_studio.py / test_game.py / test_image3d.py   (headless tests)
│  └─ requirements.txt
├─ hello.py / controller.py   the ORIGINAL tutorial files (kept for reference)
├─ README.md          feature overview
├─ WIRING.md          plain-English wiring, level by level
└─ SETUP_GUIDE.md     this file
```

---

## 8) Troubleshooting quick table

| Symptom | Fix |
|---|---|
| `Python was not found` | Install Python, tick "Add to PATH" (§1a). |
| `No module named ...` | `pip install -r requirements.txt` (§3). |
| mediapipe won't install | Use Python 3.10–3.12 (§1a note). |
| Camera window black / wrong cam | Change `CAM_INDEX` in `config.py` to 1, 2… |
| Camera won't open | Close other apps using the webcam (Zoom, Teams, browser). |
| 3D window won't open | `pip install pyvista`; update your graphics drivers. |
| App 1 stuck on MOCK with board plugged in | Close Arduino Serial Monitor; set `SERIAL_PORT` in `config.py`. |
| photo→3D looks flat/rough | Normal for luminance depth; enable MiDaS (§3 optional). |
| RGB LED + servo both dead on Uno | They clash on pins 9/10 — use one at a time (see WIRING.md). |
| Want to re-verify after any change | `python run_all_tests.py` |

---

## 9) Pushing your changes back to GitHub

```powershell
cd AYUS
git add -A
git commit -m "describe what you changed"
git push
```
First push from a new machine will ask you to log in to GitHub (browser or token).

---

## 10) Handy extras
- Re-run just one test, e.g.: `python test_object_lab.py` (writes preview PNGs to
  `python/_render_out/`).
- Change 3D window size / camera resolution in `config.py`.
- Add a new LED mode: copy any class in `modes.py`, tweak `update()`, add it to
  `build_modes()` — it lands on the next number key. (See README "Add your own mode".)

> **Demo day?** See **[EXPO_GUIDE.md](EXPO_GUIDE.md)** for the VS Code + Arduino
> setup and a booth checklist. **Wiring any build?** See **[WIRING.md](WIRING.md)**.

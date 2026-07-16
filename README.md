# AYUS — Gesture Universe 🖐️⚡

Control real electronics **with your bare hand**, using nothing but your
laptop's webcam and an Arduino. Your camera watches your hand, Python (OpenCV)
figures out your fingers/gestures, and the Arduino lights LEDs, mixes colours,
moves a servo, plays music, and reads sensors.

Built as an **all-in-one student kit**: one Arduino sketch + one Python app,
**12 switchable modes**, works on **Uno / Nano / Mega / ESP32**, and runs even
with **no hardware plugged in** (mock mode) so you can code and demo anywhere.

> Inspired by "Control LED using Python & Arduino (OpenCV)" — but taken *all
> the way out* into a dozen mini-projects and games.

---

## 🎮 The 12 modes (press number keys to switch)

| Key | Mode | What it does | Parts used |
|----|------|--------------|-----------|
| `1` | **Finger LED Bar** | Hold up N fingers → N LEDs light up | LEDs |
| `2` | **Binary Counter** | Fingers = bits → count 0–31, learn binary | LEDs |
| `3` | **Pinch Dimmer** | Pinch distance fades one LED (PWM) | 1 PWM LED |
| `4` | **RGB Colour Mixer** | Hand position mixes Red/Green/Blue | RGB LED |
| `5` | **Servo Steering** | Hand left/right sweeps a servo | Servo |
| `6` | **Theremin** | Hand height = pitch, fist = mute | Buzzer |
| `7` | **Finger Piano** | Each finger count plays a note | Buzzer |
| `8` | **Reaction Game** | Catch the random LED, measures your ms | LEDs |
| `9` | **Simon Says** | Repeat the flashing sequence with fingers | LEDs |
| `0` | **Distance Radar** | Object near ultrasonic = more LEDs | Ultrasonic |
| `-` | **Auto Night Light** | Dark room → light turns on | LDR + RGB |
| `=` | **Knob Control** | Potentiometer drives LEDs + servo | Pot + Servo |

Press **`H`** in the app for the on-screen menu, **`Q`** to quit.

Every mode also draws **virtual LEDs / bars / dials on screen**, so you can see
exactly what it *would* do even with nothing wired up yet.

---

## 🧊 NEW — 3D Gesture Studio (`python studio.py`)

A second app where your **bare hands manipulate a real 3D model** — no Arduino
needed. Built-in science models: **cell, atom, earth**.

| Do this with your hand | It does this |
|---|---|
| Open hand → **fist**, then move | **Rotate** the object |
| **Pinch** thumb+index, change the gap | **Zoom** in / out |
| **Two hands**, move apart / together | **Explode** the model into its parts |
| **Pinch + drag** across (scalpel) | **Slice** it open (cross-section) |
| **Swipe** left / right | Previous / next model |
| **Point + hold** | Un-slice / reset |
| keys `1` `2` `3` | jump to cell / atom / earth |

Powered by a proper **gesture engine** ([gesture_engine.py](AYUS/python/gesture_engine.py))
that understands grab, rotate, zoom, twist, swipe and slice — and a **3D
dissection engine** ([object_lab.py](AYUS/python/object_lab.py)) built on PyVista
that renders off-screen (so it's fully testable without a monitor).

> Install the extra 3D library once:  `pip install pyvista`
> *(Coming next: any-photo → 3D via AI depth, and a timed dissection game.)*

---

## 📁 What's in here

```
AYUS/
├─ arduino/
│  └─ gesture_control/gesture_control.ino   ← upload this to the Arduino
├─ python/
│  ├─ main.py            ← run this
│  ├─ config.py          ← your COM port + camera number live here
│  ├─ serial_comm.py     ← talks to the Arduino (auto-detect + mock mode)
│  ├─ hand_tracker.py    ← the computer-vision "eyes"
│  ├─ modes.py           ← all 12 features (copy one to add your own!)
│  └─ requirements.txt
├─ README.md
└─ WIRING.md             ← plain-English "which wire goes where"
```

---

## 🚀 Quick start

### Step 0 — Install Python (if you don't have it)
Download from <https://www.python.org/downloads/> and **tick "Add Python to
PATH"** during install. Check it worked:
```powershell
python --version
```

### Step 1 — Install the Python libraries
```powershell
cd AYUS/python
pip install -r requirements.txt
```

### Step 2 — Upload the Arduino sketch
1. Install the **Arduino IDE** (<https://www.arduino.cc/en/software>).
2. Open `arduino/gesture_control/gesture_control.ino`.
3. At the top of the file, set the `ENABLE_*` switches to `1` for the parts you
   actually have (LEDs are on by default — start there).
4. **Tools → Board** = your board, **Tools → Port** = your Arduino's port.
5. Click **Upload** (the → arrow). The LEDs do a little sweep = it's alive.

*No hardware yet? Skip this step — the app runs in mock mode.*

### Step 3 — Run it
```powershell
cd AYUS/python
python main.py
```
A camera window opens. The top bar says **LIVE** (Arduino found) or **MOCK**
(no board). Hold up some fingers on mode `1` and watch the LEDs. 🎉

---

## 🔌 Which port / camera? (the two things beginners get stuck on)

**Serial port** — in `config.py`, `SERIAL_PORT = "auto"` tries to find the
Arduino by itself. If it can't, set it manually:
- Windows: it looks like `COM3`, `COM5` … (see Arduino IDE → Tools → Port)
- Mac: `/dev/tty.usbmodem14101`
- Linux: `/dev/ttyUSB0` or `/dev/ttyACM0`

**Camera** — if the window is black or opens the wrong camera, change
`CAM_INDEX` in `config.py` to `1`, then `2`, etc.

---

## 🧠 How it works (the 30-second version)

```
   Your hand  ──▶  Webcam  ──▶  OpenCV + mediapipe (hand_tracker.py)
                                        │   "3 fingers up, pinch=120px"
                                        ▼
                               a Mode decides what to do (modes.py)
                                        │   sends text like  "BAR:3"
                                        ▼
                        USB cable ──▶  Arduino sketch (.ino)
                                        │
                                        ▼
                         LEDs / RGB / buzzer / servo / sensors
```

The Python and Arduino "speak" a tiny text language over USB. Full command list
is documented at the top of the `.ino` file. Examples: `BAR:3`, `RGB:255,0,128`,
`SERVO:90`, `TONE:440`.

---

## 🛠️ Add your own mode (super easy)

Open `modes.py`, copy any class, and change `update()`:
```python
class MyMode(Mode):
    name = "My Cool Mode"
    help = "does something awesome"
    def update(self, data, link, img):
        if data.gesture == "peace":
            link.send("RGB:0,255,0")   # green on a peace sign
```
Then add `MyMode()` to the list in `build_modes()`. Done — it's on a number key.

`data` gives you: `.count`, `.fingers`, `.gesture`, `.pinch`, `.nx`, `.ny`.

---

## ❗ Troubleshooting

| Symptom | Fix |
|---|---|
| `Python was not found` | Install Python and tick "Add to PATH" (Step 0). |
| `No module named cvzone` | `pip install -r requirements.txt` |
| mediapipe won't install | Use Python **3.9–3.11** (mediapipe lags newest versions). A `conda`/venv helps. |
| Camera window is black | Change `CAM_INDEX` to 1 or 2 in `config.py`. |
| Top bar says MOCK but board is plugged in | Set `SERIAL_PORT` manually; close Arduino IDE's Serial Monitor (it locks the port). |
| LEDs don't fade in Pinch mode | That LED must be on a **PWM** pin (marked `~` on the board). |
| RGB + Servo both dead | On an Uno they clash on pins 9/10. Use one or the other, or move pins. |
| Nothing happens on the board | Re-upload the sketch; confirm the same `NUM_LEDS`/baud (115200) on both sides. |

See **WIRING.md** for exactly which wire goes where, in plain language.

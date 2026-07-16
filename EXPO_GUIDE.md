# AYUS — Expo / Demo-Day Guide 🎪

Everything you need to run the project at a science fair / expo booth using
**VS Code + Arduino**, from a cold laptop to a crowd-pleasing demo. Pair this
with **[SETUP_GUIDE.md](SETUP_GUIDE.md)** (first-time install) and
**[WIRING.md](WIRING.md)** (which wire goes where).

---

## 0) What you'll actually show

Three stations, mix and match:
1. **Finger Lights** (Arduino + LEDs) — hold up fingers, lights follow. The crowd
   favourite; also a binary-counter "trick" (count to 31 on one hand).
2. **3D Hologram Table** (`studio.py`) — grab a cell/atom/earth in mid-air, pull
   it apart, slice it open. No wiring — just the webcam.
3. **Slice Surgeon** (`game.py`) — a timed gesture game people can queue up for.

You can run all three from **one laptop**; only Station 1 needs the Arduino.

---

## 1) Install VS Code (one time)

1. Download VS Code: https://code.visualstudio.com/ → install.
2. Open VS Code → **Extensions** (the squares icon, `Ctrl+Shift+X`) → install:
   - **Python** (by Microsoft) — required.
   - **Pylance** (auto-installs with Python) — nice-to-have.
   - *(Optional)* **Arduino** (by Microsoft) — only if you want to upload the
     sketch from inside VS Code. Otherwise use the normal Arduino IDE (simpler).
3. **File → Open Folder…** → pick the **`AYUS`** folder.

### Point VS Code at your Python
- Press `Ctrl+Shift+P` → type **"Python: Select Interpreter"** → choose your
  Python 3.x. (Bottom-right of VS Code then shows the version.)
- Open a terminal in VS Code: **Terminal → New Terminal** (`Ctrl+` \` ). It opens
  already inside the project folder.

### Install the libraries (one time, in that terminal)
```powershell
cd python
pip install -r requirements.txt
```

### Prove it's healthy (no camera/board needed)
```powershell
python run_all_tests.py
```
Look for **`ALL TESTS PASSED`**. Do this the **night before** the expo.

---

## 2) Upload the Arduino sketch (for the LED station)

**Easiest path — Arduino IDE:**
1. Open **`arduino/gesture_control/gesture_control.ino`** in the Arduino IDE.
2. At the top set the parts you're bringing: for the lights station,
   `ENABLE_LEDS 1` and everything else `0`.
3. **Tools → Board** → your board (Uno/Nano/Mega/ESP32).
4. **Tools → Port** → the one that appears when you plug the board in.
   *(Note this COM name — you'll use it if auto-detect fails.)*
5. Click **Upload** (→). LEDs sweep once = success.

**Inside VS Code (optional, Arduino extension):** `Ctrl+Shift+P` →
"Arduino: Select Board" → "Arduino: Select Serial Port" → "Arduino: Upload".

Then wire the LEDs per **WIRING.md → Level 1** (D2–D6, each LED: long leg →
resistor → pin, short leg → GND).

---

## 3) Run each app at the booth

In the VS Code terminal (or any PowerShell), from `AYUS/python`:

| Station | Command | Quit |
|---|---|---|
| Finger Lights (Arduino) | `python main.py` → press `1` | `Q` |
| 3D Hologram Table | `python studio.py` | `Q` |
| Slice Surgeon game | `python game.py` | `Q` |

- Top bar of `main.py` shows **LIVE** (Arduino found) or **MOCK** (not found —
  the on-screen virtual LEDs still work, great as a backup!).
- Switch LED modes live with number keys; press `H` for the menu.

---

## 4) Booth checklist ✅

**Bring:**
- [ ] Laptop (charged) + charger + the webcam works
- [ ] Arduino board + **USB cable** (bring a spare cable!)
- [ ] Breadboard, 5 LEDs, 5×220Ω resistors, jumper wires (in a small box)
- [ ] *(optional)* RGB LED, buzzer, servo, HC-SR04, LDR+10kΩ, potentiometer
- [ ] A powered USB hub or extra USB port if using several boards
- [ ] Printed copy of **WIRING.md** pin map (in case of a re-wire)

**Set up in this order (10 min):**
1. Power the laptop, open VS Code on the `AYUS` folder, open a terminal.
2. Plug in the Arduino → confirm its COM port shows up.
3. Run `python run_all_tests.py` → `ALL TESTS PASSED`.
4. Run `python main.py` → check top bar says **LIVE** → test mode `1` with your hand.
5. Open `studio.py` once to warm up the 3D window; close it.
6. Good lighting on your **hands** matters more than anything — aim a lamp at the
   demo area, avoid a bright window directly behind you (backlight blinds the cam).

---

## 5) 30-second crowd script 🎤

> "Watch — no controller, no touchscreen. **[hold up 3 fingers]** the lights read
> my hand. **[mode 2]** and now my hand is a *binary computer* — I can count to 31
> on five fingers. Want to see something wild? **[open studio.py]** I can reach
> into the screen, **grab this atom**, pull it apart with two hands, and **slice
> it open** to see inside — all with gestures. Try it!"

Hand the gesture over to the student — letting *them* control it is what makes it
stick. For the game, keep a **high-score** on a sticky note to draw a queue.

---

## 6) On-the-day troubleshooting 🔧

| Problem | 10-second fix |
|---|---|
| Camera window black / wrong camera | Edit `python/config.py`, set `CAM_INDEX = 1` (then 2), rerun. |
| Hands not detected | Add light on your hands; keep hand ~0.5–1 m from the camera. |
| `main.py` says MOCK but Arduino is in | Close Arduino IDE's Serial Monitor; or set `SERIAL_PORT = "COM5"` (your port) in `config.py`. |
| LEDs don't light | Re-check LED direction + resistors; confirm sketch uploaded; same board/port. |
| 3D window won't open | `pip install pyvista`; update graphics drivers; a restart usually fixes it. |
| App won't start / import error | `pip install -r requirements.txt` again in the selected interpreter. |
| Everything broke, crowd waiting | Fall back to **MOCK mode** — `main.py` still shows virtual LEDs on screen, and `studio.py`/`game.py` need no hardware at all. |

**Golden rule:** the software works with **no Arduino** (mock mode) and **no
monitor besides the laptop**. If hardware misbehaves mid-expo, switch to the 3D
studio/game and keep the crowd engaged while you re-wire.

---

## 7) Quick command reference

```powershell
# from the AYUS/python folder, in VS Code's terminal:
pip install -r requirements.txt   # one-time setup
python run_all_tests.py           # verify everything (no hardware)
python main.py                    # Station 1: gesture LEDs/sensors
python studio.py                  # Station 2: 3D dissection + photo->3D
python game.py                    # Station 3: Slice Surgeon
```

# WIRING — plain-English "which wire goes where" 🧵

You do **not** wire everything at once. Build it like levels in a game:
start with LEDs, get it working, then add the next part.

Pin numbers below match the **Arduino Uno / Nano** defaults in the sketch.
On Mega/ESP32 the sketch uses different pins — see the pin map at the top of
`gesture_control.ino`.

### Breadboard basics (read once)
- The **long side rails** (marked `+` red and `–` blue) run power along the board.
- Connect Arduino **5V → red rail** and Arduino **GND → blue rail**. Now the
  whole rail is powered, and every part can grab power from the nearest hole.
- The short rows (a–e, f–j) are connected in little groups of 5 — that's how you
  join two legs together.
- "GND" just means ground / minus / the blue rail. There are several GND pins on
  the Arduino; any of them is fine.

---

## 🔎 Which parts does each feature need? (pick your project)

Every feature is a mode in **App 1** (`python main.py`). Wire only the parts a
mode needs, and set the matching `ENABLE_*` flag to `1` in the sketch.

| Mode (key) | Parts to wire | Enable flag(s) |
|---|---|---|
| Finger LED Bar `1` | 5 LEDs + resistors | `ENABLE_LEDS` |
| Binary Counter `2` | 5 LEDs + resistors | `ENABLE_LEDS` |
| Pinch Dimmer `3` | 1 LED on a `~`PWM pin | `ENABLE_LEDS` |
| RGB Mixer `4` | 1 RGB LED + 3 resistors | `ENABLE_RGB` |
| Servo Steering `5` | 1 servo motor | `ENABLE_SERVO` |
| Theremin `6` | 1 buzzer | `ENABLE_BUZZER` |
| Finger Piano `7` | 1 buzzer | `ENABLE_BUZZER` |
| Reaction Game `8` | 5 LEDs + resistors | `ENABLE_LEDS` |
| Simon Says `9` | 5 LEDs + resistors | `ENABLE_LEDS` |
| Ultrasonic Radar `0` | HC-SR04 sensor (+ LEDs to show it) | `ENABLE_ULTRA` (+`LEDS`) |
| Auto Night Light `-` | LDR + 10kΩ + RGB LED | `ENABLE_LDR` + `ENABLE_RGB` |
| Knob Control `=` | potentiometer (+ LEDs/servo) | `ENABLE_POT` (+`LEDS`/`SERVO`) |

> The **3D Studio** (`studio.py`) and **Slice Surgeon** (`game.py`) need **no
> wiring at all** — just the webcam. Wiring is only for App 1's physical output.

## 📌 Master pin map (Arduino Uno / Nano defaults)

| Part | Pin(s) | Notes |
|---|---|---|
| LED 1–5 | D2, D3, D4, D5, D6 | D3/D5/D6 are `~`PWM (can fade) |
| RGB LED (R,G,B) | D9, D10, D11 | all `~`PWM; common leg → GND (or 5V if common-anode) |
| Buzzer | D8 | `+` to D8, other leg to GND |
| Servo (signal) | D7 | red→5V, brown/black→GND |
| Ultrasonic Trig / Echo | D12 / D13 | VCC→5V, GND→GND |
| LDR (light) | A0 | needs a 10kΩ divider resistor (see Level 6) |
| Potentiometer (wiper) | A1 | outer legs → 5V and GND |
| DHT11 data (optional) | A2 | needs the Adafruit DHT library |

> **Different board?** The sketch auto-picks pins for **Mega** and **ESP32** —
> the exact numbers are printed at the top of `gesture_control.ino`. Everything
> below is the Uno/Nano layout; the *idea* is identical on every board.

---

## LEVEL 1 — the 5 LEDs  ⭐ (do this first)

You need: 5 LEDs, 5 resistors (220Ω or 330Ω — any of these work), jumper wires.

For **each** LED:
1. An LED has a **long leg (+, anode)** and a **short leg (–, cathode / flat
   side)**. Direction matters!
2. **Long leg** → through a **resistor** → to an Arduino pin.
3. **Short leg** → to **GND** (the blue rail).

Which pin for which LED:

| LED # | Arduino pin |
|------:|:------------|
| 1 | D2 |
| 2 | D3 |
| 3 | D4 |
| 4 | D5 |
| 5 | D6 |

> The resistor protects the LED — never connect an LED straight to a pin.
> The resistor can go on either leg; it just needs to be in the line.

✅ Test: upload the sketch. On boot the LEDs sweep left→right. Run `python
main.py`, mode `1`, hold up fingers.

---

## LEVEL 2 — RGB LED 🌈 (mode 4)

An RGB LED has **4 legs**. The longest leg is the **common**. Most student ones
are **common-cathode** (common leg → GND). If yours is common-anode, it goes to
5V instead and colours look inverted — just swap it.

| RGB leg | Through resistor → | Arduino pin |
|---|---|---|
| Red   | 220Ω | D9  (~) |
| Green | 220Ω | D10 (~) |
| Blue  | 220Ω | D11 (~) |
| Common (longest) | — | GND |

> Pins 9/10/11 have a `~` = they can **fade** (PWM), which is why colour mixing
> works. Set `ENABLE_RGB 1` in the sketch.

---

## LEVEL 3 — Buzzer 🔊 (modes 6 & 7)

A small piezo buzzer, 2 legs:
- **`+` leg** → **D8**
- **other leg** → **GND**

Set `ENABLE_BUZZER 1`. Test with mode `6` (theremin): raise/lower your hand.

---

## LEVEL 4 — Servo motor ⚙️ (mode 5)

A servo has **3 wires**:

| Servo wire (colour) | Goes to |
|---|---|
| Brown / Black | GND |
| Red | 5V |
| Orange / Yellow (signal) | D7 |

Set `ENABLE_SERVO 1`.

> ⚠️ On an **Uno**, turning the servo on disables fading on pins **9 & 10**, so
> the RGB LED won't work at the same time. Pick one, or run RGB on a Mega/ESP32.
> A big/strong servo should get its own 5V battery pack (share GND with Arduino),
> or it can brown-out the board.

---

## LEVEL 5 — Ultrasonic sensor 📡 (mode 0)

The HC-SR04 has **4 pins**:

| Sensor pin | Goes to |
|---|---|
| VCC | 5V |
| Trig | D12 |
| Echo | D13 |
| GND | GND |

Set `ENABLE_ULTRA 1`. In mode `0`, move your hand toward the sensor — the closer
it is, the more LEDs light up.

---

## LEVEL 6 — Light sensor / LDR 💡 (mode `-`)

An LDR (photoresistor) needs a **voltage-divider** — one extra resistor:

1. One LDR leg → **5V**.
2. Other LDR leg → **analog pin A0** *and also* → through a **10kΩ resistor** →
   **GND**. (The junction where the LDR meets the 10kΩ is what A0 reads.)

Set `ENABLE_LDR 1`. Cover it with your hand in mode `-`; the light comes on.

---

## LEVEL 7 — Potentiometer (knob) 🎛️ (mode `=`)

A pot has **3 pins**:

| Pot pin | Goes to |
|---|---|
| Left | 5V |
| Middle (wiper) | A1 |
| Right | GND |

Set `ENABLE_POT 1`. Turn the knob in mode `=` to drive the LEDs + servo. No hand
needed — good for a demo table.

---

## LEVEL 8 — Temperature/Humidity DHT11 🌡️ (optional)

Needs a library: in Arduino IDE → **Tools → Manage Libraries** → search
**"DHT sensor library"** by Adafruit → Install. Then set `ENABLE_DHT 1`.

| DHT pin | Goes to |
|---|---|
| `+` / VCC | 5V |
| `out` / DATA | A2 |
| `–` / GND | GND |

(3-pin breakout modules have these labelled. A 10kΩ resistor between VCC and DATA
helps stability if yours is the bare 4-pin sensor.)

---

## 🧩 Ready-made project recipes (copy one)

Each recipe = a complete build. Wire the parts, set the flags, upload, run the
app, and use the listed mode. Great for picking a booth project per student.

### Recipe A — "Finger Lights" (the flagship) ⭐
- **Parts:** Arduino + 5 LEDs + 5×220Ω + breadboard + jumpers.
- **Wire:** Levels 1. LEDs on D2–D6, short legs to GND.
- **Flags:** `ENABLE_LEDS 1` (all others `0`).
- **Run:** `python main.py` → mode `1` (or `2` for binary).
- **Demo line:** "Hold up fingers — the lights count with you. Mode 2 turns your
  hand into a binary computer (count to 31 on one hand!)."

### Recipe B — "Gesture Mood Lamp" 🌈
- **Parts:** Arduino + 1 RGB LED + 3×220Ω.
- **Wire:** Level 2 (R→D9, G→D10, B→D11, common→GND).
- **Flags:** `ENABLE_RGB 1`.
- **Run:** `python main.py` → mode `4`. Move your hand to mix colours.
- **Demo line:** "Your hand paints with light — height, sideways and pinch mix
  red, green and blue."

### Recipe C — "Air Theremin / Hand Piano" 🎵
- **Parts:** Arduino + 1 buzzer.
- **Wire:** Level 3 (buzzer + → D8, other leg → GND).
- **Flags:** `ENABLE_BUZZER 1`.
- **Run:** `python main.py` → mode `6` (theremin) or `7` (piano).
- **Demo line:** "Raise your hand to raise the pitch — an instrument you play in
  thin air."

### Recipe D — "Gesture Servo Gauge / Mini Robot Arm" ⚙️
- **Parts:** Arduino + 1 SG90 servo (big servos: separate 5V battery, shared GND).
- **Wire:** Level 4 (signal→D7, red→5V, brown→GND).
- **Flags:** `ENABLE_SERVO 1`. (On an Uno, keep `ENABLE_RGB 0` — they clash on 9/10.)
- **Run:** `python main.py` → mode `5`. Move hand left/right to sweep it.
- **Demo line:** "Your hand is the joystick — no controller, just gestures."

### Recipe E — "Smart Sensor Dashboard" 📊
- **Parts:** Arduino + HC-SR04 + LDR + 10kΩ + potentiometer + 5 LEDs.
- **Wire:** Levels 1, 5, 6, 7.
- **Flags:** `ENABLE_LEDS 1`, `ENABLE_ULTRA 1`, `ENABLE_LDR 1`, `ENABLE_POT 1`.
- **Run:** `python main.py` → modes `0` (radar), `-` (night light), `=` (knob).
- **Demo line:** "It senses distance, light and a knob — a tiny smart-home kit."

### Recipe F — "3D Hologram Table" (no wiring!) 🧊
- **Parts:** just a laptop + webcam (optionally a big monitor/projector).
- **Run:** `python studio.py` (dissect a cell/atom/earth or your own photos) and
  `python game.py` (Slice Surgeon). Add photos to `assets/images/`.
- **Demo line:** "Grab the atom out of the air, pull it apart, slice it open —
  all with your bare hands."

## ⚡ Powering more than one thing at once
- **A few LEDs** are fine straight from Arduino pins (each pin ≤ ~20mA; keep the
  whole board under ~200mA total).
- **Servos** can dip the voltage and reset the board. For anything bigger than a
  small SG90, power the servo from a **separate 5V supply / battery pack** and
  **join the grounds** (servo GND ↔ Arduino GND). Signal still goes to D7.
- **Sensor modules** (HC-SR04, DHT, pot) draw very little — 5V and GND are fine.
- Feed power along the breadboard **rails** (5V→red, GND→blue) so every part taps
  the nearest hole instead of crowding the Arduino's pins.
- On an **Uno**, remember: enabling the servo library disables `~`PWM on pins
  9 & 10, so don't run the RGB LED and the servo at the same time. On a **Mega**
  or **ESP32** there are enough pins to do both.

---

## Safety & sanity 🧯
- **Unplug the USB** before changing wiring, then plug back in.
- Double-check **LED direction** and that every LED has a **resistor**.
- Never connect a **motor's power straight from a pin** — pins are for signals.
- If the board keeps resetting or a part gets warm, unplug and re-check GND/5V.
- Confused which pin is which? The Arduino has tiny numbers printed next to each
  hole — `~` numbers can fade, `A0–A5` are the analog ones.

---

## The "I have no hardware yet" path 🖥️
Everything above is optional! Just run `python main.py`. The app shows **MOCK**
in the top bar, draws virtual LEDs/dials on screen, and prints every command it
would send to the terminal. You can build, learn, and even present the whole
project before a single wire is connected — then wire it up level by level.

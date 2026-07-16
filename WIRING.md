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

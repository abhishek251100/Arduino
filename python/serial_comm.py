"""
serial_comm.py  -  the "phone line" between Python and the Arduino.

This class hides ALL the messy details:
  * finds the Arduino automatically (or uses the port from config)
  * sends short text commands   link.send("BAR:3")
  * reads sensor reports in the background   link.sensors["dist"]
  * if there is NO Arduino, it runs in MOCK mode and just prints/keeps the
    commands so the rest of the program works exactly the same.

Nothing else in the project needs to know whether real hardware is present.
"""

import threading
import time

import config

# pyserial is optional at runtime: if it isn't installed we simply go mock.
try:
    import serial
    import serial.tools.list_ports
    HAVE_PYSERIAL = True
except Exception:                       # pragma: no cover
    HAVE_PYSERIAL = False


class ArduinoLink:
    def __init__(self):
        self.ser = None
        self.mock = True
        self.last_command = ""          # for on-screen display
        self.sensors = {                # latest values from the board
            "dist": -1, "ldr": -1, "pot": -1, "temp": -1, "hum": -1,
        }
        self.board = "unknown"
        self._rx = ""
        self._running = False
        self._connect()

    # ------------------------------------------------------------------ setup
    def _connect(self):
        if not HAVE_PYSERIAL:
            print("[link] pyserial not installed -> MOCK mode "
                  "(pip install pyserial to use real hardware)")
            return

        port = config.SERIAL_PORT
        if port == "auto":
            port = self._autodetect()

        if not port:
            if config.ALLOW_MOCK:
                print("[link] No Arduino found -> MOCK mode. "
                      "Plug it in and restart to go live.")
                return
            raise RuntimeError("No Arduino found and ALLOW_MOCK is False.")

        try:
            self.ser = serial.Serial(port, config.BAUD_RATE, timeout=0.05)
            time.sleep(2.0)             # boards reset when the port opens
            self.mock = False
            self._running = True
            threading.Thread(target=self._reader, daemon=True).start()
            print(f"[link] Connected to Arduino on {port}")
        except Exception as e:
            print(f"[link] Could not open {port} ({e}) -> MOCK mode")
            self.ser = None

    def _autodetect(self):
        """Pick the most likely Arduino among the serial ports."""
        likely = ("arduino", "ch340", "usb serial", "wch", "cp210",
                  "usb-serial", "ftdi", "silicon labs", "usbmodem", "usbserial")
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            blob = f"{p.description} {p.manufacturer} {p.device}".lower()
            if any(k in blob for k in likely):
                return p.device
        # fall back to the only port available, if there is exactly one
        if len(ports) == 1:
            return ports[0].device
        return None

    # ------------------------------------------------------------------- send
    def send(self, command: str):
        """Send one command line to the Arduino (or record it in mock mode)."""
        self.last_command = command
        if self.mock or self.ser is None:
            print(f"[MOCK->arduino] {command}")
            return
        try:
            self.ser.write((command + "\n").encode())
        except Exception as e:
            print(f"[link] write failed ({e}) -> switching to MOCK")
            self.mock = True

    # send but skip repeats, to avoid flooding the serial line 60x/second
    def send_if_changed(self, command: str):
        if command != self.last_command:
            self.send(command)

    # --------------------------------------------------------------- receive
    def _reader(self):
        while self._running and self.ser is not None:
            try:
                chunk = self.ser.read(120).decode(errors="ignore")
            except Exception:
                break
            if not chunk:
                continue
            self._rx += chunk
            while "\n" in self._rx:
                line, self._rx = self._rx.split("\n", 1)
                self._handle_line(line.strip())

    def _handle_line(self, line: str):
        if not line:
            return
        if line.startswith(">SENS:"):
            self._parse_sensors(line[6:])
        elif line.startswith(">READY"):
            self.board = line
            print(f"[link] {line}")
        elif line.startswith(">"):
            pass                        # PONG / debug - ignore quietly

    def _parse_sensors(self, body: str):
        for pair in body.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                try:
                    self.sensors[k] = float(v)
                except ValueError:
                    pass

    # ------------------------------------------------------------- utilities
    def enable_stream(self, on=True):
        self.send("STREAM:1" if on else "STREAM:0")

    def close(self):
        self._running = False
        try:
            self.send("ALLOFF")
            if self.ser:
                self.ser.close()
        except Exception:
            pass


# quick manual test:  python serial_comm.py
if __name__ == "__main__":
    link = ArduinoLink()
    print("mock =", link.mock)
    link.send("PING")
    for n in range(6):
        link.send(f"BAR:{n}")
        time.sleep(0.3)
    link.close()

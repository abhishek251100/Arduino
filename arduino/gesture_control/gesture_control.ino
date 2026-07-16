/* =============================================================================
   AYUS  -  Gesture Universe  |  Universal Arduino Firmware
   -----------------------------------------------------------------------------
   ONE sketch that turns your Arduino into a "command server".
   Your laptop's camera + Python (OpenCV) reads your HAND, decides what to do,
   and sends short text commands over the USB cable. This sketch listens for
   those commands and drives whatever parts you have plugged in:
       LEDs, RGB LED, buzzer, servo motor, ultrasonic, LDR, potentiometer, DHT.

   Works on:  Arduino Uno / Nano  |  Arduino Mega  |  ESP32 / ESP8266
   -----------------------------------------------------------------------------
   HOW IT TALKS  (each line ends with a newline '\n', baud = 115200)

   PC  -> Arduino:
     PING              -> replies ">PONG"          (are you alive?)
     BAR:n             light first n LEDs like a bar graph (n = 0..NUM_LEDS)
     LED:i,s           set LED number i to state s  (s = 0 off / 1 on)
     MASK:b            set all LEDs from a number's bits (e.g. 5 -> LEDs 0 & 2)
     BRIGHT:v          fade the FIRST led with PWM  (v = 0..255)
     RGB:r,g,b         set RGB led colour           (each 0..255)
     TONE:f            play tone of f Hz on buzzer   (0 = silence)
     BEEP:ms           quick beep for ms milliseconds
     SERVO:a           move servo to angle a         (0..180)
     STREAM:1 / :0     turn sensor auto-reporting on / off
     ALLOFF            everything off (LEDs, rgb, buzzer)

   Arduino -> PC:
     >READY board=...  printed once on boot
     >PONG             answer to PING
     >SENS:dist=..,ldr=..,pot=..,temp=..,hum=..     (only while STREAM is on)
   -----------------------------------------------------------------------------
   IMPORTANT for students:  You almost never plug in EVERYTHING at once.
   Turn features on/off below with the ENABLE_* switches so the pins you use
   match the parts you actually have. Some parts fight over the same pins
   (see the notes) - that is normal electronics life, not a bug. :)
   ============================================================================= */

// ----------------------------------------------------------------------------
// 1) FEATURE SWITCHES  ->  set to 1 for parts you HAVE, 0 for parts you DON'T
// ----------------------------------------------------------------------------
#define ENABLE_LEDS      1   // the row of plain LEDs (the classic reel project)
#define ENABLE_RGB       1   // one 4-pin RGB led (colour mixing)
#define ENABLE_BUZZER    1   // piezo buzzer (sound / music / theremin)
#define ENABLE_ULTRA     1   // HC-SR04 ultrasonic distance sensor
#define ENABLE_LDR       1   // light sensor (photoresistor) on an analog pin
#define ENABLE_POT       1   // potentiometer (a knob) on an analog pin

#define ENABLE_SERVO     0   // SG90 servo.  NOTE: on Uno the Servo library
                             // steals PWM from pins 9 & 10 -> disable RGB if
                             // you use servo, or move RGB pins. Off by default.
#define ENABLE_DHT       0   // DHT11/DHT22 temp+humidity. Needs the library
                             // "DHT sensor library" by Adafruit installed.
                             // Off by default so the sketch compiles for all.

// ----------------------------------------------------------------------------
// 2) PIN MAP  ->  auto-selected per board. Change numbers if you wired others.
// ----------------------------------------------------------------------------
#if defined(ESP32)
  // ---- ESP32 devkit ----
  const int LED_PINS[] = {13, 12, 14, 27, 26};   // safe output pins
  #define RGB_R  25
  #define RGB_G  33
  #define RGB_B  32
  #define BUZZER 4
  #define SERVO_PIN 15
  #define TRIG   17
  #define ECHO   16          // input-only capable
  #define LDR_PIN 34         // ADC1 (input only)
  #define POT_PIN 35         // ADC1 (input only)
  #define DHT_PIN 5
  #define ADC_MAX 4095       // ESP32 ADC is 12-bit

#elif defined(ARDUINO_AVR_MEGA2560)
  // ---- Arduino Mega ----
  const int LED_PINS[] = {22, 24, 26, 28, 30};
  #define RGB_R  9
  #define RGB_G  10
  #define RGB_B  11
  #define BUZZER 8
  #define SERVO_PIN 7
  #define TRIG   12
  #define ECHO   13
  #define LDR_PIN A0
  #define POT_PIN A1
  #define DHT_PIN 6
  #define ADC_MAX 1023

#else
  // ---- Arduino Uno / Nano (default) ----
  const int LED_PINS[] = {2, 3, 4, 5, 6};        // 3,5,6 are PWM-capable
  #define RGB_R  9           // 9,10,11 are PWM (needed for colour fading)
  #define RGB_G  10
  #define RGB_B  11
  #define BUZZER 8
  #define SERVO_PIN 7
  #define TRIG   12
  #define ECHO   13
  #define LDR_PIN A0
  #define POT_PIN A1
  #define DHT_PIN A2
  #define ADC_MAX 1023
#endif

const int NUM_LEDS = sizeof(LED_PINS) / sizeof(LED_PINS[0]);

// ----------------------------------------------------------------------------
// 3) OPTIONAL LIBRARIES (only pulled in when the feature is enabled)
// ----------------------------------------------------------------------------
#if ENABLE_SERVO
  #if defined(ESP32)
    #include <ESP32Servo.h>     // install "ESP32Servo" if on ESP32
  #else
    #include <Servo.h>          // built in, nothing to install
  #endif
  Servo myServo;
#endif

#if ENABLE_DHT
  #include <DHT.h>              // install Adafruit "DHT sensor library"
  #define DHT_TYPE DHT11        // change to DHT22 if that is your sensor
  DHT dht(DHT_PIN, DHT_TYPE);
#endif

// ----------------------------------------------------------------------------
// 4) STATE
// ----------------------------------------------------------------------------
bool streamOn = false;
unsigned long lastStream = 0;
const unsigned long STREAM_EVERY = 150;   // ms between sensor reports
String rx = "";                           // incoming line buffer

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);

#if ENABLE_LEDS
  for (int i = 0; i < NUM_LEDS; i++) pinMode(LED_PINS[i], OUTPUT);
#endif
#if ENABLE_RGB
  pinMode(RGB_R, OUTPUT); pinMode(RGB_G, OUTPUT); pinMode(RGB_B, OUTPUT);
#endif
#if ENABLE_BUZZER
  pinMode(BUZZER, OUTPUT);
#endif
#if ENABLE_ULTRA
  pinMode(TRIG, OUTPUT); pinMode(ECHO, INPUT);
#endif
#if ENABLE_SERVO
  myServo.attach(SERVO_PIN);
  myServo.write(90);
#endif
#if ENABLE_DHT
  dht.begin();
#endif

  allOff();
  bootBlink();

  Serial.print(F(">READY board="));
#if defined(ESP32)
  Serial.print(F("ESP32"));
#elif defined(ARDUINO_AVR_MEGA2560)
  Serial.print(F("MEGA"));
#else
  Serial.print(F("UNO/NANO"));
#endif
  Serial.print(F(" leds=")); Serial.println(NUM_LEDS);
}

// ============================================================================
// MAIN LOOP  -  read commands, then maybe stream sensors
// ============================================================================
void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') { handleLine(rx); rx = ""; }
    else if (c != '\r') { rx += c; if (rx.length() > 60) rx = ""; }
  }

  if (streamOn && millis() - lastStream >= STREAM_EVERY) {
    lastStream = millis();
    reportSensors();
  }
}

// ============================================================================
// COMMAND PARSER
// ============================================================================
void handleLine(String line) {
  line.trim();
  if (line.length() == 0) return;

  int colon = line.indexOf(':');
  String cmd = (colon == -1) ? line : line.substring(0, colon);
  String arg = (colon == -1) ? ""   : line.substring(colon + 1);
  cmd.toUpperCase();

  if      (cmd == "PING")   Serial.println(F(">PONG"));
  else if (cmd == "ALLOFF") allOff();
  else if (cmd == "BAR")    setBar(arg.toInt());
  else if (cmd == "MASK")   setMask(arg.toInt());
  else if (cmd == "LED")    setLed(arg);
  else if (cmd == "BRIGHT") setBright(arg.toInt());
  else if (cmd == "RGB")    setRGB(arg);
  else if (cmd == "TONE")   setTone(arg.toInt());
  else if (cmd == "BEEP")   beep(arg.toInt());
  else if (cmd == "SERVO")  setServo(arg.toInt());
  else if (cmd == "STREAM") streamOn = (arg.toInt() == 1);
  // unknown commands are silently ignored so the link never crashes
}

// ============================================================================
// ACTIONS
// ============================================================================
void allOff() {
#if ENABLE_LEDS
  for (int i = 0; i < NUM_LEDS; i++) digitalWrite(LED_PINS[i], LOW);
#endif
#if ENABLE_RGB
  analogWrite(RGB_R, 0); analogWrite(RGB_G, 0); analogWrite(RGB_B, 0);
#endif
#if ENABLE_BUZZER
  noTone(BUZZER);
#endif
}

void setBar(int n) {
#if ENABLE_LEDS
  n = constrain(n, 0, NUM_LEDS);
  for (int i = 0; i < NUM_LEDS; i++) digitalWrite(LED_PINS[i], i < n ? HIGH : LOW);
#endif
}

void setMask(long b) {
#if ENABLE_LEDS
  for (int i = 0; i < NUM_LEDS; i++) digitalWrite(LED_PINS[i], (b >> i) & 1 ? HIGH : LOW);
#endif
}

void setLed(String arg) {
#if ENABLE_LEDS
  int comma = arg.indexOf(',');
  if (comma == -1) return;
  int i = arg.substring(0, comma).toInt();
  int s = arg.substring(comma + 1).toInt();
  if (i >= 0 && i < NUM_LEDS) digitalWrite(LED_PINS[i], s ? HIGH : LOW);
#endif
}

void setBright(int v) {
#if ENABLE_LEDS
  v = constrain(v, 0, 255);
  analogWrite(LED_PINS[0], v);   // pin must be PWM-capable for smooth fade
#endif
}

void setRGB(String arg) {
#if ENABLE_RGB
  int c1 = arg.indexOf(',');
  int c2 = arg.indexOf(',', c1 + 1);
  if (c1 == -1 || c2 == -1) return;
  int r = arg.substring(0, c1).toInt();
  int g = arg.substring(c1 + 1, c2).toInt();
  int b = arg.substring(c2 + 1).toInt();
  analogWrite(RGB_R, constrain(r, 0, 255));
  analogWrite(RGB_G, constrain(g, 0, 255));
  analogWrite(RGB_B, constrain(b, 0, 255));
#endif
}

void setTone(int f) {
#if ENABLE_BUZZER
  if (f <= 0) noTone(BUZZER);
  else tone(BUZZER, constrain(f, 30, 5000));
#endif
}

void beep(int ms) {
#if ENABLE_BUZZER
  ms = constrain(ms, 10, 2000);
  tone(BUZZER, 1000, ms);
#endif
}

void setServo(int a) {
#if ENABLE_SERVO
  myServo.write(constrain(a, 0, 180));
#endif
}

// ============================================================================
// SENSORS
// ============================================================================
long readDistanceCM() {
#if ENABLE_ULTRA
  digitalWrite(TRIG, LOW);  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long dur = pulseIn(ECHO, HIGH, 25000);   // timeout ~4.3 m
  if (dur == 0) return -1;                 // nothing in range
  return dur / 58;                         // convert to centimetres
#else
  return -1;
#endif
}

void reportSensors() {
  Serial.print(F(">SENS:"));

  long dist = readDistanceCM();
  Serial.print(F("dist=")); Serial.print(dist);

#if ENABLE_LDR
  Serial.print(F(",ldr=")); Serial.print(analogRead(LDR_PIN));
#else
  Serial.print(F(",ldr=-1"));
#endif

#if ENABLE_POT
  Serial.print(F(",pot=")); Serial.print(analogRead(POT_PIN));
#else
  Serial.print(F(",pot=-1"));
#endif

#if ENABLE_DHT
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  Serial.print(F(",temp=")); Serial.print(isnan(t) ? -1 : t);
  Serial.print(F(",hum="));  Serial.print(isnan(h) ? -1 : h);
#else
  Serial.print(F(",temp=-1,hum=-1"));
#endif

  Serial.println();
}

// ============================================================================
// little boot animation so you can SEE it is alive
// ============================================================================
void bootBlink() {
#if ENABLE_LEDS
  for (int i = 0; i < NUM_LEDS; i++) { digitalWrite(LED_PINS[i], HIGH); delay(60); }
  for (int i = NUM_LEDS - 1; i >= 0; i--) { digitalWrite(LED_PINS[i], LOW); delay(60); }
#endif
}

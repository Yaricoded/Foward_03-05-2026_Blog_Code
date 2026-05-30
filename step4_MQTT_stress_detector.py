# ============================================================
# APAN 5570 – Assignment 3 (Yaritza & Felice Version)
# Core2 Stress Signal Detector (Upload Mode + MQTT)
# ============================================================
# Phases 1-3 run ONCE on boot:
#   Phase 1 - File verification  (checks /flash/ for files)
#   Phase 2 - WiFi connection    (connects once, halts on fail)
#   Phase 3 - MQTT connection    (connects once, halts on fail)
#
# Phase 4 loops FOREVER:
#   - Samples audio + motion every cycle
#   - Classifies stress level (0-3)
#   - Updates display in real time
#   - Publishes live JSON to MQTT every cycle
#   - Auto-reconnects MQTT if connection drops mid-loop
#
# SOUND-BASED files (upload to /flash/):
#   baseline.wav, humming.wav,
#   vocal_distress.wav, sucking_teeth.wav
#
# MOTION-BASED files (upload to /flash/):
#   shaking.csv, tapping.csv, fidgeting.csv
#
# MQTT payload (topic: apan5570/core2/stress):
#   {"device":"core2","stress_level":<0-3>,
#    "sound":<bool>,"motion":<bool>,
#    "energy":<float>,"motion_var":<float>,
#    "count":<int>}
#
# HOW TO RUN:
#   1. Set WIFI_SSID, WIFI_PASSWORD, and BROKER_IP below
#   2. Upload .wav and .csv files to /flash/ via UIFlow
#      file manager BEFORE running
#   3. Paste into UIFlow 2.x and click Run
# ============================================================

import os, sys, io
import M5
from M5 import *
from umqtt.simple import MQTTClient
import network
import time
import struct
import math

# ----------------------------------------------------------
# WiFi + MQTT Configuration  -- CHANGE THESE!
# ----------------------------------------------------------
WIFI_SSID      = "YourWiFi"       # Same WiFi as your computer
WIFI_PASSWORD  = "YourPassword"
BROKER_IP      = "192.168.0.88"   #computer's local IP

MQTT_CLIENT_ID = "core2_stress"
MQTT_TOPIC     = b"apan5570/core2/stress"
MQTT_PORT      = 1883

# ----------------------------------------------------------
# Stress detector configuration
# ----------------------------------------------------------
SAMPLE_RATE      = 8000
BITS_PER_SAMPLE  = 16
NUM_CHANNELS     = 1
BYTES_PER_SAMPLE = BITS_PER_SAMPLE // 8

# Detection thresholds (tune after analysing your recordings)
AUDIO_ENERGY_THRESHOLD  = 500    # RMS energy -> sound detected
MOTION_ENERGY_THRESHOLD = 0.15   # Accel variance -> motion detected

# Live detection window: 1 second of audio per cycle
DETECT_AUDIO_DURATION = 1
DETECT_AUDIO_BUF      = SAMPLE_RATE * DETECT_AUDIO_DURATION * BYTES_PER_SAMPLE

# Expected uploaded files
AUDIO_FILES  = ['baseline.wav', 'humming.wav', 'vocal_distress.wav', 'sucking_teeth.wav']
MOTION_FILES = ['shaking.csv',  'tapping.csv', 'fidgeting.csv']
ALL_FILES    = AUDIO_FILES + MOTION_FILES

# ----------------------------------------------------------
# Initialize hardware (once at boot)
# ----------------------------------------------------------
M5.begin()
Widgets.fillScreen(0x000000)

Speaker.begin()
Speaker.setVolumePercentage(0)
Speaker.end()

# ----------------------------------------------------------
# Helpers
# ----------------------------------------------------------
def show(line1, line2='', color=0xFFFFFF, bg=0x000000):
    Widgets.fillScreen(bg)
    Widgets.Label(line1, 10, 60,  1.0, color,    bg, Widgets.FONTS.DejaVu24)
    if line2:
        Widgets.Label(line2, 10, 100, 1.0, 0xCCCCCC, bg, Widgets.FONTS.DejaVu18)
    M5.update()

def rms_energy(buf):
    n     = len(buf) // 2
    total = 0
    for i in range(n):
        sample = struct.unpack_from('<h', buf, i * 2)[0]
        total += sample * sample
    return math.sqrt(total / n) if n > 0 else 0

def motion_variance(n_samples=25):
    mags = []
    for _ in range(n_samples):
        ax, ay, az = Imu.getAccel()
        mags.append(math.sqrt(ax*ax + ay*ay + az*az))
        time.sleep_ms(20)
    mean = sum(mags) / len(mags)
    return sum((m - mean)**2 for m in mags) / len(mags)

LEVEL_COLORS = {
    0: (0x002200, 0x00FF00, 'No stress detected', 'Continue'),
    1: (0x221100, 0xFFAA00, 'Stress Level 1',     'Signs of fatigue'),
    2: (0x110022, 0xCC44FF, 'Stress Level 2',     'Declining attention'),
    3: (0x220000, 0xFF2222, 'Stress Level 3',     'Break recommended'),
}

def show_stress_level(level):
    bg, fg, title, subtitle = LEVEL_COLORS[level]
    Widgets.fillScreen(bg)
    Widgets.Label(title,    10, 40,  1.0, fg,       bg, Widgets.FONTS.DejaVu24)
    Widgets.Label(subtitle, 10, 80,  1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
    filled = '=' * (level * 7)
    bar_str = '[' + filled + ' ' * (21 - len(filled)) + ']'
    Widgets.Label(bar_str,  10, 120, 1.0, fg,       bg, Widgets.FONTS.DejaVu18)
    M5.update()

# ===========================================================
# PHASE 1: FILE VERIFICATION  (runs once)
# ===========================================================
show('STRESS DETECTOR', 'Yaritza & Felice', 0x00CCFF)
time.sleep(2)

show('Checking files...', '/flash/', 0xFFFF00)
time.sleep(1)

missing = []
for fname in ALL_FILES:
    try:
        with open('/flash/' + fname, 'rb') as f:
            pass
    except OSError:
        missing.append(fname)

if missing:
    Widgets.fillScreen(0x220000)
    Widgets.Label('MISSING FILES:', 10, 10, 1.0, 0xFF4444, 0x220000, Widgets.FONTS.DejaVu24)
    Widgets.Label('Upload to /flash/', 10, 44, 1.0, 0xFFFFFF, 0x220000, Widgets.FONTS.DejaVu18)
    y = 70
    for fname in missing:
        Widgets.Label('  ' + fname, 10, y, 1.0, 0xFF8888, 0x220000, Widgets.FONTS.DejaVu18)
        y += 22
    Widgets.Label('Then re-run script', 10, y + 4, 1.0, 0xFFFF00, 0x220000, Widgets.FONTS.DejaVu18)
    M5.update()
    raise SystemExit('Missing files: ' + ', '.join(missing))

Widgets.fillScreen(0x000000)
Widgets.Label('FILES FOUND',       10, 10,  1.0, 0x00FF00, 0x000000, Widgets.FONTS.DejaVu24)
Widgets.Label('Files in /flash/:', 10, 44,  1.0, 0xFFFFFF, 0x000000, Widgets.FONTS.DejaVu18)
y = 66
for fname in AUDIO_FILES:
    Widgets.Label('+ ' + fname, 10, y, 1.0, 0x88FFCC, 0x000000, Widgets.FONTS.DejaVu18)
    y += 22
for fname in MOTION_FILES:
    Widgets.Label('+ ' + fname, 10, y, 1.0, 0xCC88FF, 0x000000, Widgets.FONTS.DejaVu18)
    y += 22
M5.update()
time.sleep(2)

# ===========================================================
# PHASE 2: WiFi CONNECTION  (runs once)
# ===========================================================
show('Connecting WiFi...', WIFI_SSID, 0xFFFF00)
time.sleep(2)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
time.sleep(1)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 20
while not wlan.isconnected() and timeout > 0:
    show('Connecting WiFi...', str(timeout) + 's remaining', 0xFFFF00)
    time.sleep(1)
    timeout -= 1

if not wlan.isconnected():
    show('WiFi Failed!', 'Check SSID/password', 0xFF2222, 0x220000)
    raise SystemExit('WiFi connection failed')

ip = wlan.ifconfig()[0]
show('WiFi Connected!', ip, 0x00FF00)
time.sleep(2)

# ===========================================================
# PHASE 3: MQTT CONNECTION  (runs once)
# ===========================================================
show('Connecting MQTT...', BROKER_IP, 0xFFAA00)
try:
    mqtt_client = MQTTClient(MQTT_CLIENT_ID, BROKER_IP, MQTT_PORT)
    mqtt_client.connect()
except Exception as e:
    show('MQTT Error!', str(e), 0xFF2222, 0x220000)
    raise SystemExit('MQTT connection failed: ' + str(e))

show('MQTT Connected!', 'Topic: ' + MQTT_TOPIC.decode(), 0x00FF00)
time.sleep(2)

# ===========================================================
# PHASE 4: LIVE DETECTION LOOP  (loops forever)
# ===========================================================
# Samples audio + motion every cycle, classifies stress 0-3,
# updates the display, and publishes to MQTT immediately.
#
# If MQTT drops, one reconnect is attempted in-place so the
# loop never stops -- display keeps updating even if the
# broker is temporarily unreachable.
# ===========================================================

show('DETECTION MODE', 'Live monitoring...', 0x00CCFF)
time.sleep(1)

count = 0

while True:
    M5.update()

    # --- Audio sample (1 second) ---
    audio_buf = bytearray(DETECT_AUDIO_BUF)
    Mic.begin()
    Mic.record(audio_buf, SAMPLE_RATE, False)
    while Mic.isRecording():
        M5.update()
        time.sleep_ms(20)
    Mic.end()

    energy = rms_energy(audio_buf)

    # --- Motion sample (~0.5 s) ---
    mv = motion_variance(n_samples=25)

    # --- Classify stress level ---
    sound_detected  = energy > AUDIO_ENERGY_THRESHOLD
    motion_detected = mv     > MOTION_ENERGY_THRESHOLD

    if sound_detected and motion_detected:
        level = 3
    elif motion_detected:
        level = 2
    elif sound_detected:
        level = 1
    else:
        level = 0

    # --- Update display immediately ---
    show_stress_level(level)

    # --- Build and publish JSON to MQTT ---
    msg = (
        '{"device":"core2"'
        + ',"stress_level":' + str(level)
        + ',"sound":'        + ('true' if sound_detected  else 'false')
        + ',"motion":'       + ('true' if motion_detected else 'false')
        + ',"energy":'       + '{:.2f}'.format(energy)
        + ',"motion_var":'   + '{:.4f}'.format(mv)
        + ',"count":'        + str(count)
        + '}'
    )

    try:
        mqtt_client.publish(MQTT_TOPIC, msg.encode())
    except Exception:
        # MQTT dropped -- attempt one silent reconnect and continue
        try:
            mqtt_client = MQTTClient(MQTT_CLIENT_ID, BROKER_IP, MQTT_PORT)
            mqtt_client.connect()
            mqtt_client.publish(MQTT_TOPIC, msg.encode())
        except Exception:
            pass   # display keeps updating even if broker unreachable

    count += 1

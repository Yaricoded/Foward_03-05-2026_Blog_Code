# ============================================================
# APAN 5570 – Group Project
# Core2 Stress Signal Detector
# AWS IoT Core Upload Version
# One-Hour Study Session + Streamlit Dashboard Version
# ============================================================
# This version sends data directly to AWS IoT Core.
# It does NOT use a local Mosquitto/MQTT broker IP.
#
# Main output logic:
#   Level 0 = No Stress Detected: Continue
#   Level 1 = Signs of Fatigue Warning
#   Level 2 = Declining Attention Warning
#   Level 3 = Alert! Break Recommended
#
# Session logic:
#   - User presses BtnA to start a study session
#   - Session runs for 1 hour
#   - Each MQTT message includes:
#       session_id
#       session_elapsed_seconds
#       session_elapsed_minutes
#       session_remaining_seconds
#       session_remaining_minutes
#       session_duration_seconds
#   - After 1 hour, Core2 shows TAKE A BREAK and sends a final message
#
# AWS IoT topic:
#   apan5570/core2/stress
# ============================================================

import os
import sys
import io
import M5
from M5 import *
from umqtt.simple import MQTTClient
import network
import time
import struct
import math

try:
    import ntptime
except Exception:
    ntptime = None

# ----------------------------------------------------------
# WiFi Configuration
# ----------------------------------------------------------
WIFI_SSID = "Columbia University"
WIFI_PASSWORD = ""

# ----------------------------------------------------------
# AWS IoT Core Configuration
# ----------------------------------------------------------
AWS_ENDPOINT = "a2720igu64prx8-ats.iot.us-east-1.amazonaws.com"
AWS_PORT = 8883
CLIENT_ID = "Core2_Project"
AWS_TOPIC = b"apan5570/core2/stress"

ROOT_CA_PATH = "/flash/certificate/AmazonRootCA1.pem"
CERT_PATH = "/flash/certificate/device_cert.pem.crt"
KEY_PATH = "/flash/certificate/private_key.pem.key"

# ----------------------------------------------------------
# Study Session Configuration
# ----------------------------------------------------------
SESSION_DURATION_SECONDS = 60 * 60   # 1 hour

# For quick testing/demo, temporarily use this instead:
# SESSION_DURATION_SECONDS = 2 * 60   # 2 minutes

SESSION_STATUS_WAITING = "waiting"
SESSION_STATUS_RUNNING = "running"
SESSION_STATUS_COMPLETE = "complete"

# ----------------------------------------------------------
# Stress Detector Configuration
# ----------------------------------------------------------
SAMPLE_RATE = 8000
BITS_PER_SAMPLE = 16
NUM_CHANNELS = 1
BYTES_PER_SAMPLE = BITS_PER_SAMPLE // 8

# Tune these after testing.
AUDIO_ENERGY_THRESHOLD = 500
MOTION_ENERGY_THRESHOLD = 0.15

# These define the value that counts as 100%.
# If values are too sensitive or too weak, adjust these.
AUDIO_ENERGY_MAX = AUDIO_ENERGY_THRESHOLD * 3
MOTION_ENERGY_MAX = MOTION_ENERGY_THRESHOLD * 3

# 1 second audio window.
DETECT_AUDIO_DURATION = 1
DETECT_AUDIO_BUF = SAMPLE_RATE * DETECT_AUDIO_DURATION * BYTES_PER_SAMPLE

# Expected uploaded demo/training files.
AUDIO_FILES = [
    "baseline.wav",
    "humming.wav",
    "vocal_distress.wav",
    "sucking_teeth.wav"
]

MOTION_FILES = [
    "shaking.csv",
    "tapping.csv",
    "fidgeting.csv"
]

CERT_FILES = [
    ROOT_CA_PATH,
    CERT_PATH,
    KEY_PATH
]

ALL_FILES = AUDIO_FILES + MOTION_FILES

# ----------------------------------------------------------
# Initialize Hardware
# ----------------------------------------------------------
M5.begin()
Widgets.fillScreen(0x000000)

Speaker.begin()
Speaker.setVolumePercentage(0)
Speaker.end()

# ----------------------------------------------------------
# Display Helper
# ----------------------------------------------------------
def show(line1, line2="", color=0xFFFFFF, bg=0x000000):
    Widgets.fillScreen(bg)
    Widgets.Label(line1, 10, 60, 1.0, color, bg, Widgets.FONTS.DejaVu24)

    if line2:
        Widgets.Label(line2, 10, 100, 1.0, 0xCCCCCC, bg, Widgets.FONTS.DejaVu18)

    M5.update()

# ----------------------------------------------------------
# Utility Helpers
# ----------------------------------------------------------
def clamp(value, low, high):
    if value < low:
        return low
    elif value > high:
        return high
    else:
        return value

def current_utc_iso():
    try:
        t = time.localtime()
        return (
            str(t[0]) + "-"
            + "{:02d}".format(t[1]) + "-"
            + "{:02d}".format(t[2]) + "T"
            + "{:02d}".format(t[3]) + ":"
            + "{:02d}".format(t[4]) + ":"
            + "{:02d}".format(t[5]) + "Z"
        )
    except Exception:
        return "unknown"

def make_session_id():
    # Creates a unique ID for each study session.
    # Example: Core2_Project_2026-05-08T20:30:00Z
    return CLIENT_ID + "_" + current_utc_iso()

def format_minutes(seconds):
    minutes = seconds / 60
    return "{:.1f}".format(minutes)

def wait_for_start_button():
    Widgets.fillScreen(0x000000)
    Widgets.Label("Study Session", 10, 25, 1.0, 0x00CCFF, 0x000000, Widgets.FONTS.DejaVu24)
    Widgets.Label("Press BtnA", 10, 70, 1.0, 0xFFFFFF, 0x000000, Widgets.FONTS.DejaVu18)
    Widgets.Label("to start", 10, 100, 1.0, 0xFFFFFF, 0x000000, Widgets.FONTS.DejaVu18)
    Widgets.Label("Duration: 1 hour", 10, 130, 1.0, 0xFFFF00, 0x000000, Widgets.FONTS.DejaVu18)
    M5.update()

    while True:
        M5.update()

        try:
            if BtnA.wasPressed():
                break
        except Exception:
            # Fallback if BtnA is not available in this firmware.
            # It will start automatically after 5 seconds.
            time.sleep(5)
            break

        time.sleep_ms(100)

def show_session_countdown(remaining_seconds):
    remaining_minutes = remaining_seconds / 60

    Widgets.fillScreen(0x000000)
    Widgets.Label("Session Starting", 10, 45, 1.0, 0x00CCFF, 0x000000, Widgets.FONTS.DejaVu24)
    Widgets.Label("Time left:", 10, 90, 1.0, 0xFFFFFF, 0x000000, Widgets.FONTS.DejaVu18)
    Widgets.Label("{:.1f} min".format(remaining_minutes), 10, 120, 1.0, 0xFFFF00, 0x000000, Widgets.FONTS.DejaVu24)
    M5.update()

# ----------------------------------------------------------
# Audio Helpers
# ----------------------------------------------------------
def rms_energy(buf):
    n = len(buf) // 2
    total = 0

    for i in range(n):
        sample = struct.unpack_from("<h", buf, i * 2)[0]
        total += sample * sample

    if n > 0:
        return math.sqrt(total / n)
    else:
        return 0

def zero_crossing_rate(buf):
    n = len(buf) // 2

    if n <= 1:
        return 0

    crossings = 0
    prev = struct.unpack_from("<h", buf, 0)[0]

    for i in range(1, n):
        current = struct.unpack_from("<h", buf, i * 2)[0]

        if (prev < 0 and current >= 0) or (prev >= 0 and current < 0):
            crossings += 1

        prev = current

    return crossings / n

def audio_percent(audio_energy):
    percent = (audio_energy / AUDIO_ENERGY_MAX) * 100
    return clamp(percent, 0, 100)

def classify_audio_signal(audio_energy, zcr):
    # This is a simple heuristic label.
    # It is not a trained audio classifier.

    if audio_energy <= AUDIO_ENERGY_THRESHOLD:
        return "none"

    if zcr < 0.05:
        return "possible_humming"

    elif zcr < 0.18:
        return "possible_vocal_distress"

    else:
        return "possible_sucking_teeth_or_sharp_sound"

# ----------------------------------------------------------
# Motion Helpers
# ----------------------------------------------------------
def motion_variance(n_samples=25):
    mags = []

    for _ in range(n_samples):
        ax, ay, az = Imu.getAccel()
        mag = math.sqrt(ax * ax + ay * ay + az * az)
        mags.append(mag)
        time.sleep_ms(20)

    mean = sum(mags) / len(mags)
    variance = sum((m - mean) ** 2 for m in mags) / len(mags)

    return variance

def motion_percent(motion_var):
    percent = (motion_var / MOTION_ENERGY_MAX) * 100
    return clamp(percent, 0, 100)

def classify_motion_signal(motion_var):
    # This is a simple heuristic label.
    # Tune ranges after observing live values.

    if motion_var <= MOTION_ENERGY_THRESHOLD:
        return "none"

    elif motion_var < MOTION_ENERGY_THRESHOLD * 1.5:
        return "possible_fidgeting"

    elif motion_var < MOTION_ENERGY_THRESHOLD * 2.5:
        return "possible_tapping"

    else:
        return "possible_shaking"

# ----------------------------------------------------------
# Per-Level Decision Logic
# ----------------------------------------------------------
def classify_stress_level(audio_pct, motion_pct):
    audio_detected = audio_pct >= 35
    motion_detected = motion_pct >= 35

    if audio_detected and motion_detected:
        return 3

    elif motion_detected:
        return 2

    elif audio_detected:
        return 1

    else:
        return 0

def combined_percent(audio_pct, motion_pct):
    # Combined Level 3 strength.
    # Uses the average of the two signals.
    return clamp((audio_pct + motion_pct) / 2, 0, 100)

def contribution_percentages(audio_pct, motion_pct):
    total = audio_pct + motion_pct

    if total <= 0:
        return 0.0, 0.0

    audio_contribution = (audio_pct / total) * 100
    motion_contribution = (motion_pct / total) * 100

    return audio_contribution, motion_contribution

# ----------------------------------------------------------
# AWS IoT Connection Helper
# ----------------------------------------------------------
def connect_aws_iot():
    with open(CERT_PATH, "rb") as f:
        cert = f.read()

    with open(KEY_PATH, "rb") as f:
        key = f.read()

    ssl_params = {
        "cert": cert,
        "key": key,
        "server_hostname": AWS_ENDPOINT
    }

    client = MQTTClient(
        client_id=CLIENT_ID,
        server=AWS_ENDPOINT,
        port=AWS_PORT,
        keepalive=60,
        ssl=True,
        ssl_params=ssl_params
    )

    client.connect()
    return client

# ----------------------------------------------------------
# Display Logic
# ----------------------------------------------------------
LEVEL_COLORS = {
    0: (0x002200, 0x00FF00, "Level 0", "No Stress Detected: Continue"),
    1: (0x221100, 0xFFAA00, "Level 1", "Signs of Fatigue Warning"),
    2: (0x110022, 0xCC44FF, "Level 2", "Declining Attention Warning"),
    3: (0x220000, 0xFF2222, "Level 3", "Alert! Break Recommended")
}

def show_stress_level(level, audio_pct, motion_pct, combined_pct, audio_label, motion_label, remaining_seconds):
    bg, fg, title, subtitle = LEVEL_COLORS[level]
    remaining_minutes = remaining_seconds / 60

    Widgets.fillScreen(bg)
    Widgets.Label(title, 10, 16, 1.0, fg, bg, Widgets.FONTS.DejaVu24)
    Widgets.Label(subtitle[:28], 10, 50, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)

    Widgets.Label("Left: " + "{:.1f}".format(remaining_minutes) + " min", 10, 78, 1.0, 0xFFFF00, bg, Widgets.FONTS.DejaVu18)

    if level == 0:
        Widgets.Label("Audio: " + "{:.0f}".format(audio_pct) + "%", 10, 108, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
        Widgets.Label("Motion: " + "{:.0f}".format(motion_pct) + "%", 10, 136, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)

    elif level == 1:
        Widgets.Label("Voice: " + "{:.0f}".format(audio_pct) + "%", 10, 108, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
        Widgets.Label(audio_label[:24], 10, 136, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)

    elif level == 2:
        Widgets.Label("Motion: " + "{:.0f}".format(motion_pct) + "%", 10, 108, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
        Widgets.Label(motion_label[:24], 10, 136, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)

    else:
        Widgets.Label("Combined: " + "{:.0f}".format(combined_pct) + "%", 10, 108, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
        Widgets.Label("Voice: " + "{:.0f}".format(audio_pct) + "%", 10, 136, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
        Widgets.Label("Motion: " + "{:.0f}".format(motion_pct) + "%", 10, 164, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)

    M5.update()

# ===========================================================
# PHASE 1: File Verification
# ===========================================================
show("STRESS DETECTOR", "AWS IoT Mode", 0x00CCFF)
time.sleep(2)

show("Checking files...", "/flash/", 0xFFFF00)
time.sleep(1)

missing = []

# Check sound and motion files.
for fname in ALL_FILES:
    try:
        with open("/flash/" + fname, "rb") as f:
            pass
    except OSError:
        missing.append("/flash/" + fname)

# Check AWS certificate files.
for cert_file in CERT_FILES:
    try:
        with open(cert_file, "rb") as f:
            pass
    except OSError:
        missing.append(cert_file)

if missing:
    Widgets.fillScreen(0x220000)
    Widgets.Label("MISSING FILES:", 10, 10, 1.0, 0xFF4444, 0x220000, Widgets.FONTS.DejaVu24)
    Widgets.Label("Upload then rerun", 10, 44, 1.0, 0xFFFFFF, 0x220000, Widgets.FONTS.DejaVu18)

    y = 70

    for fname in missing:
        Widgets.Label(fname[-26:], 10, y, 1.0, 0xFF8888, 0x220000, Widgets.FONTS.DejaVu18)
        y += 22

        if y > 210:
            break

    M5.update()
    raise SystemExit

Widgets.fillScreen(0x000000)
Widgets.Label("FILES FOUND", 10, 10, 1.0, 0x00FF00, 0x000000, Widgets.FONTS.DejaVu24)
Widgets.Label("Ready for WiFi", 10, 44, 1.0, 0xFFFFFF, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label("+ audio files", 10, 76, 1.0, 0x88FFCC, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label("+ motion files", 10, 104, 1.0, 0xCC88FF, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label("+ AWS certs", 10, 132, 1.0, 0xFFFF88, 0x000000, Widgets.FONTS.DejaVu18)
M5.update()
time.sleep(2)

# ===========================================================
# PHASE 2: WiFi Connection
# ===========================================================
show("Connecting WiFi...", WIFI_SSID, 0xFFFF00)
time.sleep(2)

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
time.sleep(1)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

timeout = 20

while not wlan.isconnected() and timeout > 0:
    show("Connecting WiFi...", str(timeout) + "s remaining", 0xFFFF00)
    time.sleep(1)
    timeout -= 1

if not wlan.isconnected():
    show("WiFi Failed!", "Check SSID/password", 0xFF2222, 0x220000)
    raise SystemExit

ip = wlan.ifconfig()[0]
show("WiFi Connected!", ip, 0x00FF00)
time.sleep(2)

# Optional NTP sync for UTC timestamp.
if ntptime is not None:
    try:
        show("Syncing time...", "NTP", 0xFFFF00)
        ntptime.settime()
        show("Time synced", current_utc_iso(), 0x00FF00)
        time.sleep(1)
    except Exception:
        show("NTP skipped", "timestamp approximate", 0xFFAA00)
        time.sleep(1)

# ===========================================================
# PHASE 3: AWS IoT Core Connection
# ===========================================================
show("Connecting AWS IoT...", AWS_ENDPOINT, 0xFFAA00)
time.sleep(1)

try:
    aws_client = connect_aws_iot()

except Exception as e:
    show("AWS IoT Error!", str(e), 0xFF2222, 0x220000)
    raise SystemExit

show("AWS IoT Connected!", AWS_TOPIC.decode(), 0x00FF00)
time.sleep(2)

# ===========================================================
# PHASE 4: One-Hour Study Session Loop
# ===========================================================
wait_for_start_button()

session_id = make_session_id()
session_start_ms = time.ticks_ms()
count = 0

show("SESSION STARTED", "1 hour monitoring", 0x00CCFF)
time.sleep(1)

while True:
    M5.update()

    # ------------------------------------------------------
    # Session timer
    # ------------------------------------------------------
    elapsed_ms = time.ticks_diff(time.ticks_ms(), session_start_ms)
    elapsed_seconds = elapsed_ms // 1000
    elapsed_minutes = elapsed_seconds / 60

    remaining_seconds = SESSION_DURATION_SECONDS - elapsed_seconds

    if remaining_seconds < 0:
        remaining_seconds = 0

    remaining_minutes = remaining_seconds / 60

    if remaining_seconds <= 0:
        show("TAKE A BREAK", "1 hour complete", 0xFF2222, 0x220000)
        break

    # ------------------------------------------------------
    # Audio sample
    # ------------------------------------------------------
    audio_buf = bytearray(DETECT_AUDIO_BUF)

    Mic.begin()
    Mic.record(audio_buf, SAMPLE_RATE, False)

    while Mic.isRecording():
        M5.update()
        time.sleep_ms(20)

    Mic.end()

    energy = rms_energy(audio_buf)
    zcr = zero_crossing_rate(audio_buf)

    # ------------------------------------------------------
    # Motion sample
    # ------------------------------------------------------
    mv = motion_variance(n_samples=25)

    # ------------------------------------------------------
    # Convert raw features into per-level percentages
    # ------------------------------------------------------
    audio_pct = audio_percent(energy)
    motion_pct = motion_percent(mv)
    combined_pct = combined_percent(audio_pct, motion_pct)

    level = classify_stress_level(audio_pct, motion_pct)

    audio_detected = audio_pct >= 35
    motion_detected = motion_pct >= 35

    audio_label = classify_audio_signal(energy, zcr)
    motion_label = classify_motion_signal(mv)

    level_1_audio_percent = 0.0
    level_2_motion_percent = 0.0
    level_3_combined_percent = 0.0
    level_3_audio_contribution_percent = 0.0
    level_3_motion_contribution_percent = 0.0

    if level == 1:
        level_1_audio_percent = audio_pct

    elif level == 2:
        level_2_motion_percent = motion_pct

    elif level == 3:
        level_3_combined_percent = combined_pct
        level_3_audio_contribution_percent, level_3_motion_contribution_percent = contribution_percentages(audio_pct, motion_pct)

    # ------------------------------------------------------
    # Update Core2 display
    # ------------------------------------------------------
    show_stress_level(
        level,
        audio_pct,
        motion_pct,
        combined_pct,
        audio_label,
        motion_label,
        remaining_seconds
    )

    # ------------------------------------------------------
    # Build JSON message for AWS IoT Core
    # ------------------------------------------------------
    msg = (
        "{"
        + '"device_id":"Core2_Project"'
        + ',"session_id":"' + session_id + '"'
        + ',"session_status":"' + SESSION_STATUS_RUNNING + '"'
        + ',"session_elapsed_seconds":' + str(elapsed_seconds)
        + ',"session_elapsed_minutes":' + "{:.2f}".format(elapsed_minutes)
        + ',"session_remaining_seconds":' + str(remaining_seconds)
        + ',"session_remaining_minutes":' + "{:.2f}".format(remaining_minutes)
        + ',"session_duration_seconds":' + str(SESSION_DURATION_SECONDS)
        + ',"timestamp_utc":"' + current_utc_iso() + '"'
        + ',"stress_level":' + str(level)
        + ',"stress_level_label":"' + LEVEL_COLORS[level][3] + '"'

        + ',"level_1_audio_percent":' + "{:.1f}".format(level_1_audio_percent)
        + ',"level_2_motion_percent":' + "{:.1f}".format(level_2_motion_percent)
        + ',"level_3_combined_percent":' + "{:.1f}".format(level_3_combined_percent)
        + ',"level_3_audio_contribution_percent":' + "{:.1f}".format(level_3_audio_contribution_percent)
        + ',"level_3_motion_contribution_percent":' + "{:.1f}".format(level_3_motion_contribution_percent)

        + ',"audio_detected":' + ("true" if audio_detected else "false")
        + ',"motion_detected":' + ("true" if motion_detected else "false")
        + ',"detected_audio_signal":"' + audio_label + '"'
        + ',"detected_motion_signal":"' + motion_label + '"'

        + ',"audio_energy_rms":' + "{:.2f}".format(energy)
        + ',"audio_zero_crossing_rate":' + "{:.4f}".format(zcr)
        + ',"audio_energy_unit":"RMS amplitude"'
        + ',"motion_variance":' + "{:.4f}".format(mv)
        + ',"motion_variance_unit":"g^2"'
        + ',"audio_window_seconds":' + str(DETECT_AUDIO_DURATION)
        + ',"msg_count":' + str(count)
        + "}"
    )

    # ------------------------------------------------------
    # Publish to AWS IoT Core
    # ------------------------------------------------------
    try:
        aws_client.publish(AWS_TOPIC, msg.encode())

    except Exception:
        try:
            aws_client = connect_aws_iot()
            aws_client.publish(AWS_TOPIC, msg.encode())

        except Exception:
            pass

    count += 1

# ===========================================================
# PHASE 5: Session Complete Message
# ===========================================================
complete_msg = (
    "{"
    + '"device_id":"Core2_Project"'
    + ',"session_id":"' + session_id + '"'
    + ',"session_status":"' + SESSION_STATUS_COMPLETE + '"'
    + ',"session_elapsed_seconds":' + str(SESSION_DURATION_SECONDS)
    + ',"session_elapsed_minutes":' + "{:.2f}".format(SESSION_DURATION_SECONDS / 60)
    + ',"session_remaining_seconds":0'
    + ',"session_remaining_minutes":0'
    + ',"session_duration_seconds":' + str(SESSION_DURATION_SECONDS)
    + ',"timestamp_utc":"' + current_utc_iso() + '"'
    + ',"stress_level":3'
    + ',"stress_level_label":"One-hour session complete: break recommended"'
    + ',"level_1_audio_percent":0.0'
    + ',"level_2_motion_percent":0.0'
    + ',"level_3_combined_percent":100.0'
    + ',"level_3_audio_contribution_percent":0.0'
    + ',"level_3_motion_contribution_percent":0.0'
    + ',"audio_detected":false'
    + ',"motion_detected":false'
    + ',"detected_audio_signal":"none"'
    + ',"detected_motion_signal":"none"'
    + ',"audio_energy_rms":0.0'
    + ',"audio_zero_crossing_rate":0.0'
    + ',"audio_energy_unit":"RMS amplitude"'
    + ',"motion_variance":0.0'
    + ',"motion_variance_unit":"g^2"'
    + ',"audio_window_seconds":' + str(DETECT_AUDIO_DURATION)
    + ',"msg_count":' + str(count)
    + "}"
)

try:
    aws_client.publish(AWS_TOPIC, complete_msg.encode())
except Exception:
    pass

show("SESSION COMPLETE", "Break recommended", 0xFF2222, 0x220000)
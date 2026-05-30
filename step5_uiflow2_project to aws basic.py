# ============================================================
# APAN 5570 – Group Project
# Core2 Stress Signal Detector
# AWS IoT Core Upload Version
# ============================================================
# This version sends data directly to AWS IoT Core.
# It does NOT use your local Mosquitto/MQTT broker IP.
#
# Upload these sound files to /flash/:
#   baseline.wav
#   humming.wav
#   vocal_distress.wav
#   sucking_teeth.wav
#
# Upload these motion files to /flash/:
#   shaking.csv
#   tapping.csv
#   fidgeting.csv
#
# Upload these AWS certificate files to /flash/certificate/:
#   AmazonRootCA1.pem
#   device_cert.pem.crt
#   private_key.pem.key
#
# Subscribe to this topic in AWS IoT Core MQTT test client:
#   apan5570/core2/stress
# ============================================================

import M5
from M5 import *
from umqtt.simple import MQTTClient
import network
import time
import struct
import math

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
# Stress Detector Configuration
# ----------------------------------------------------------
SAMPLE_RATE = 8000
BITS_PER_SAMPLE = 16
BYTES_PER_SAMPLE = BITS_PER_SAMPLE // 8

AUDIO_ENERGY_THRESHOLD = 500
MOTION_ENERGY_THRESHOLD = 0.15

DETECT_AUDIO_DURATION = 1
DETECT_AUDIO_BUF = SAMPLE_RATE * DETECT_AUDIO_DURATION * BYTES_PER_SAMPLE

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
# Audio Energy Helper
# ----------------------------------------------------------
def rms_energy(buf):
    n = len(buf) // 2
    total = 0

    for i in range(n):
        sample = struct.unpack_from("<h", buf, i * 2)[0]
        total += sample * sample

    if n > 0:
        return math.sqrt(total / n)
    return 0

# ----------------------------------------------------------
# Motion Variance Helper
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

# ----------------------------------------------------------
# AWS IoT Connection Helper
# ----------------------------------------------------------
def connect_aws_iot():
    with open(CERT_PATH, "rb") as f:
        cert = f.read()

    with open(KEY_PATH, "rb") as f:
        key = f.read()

    with open(ROOT_CA_PATH, "rb") as f:
        root_ca = f.read()

    try:
        ssl_params = {
            "cert": cert,
            "key": key,
            "server_hostname": AWS_ENDPOINT,
            "cadata": root_ca
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

    except Exception:
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
# Stress Level Display
# ----------------------------------------------------------
LEVEL_COLORS = {
    0: (0x002200, 0x00FF00, "No stress detected", "Continue"),
    1: (0x221100, 0xFFAA00, "Stress Level 1", "Signs of fatigue"),
    2: (0x110022, 0xCC44FF, "Stress Level 2", "Declining attention"),
    3: (0x220000, 0xFF2222, "Stress Level 3", "Break recommended")
}

def show_stress_level(level):
    bg, fg, title, subtitle = LEVEL_COLORS[level]

    Widgets.fillScreen(bg)
    Widgets.Label(title, 10, 40, 1.0, fg, bg, Widgets.FONTS.DejaVu24)
    Widgets.Label(subtitle, 10, 80, 1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)

    filled = "=" * (level * 7)
    bar_str = "[" + filled + " " * (21 - len(filled)) + "]"
    Widgets.Label(bar_str, 10, 120, 1.0, fg, bg, Widgets.FONTS.DejaVu18)

    M5.update()

# ===========================================================
# PHASE 1: File Verification
# ===========================================================
show("STRESS DETECTOR", "AWS IoT Mode", 0x00CCFF)
time.sleep(2)

show("Checking files...", "/flash/", 0xFFFF00)
time.sleep(1)

missing = []

for fname in ALL_FILES:
    try:
        with open("/flash/" + fname, "rb") as f:
            pass
    except OSError:
        missing.append("/flash/" + fname)

for cert_file in CERT_FILES:
    try:
        with open(cert_file, "rb") as f:
            pass
    except OSError:
        missing.append(cert_file)

if missing:
    Widgets.fillScreen(0x220000)
    Widgets.Label("MISSING FILES:", 10, 10, 1.0, 0xFF4444, 0x220000, Widgets.FONTS.DejaVu24)
    Widgets.Label("Upload then re-run", 10, 44, 1.0, 0xFFFFFF, 0x220000, Widgets.FONTS.DejaVu18)

    y = 70
    for fname in missing:
        Widgets.Label(fname[-26:], 10, y, 1.0, 0xFF8888, 0x220000, Widgets.FONTS.DejaVu18)
        y += 22
        if y > 210:
            break

    M5.update()
    raise SystemExit("Missing files")

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
    raise SystemExit("WiFi connection failed")

ip = wlan.ifconfig()[0]
show("WiFi Connected!", ip, 0x00FF00)
time.sleep(2)

# ===========================================================
# PHASE 3: AWS IoT Core Connection
# ===========================================================
show("Connecting AWS IoT...", AWS_ENDPOINT, 0xFFAA00)
time.sleep(1)

try:
    aws_client = connect_aws_iot()
except Exception as e:
    show("AWS IoT Error!", str(e), 0xFF2222, 0x220000)
    raise SystemExit("AWS IoT connection failed")

show("AWS IoT Connected!", AWS_TOPIC.decode(), 0x00FF00)
time.sleep(2)

# ===========================================================
# PHASE 4: Live Detection Loop
# ===========================================================
show("DETECTION MODE", "Live monitoring...", 0x00CCFF)
time.sleep(1)

count = 0

while True:
    M5.update()

    audio_buf = bytearray(DETECT_AUDIO_BUF)

    Mic.begin()
    Mic.record(audio_buf, SAMPLE_RATE, False)

    while Mic.isRecording():
        M5.update()
        time.sleep_ms(20)

    Mic.end()
    energy = rms_energy(audio_buf)

    mv = motion_variance(n_samples=25)

    sound_detected = energy > AUDIO_ENERGY_THRESHOLD
    motion_detected = mv > MOTION_ENERGY_THRESHOLD

    if sound_detected and motion_detected:
        level = 3
    elif motion_detected:
        level = 2
    elif sound_detected:
        level = 1
    else:
        level = 0

    show_stress_level(level)

    msg = (
        '{"device":"core2"'
        + ',"stress_level":' + str(level)
        + ',"sound":' + ("true" if sound_detected else "false")
        + ',"motion":' + ("true" if motion_detected else "false")
        + ',"energy":' + "{:.2f}".format(energy)
        + ',"motion_var":' + "{:.4f}".format(mv)
        + ',"count":' + str(count)
        + "}"
    )

    try:
        aws_client.publish(AWS_TOPIC, msg.encode())
    except Exception:
        try:
            aws_client = connect_aws_iot()
            aws_client.publish(AWS_TOPIC, msg.encode())
        except Exception:
            pass

    count += 1

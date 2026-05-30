# ============================================================
# Core2 Stress Signal Recorder + Detector
# Records SIX 5-second audio/motion clips:
#
# SOUND-BASED (audio via SPM1423 PDM mic):
#   1. Baseline        → baseline.wav
#   1. Humming         → humming.wav
#   2. Vocal distress  → vocal_distress.wav
#   3. Sucking teeth   → sucking_teeth.wav
#
# MOTION-BASED (IMU via MPU6886 accelerometer):
#   4. Shaking         → shaking.csv
#   5. Tapping         → tapping.csv
#   6. Fidgeting       → fidgeting.csv
#
# After recording, enters live DETECTION mode and displays
# stress level on screen based on audio + motion activity:
#   Level 0 – No stress detected
#   Level 1 – Signs of fatigue     (sound signal)
#   Level 2 – Declining attention  (motion signal)
#   Level 3 – Break recommended    (sound + motion)
#
# HOW TO RUN:
#   1. Paste into UIFlow 2.x (MicroPython mode)
#   2. Click Run and follow on-screen prompts
#   3. After recording, device enters live detection mode
#   4. Download .wav and .csv files from /flash/ via file mgr
# ============================================================

import M5
from M5 import *
import time
import struct
import math

# ----------------------------------------------------------
# Configuration
# ----------------------------------------------------------
SAMPLE_RATE      = 8000   # Hz for audio recording
DURATION         = 5      # seconds per recording
BITS_PER_SAMPLE  = 16
NUM_CHANNELS     = 1      # mono
BYTES_PER_SAMPLE = BITS_PER_SAMPLE // 8
BUFFER_SIZE      = SAMPLE_RATE * DURATION * BYTES_PER_SAMPLE

# IMU polling rate for motion recording (samples per second)
IMU_RATE         = 50     # 50 Hz
IMU_SAMPLES      = IMU_RATE * DURATION

# Detection thresholds (tune after analysing your recordings)
AUDIO_ENERGY_THRESHOLD  = 500    # RMS energy above baseline → sound detected
MOTION_ENERGY_THRESHOLD = 0.15   # Accel magnitude variance → motion detected

# Live detection window
DETECT_AUDIO_DURATION   = 1      # seconds of audio to analyse per cycle
DETECT_AUDIO_BUF        = SAMPLE_RATE * DETECT_AUDIO_DURATION * BYTES_PER_SAMPLE

# ----------------------------------------------------------
# WAV header builder
def make_wav_header(sample_rate, bits_per_sample, num_channels, data_size):
    byte_rate   = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    header = struct.pack('<4sI4s',
        b'RIFF', 36 + data_size, b'WAVE')
    header += struct.pack('<4sIHHIIHH',
        b'fmt ', 16, 1,
        num_channels, sample_rate,
        byte_rate, block_align, bits_per_sample)
    header += struct.pack('<4sI', b'data', data_size)
    return header

# ----------------------------------------------------------
# Initialize hardware
M5.begin()
Widgets.fillScreen(0x000000)

# Release I2S from speaker before using mic
Speaker.begin()
Speaker.setVolumePercentage(0)
Speaker.end()

# ----------------------------------------------------------
# Display helper
def show(line1, line2='', color=0xFFFFFF, bg=0x000000):
    Widgets.fillScreen(bg)
    Widgets.Label(line1, 10, 60,  1.0, color,    bg, Widgets.FONTS.DejaVu24)
    if line2:
        Widgets.Label(line2, 10, 100, 1.0, 0xCCCCCC, bg, Widgets.FONTS.DejaVu18)
    M5.update()

# ----------------------------------------------------------
# Countdown helper
def countdown(label, seconds=3):
    for i in range(seconds, 0, -1):
        show(f'{label}', f'Starting in {i}...', 0xFFFF00)
        time.sleep(1)

# ----------------------------------------------------------
# AUDIO RECORDING
# Records DURATION seconds and saves as WAV to /flash/
def record_audio(filename, prompt_line1, prompt_line2=''):
    """Show prompt, countdown, record audio, save WAV."""
    show(prompt_line1, prompt_line2, 0x00CCFF)
    time.sleep(2)
    countdown('SOUND', 3)

    show('RECORDING...', prompt_line1, 0xFF0000)

    buf = bytearray(BUFFER_SIZE)
    Mic.begin()
    Mic.record(buf, SAMPLE_RATE, False)   # False = mono
    while Mic.isRecording():
        M5.update()
        time.sleep_ms(50)
    Mic.end()

    filepath = '/flash/' + filename
    header   = make_wav_header(SAMPLE_RATE, BITS_PER_SAMPLE, NUM_CHANNELS, len(buf))
    with open(filepath, 'wb') as f:
        f.write(header)
        f.write(buf)

    show('Saved!', filename, 0x00FF00)
    time.sleep(1)

# ----------------------------------------------------------
# MOTION RECORDING
# Polls MPU6886 at IMU_RATE for DURATION seconds,
# saves ax,ay,az,gx,gy,gz columns to CSV in /flash/
def record_motion(filename, prompt_line1, prompt_line2=''):
    """Show prompt, countdown, record IMU data, save CSV."""
    show(prompt_line1, prompt_line2, 0xCC88FF)
    time.sleep(2)
    countdown('MOTION', 3)

    show('RECORDING...', prompt_line1, 0xFF0000)

    interval_ms = 1000 // IMU_RATE
    rows = []

    for _ in range(IMU_SAMPLES):
        t0 = time.ticks_ms()
        ax, ay, az = Imu.getAccel()
        gx, gy, gz = Imu.getGyro()
        rows.append(f'{ax:.4f},{ay:.4f},{az:.4f},{gx:.4f},{gy:.4f},{gz:.4f}')
        M5.update()
        elapsed = time.ticks_diff(time.ticks_ms(), t0)
        wait    = interval_ms - elapsed
        if wait > 0:
            time.sleep_ms(wait)

    filepath = '/flash/' + filename
    with open(filepath, 'w') as f:
        f.write('ax,ay,az,gx,gy,gz\n')
        f.write('\n'.join(rows))

    show('Saved!', filename, 0x00FF00)
    time.sleep(1)

# ----------------------------------------------------------
# RMS energy of 16-bit signed PCM buffer
def rms_energy(buf):
    n      = len(buf) // 2
    total  = 0
    for i in range(n):
        sample = struct.unpack_from('<h', buf, i * 2)[0]
        total += sample * sample
    return math.sqrt(total / n) if n > 0 else 0

# ----------------------------------------------------------
# Live IMU motion magnitude
# Returns variance of accel magnitude over a short burst
def motion_variance(n_samples=25):
    mags = []
    for _ in range(n_samples):
        ax, ay, az = Imu.getAccel()
        mag = math.sqrt(ax*ax + ay*ay + az*az)
        mags.append(mag)
        time.sleep_ms(20)
    mean = sum(mags) / len(mags)
    var  = sum((m - mean)**2 for m in mags) / len(mags)
    return var

# ----------------------------------------------------------
# DETECTION DISPLAY
# Shows stress level based on audio energy + motion variance
LEVEL_COLORS = {
    0: (0x002200, 0x00FF00, 'No stress detected', 'Continue'),
    1: (0x221100, 0xFFAA00, 'Stress Level 1',     'Signs of fatigue'),
    2: (0x110022, 0xCC44FF, 'Stress Level 2',     'Declining attention'),
    3: (0x220000, 0xFF2222, 'Stress Level 3',     'Break recommended ⚠'),
}

def show_stress_level(level):
    bg, fg, title, subtitle = LEVEL_COLORS[level]
    Widgets.fillScreen(bg)
    Widgets.Label(title,    10, 40,  1.0, fg,       bg, Widgets.FONTS.DejaVu24)
    Widgets.Label(subtitle, 10, 80,  1.0, 0xFFFFFF, bg, Widgets.FONTS.DejaVu18)
    # Draw level bar
    bar_w = int((level / 3) * 220)
    # Simple text indicator since drawing API varies
    bar_str = '[' + ('=' * (level * 7)).ljust(21) + ']'
    Widgets.Label(bar_str,  10, 120, 1.0, fg,       bg, Widgets.FONTS.DejaVu18)
    M5.update()

# ===========================================================
# PHASE 1: RECORDING
#this records 7 sounds/motions

show('STRESS RECORDER', 'Yaritza & Felice', 0x00CCFF)
time.sleep(2)

# --- SOUND-BASED ---

show('PART 1 OF 7', 'SOUND: Baseline', 0x00FFCC)
time.sleep(1)
record_audio(
    'baseline.wav',
    'Record baseline sound',
    'Stay quiet 0-5 sec'
)

show('PART 2 OF 7', 'SOUND: Humming', 0x00FFCC)
time.sleep(1)
record_audio(
    'humming.wav',
    'Record humming',
    '0-5 seconds'
)

show('PART 3 OF 7', 'SOUND: Screaming / Sighing', 0x00FFCC)
time.sleep(1)
record_audio(
    'vocal_distress.wav',
    'Record vocal distress',
    'Sigh or scream 0-5 sec'
)

show('PART 4 OF 7', 'SOUND: Sucking teeth', 0x00FFCC)
time.sleep(1)
record_audio(
    'sucking_teeth.wav',
    'Record sucking teeth',
    '0-5 seconds'
)

# --- MOTION-BASED ---

show('PART 5 OF 7', 'MOTION: Shaking', 0xCC88FF)
time.sleep(1)
record_motion(
    'shaking.csv',
    'Record shaking motion',
    '0-5 seconds'
)

show('PART 6 OF 7', 'MOTION: Tapping', 0xCC88FF)
time.sleep(1)
record_motion(
    'tapping.csv',
    'Record tapping motion',
    '0-5 seconds'
)

show('PART 7 OF 7', 'MOTION: Fidgeting', 0xCC88FF)
time.sleep(1)
record_motion(
    'fidgeting.csv',
    'Record fidgeting motion',
    '0-5 seconds'
)

# ----------------------------------------------------------
# Summary before entering detection mode
# ----------------------------------------------------------
Widgets.fillScreen(0x000000)
Widgets.Label('ALL RECORDED!',    10, 20,  1.0, 0x00FF00, 0x000000, Widgets.FONTS.DejaVu24)
Widgets.Label('Files in /flash/:', 10, 60,  1.0, 0xFFFFFF, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('baseline.wav',      10, 90,  1.0, 0x88FFCC, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('humming.wav',       10, 90,  1.0, 0x88FFCC, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('vocal_distress.wav',10, 112, 1.0, 0x88FFCC, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('sucking_teeth.wav', 10, 134, 1.0, 0x88FFCC, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('shaking.csv',       10, 156, 1.0, 0xCC88FF, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('tapping.csv',       10, 178, 1.0, 0xCC88FF, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('fidgeting.csv',     10, 200, 1.0, 0xCC88FF, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('Entering detection',10, 234, 1.0, 0xFFFF00, 0x000000, Widgets.FONTS.DejaVu18)
Widgets.Label('mode in 5s...',     10, 256, 1.0, 0xFFFF00, 0x000000, Widgets.FONTS.DejaVu18)
M5.update()
time.sleep(5)

# ===========================================================
# PHASE 2: LIVE DETECTION LOOP
# Stress level logic (levels 0-3 in order):
#   No sound, no motion  → Level 0 (baseline, no stress)
#   Sound only           → Level 1 (signs of fatigue)
#   Motion only          → Level 2 (declining attention)
#   Sound + motion       → Level 3 (break recommended)
#
# Audio energy and motion variance are sampled each cycle.
# Thresholds can be tuned after reviewing your recordings
# in the Jupyter notebook (compare RMS / variance values).

show('DETECTION MODE', 'Monitoring stress...', 0x00CCFF)
time.sleep(1)

while True:
    # --- Audio sample ---
    audio_buf = bytearray(DETECT_AUDIO_BUF)
    Mic.begin()
    Mic.record(audio_buf, SAMPLE_RATE, False)
    while Mic.isRecording():
        M5.update()
        time.sleep_ms(20)
    Mic.end()

    energy = rms_energy(audio_buf)

    # --- Motion sample (runs concurrently via polling) ---
    mv = motion_variance(n_samples=25)   # ~0.5 s

    # --- Classify ---
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

    show_stress_level(level)

    # Cycle delay (tune if needed)
    time.sleep_ms(200)

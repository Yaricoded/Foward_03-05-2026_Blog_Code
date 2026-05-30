import json
import csv
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

AWS_ENDPOINT = "a2720igu64prx8-ats.iot.us-east-1.amazonaws.com"
AWS_PORT = 8883
TOPIC = "apan5570/core2/stress"

CLIENT_ID = "streamlit_logger_client"

CA_PATH = "cert/AmazonRootCA1.pem"
CERT_PATH = "cert/device_cert.pem.crt"
KEY_PATH = "cert/private_key.pem.key"

CSV_FILE = "core2_stress_messages.csv"

FIELDNAMES = [
    "received_at_utc",
    "session_id",
    "session_status",
    "session_elapsed_seconds",
    "session_elapsed_minutes",
    "session_duration_seconds",
    "device_id",
    "timestamp_utc",
    "stress_level",
    "stress_level_label",
    "level_1_audio_percent",
    "level_2_motion_percent",
    "level_3_combined_percent",
    "level_3_audio_contribution_percent",
    "level_3_motion_contribution_percent",
    "audio_detected",
    "motion_detected",
    "detected_audio_signal",
    "detected_motion_signal",
    "audio_energy_rms",
    "audio_zero_crossing_rate",
    "audio_energy_unit",
    "motion_variance",
    "motion_variance_unit",
    "audio_window_seconds",
    "msg_count",
    "raw_payload"
]


def ensure_csv_exists():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to AWS IoT Core")
        client.subscribe(TOPIC, qos=0)
        print("Subscribed to topic:", TOPIC)
    else:
        print("Failed to connect. Return code:", rc)


def on_message(client, userdata, msg):
    payload_text = msg.payload.decode("utf-8", errors="replace")
    print("Message received:", payload_text)

    received_at = datetime.now(timezone.utc).isoformat()

    try:
        data = json.loads(payload_text)
    except json.JSONDecodeError:
        data = {}

    row = {field: "" for field in FIELDNAMES}
    row["received_at_utc"] = received_at
    row["raw_payload"] = payload_text

    for key, value in data.items():
        if key in row:
            row[key] = value

    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)


def main():
    ensure_csv_exists()

    client = mqtt.Client(client_id=CLIENT_ID)

    client.tls_set(
        ca_certs=CA_PATH,
        certfile=CERT_PATH,
        keyfile=KEY_PATH
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print("Connecting to AWS IoT Core...")
    client.connect(AWS_ENDPOINT, AWS_PORT, keepalive=60)

    client.loop_forever()


if __name__ == "__main__":
    main()
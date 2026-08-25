import paho.mqtt.client as mqtt
import ssl
import json
import time

# --- HIVEMQ CONFIGURATION ---
MQTT_BROKER = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "Networking_Project"
MQTT_PASSWORD = "sciaobello"
TOPIC = "/people/events"

event = {
    "person_id": 99,
    "from_zone": "Zone_A",
    "to_zone": "Zone_B",
    "ts_send_ns": time.time_ns(),
    "confidence": 0.92
}

# Add callback to verify the publisher actually connects
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Publisher connected to HiveMQ successfully.")
    else:
        print(f"[MQTT] Publisher connection failed with code {reason_code}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="mock_publisher_123")
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect

print("Connecting Publisher to HiveMQ Cloud...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

# Wait briefly to ensure the connection completes before publishing
time.sleep(1)

payload = json.dumps(event)
# QoS 1 ensures the broker must acknowledge receipt
result = client.publish(TOPIC, payload, qos=1)

print("Waiting for broker acknowledgment...")
result.wait_for_publish() 
print(f"Mock ESP32 published to cloud: {payload}")

client.disconnect()
client.loop_stop()
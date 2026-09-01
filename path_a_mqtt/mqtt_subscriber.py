import paho.mqtt.client as mqtt
import ssl
import json
import time

# --- HIVEMQ CONFIGURATION ---
MQTT_BROKER = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "Networking_Project"
MQTT_PASSWORD = "sciaobello"
TOPIC = "/people/events/gianluca"

# VERSION2 requires reason_code and properties in the signature
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Connected to HiveMQ Cloud successfully.")
        client.subscribe(TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {reason_code}")

def on_message(client, userdata, msg):
    t_receive = time.time_ns()
    payload = msg.payload.decode()
    
    try:
        event = json.loads(payload)
        t_send = event.get("ts_send_ns", t_receive)
        latency_ms = (t_receive - t_send) / 1_000_000
        print(f"[RECV] Event: {event['from_zone']} -> {event['to_zone']} | Cloud Latency: {latency_ms:.2f} ms")
    except json.JSONDecodeError:
        print(f"[RECV Raw]: {payload}")

# Fix Deprecation Warning by using VERSION2
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to HiveMQ Cloud...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
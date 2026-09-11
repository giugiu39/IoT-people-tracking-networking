import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
import argparse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── PARSER PER IL LIVELLO DI QOS ───────────────────────────────────────────
parser = argparse.ArgumentParser(description="Subscriber MQTT con supporto QoS selezionabile")
parser.add_argument("--qos", type=int, choices=[0, 1, 2], default=0, help="Livello QoS MQTT (0, 1, o 2)")
args = parser.parse_args()

TARGET_QOS = args.qos

# ── CONFIGURAZIONE AES-GCM ─────────────────────────────────────────────────
SHARED_AES_KEY = b"Networking_IoT_Project_Key_32B!!" 
AES_GCM_CIPHER = AESGCM(SHARED_AES_KEY)

# ── CONFIGURAZIONE HIVEMQ CLOUD (Path A) ───────────────────────────────────
MQTT_BROKER = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "Networking_Project"
MQTT_PASSWORD = "sciaobello"
TOPIC = "/people/events/gianluca"

os.makedirs("edge_ai/output", exist_ok=True)

clock_offset_ns = None
msg_counter = 0

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[MQTT QoS {TARGET_QOS}] Connessione riuscita a HiveMQ Cloud.")
        # Iscrizione al topic specificando il livello di QoS target
        client.subscribe(TOPIC, qos=TARGET_QOS)
        print(f"[MQTT] Iscritto al topic {TOPIC} con QoS {TARGET_QOS}")
    else:
        print(f"[MQTT] Connessione fallita con codice {reason_code}")

def on_message(client, userdata, msg):
    global clock_offset_ns, msg_counter
    
    t_receive_ns = time.time_ns()
    msg_counter += 1
    
    try:
        raw_payload = msg.payload
        nonce = raw_payload[:12]
        ciphertext = raw_payload[12:]
        
        decrypted_data = AES_GCM_CIPHER.decrypt(nonce, ciphertext, None)
        event = json.loads(decrypted_data.decode('utf-8'))
        
        t_send_ns = event.get("ts_send_ns", t_receive_ns)
        raw_diff_ns = t_receive_ns - t_send_ns
        
        # Compensazione Clock Skew fisso al primo messaggio
        if clock_offset_ns is None:
            estimated_cloud_delay_ns = 30.0 * 1_000_000
            clock_offset_ns = raw_diff_ns - estimated_cloud_delay_ns
            print(f"\n[SYSTEM SKEW QoS {TARGET_QOS}] Clock Skew Fisso: {clock_offset_ns / 1_000_000:.2f} ms\n")

        raw_latency_ms = raw_diff_ns / 1_000_000.0
        compensated_diff_ns = raw_diff_ns - clock_offset_ns
        compensated_latency_ms = max(1.0, compensated_diff_ns / 1_000_000.0)
        
        event.pop("confidence", None)
        event["path"] = f"BLE_MQTT_QoS{TARGET_QOS}"
        event["latency_ms"] = round(compensated_latency_ms, 3)
        
        output_filename = f"edge_ai/output/events_qos{TARGET_QOS}.jsonl"
        with open(output_filename, "a") as f:
            f.write(json.dumps(event) + "\n")
            
        person_id = event.get('person_id', 'Unknown')
        from_z = event.get('from_zone', '?')
        to_z = event.get('to_zone', '?')
        
        print(f"[QoS {TARGET_QOS} - Msg #{msg_counter}] Person {person_id}: {from_z} -> {to_z} | "
              f"Latenza Grezza: {raw_latency_ms:.2f} ms | "
              f"Latenza Compensata: {compensated_latency_ms:.3f} ms")
        
    except Exception as e:
        print(f"[MQTT QoS {TARGET_QOS} Error] Errore di decifratura/parsing: {e}")

# INIZIALIZZAZIONE CLIENT MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect
client.on_message = on_message

print(f"Avvio Subscriber per test MQTT QoS {TARGET_QOS}...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

client.loop_forever()
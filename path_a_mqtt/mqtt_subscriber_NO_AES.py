import paho.mqtt.client as mqtt
import ssl
import json
import time
import os

# ── CONFIGURAZIONE HIVEMQ CLOUD (Path A - NO_AES) ───────────────────────────
MQTT_BROKER = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "Networking_Project"
MQTT_PASSWORD = "sciaobello"
TOPIC = "/people/events/gianluca"

# Assicuriamoci che la cartella di output esista
os.makedirs("edge_ai/output", exist_ok=True)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Connected to HiveMQ Cloud successfully (NO_AES).")
        client.subscribe(TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {reason_code}")

def on_message(client, userdata, msg):
    # Timestamp ad alta risoluzione
    t_receive = time.time_ns()
    
    try:
        # 1. Estrazione diretta del payload in chiaro (JSON)
        raw_payload = msg.payload
        
        # 2. Parsing del JSON ricevuto direttamente dai byte grezzi
        event = json.loads(raw_payload.decode('utf-8'))
        
        # Calcolo della latenza: differenza tra ricezione cloud e generazione sull'edge
        t_send = event.get("ts_send_ns", t_receive)
        latency_ms = (t_receive - t_send) / 1_000_000.0
        
        # 3. Formattazione e salvataggio sul file di baseline NO_AES
        event.pop("confidence", None)
        event["path"] = "BLE_MQTT"
        event["latency_ms"] = round(latency_ms, 3)
        
        with open("edge_ai/output/events_NO_AES.jsonl", "a") as f:
            f.write(json.dumps(event) + "\n")
            
        print(f"[RECV NO_AES] Event: {event['from_zone']} -> {event['to_zone']} | Cloud Latency: {latency_ms:.2f} ms")
        
    except Exception as e:
        print(f"[MQTT Error] Impossibile parsare il messaggio in chiaro: {e}")

# INIZIALIZZAZIONE CLIENT MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Credenziali e cifratura TLS per i cluster HiveMQ Cloud
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to HiveMQ Cloud (NO_AES Mode)...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Mantiene vivo il thread e gestisce le riconnessioni in automatico
client.loop_forever()
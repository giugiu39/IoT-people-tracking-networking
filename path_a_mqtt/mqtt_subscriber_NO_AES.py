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

msg_counter = 0

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Connected to HiveMQ Cloud successfully (NO_AES).")
        client.subscribe(TOPIC)
    else:
        print(
            f"[MQTT] Connection failed with code {reason_code}"
        )

def on_message(client, userdata, msg):
    global msg_counter
    
    # Timestamp di ricezione sul Mac
    receive_time_ns = time.time_ns()
    msg_counter += 1
    
    try:
        # 1. Parsing diretto del JSON in chiaro
        raw_payload = msg.payload
        event = json.loads(raw_payload.decode('utf-8'))
        
        # 2. Timestamp generato dal Raspberry
        send_time_ns = event.get(
            "ts_send_ns",
            receive_time_ns
        )
        
        # 3. Latenza end-to-end reale
        #    Raspberry -> BLE -> ESP32 -> MQTT -> HiveMQ -> Mac
        raw_diff_ns = receive_time_ns - send_time_ns
        latency_ms = raw_diff_ns / 1_000_000.0
        
        # 4. Formattazione e salvataggio
        event.pop("confidence", None)
        
        event["path"] = "BLE_MQTT_NO_AES"
        event["latency_ms"] = round(
            latency_ms,
            3
        )
        
        with open(
            "edge_ai/output/events_NO_AES.jsonl",
            "a"
        ) as f:
            f.write(
                json.dumps(event) + "\n"
            )
            
        person_id = event.get(
            "person_id",
            "Unknown"
        )
        from_z = event.get(
            "from_zone",
            "?"
        )
        to_z = event.get(
            "to_zone",
            "?"
        )
        
        print(
            f"[Msg #{msg_counter}] "
            f"Person {person_id}: "
            f"{from_z} -> {to_z} | "
            f"Latenza: {latency_ms:.3f} ms"
        )
        
    except Exception as e:
        print(
            f"[MQTT Error] "
            f"Impossibile parsare il messaggio in chiaro: {e}"
        )

# ── INIZIALIZZAZIONE CLIENT MQTT ───────────────────────────────────────────

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)

client.username_pw_set(
    MQTT_USERNAME,
    MQTT_PASSWORD
)

client.tls_set(
    tls_version=ssl.PROTOCOL_TLS
)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to HiveMQ Cloud (NO_AES Mode)...")

client.connect(
    MQTT_BROKER,
    MQTT_PORT,
    60
)

# Mantiene vivo il thread e gestisce le riconnessioni
client.loop_forever()
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

# ── GESTIONE CLOCK SKEW ────────────────────────────────────────────────────
clock_offset_ns = None
msg_counter = 0

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Connected to HiveMQ Cloud successfully (NO_AES).")
        client.subscribe(TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {reason_code}")

def on_message(client, userdata, msg):
    global clock_offset_ns, msg_counter
    
    t_receive_ns = time.time_ns()
    msg_counter += 1
    
    try:
        # 1. Parsing diretto del JSON in chiaro
        raw_payload = msg.payload
        event = json.loads(raw_payload.decode('utf-8'))
        
        t_send_ns = event.get("ts_send_ns", t_receive_ns)
        raw_diff_ns = t_receive_ns - t_send_ns
        
        # ── COMPENSAZIONE CLOCK SKEW (UNA SOLA VOLTA ALL'AVVIO) ───────────────
        if clock_offset_ns is None:
            # Baseline stimata per percorso Cloud (30.0 ms)
            estimated_cloud_delay_ns = 30.0 * 1_000_000
            clock_offset_ns = raw_diff_ns - estimated_cloud_delay_ns
            print(f"\n[SYSTEM SKEW NO_AES] Clock Skew Fisso Impostato: {clock_offset_ns / 1_000_000:.2f} ms\n")

        # ── CALCOLO LATENZE ────────────────────────────────────────────────
        raw_latency_ms = raw_diff_ns / 1_000_000.0
        compensated_diff_ns = raw_diff_ns - clock_offset_ns
        
        compensated_latency_ms = compensated_diff_ns / 1_000_000.0
        if compensated_latency_ms < 1.0:
            compensated_latency_ms = 1.0  # Soglia minima di sicurezza
        
        # 2. Formattazione e salvataggio
        event.pop("confidence", None)
        event["path"] = "BLE_MQTT_NO_AES"
        event["latency_ms"] = round(compensated_latency_ms, 3)
        
        with open("edge_ai/output/events_NO_AES.jsonl", "a") as f:
            f.write(json.dumps(event) + "\n")
            
        person_id = event.get('person_id', 'Unknown')
        from_z = event.get('from_zone', '?')
        to_z = event.get('to_zone', '?')
        
        print(f"[Msg #{msg_counter}] Person {person_id}: {from_z} -> {to_z} | "
              f"Latenza Grezza: {raw_latency_ms:.2f} ms | "
              f"Latenza Compensata: {compensated_latency_ms:.3f} ms")
        
    except Exception as e:
        print(f"[MQTT Error] Impossibile parsare il messaggio in chiaro: {e}")

# INIZIALIZZAZIONE CLIENT MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to HiveMQ Cloud (NO_AES Mode)...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Mantiene vivo il thread e gestisce le riconnessioni
client.loop_forever()
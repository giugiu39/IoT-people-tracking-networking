import paho.mqtt.client as mqtt
import ssl
import json
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── CONFIGURAZIONE AES-GCM ─────────────────────────────────────────────────
SHARED_AES_KEY = b"Networking_IoT_Project_Key_32B!!" 
AES_GCM_CIPHER = AESGCM(SHARED_AES_KEY)

# ── CONFIGURAZIONE HIVEMQ CLOUD (Path A) ───────────────────────────────────
MQTT_BROKER = "ab23ed51f0614c02b127cb1f32883fbc.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USERNAME = "Networking_Project"
MQTT_PASSWORD = "sciaobello"
TOPIC = "/people/events/gianluca"

def on_connect(client, userdata, flags, reason_code, properties):
    # Verifica che la connessione al broker sia andata a buon fine prima di iscriversi
    if reason_code == 0:
        print("[MQTT] Connected to HiveMQ Cloud successfully.")
        client.subscribe(TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {reason_code}")

def on_message(client, userdata, msg):
    # Timestamp ad alta risoluzione
    t_receive = time.time_ns()
    
    try:
        # 1. Estrazione del payload grezzo (byte crittografati)
        raw_payload = msg.payload
        
        # 2. Separazione del nonce (primi 12 byte) dal testo cifrato
        nonce = raw_payload[:12]
        ciphertext = raw_payload[12:]
        
        # 3. Decifratura AES-GCM
        decrypted_data = AES_GCM_CIPHER.decrypt(nonce, ciphertext, None)
        
        # 4. Parsing del JSON in chiaro
        event = json.loads(decrypted_data.decode('utf-8'))
        
        # Calcolo della latenza: differenza tra ricezione cloud e generazione sull'edge
        t_send = event.get("ts_send_ns", t_receive)
        latency_ms = (t_receive - t_send) / 1_000_000.0
        
        print(f"[RECV] Event: {event['from_zone']} -> {event['to_zone']} | Cloud Latency: {latency_ms:.2f} ms")
        
    except Exception as e:
        # Fallback in caso di errore di decifratura (chiave errata, dati corrotti o test in chiaro)
        print(f"[MQTT Error] Impossibile decifrare o parsare il messaggio: {e}")

# INIZIALIZZAZIONE CLIENT MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Credenziali e cifratura TLS per i cluster HiveMQ Cloud
client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
client.tls_set(tls_version=ssl.PROTOCOL_TLS)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to HiveMQ Cloud...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Mantiene vivo il thread e gestisce le riconnessioni in automatico
client.loop_forever()
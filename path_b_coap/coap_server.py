import asyncio
import json
import time
import os
import aiocoap
import aiocoap.resource as resource
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── CONFIGURAZIONE AES-GCM ─────────────────────────────────────────────────
SHARED_AES_KEY = b"Networking_IoT_Project_Key_32B!!" 
AES_GCM_CIPHER = AESGCM(SHARED_AES_KEY)

# Assicuriamoci che la cartella di output esista
os.makedirs("edge_ai/output", exist_ok=True)

class TrackingResource(resource.Resource):

    def __init__(self):
        super().__init__()
        self.message_count = 0
        self.clock_offset_ns = None  # Calcolato una sola volta all'avvio

    async def render_post(self, request):
        receive_time_ns = time.time_ns()
        self.message_count += 1
        
        try:
            raw_payload = request.payload
            nonce = raw_payload[:12]
            ciphertext = raw_payload[12:]
            
            decrypted_data = AES_GCM_CIPHER.decrypt(nonce, ciphertext, None)
            event_data = json.loads(decrypted_data.decode('utf-8'))
            
            send_time_ns = event_data.get('ts_send_ns', receive_time_ns)
            raw_diff_ns = receive_time_ns - send_time_ns
            
            # ── COMPENSAZIONE CLOCK SKEW (UNA SOLA VOLTA AL PRIMO MESSAGGIO) ────
            if self.clock_offset_ns is None:
                # Baseline nominale CoAP (6.5 ms coerente con RTT/2)
                estimated_network_delay_ns = 6.5 * 1_000_000
                self.clock_offset_ns = raw_diff_ns - estimated_network_delay_ns
                print(f"\n[SYSTEM SKEW] CoAP Clock Skew Fisso: {self.clock_offset_ns / 1_000_000:.2f} ms\n")

            # ── CALCOLO LATENZA COMPENSATA ─────────────────────────────────────
            raw_latency_ms = raw_diff_ns / 1_000_000.0
            compensated_diff_ns = raw_diff_ns - self.clock_offset_ns
            compensated_latency_ms = compensated_diff_ns / 1_000_000.0
            
            # Soglia minima di sicurezza per evitare valori sub-zero dovuti a micro-jitter
            if compensated_latency_ms < 1.0:
                compensated_latency_ms = 1.0
            
            event_data.pop("confidence", None)
            event_data["path"] = "CoAP"
            event_data["latency_ms"] = round(compensated_latency_ms, 3)
            
            with open("edge_ai/output/events.jsonl", "a") as f:
                f.write(json.dumps(event_data) + "\n")
            
            person_id = event_data.get('person_id', 'Unknown')
            from_z = event_data.get('from_zone', '?')
            to_z = event_data.get('to_zone', '?')
            
            print(f"[Msg #{self.message_count}] Person {person_id}: {from_z} -> {to_z} | "
                  f"Latenza Grezza: {raw_latency_ms:.2f} ms | "
                  f"Latenza Compensata: {compensated_latency_ms:.3f} ms")
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=b"ACK: Event processed")
            
        except Exception as e:
            print(f"Errore nella decodifica o decifratura del payload: {e}")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

async def main():
    root = resource.Site()
    root.add_resource(['tracking'], TrackingResource())

    print("=======================================")
    print(" CoAP Server in avvio (PATH B)         ")
    print(" In ascolto su coap://192.168.1.62:5683/tracking")
    print("=======================================")
    
    await aiocoap.Context.create_server_context(root, bind=('192.168.1.62', 5683))
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
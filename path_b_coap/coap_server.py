import asyncio
import json
import time
import aiocoap
import aiocoap.resource as resource
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# ── CONFIGURAZIONE AES-GCM ─────────────────────────────────────────────────
SHARED_AES_KEY = b"Networking_IoT_Project_Key_32B!!" 
AES_GCM_CIPHER = AESGCM(SHARED_AES_KEY)

class TrackingResource(resource.Resource):

    def __init__(self):
        super().__init__()
        self.message_count = 0

    async def render_post(self, request):
        # Utilizziamo i nanosecondi per una misurazione ad alta precisione
        receive_time_ns = time.time_ns() 
        self.message_count += 1
        
        try:
            # 1. Estrazione del payload grezzo (byte crittografati)
            raw_payload = request.payload
            
            # 2. Separazione del nonce (primi 12 byte) dal testo cifrato
            nonce = raw_payload[:12]
            ciphertext = raw_payload[12:]
            
            # 3. Decifratura AES-GCM
            decrypted_data = AES_GCM_CIPHER.decrypt(nonce, ciphertext, None)
            
            # 4. Parsing del JSON in chiaro
            event_data = json.loads(decrypted_data.decode('utf-8'))
            
            # Calcolo della latenza End-to-End
            send_time_ns = event_data.get('ts_send_ns', receive_time_ns)
            latency_ms = (receive_time_ns - send_time_ns) / 1_000_000.0
            
            person_id = event_data.get('person_id', 'Unknown')
            event_type = event_data.get('event', 'Unknown')
            
            print(f"[Msg #{self.message_count}] Person {person_id}: {event_type} | Latenza E2E: {latency_ms:.3f} ms")
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=b"ACK: Event processed")
            
        except Exception as e:
            print(f"Errore nella decodifica o decifratura del payload: {e}")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

async def main():
    root = resource.Site()
    root.add_resource(['tracking'], TrackingResource())

    print("=======================================")
    print(" CoAP Server in avvio (PATH B)         ")
    print(" In ascolto su coap://127.0.0.1:5683/tracking")
    print("=======================================")
    
    # Rimosso 0.0.0.0, usiamo localhost per i test in locale
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
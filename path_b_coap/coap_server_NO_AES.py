import asyncio
import json
import time
import os
import aiocoap
import aiocoap.resource as resource

# Assicuriamoci che la cartella di output esista
os.makedirs("edge_ai/output", exist_ok=True)

class TrackingResource(resource.Resource):

    def __init__(self):
        super().__init__()
        self.message_count = 0

    async def render_post(self, request):
        # Utilizziamo i nanosecondi per una misurazione ad alta precisione
        receive_time_ns = time.time_ns() # Timestamp di ricezione del messaggio
        self.message_count += 1
        
        try:
            # 1. Estrazione diretta del payload in chiaro (JSON)
            raw_payload = request.payload
            
            # 2. Parsing del JSON dai byte grezzi ricevuti
            event_data = json.loads(raw_payload.decode('utf-8'))
            
            # Calcolo della latenza End-to-End
            send_time_ns = event_data.get('ts_send_ns', receive_time_ns)
            latency_ms = (receive_time_ns - send_time_ns) / 1_000_000.0
            
            # 3. Formattazione e salvataggio sul file di baseline NO_AES
            event_data.pop("confidence", None)
            event_data["path"] = "CoAP"
            event_data["latency_ms"] = round(latency_ms, 3)
            
            with open("edge_ai/output/events_NO_AES.jsonl", "a") as f:
                f.write(json.dumps(event_data) + "\n")
            
            person_id = event_data.get('person_id', 'Unknown')
            event_type = event_data.get('event', 'Unknown')
            
            print(f"[Msg #{self.message_count}] Person {person_id}: {event_type} | Latenza E2E (NO_AES): {latency_ms:.3f} ms")
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=b"ACK: Event processed (NO_AES)")
            
        except Exception as e:
            print(f"Errore nel parsing del payload in chiaro: {e}")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

async def main():
    root = resource.Site()
    root.add_resource(['tracking'], TrackingResource())

    print("=======================================")
    print(" CoAP Server in avvio (PATH B - NO_AES)")
    print(" In ascolto su coap://127.0.0.1:5683/tracking")
    print("=======================================")
    
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import json
import time
import aiocoap
import aiocoap.resource as resource

class TrackingResource(resource.Resource):
    """Risorsa CoAP che riceve gli eventi di tracking tramite POST e calcola la latenza E2E."""

    def __init__(self):
        super().__init__()
        self.message_count = 0

    # IMPORTANTE: In aiocoap si usa il minuscolo "render_post"
    async def render_post(self, request):
        receive_time = time.time()
        self.message_count += 1
        
        try:
            payload_str = request.payload.decode('utf-8')
            event_data = json.loads(payload_str)
            
            send_time = event_data.get('timestamp', receive_time)
            latency_ms = (receive_time - send_time) * 1000
            
            person_id = event_data.get('person_id', 'Unknown')
            event_type = event_data.get('event', 'Unknown')
            
            print(f"[Msg #{self.message_count}] Person {person_id}: {event_type} | Latenza E2E: {latency_ms:.2f} ms")
            
            return aiocoap.Message(code=aiocoap.CHANGED, payload=b"ACK: Event processed")
            
        except Exception as e:
            print(f"Errore nella decodifica del payload: {e}")
            return aiocoap.Message(code=aiocoap.BAD_REQUEST)

async def main():
    root = resource.Site()
    root.add_resource(['tracking'], TrackingResource())

    print("=======================================")
    print(" CoAP Server in avvio (PATH B)         ")
    print(" In ascolto su coap://127.0.0.1:5683/tracking")
    print("=======================================")
    
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())
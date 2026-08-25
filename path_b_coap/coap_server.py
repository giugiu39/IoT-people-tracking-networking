import asyncio
import json
import time
from aiocoap import *
import aiocoap.resource as resource

class EventResource(resource.Resource):
    async def render_post(self, request):
        t_receive = time.time_ns()
        payload = request.payload.decode('utf-8')
        
        try:
            event = json.loads(payload)
            t_send = event.get("ts_send_ns", t_receive)
            latency_ms = (t_receive - t_send) / 1_000_000
            print(f"[CoAP RECV] Event: {event['from_zone']}->{event['to_zone']} | Latency: {latency_ms:.2f} ms")
        except json.JSONDecodeError:
            print(f"[CoAP RAW]: {payload}")
            
        return Message(code=CHANGED, payload=b"ACK")

async def main():
    root = resource.Site()
    root.add_resource(['events'], EventResource())
    
    await Context.create_server_context(root, bind=('0.0.0.0', 5683))
    print("CoAP Server listening on UDP 5683...")
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())